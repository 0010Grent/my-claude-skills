---
name: github-push
description: "将本地项目一键上传到 GitHub 私有仓库，或对已有仓库进行改名。自动处理 gitignore、创建仓库、提交推送、全量重命名。触发词: '/github-push', '上传到github', '推到私有仓库', '创建私有仓库并推送', '/github-push rename', '改项目名', '重命名仓库'。"
origin: custom
---

# GitHub Push Skill

将本地项目一键上传到当前 GitHub 账户的私有仓库，或对已有仓库进行改名。自动完成：检查认证 → 补全 .gitignore → 创建仓库 → 提交推送。支持全量重命名（代码引用、文档、GitHub 仓库）。

## When to Activate

- 用户说"上传到 GitHub"、"推到私有仓库"、"创建私有仓库并推送"
- 用户输入 `/github-push`
- 用户输入 `/github-push <repo-name>`
- 用户说"改项目名"、"重命名仓库"、"rename repo"
- 用户输入 `/github-push rename <new-name>`

## Commands

| Command | Action |
|---------|--------|
| `/github-push` | 使用当前目录名作为仓库名，完整推送流程 |
| `/github-push <repo-name>` | 指定仓库名，完整推送流程 |
| `/github-push rename <new-name>` | 全量重命名：代码引用 + 文档 + GitHub 仓库 + 本地目录 |

## Protocol

### Step 0: Path Decision（路径决策——在 Pre-flight 之前）

首先判断当前场景，避免对已有仓库执行全套新项目流水线：

```bash
# 0.1 检查远程仓库是否存在
git remote get-url origin 2>/dev/null && _has_origin=true || _has_origin=false

# 0.2 检查本地与远程的差异范围
if $_has_origin; then
  _branch=$(git rev-parse --abbrev-ref HEAD)
  git fetch origin $_branch 2>/dev/null
  _diff_files=$(git diff --name-only origin/$_branch 2>/dev/null | wc -l | tr -d ' ')
  echo "与远程差异文件数: $_diff_files"
fi
```

**路由判定**：

| 条件 | 路由 | 说明 |
|------|------|------|
| `origin` 已存在 | **Route A: Fast-track** | 跳过目录诊断、企业信息清洗 |
| 无 `origin` 远程仓库 | **Route B: 新项目初始化** | 走完整流水线 |

---

### Route A: Existing Repository Fast-track（已有仓库增量推送）

当 Step 0 判定为已有仓库时，不执行 Step 2.5（目录结构诊断）和 Step 3.5（企业信息清洗）。直接进入以下三步：

#### Route A Step 1: Snapshot & Diff

```bash
# 暂存当前未提交更改作为可恢复快照
git stash push -m "github-push-auto-$(date +%s)" --include-untracked 2>/dev/null || true

# 查看本地与远程的差异范围
_branch=$(git rev-parse --abbrev-ref HEAD)
git fetch origin $_branch 2>/dev/null
git diff origin/$_branch --stat

# 查看分叉关系
_merge_base=$(git merge-base HEAD origin/$_branch)
_local_head=$(git rev-parse HEAD)
_remote_head=$(git rev-parse origin/$_branch)
echo "merge_base=$_merge_base local=$_local_head remote=$_remote_head"
```

#### Route A Step 2: Divergence Strategy（分叉处理策略 ——核心改进）

根据 merge-base 结果选择策略：

```bash
_branch=$(git rev-parse --abbrev-ref HEAD)
if git merge-base --is-ancestor origin/$_branch HEAD 2>/dev/null; then
  _strategy="fast_forward"       # 本地领先，直接 push
elif git merge-base --is-ancestor HEAD origin/$_branch 2>/dev/null; then
  _strategy="behind_remote"        # 本地落后，reset 到远程再应用
else
  _strategy="diverged"             # 分叉，必须报告用户
fi
echo "Strategy: $_strategy"
```

**Fork 处理决策树**（按优先级）：

1. **fast_forward**（最常见）：远程是本地的祖先 → 恢复 stash，`git add -A`，commit，`git push`
2. **behind_remote**（远程领先）：本地是远程的祖先 → 恢复 stash，`git reset --hard origin/branch`，重新 commit，push。回滚：`git reset --hard <original_commit>`
3. **diverged**（分叉）：禁止自动 merge/rebase。必须向用户报告：
   ```
   本地与远程已分叉，差异文件：{file_list}
   请选择处理方式：
   1) rebase → git pull --rebase origin main
   2) merge → git merge origin/main
   3) exit → 退出，由你手动处理
   ```
   等待用户回复后再执行，不要擅自做主。

#### Route A Step 3: Commit & Push

```bash
# 恢复工作树
git stash pop 2>/dev/null || true

# 暂存变更（如果用户指定了特定文件如 README.md，只暂存该文件）
git add -A  # 或 git add <user-specified-files>

git commit -m "$(cat <<'EOF'
sync: 更新 {files}
EOF
)"

git push origin $(git rev-parse --abbrev-ref HEAD)
```

**Route A 禁止行为**：
- 禁止对已有仓库执行 `git pull --no-rebase`（会导致大规模合并冲突）
- 禁止在未确认差异范围的情况下自动 merge
- 禁止覆盖远程主分支 commit（非 fast-forward push）

---

### Route B: New Project Initialization（新项目初始化）

当 Step 0 判定为无远程仓库时，执行以下完整流程。标记为 `*仅 Route B*` 的步骤在已有仓库场景下跳过。

### Step 1: Pre-flight Checks

依次执行以下检查，任一失败则中止并提示用户修复：

```bash
# 1.1 检查是否在 git 仓库内
git rev-parse --is-inside-work-tree

# 1.2 检查 gh CLI 认证状态
gh auth status

# 1.3 检查是否已有远程仓库
git remote -v

# 1.4 检查是否存在本地私有文件（应在 .gitignore 中）
_PRIVATE_FILES=(
  "CLAUDE.md"
  "task.txt"
  "tasks.txt"
  "TODO.txt"
  "PLAN.md"
  "ARCHITECTURE.md"
  "tests/"
  "test/"
  "记录自建文件/"
  "notes/"
)
_found_private=()
for f in "${_PRIVATE_FILES[@]}"; do
  if [ -e "$f" ]; then
    # 检查是否已在 .gitignore 中
    if ! grep -q "^${f}$" .gitignore 2>/dev/null; then
      _found_private+=("$f")
    fi
  fi
done
```

**判定逻辑**：
- 如果已有 `origin` 远程仓库 → 提示用户"已有远程仓库 `origin`，是否要推送到现有仓库？" 等待确认
- 如果 `gh auth status` 失败 → 中止，提示用户运行 `gh auth login`
- 如果不在 git 仓库 → 自动执行 `git init`，无需用户手动操作（推送新项目是此 skill 的核心用途）
- 如果发现未忽略的私有文件 → 记录到待处理列表，Step 3 自动添加到 .gitignore

### Step 2: Resolve Repo Name

```
如果没有通过命令参数指定 repo-name:
  repo_name = 当前目录的文件夹名（basename）
如果通过参数指定:
  repo_name = 参数值
```

**中文/空格目录名处理**：
- 如果 `basename` 包含中文字符或空格，**不得**直接作为仓库名
- 必须提示用户指定 ASCII 仓库名：`目录名含中文（{basename}），请通过参数指定英文仓库名，如 /github-push my-repo-name`
- 收到用户指定的 ASCII 名后继续流程

向用户确认：
- 仓库名：`{repo_name}`（默认，可修改）
- 可见性：`private`（默认，可选 `public` 或 `internal`）
- 描述：基于项目内容自动生成英文 description，用户可修改

### Step 2.5: Directory Structure Audit（仅 Route B：新项目推送时执行）（目录结构诊断）

**在暂存文件之前**，检测是否存在单层嵌套——即仓库根目录下只有一个包含源码的子目录（Python 包），而根目录本身几乎为空。这种结构会造成 `repo/{subdir}/main.py` 冗余路径。

```bash
# 找出根目录下包含 .py 文件的直接子目录
_src_subdirs=()
for d in */; do
  [ -d "$d" ] || continue
  # 跳过常见非源码目录
  case "$d" in tests/|test/|data/|workspace/|datasets/|docs/|node_modules/|.venv/|.git/) continue;; esac
  if find "$d" -maxdepth 3 -name "*.py" | grep -q .; then
    _src_subdirs+=("${d%/}")
  fi
done
```

**判定逻辑**：
- 如果 `_src_subdirs` 只有 **1 个**子目录，且根目录下的 `.py` 文件数量 = 0（即所有源码都在子目录里）→ **警告**：
  ```
  ⚠️  检测到单层嵌套：所有 Python 源码均在 {subdir}/ 子目录中，
      推送后路径为 {repo}/{subdir}/main.py，存在冗余层级。
      建议：将 {subdir}/ 内容提升到根目录，再推送。
      是否继续提升？[Y/n]
  ```
- 用户选择 Y → 执行提升（见下方提升流程），再继续 Step 3
- 用户选择 N → 记录警告，按原结构继续推送

**提升流程**（用户确认后执行）：

```bash
# 用 git mv 保留文件历史（如已 git init）
subdir="{检测到的子目录名}"
git mv "$subdir"/* .          # 提升文件
git mv "$subdir"/.[!.]* . 2>/dev/null  # 提升隐藏文件（如有）
rmdir "$subdir" 2>/dev/null   # 删除空目录

# 检查被提升的 config.py 中是否有硬编码了 subdir 层级的路径
grep -n "parent\.parent\|/$subdir/" config.py 2>/dev/null && \
  echo "⚠️  config.py 可能含有需要同步修正的路径，请检查 _ROOT 定义"
```

提升完成后提示用户检查并修正受影响的路径引用（如 `config.py` 中的 `_ROOT`、`DATA_DIR` 等）。

### Step 3: Patch .gitignore

读取当前 `.gitignore`，检查是否缺少以下常见条目。**仅追加不存在的条目，不修改已有行**：

**必须排除（安全/隐私）**：
```
.env
*.pem
*.key
credentials.json
service-account*.json
```

**必须排除（构建产物）**：
```
node_modules/
__pycache__/
*.pyc
.venv/
venv/
```

**必须排除（运行时日志）**：
```
nohup.out
output.log
*.log
```

**必须排除（IDE/OS）**：
```
.DS_Store
.idea/
.vscode/
```

**必须排除（本地/私有文件）——所有新项目默认添加**：
```
# 本地任务和笔记文件
task.txt
tasks.txt
TODO.txt
NOTES.txt

# 本地项目指导（Claude Code 专用）
CLAUDE.md
PLAN.md
ARCHITECTURE.md

# 本地测试（不推送到远程）
tests/
test/
__tests__/
*.test.js
*.test.ts
*.test.py

# 私有文档（README.md 除外）
*.md
!README.md

# 本地记录目录（常见中文命名）
记录自建文件/
notes/
私人文件/
```

**特殊处理**：
- 如果 `.venv` 是符号链接（`ls -la .venv` 显示 `->`），确保 `.gitignore` 包含 `.venv`
- 如果项目有 `data/` 目录且包含大量生成数据，建议添加 `data/0*/` 或类似模式
- **隐私优先**：如果不确定是否应推送，先添加到 `.gitignore`，用户需要时再手动移除

**自动追加逻辑**：
```bash
# 定义必须排除的条目数组（合并所有类别）
REQUIRED_IGNORES=(
  # 安全/隐私
  ".env" "*.pem" "*.key" "credentials.json" "service-account*.json"
  # 构建产物
  "node_modules/" "__pycache__/" "*.pyc" ".venv/" "venv/" "dist/" "build/"
  # 运行时日志
  "nohup.out" "output.log" "*.log"
  # IDE/OS
  ".DS_Store" ".idea/" ".vscode/" "*.swp" "*.swo" "*~"
  # 本地私有文件
  "task.txt" "tasks.txt" "TODO.txt" "NOTES.txt"
  "CLAUDE.md" "PLAN.md" "ARCHITECTURE.md"
  "记录自建文件/" "notes/" "私人文件/"
  # 测试目录
  "tests/" "test/" "__tests__/"
  # 除README外的所有markdown（放在最后确保优先级）
  "*.md" "!README.md"
)

# 创建或读取 .gitignore
touch .gitignore

# 追加缺失的条目
_added=()
for pattern in "${REQUIRED_IGNORES[@]}"; do
  if ! grep -qF "^${pattern}$" .gitignore 2>/dev/null; then
    echo "$pattern" >> .gitignore
    _added+=("$pattern")
  fi
done

# 如果添加了除 README.md 的全局排除，确保 !README.md 在它之后
if grep -q "^\*.md$" .gitignore && ! grep -q "^!README.md$" .gitignore; then
  echo "!README.md" >> .gitignore
fi

# 报告新增的条目
if [ ${#_added[@]} -gt 0 ]; then
  echo "已自动添加到 .gitignore:"
  printf '  - %s\n' "${_added[@]}"
fi
```

追加缺失条目后，如果 `.gitignore` 有变更，需 git add 它。

### Step 3.5: Corporate Information Sanitization（仅 Route B：新项目推送时执行）（企业信息清洗）

**在暂存文件之前**，扫描整个项目目录，检测并清除与蚂蚁集团（Ant Group）相关的企业内部信息。此步骤为强制步骤，不可跳过。

#### 3.5.1 关键词列表

以下关键词用于匹配企业相关内容（不区分大小写）：

```bash
_CORP_KEYWORDS=(
  # 公司名称
  "蚂蚁" "蚂蚁集团" "蚂蚁金服" "Ant Group" "AntGroup" "Ant Financial"
  # 内部域名
  "antfin.com" "antgroup.com" "alipay.com" "mybank.cn"
  "antfin-inc.com" "ant-inc.com"
  # 内部平台/工具
  "yuque.antfin" "aone.alibaba" "def.alibaba" "antcode"
  "sofa" "oceanbase" "miniapp"
  # 内部邮箱后缀
  "@antfin.com" "@antgroup.com" "@alibaba-inc.com" "@alipay.com"
  # 产品/服务名（内部语境）
  "支付宝内部" "蚂蚁内部" "集团内部" "AIS" "蚂蚁MCP" "蚂蚁网关"
  "mpaas" "金融云" "蚂蚁云"
)
```

#### 3.5.2 扫描流程

```bash
# 排除目录
_SCAN_EXCLUDES=".git/ .venv/ venv/ __pycache__/ node_modules/ data/ .idea/ .pytest_cache/"

# 构建 grep 模式（用 | 连接所有关键词）
_pattern=$(printf '%s|' "${_CORP_KEYWORDS[@]}")
_pattern="${_pattern%|}"  # 去掉末尾 |

# 扫描所有文本文件
grep -rni --include="*.py" --include="*.md" --include="*.txt" \
  --include="*.json" --include="*.yml" --include="*.yaml" \
  --include="*.toml" --include="*.cfg" --include="*.ini" \
  --include="*.sh" --include="*.env.example" --include="*.html" \
  -E "$_pattern" . \
  | grep -v ".git/" | grep -v ".venv/" | grep -v "__pycache__/" \
  | grep -v "node_modules/" | grep -v ".idea/"
```

#### 3.5.3 分类处理

扫描结果按以下三类分别处理：

**类型 A：整文件为企业内容（删除）**

文件名或路径包含企业关键词，或文件内容 >50% 涉及企业信息的文件。

判定条件（满足任一即为 A 类）：
- 文件名包含"蚂蚁"、"antfin"、"antgroup"、"AIS"等关键词
- 文件内容主要描述企业内部工具/平台/接入流程
- 文件为企业内部手册、接入文档、对接指南

处理方式：
```bash
# 如果文件已被 git 追踪，从 git 中移除
git rm --cached "{file}" 2>/dev/null

# 如果文件未被追踪，直接删除或添加到 .gitignore
# 优先删除（推送前清理），若用户需要本地保留则添加到 .gitignore
rm -f "{file}"   # 默认删除
# 或: echo "{file}" >> .gitignore  # 用户选择本地保留时
```

向用户报告：
```
🗑️  已删除企业相关文件：
  - 其他文件/蚂蚁MCP网关接入手册.md（企业内部接入文档）
  - scripts/deploy_ais_internal.sh（内部部署脚本）
```

**类型 B：文件中混有企业引用（清洗）**

项目核心代码文件中包含少量企业相关的 URL、邮箱、注释、配置项。

处理方式：
```bash
# 替换企业内部 URL 为占位符
sed -i '' 's|https\?://[a-zA-Z0-9._-]*\.antfin\.com[^ ]*|https://your-internal-url|g' "{file}"
sed -i '' 's|https\?://[a-zA-Z0-9._-]*\.antgroup\.com[^ ]*|https://your-internal-url|g' "{file}"
sed -i '' 's|https\?://yuque\.antfin\.com[^ ]*|https://your-docs-url|g' "{file}"

# 替换企业邮箱为占位符
sed -i '' 's|[a-zA-Z0-9._-]*@antfin\.com|user@example.com|g' "{file}"
sed -i '' 's|[a-zA-Z0-9._-]*@antgroup\.com|user@example.com|g' "{file}"
sed -i '' 's|[a-zA-Z0-9._-]*@alibaba-inc\.com|user@example.com|g' "{file}"
sed -i '' 's|[a-zA-Z0-9._-]*@alipay\.com|user@example.com|g' "{file}"

# 删除整行为企业内部注释的行（如 # 蚂蚁内部XXX）
sed -i '' '/^[[:space:]]*#.*蚂蚁内部/d' "{file}"
sed -i '' '/^[[:space:]]*#.*集团内部/d' "{file}"
```

向用户报告每个文件的清洗详情。

**类型 C：.env / .env.example 中的企业配置（清洗或移除）**

处理方式：
```bash
# 检查 .env.example 中是否有企业内部 endpoint
grep -n "antfin\|antgroup\|alipay\|蚂蚁" .env.example 2>/dev/null

# 替换为通用占位符
sed -i '' 's|=.*antfin\.com.*|=https://your-api-endpoint|g' .env.example
sed -i '' 's|=.*antgroup\.com.*|=https://your-api-endpoint|g' .env.example
```

#### 3.5.4 Git 历史中的企业信息

如果企业相关文件**已经在之前的 commit 中被推送过**：

```bash
# 检查 git 历史中是否追踪过企业文件
git log --all --diff-filter=A --name-only --pretty=format: -- "*蚂蚁*" "*antfin*" "*AIS*" 2>/dev/null | sort -u
```

处理策略：
- 如果仅在最近 1-2 个未推送的 commit 中 → 用 `git rm --cached` 移除并在新 commit 中清理
- 如果已推送到远程 → **警告用户**：历史中存在企业信息，建议使用 `git filter-repo` 清理历史（提供命令但不自动执行，需用户确认）
- 警告文本：
  ```
  ⚠️  以下企业相关文件存在于 git 历史中（已推送到远程）：
    - {file_list}
  建议使用 git filter-repo 清理历史，但此操作会重写 commit，需 force-push。
  是否执行历史清理？[y/N]
  ```

#### 3.5.5 验证

清洗完成后，重新扫描确认无残留：

```bash
# 最终验证：项目中不应有任何企业关键词
grep -rni -E "$_pattern" . \
  | grep -v ".git/" | grep -v ".venv/" | grep -v "__pycache__/" \
  | grep -v "node_modules/" | grep -v ".idea/"
```

如果仍有残留，逐一处理后重新验证，直到通过。

#### 3.5.6 向用户报告

```
🔒 企业信息清洗完成

已删除文件: {delete_count} 个
  - {file1}（原因）
  - {file2}（原因）

已清洗文件: {sanitize_count} 个
  - {file3}: 替换了 {n} 处企业 URL / 邮箱
  - {file4}: 移除了 {m} 行企业内部注释

历史风险: {yes/no}
  {如有历史风险，展示具体文件和建议操作}

验证结果: ✅ 无企业信息残留
```

### Step 3.8: Auto-Generate README.md（仅 Route B，自动执行）

**触发条件**（满足任一即执行）：
- 项目根目录下不存在 `README.md`
- 用户明确说"帮我生成 README"

**跳过条件**（满足任一即跳过）：
- `README.md` 已存在且非空
- 用户说"不要生成 README"

**前置要求**：
- 必须在 Step 2（Resolve Repo Name）之后执行，确保 `repo_name` 已确定
- 必须在 Step 3.5（企业信息清洗）之后执行，确保生成内容不含企业信息
- 复用 Project Positioning Protocol 已分析出的 `style`

#### 3.8.1 提取项目元数据

```bash
# 检测主语言（用于 badge 和 Quick Start 安装命令）
_lang=""; _lang_badge=""; _install_cmd=""; _run_cmd=""
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ] || find . -maxdepth 1 -name "*.py" | grep -q .; then
  _lang="Python"
  _lang_badge="Python-3.10+-3776AB?logo=python&logoColor=white"
  [ -f "requirements.txt" ] && _install_cmd="pip install -r requirements.txt"
  [ -f "pyproject.toml" ] && _install_cmd="pip install -e ."
  _run_cmd="python"
elif [ -f "package.json" ]; then
  _lang="JavaScript"
  _lang_badge="Node.js-18+-339933?logo=node.js&logoColor=white"
  _install_cmd="npm install"
  _run_cmd="npm run"
  [ -f "vite.config.js" ] || [ -f "vite.config.ts" ] && _run_cmd="npm run dev"
elif find . -maxdepth 1 -name "*.go" | grep -q .; then
  _lang="Go"
  _lang_badge="Go-1.21+-00ADD8?logo=go&logoColor=white"
  _install_cmd="go mod download"
  _run_cmd="go run"
fi

# 检测入口文件
_entry=""
for f in "src/cli.py" "cli.py" "main.py" "app.py" "run.py" "index.js" "main.go" "cmd/main.go"; do
  [ -f "$f" ] && { _entry="$f"; break; }
done

# 检测 CLI 工具特征
_has_cli=false
if grep -q "argparse\|click\|typer" *.py 2>/dev/null || grep -q "commander\|yargs\|oclif" "*.js" 2>/dev/null || [ -f "src/cli.py" ] || [ -f "cmd/main.go" ]; then
  _has_cli=true
fi

# 检测是否已发布到 PyPI / npm
_is_package=false
[ -f "pyproject.toml" ] && grep -q "\[project\]" pyproject.toml && _is_package=true
[ -f "setup.py" ] && _is_package=true
[ -f "package.json" ] && grep -q '"name"' package.json && _is_package=true
```

#### 3.8.2 风格确认

复用 Step 2 的 Project Positioning Protocol 已分析出的 `style`（concise / technical / product / pipeline）。

**风格推断辅助规则**（当定位协议输出模糊时使用）：

| 检测特征 | 推断风格 | 描述 |
|---------|---------|------|
| `_has_cli=true` 且 `_is_package=false` | concise | CLI 小工具 |
| `_is_package=true` 且有 API/接口代码 | technical | 库/SDK |
| 存在 Web 框架引用（Flask/FastAPI/Express/Next.js） | product | 应用/服务 |
| 文件名含 `pipeline`、`stage`、`ETL`、`transform` | pipeline | 数据管线 |

#### 3.8.3 README 生成模板（FinSight 格式）

README.md 必须按以下区块生成，格式参考 `github-push` 自身的 README.md（FinSight 风格）。各区块内容根据所选风格动态填充，**默认使用全英文撰写**。

**区块 A：居中 Header + Badges**

```markdown
<div align="center">

# {_repo_name} — {按 Project Positioning Protocol 的标题公式}

*{One-line subtitle}*

<p>
  <img src="https://img.shields.io/badge/{_lang_badge}" />
  <img src="https://img.shields.io/github/license/{username}/{_repo_name}" />
  <img src="https://img.shields.io/github/last-commit/{username}/{_repo_name}" />
</p>

</div>
```

Badge 规则：最多 5 个，通用徽章（Language、License、Last Commit）前置，项目特有徽章（如 PyPI Version、CI Status）后置。不要硬凑不存在的徽章。

**区块 B：一句话定位**

按所选风格写 2-3 句话（英文）：
- What this is (项目本质)
- Why it's worth using (解决什么特定问题)
- Who should use it (目标用户或下游消费方)

**区块 C：Table of Contents**

生成标准锚点链接列表，至少包含：
- Key Features
- Quick Start
- File Structure
- License

技术型/管线型额外加入 Architecture。

**区块 D：Key Features**（4-6 项，每项带 emoji 前缀 + 一句话英文描述）

从项目代码和文件结构中推断：
- 读取 `src/` 或根目录下的 `.py`/`.js`/`.go` 文件名
- 提取核心功能模块名
- 从 `README.md` 之外的其他文档（如 `docs/`、代码注释）中提取功能描述
- **严禁编造未在代码中实际存在的功能**

| 风格 | Feature 描述侧重点 |
|------|-------------------|
| concise | Core functionality points + CLI quick calls |
| technical | Architecture characteristics, interface design, extension points |
| product | User value, usage scenarios, pain points solved |
| pipeline | Processing stages, input/output formats, quality assurance |

**区块 E：Quick Start**

```markdown
### Prerequisites

- {_lang} version requirement (inferred from pyproject.toml's requires-python or package.json's engines)
- Other hard dependencies (Pandoc, Node.js, etc., inferred from code references)

### Installation

```bash
git clone https://github.com/{username}/{_repo_name}.git
cd {_repo_name}
{_install_cmd}
```
```

**Usage 根据风格变化：**
- concise: CLI commands + parameter descriptions (parsed from argparse/click code)
- technical: import + API call code snippets
- product: Feature entry points and configuration instructions
- pipeline: Input format, run command, output directory

**区块 F：Architecture（简洁型可省略）**

使用 `<pre>` ASCII 流程图或文字描述（英文）：
- 简洁型：省略此区块，保留 File Structure
- 技术型：Module relationship diagram + key interface descriptions
- 产品型：System architecture diagram + tech stack list
- 管线型：Data flow diagram, labeling input/output for each stage

**区块 G：File Structure**

用 `tree` 符号生成项目目录树，每个目录/文件附带一行英文注释说明用途。不要只列出文件名。

```markdown
```text
{_repo_name}/
├── src/{package}/              # Core source code
│   ├── __init__.py
│   └── cli.py                  # CLI entry point
├── tests/                       # Test cases
├── docs/                        # Documentation
├── pyproject.toml              # Package configuration
└── README.md                    # Project description (this file)
```
```

**区块 H：License**

链接到仓库 LICENSE 文件：
```markdown
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
```

如果 LICENSE 不存在，提示用户创建。

#### 3.8.4 防幻觉规则

**严禁编造未在项目代码中实际存在的内容：**

| 禁止行为 | 正确做法 |
|---------|---------|
| 描述未实现的 Feature | 只列出代码中已有对应实现的模块/函数 |
| 虚构 CLI 参数 | 从 `argparse.add_argument` 或 `click.option` 代码中解析 |
| 编造 Roadmap/TODO 项 | 省略，或写"持续开发中" |
| 声称支持未测试的平台 | 不写兼容性声明 |
| 虚构评估指标/性能数据 | 不写任何未运行过的 benchmark |
| 声称有文档但实际不存在 | 不生成指向不存在文件的链接 |

**推断规则**：
- 如果某 Feature 在代码中只有函数签名但无实现体（`pass`/`...`），不计入 Key Features
- 如果 `tests/` 存在且非空，可写"包含单元测试"
- 如果 `docs/` 存在且非空，可写"提供扩展文档"
- 如果 `.env.example` 存在，Quick Start 中提示用户 `cp .env.example .env`

#### 3.8.5 写入与暂存

```bash
# 将生成的内容写入 README.md
cat > README.md << 'GENERATED_README'
{按 3.8.3 模板生成的完整内容}
GENERATED_README

echo "README.md 已自动生成（风格: {style}）"

# Stage README.md，确保在 Step 4 的 git add -A 前已纳入跟踪
git add README.md 2>/dev/null || true
```

生成后向用户展示定位分析结果：
```
📄 README.md 自动生成完成

风格: {concise|technical|product|pipeline}
推断依据: {feature1}, {feature2}, {feature3}

副本标题: {repo_name} — {定位公式}
Key Features: {n} 项（从代码推断）
```

---

### Step 4: Stage & Review

```bash
# 暂存所有文件（Step 3.8 自动生成的 README.md 已在该步骤末尾执行 git add，此处 git add -A 确保全部纳入）
git add -A

# 检查是否有符号链接被误暂存
git status -s | grep "^A" | while read line; do
  file=$(echo "$line" | awk '{print $2}')
  if [ -L "$file" ]; then
    echo "WARNING: symlink staged: $file"
  fi
done

# 查看暂存概况
git status -s
```

**符号链接处理**：
- 如果发现 `.venv` 等符号链接被暂存 → `git reset HEAD <symlink>` 并添加到 `.gitignore`
- 其他符号链接 → 提示用户确认是否应排除

### Step 5: Create GitHub Repo

```bash
gh repo create {repo_name} --{visibility} --source=. --description "{description}"
```

- `visibility` 默认 `private`
- `--source=.` 会自动添加 remote origin
- `description` 使用 Project Positioning Protocol 生成的英文一句话描述
- 如果仓库已存在同名 → 提示用户选择：换名 / 推送到已有仓库 / 中止

### Step 6: Commit

```bash
git commit -m "feat: 初始化仓库，推送项目文件

- 项目完整代码与配置
- .gitignore 安全规则补全"
```

**commit message 规则**：
- 禁止包含任何 `Co-Authored-By` 署名
- 使用 conventional commits 格式
- 首次推送用 `feat: 初始化仓库`
- 后续推送根据实际变更类型选择 `feat/fix/docs/refactor` 等

### Step 7: Push

```bash
git push -u origin main
```

如果默认分支不是 `main`（如 `master`），使用实际分支名：
```bash
current_branch=$(git branch --show-current)
git push -u origin $current_branch
```

### Step 8: Verify & Report

```bash
# 验证远程仓库
gh repo view {username}/{repo_name} --json url,isPrivate

# 验证推送成功
git log --oneline -3
git status
```

**同步更新 GitHub 仓库描述（必须执行）**：

根据 Project Positioning Protocol 中选定的风格，撰写英文描述并更新：

```bash
gh repo edit {username}/{repo_name} --description "{按所选风格撰写的一句话英文描述}"
```

验证描述已更新：

```bash
gh repo view {username}/{repo_name} --json description
```

向用户报告：
```
✅ 推送完成

仓库: https://github.com/{username}/{repo_name}
描述: {新描述内容}
可见性: private
分支: main
提交: {commit_count} 个文件

README.md: {auto_generated | 已存在未覆盖 | 用户跳过}
  风格: {concise | technical | product | pipeline}
  定位: {README 标题}
```

---

## Project Positioning Protocol（项目定位协议）

**推送或重命名时，必须先分析项目再撰写 README 标题、仓库描述和项目简介。**

### 核心原则：根据项目类型选择描述风格

不同项目适合不同的表达方式。强制用一种"引擎/管线/蒸馏"风格套在所有项目上，反而会让描述失去辨识度。根据项目规模和性质，从以下四种风格中选择最合适的一种：

| 风格 | 适合场景 | 特点 |
|------|---------|------|
| **简洁型** | 小工具、单功能脚本、CLI | 直接说清做什么，不过度包装 |
| **技术型** | 框架、库、SDK、中间件 | 强调技术机制、接口设计、架构决策 |
| **产品型** | 应用、服务、平台 | 强调用户价值、使用场景、解决什么问题 |
| **管线型** | 数据管道、训练流程、ETL | 强调数据流、处理阶段、输入输出格式 |

**关键判断**：如果一个项目本质就是一个小脚本，用简洁型；如果是一个需要别人集成使用的库，用技术型；如果是面向终端用户的应用，用产品型；如果是一连串自动化步骤的处理流程，用管线型。

### 风格模板与示例（生成 README 时默认使用英文）

#### 简洁型

标题：直接的功能陈述（英文）
```
# repo-name — {one-line functional description}

{A brief description of what this tool does}
```

示例：
```
# csv-merge — Smart CSV merger by column name

Batch merge multiple CSVs with automatic column alignment, encoding handling, and deduplicated output.
```

#### 技术型

标题：技术定位 + 关键机制（英文）
```
# repo-name — {technical category}: {core mechanism/design decision}

{Technical description focusing on architecture and design decisions}
```

示例：
```
# async-cache — Async caching middleware: TTL-based tiered fallback strategy

Caching abstraction layer for asyncio applications with memory → Redis → source three-tier fallback, handling race conditions and cascade invalidation automatically.
```

#### 产品型

标题：用户价值 + 核心场景（英文）
```
# repo-name — {target user}'s {scenario} solution

{Product description focusing on user value and pain points solved}
```

示例：
```
# invoice-parser — Automated PDF invoice extraction for finance teams

Extract structured invoice data from scanned PDFs and import directly into ERP systems, reducing manual entry time and error rates.
```

#### 管线型

标题：领域 + 数据流定位（英文）
```
# repo-name — {domain} {pipeline type}: {key stages}

{Pipeline description showing data flow through each stage}
```

示例：
```
# finforge — Financial domain corpus synthesis pipeline: distill → QC → iterate

From exam outlines through teacher model distillation, multi-dimensional purity verification, and multi-round self-optimization to produce high-purity seed datasets ready for fine-tuning.
```

### README 撰写要求

根据所选风格，README 按以下结构组织，**所有内容默认使用英文撰写**：

#### 1. 标题行

`# ProjectName — {按所选风格的英文标题模板}`

标题直接反映项目本质，使用英文撰写，不刻意包装也不过度谦虚。

#### 2. 一句话定位（标题下方第一段，英文）

用 2-3 句话说明：
- **What this is** (项目本质)
- **Why it's worth using** (比同类方案好在哪里，或解决了什么特定问题)
- **Who should use it** (目标用户或下游消费方)

#### 3. "Why We Need This" 段落（英文）

回答项目存在的技术或业务理由。根据风格选择侧重点：
- **简洁型**: What's inconvenient about existing tools, what gap this tool fills
- **技术型**: Trade-offs behind technical choices, why this architecture was selected
- **产品型**: Current user pain points, what happens without this solution
- **管线型**: Data quality issues, workflow gaps, scaling bottlenecks

#### 4. 架构/流程图（英文标注）

按 README Visual Enhancement 规范（见下文）绘制。形式根据项目复杂度选择：
- 简单项目：英文文字描述即可，不必强画流程图
- 有明确阶段的项目：用 `<pre>` 文本图或 Mermaid（如果确定主要在亮色主题下浏览）
- 复杂架构：建议生成 HTML 可视化文件（skill 可辅助生成）

#### 5. 核心机制/使用方式（英文）

- **技术型**: API design approach, key abstractions, extension points
- **产品型**: Core features, usage scenarios, quick start
- **管线型**: Data flow explanation, technical motivation for each stage, output formats
- **简洁型**: Installation method, CLI usage, parameter descriptions

#### 6. 产出物说明（管线型项目必须，英文）

明确数据结构、输出格式、下游使用方式。

### 仓库描述（--description）格式

仓库描述不是 README 的缩略版，而是搜索结果中的"一句话广告"。按所选风格撰写，**默认使用英文**：

```bash
# 简洁型 (concise)
gh repo edit --description "{One-line functional description}"

# 技术型 (technical)
gh repo edit --description "{Technical category}: {Core mechanism}"

# 产品型 (product)
gh repo edit --description "{Problem solved} for {Target user}"

# 管线型 (pipeline)
gh repo edit --description "{Domain} {pipeline type}: {Key stages}"
```

描述中避免出现以下空洞修饰词（除非有具体指标支撑）：
- "intelligent / smart / 智能的"（什么指标证明？）
- "efficient / high-performance / 高效的"（和什么比？快多少？）
- "fully automated / 全自动的"（哪个环节还需要人工介入？）
- "AI-powered / 基于 AI 的"（具体用了什么模型/算法？）

### 重命名时的 README 同步

执行 `/github-push rename` 时，按以下清单同步更新：

1. **重写 README 标题**——根据新名称的语义重新选择合适的风格模板
2. **更新 CLI/入口描述**——`argparse.ArgumentParser(description=...)` 或 `__doc__` 中的项目简介
3. **更新所有 docstring/注释中的项目名**——搜索第一条 docstring 或模块注释中的定位句
4. **更新 GitHub 仓库描述**——按上述格式重新撰写
5. **如果在代码中有硬编码的项目定位**，同步更新（如 `config.py` 中的 `PROJECT_DESCRIPTION`）

---

## Rename Protocol

当用户执行 `/github-push rename <new-name>` 时，执行全量重命名流程。

### Step R1: 确定旧名和新名

```
old_name = 当前 Python 包名 / 项目名（从代码中推断）
new_name = 用户指定的 new-name
```

**推断旧名的方法**（按优先级）：
1. 目录中包含 `__init__.py` 的包目录名
2. Python 文件中 `from xxx import` 的最常见包名前缀
3. 当前目录的 `basename`

**向用户确认**：
- 旧名：`{old_name}`（自动检测，可修改）
- 新名：`{new_name}`
- 重命名范围：代码引用 + 文档 + 定位措辞 + GitHub 仓库 + 本地目录

### Step R2: 影响分析

搜索所有受影响的文件和引用点：

```bash
# 搜索代码和文档中的旧名引用
grep -rn "{old_name}" --include="*.py" --include="*.md" --include="*.txt" \
  --include="*.json" --include="*.yml" --include="*.yaml" .
```

**分类统计**：
1. **Python import 语句**：`from {old_name}.xxx import`
2. **Python docstring / 注释**：文档字符串中的项目名
3. **CLI 描述**：`argparse.ArgumentParser(description=...)`
4. **Markdown 文档**：README、CLAUDE.md 等
5. **文件名**：包含旧名的文件（如 `INFRASTRUCTURE_PATTERNS({old_name}).md`）
6. **配置文件**：`.env` 中的注释、`requirements.txt` 等

**排除**：
- `data/` 目录下的运行时输出文件（评估报告等）—— 这些是历史数据，不应修改
- `.git/` 目录
- `.venv/` 目录

向用户展示影响范围，确认后继续。

### Step R3: 执行重命名

按照以下顺序执行，确保每步可回退：

**3.1 替换 Python 源文件中的引用**

```bash
# 批量替换（适用于所有 .py 文件）
find . -name "*.py" -not -path "./.venv/*" -not -path "./.git/*" \
  -exec sed -i '' 's/{old_name}/{new_name}/g' {} +
```

**3.2 替换文档中的引用**

```bash
# Markdown 和其他文本文件
sed -i '' 's/{old_name}/{new_name}/g' README.md CLAUDE.md PLAN.md
```

**3.3 执行定位迁移**

按照 **Project Positioning Protocol** 中的"重命名时的定位迁移"清单执行：
- 重写 README 标题和一句话定位
- 更新 CLI description
- 更新所有 docstring 中的项目定位句
- 更新 GitHub 仓库描述
- 搜索并替换措辞降级词汇

**3.4 重命名文件**

```bash
# 重命名包含旧名的文件
mv "INFRASTRUCTURE_PATTERNS({old_name}).md" "INFRASTRUCTURE_PATTERNS({new_name}).md"
# 以及其他包含旧名的文件
```

**3.5 替换文件内部引用**

对重命名的文件，更新其内部的旧名引用：

```bash
sed -i '' 's/{old_name}/{new_name}/g' "INFRASTRUCTURE_PATTERNS({new_name}).md"
```

### Step R4: 验证替换

```bash
# 验证源码和文档中无残留引用（排除 data/ 目录）
grep -rn "{old_name}" --include="*.py" --include="*.md" --include="*.txt" . \
  | grep -v ".git/" | grep -v ".venv/" | grep -v "data/"
```

如果发现残留引用，逐一修复。

### Step R5: 重命名 GitHub 仓库

```bash
# 使用 gh CLI 重命名
gh repo rename {new_name} --yes
```

**重命名后**：
- GitHub 会自动设置从旧名到新名的重定向（持续一段时间）
- 需要更新本地 remote URL，**必须先检测当前协议，保持一致**：

```bash
# 检测当前 remote URL 协议（SSH 或 HTTPS），不能硬编码
_current_url=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$_current_url" == git@* ]]; then
  git remote set-url origin "git@github.com:{username}/{new_name}.git"
else
  git remote set-url origin "https://github.com/{username}/{new_name}.git"
fi

# 验证新 URL 可达
git ls-remote --exit-code origin HEAD > /dev/null 2>&1 || \
  echo "⚠️  remote URL 验证失败，请手动检查: git remote -v"
```

同时更新仓库描述（按 Project Positioning Protocol 格式，使用英文）：

```bash
gh repo edit {new_name} --description "{Domain}: {Core mechanism / One-line description}"
```

### Step R6: 提交并推送

```bash
git add -A
git commit -m "refactor: rename project from {old_name} to {new_name}

- Package: {old_name} → {new_name}
- CLI: python -m {new_name}.cli
- Branding: {新定位公式}
- GitHub repo: {username}/{new_name}"
git push -u origin {branch}
```

### Step R7: 报告

向用户报告：
```
✅ 重命名完成

包名: {old_name} → {new_name}
仓库: https://github.com/{username}/{new_name}
描述: [新定位公式]
变更文件: {count} 个
替换引用: {old_name} → {new_name}（代码 + 文档 + 定位措辞 + 文件名）
```

---

## Error Handling

| 错误 | 处理方式 |
|------|----------|
| `gh auth status` 失败 | 中止，提示 `gh auth login` |
| 不在 git 仓库 | 自动执行 `git init`，继续流程 |
| 仓库同名已存在 | 询问用户：换名 / 推送到已有 / 中止 |
| `.gitignore` 缺少安全规则 | 自动补全，告知用户追加了哪些条目 |
| 符号链接被暂存 | 自动 unstage 并添加到 .gitignore |
| push 被拒绝（remote 有更新） | 提示用户先 `git pull --rebase` |
| 目录名含中文/空格 | 要求用户通过参数指定 ASCII 仓库名 |
| SSH 协议不可用 | 切换 HTTPS：`gh config set git_protocol https` |
| 重命名后 remote URL 失效 | 检测当前协议（SSH/HTTPS），用同协议重设 URL |
| grep 发现残留引用 | 逐一修复后重新验证 |
| `gh repo rename` 失败 | 检查仓库权限，可能需要手动在 GitHub 网页重命名 |
| 企业信息扫描发现残留 | 逐一清洗后重新验证，直到扫描通过 |
| 企业文件已存在于 git 历史 | 警告用户，提供 `git filter-repo` 命令但不自动执行 |
| 企业 URL 嵌在代码逻辑中（非注释） | 替换为占位符后提示用户检查功能是否受影响 |

## Anti-Patterns

- **禁止**在 `.gitignore` 未补全安全规则的情况下推送
- **禁止**推送包含 `.env`、API key、密码等敏感文件的提交
- **禁止** force-push 到已有远程仓库
- **禁止**自动修改用户已有的 `.gitignore` 规则（只追加不修改）
- **禁止** commit message 包含 AI 署名（Co-Authored-By）
- **禁止**修改 `data/` 目录下的运行时输出文件（历史数据不应被重命名影响）
- **禁止**跳过验证步骤直接推送（重命名后必须 grep 确认无残留引用）
- **禁止**强制所有项目套用统一的"引擎/管线/蒸馏"风格——应根据项目类型选择简洁型、技术型、产品型或管线型
- **禁止**在仓库描述中使用无具体指标支撑的空洞修饰词（"智能""高效""全自动"）
- **禁止**推送 CLAUDE.md、task.txt、tests/、记录自建文件/ 等本地私有文件
- **禁止**推送除 README.md 外的其他 Markdown 文件（如 PLAN.md、ARCHITECTURE.md、INFRASTRUCTURE_PATTERNS.md 等）
- **禁止**直接使用中文或含空格的目录名作为 GitHub 仓库名（必须要求用户指定 ASCII 名）
- **禁止**在 Step 2.5 诊断出单层嵌套后跳过警告直接推送（必须告知用户并等待确认）
- **禁止**对已有仓库执行全套新项目检查——仓库已存在时必须走 Route A Fast-track，跳过目录诊断和企业信息清洗
- **禁止**对已有仓库自动执行 `git pull --no-rebase`——可能引发大规模合并冲突
- **禁止**在分叉未确认范围时自动 merge/rebase——必须先报告差异再等待用户选择
- **禁止**重命名后硬编码 SSH 或 HTTPS 协议重设 remote URL（必须检测当前协议后保持一致）
- **禁止**推送包含蚂蚁集团（Ant Group）企业内部信息的文件——包括内部手册、内部 URL（`*.antfin.com`、`*.antgroup.com`）、内部邮箱（`@antfin.com`）、内部工具名称等
- **禁止**跳过 Step 3.5 企业信息清洗步骤直接进入暂存
- **禁止**在未完成企业信息验证扫描的情况下执行 commit 和 push
- **禁止**推送后不执行 `gh repo edit --description` 同步更新 GitHub 仓库描述（每次推送必须更新，且默认使用英文）
- **禁止**自动生成 README 时编造未在代码中实际存在的功能、特性或评估指标——所有 Key Features 必须在源码中有对应实现
- **禁止**在 `README.md` 已存在且用户未明确要求的情况下自动覆盖已有 README
- **禁止**为未实现的特性在 README 的 Roadmap 中写 TODO 项（可以写"持续开发中"或直接省略）
- **禁止**自动生成 README 时声称项目支持未实际测试的平台或未安装的依赖
- **禁止**在自动生成 README 的 File Structure 中列出不存在或已废弃的文件/目录

## README Visual Enhancement（可视化增强）

README 的视觉层次直接影响第一印象。通过 badges、banner、流程图和徽章系统，让项目在一众纯文本 README 中脱颖而出。

### Badges / Shields

README 顶部应在标题下方放置一行 badges，使用 [shields.io](https://shields.io) 动态生成。

**推荐徽章组合**

| 徽章 | URL 模板 | 适用条件 |
|------|----------|----------|
| **Language** | `https://img.shields.io/badge/Python-3.11-blue` | 所有项目，标明主语言版本 |
| **License** | `https://img.shields.io/github/license/{user}/{repo}` | 有 LICENSE 文件时 |
| **Last Commit** | `https://img.shields.io/github/last-commit/{user}/{repo}` | 活跃项目 |
| **Repo Size** | `https://img.shields.io/github/repo-size/{user}/{repo}` | 体积敏感项目 |
| **PyPI** | `https://img.shields.io/pypi/v/{package}` | 已发布到 PyPI 时 |
| **CI Status** | `https://img.shields.io/github/actions/workflow/status/{user}/{repo}/ci.yml` | 有 GitHub Actions 时 |
| **Code Style** | `https://img.shields.io/badge/style-black-000000` | 使用 black/ruff 等 |

**badge 行格式**：

```markdown
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue" />
  <img src="https://img.shields.io/github/license/0010Grent/repo-name" />
  <img src="https://img.shields.io/github/last-commit/0010Grent/repo-name" />
</p>
```

**规则**：
1. 最多 4-5 个徽章，过多会造成视觉噪音
2. 将最重要、最独特的前置，通用徽章（如 language）后置
3. 使用 `align="center"` 让徽章行居中
4. 如果项目无 PyPI 发布、无 CI、无 LICENSE，不要硬凑徽章

### Banner / Header 区

README 顶部可以设计一个视觉 header 区，提升辨识度。

**方案 A：纯文本 Banner（推荐，零依赖）**

```markdown
<div align="center">

# ProjectName

**{一句话副标题}**

<p align="center">
  <img src="...badges..." />
</p>

</div>

---
```

**方案 B：ASCII Art Banner（适合 CLI 工具）**

如果项目是 CLI 工具，在 README 顶部放置一个由字符构成的 Logo banner：

```markdown
<pre align="center">
╔═══════════════════════════════════╗
║  ██╗  ██╗██████╗ ██╗    ██████╗   ║
║  ██║  ██║╚════██╗██║    ╚════██╗  ║
║  ███████║ █████╔╝██║     █████╔╝  ║
║  ██╔══██║██╔═══╝ ██║     ╚═══██╗  ║
║  ██║  ██║███████╗███████╗██████╔╝  ║
║  ╚═╝  ╚═╝╚══════╝╚══════╝╚═════╝   ║
╚═══════════════════════════════════╝
</pre>
```

使用 [figlet](http://www.figlet.org/) 生成，选择 `slant`、`big`、`standard` 等字体。

**方案 C：Social Preview 图片（最佳视觉效果）**

GitHub 仓库支持设置一张 1280×640 的 Social Preview 图片，在分享仓库链接时展示。技能可以辅助生成：

推送完成后，如果用户需要，运行 bundled 脚本生成预览 HTML：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_social_preview.py "ProjectName" "一句话副标题" Python CLI MIT
```

这会在项目 `docs/social-preview.html` 生成一个自包含的 HTML 页面。用户用浏览器打开（100% 缩放），截图 1280×640 区域，上传到 GitHub Settings → Social preview。

### 流程图规范

README 中的流程图应根据复杂度和目标读者选择合适的形式。

**选项 1：文字描述（适合简单项目）**

对于步骤简单的流程，直接用有序列表说明，不需要流程图：

```markdown
处理流程：
1. 读取配置 → 2. 验证输入 → 3. 执行转换 → 4. 输出结果
```

**选项 2：`<pre>` + Unicode 框线（适合中等复杂度）**

用 HTML `<pre>` 包裹纯文本流程图，兼容任意 GitHub 主题：

```html
<pre>
<b>输入</b>
    │
    ▼
╔════════════════════════════╗
║  <b>阶段名称</b>                  ║
║  ├─ 维度1: 值1 / 值2        ║
║  └─ 维度2: 值a / 值b        ║
╚════════════════════════════╝
    │
    ▼ <b>输出文件</b>
    │
  ┌─ 条件A? ──是──→ <b>结果A</b>
  └─ 条件B? ──是──→ <b>结果B</b>
</pre>
```

| 符号 | 用途 |
|------|------|
| `╔═╗ ╚═╝` | 阶段容器（双线框） |
| `┌─┐ └─┘` | 条件/分支框（单线框） |
| `│ ▼ ►` | 流向 |
| `├─ └─` | 树形展开 |
| `──→` | 条件分支指向结果 |

规则：
- 核心节点加粗（`<b>`）
- 普通文字不加粗
- 对齐：英文用空格，中文可用全角字符
- 容器内缩进 2 空格

**选项 3：Mermaid（仅在亮色主题为主时使用）**

如果目标用户主要在亮色主题下浏览，可使用 Mermaid：

```markdown
```mermaid
flowchart LR
    A[输入] --> B{判断}
    B -->|条件1| C[处理A]
    B -->|条件2| D[处理B]
    C --> E[输出]
    D --> E
```
```

注意：Mermaid 在深色主题下文字可能不可读。如果 README 面向不确定的读者群，优先使用 `<pre>` 方案。

### 文件结构树

展示项目结构时，使用树形符号增强可读性：

```markdown
```text
repo-name/
├── src/
│   ├── core/
│   │   ├── engine.py          # 核心处理引擎
│   │   └── pipeline.py        # 数据管线编排
│   ├── io/
│   │   ├── reader.py          # 多格式输入解析
│   │   └── writer.py          # 结构化输出序列化
│   └── cli.py                 # 命令行入口
├── tests/
├── resources/
│   └── prompts/               # LLM prompt 模板
├── pyproject.toml
└── README.md
```
```

使用缩进和注释说明每个目录的用途，避免只是一个干巴巴的 tree。

### 状态指示器

在技术文档中，用 emoji 或符号标记组件状态：

```markdown
| 组件 | 状态 | 说明 |
|------|------|------|
| 输入解析 | ✅ 稳定 | 支持 CSV / JSON / Parquet |
| 核心引擎 | ⚡ 实验性 | API 可能变动 |
| 输出序列化 | 🚧 开发中 | 仅支持 JSON 目前 |
```

可选的指示符：
- ✅ 稳定 / 🚧 开发中 / ⚡ 实验性 / ❌ 已弃用
- 🟢 高性能 / 🟡 中等 / 🔴 需优化

## Python 项目目录结构规范

新建 Python 项目或重构现有项目时，遵循以下标准目录结构（参考 FinSight 模式）：

### 标准结构

```
project_name/                  # 项目根目录（与仓库名一致）
├── src/package_name/          # 源代码目录（必须放在 src/ 下，避免父子重名）
│   ├── __init__.py
│   ├── __main__.py            # 支持 python -m package_name
│   ├── cli.py                 # CLI 入口
│   ├── config.py              # 配置管理
│   └── ...                    # 其他模块
├── tests/                     # 测试目录（与 src/ 同级）
│   ├── __init__.py
│   └── test_*.py
├── resources/                 # 资源文件（提示词、模板等）
│   ├── prompts/
│   └── templates/
├── datasets/                  # 用户数据集（输入/输出）
├── workspace/                 # 运行时工作目录（日志、备份、临时文件）
├── docs/                      # 文档目录
├── pyproject.toml            # 现代 Python 包配置
├── requirements.txt          # 依赖列表
├── .env                      # 环境变量（已加入 .gitignore）
├── .env.example              # 环境变量示例
├── .gitignore
└── README.md
```

### 关键原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **src/ 布局** | Python 包必须放在 `src/` 下 | `src/finforge/` 而非 `finforge/finforge/` |
| **避免父子重名** | 包目录与项目根目录禁止同名 | 错误：`myapp/myapp/` 正确：`myapp/src/myapp/` |
| **数据集分离** | 用户数据与运行时数据分离 | `datasets/`（用户数据）+ `workspace/`（运行时） |
| **资源独立** | 提示词、模板放入 `resources/` | `resources/prompts/` |
| **测试同级** | `tests/` 与 `src/` 同级 | 便于 pytest 发现和运行 |

### 路径管理

在 `config.py` 中统一定义路径：

```python
from pathlib import Path

# 项目根目录（从 src/package/ 上两级）
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 标准子目录
DATASETS_DIR = PROJECT_ROOT / "datasets"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
RESOURCES_DIR = PROJECT_ROOT / "resources"
PROMPTS_DIR = RESOURCES_DIR / "prompts"
```

### pyproject.toml 最小配置

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "package_name"
version = "0.1.0"
description = "项目描述"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "openai>=1.0.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
package_name = "package_name.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

### 推送前检查清单

- [ ] 源代码位于 `src/` 下，非项目根目录
- [ ] 无父子文件夹重名（如 `foo/foo/`）
- [ ] `tests/` 与 `src/` 同级
- [ ] 数据集分离为用户数据和运行时数据
- [ ] 存在 `pyproject.toml` 或 `setup.py`
- [ ] `.gitignore` 包含 `.env`、`__pycache__/`、`.venv/`、`workspace/`、`datasets/`

---

## Best Practices

- 推送前始终检查符号链接，避免将外部目录内容推入仓库
- **推送前检查本地私有文件**：CLAUDE.md、task.txt、tests/、记录自建文件/ 等不应推送到远程
- **默认排除除 README.md 外的所有 Markdown 文件**：PLAN.md、ARCHITECTURE.md、INFRASTRUCTURE_PATTERNS.md 等属于本地工作文件
- 描述字段根据项目内容自动生成，但让用户确认
- 首次推送后建议用户在 GitHub 上检查文件列表，确认无敏感信息泄露
- 如果项目有 `.env.example`，推送后提醒用户补充环境变量说明
- 重命名后验证所有引用点已更新，特别关注 Python import 语句和 CLI 入口
- 重命名后提醒用户更新其他可能引用旧名的地方（如 CI/CD 配置、Docker compose、部署脚本等）
- 撰写 README 时执行 Project Positioning Protocol，根据项目类型（简洁/技术/产品/管线）选择合适风格，避免所有项目套用同一套措辞
- 如果用户需要，在推送完成后运行 `scripts/generate_social_preview.py` 生成 Social Preview 辅助图
- **推送前必须执行 Step 3.5 企业信息清洗**：扫描蚂蚁集团相关关键词，删除企业内部文档，清洗代码中的内部 URL/邮箱/工具名
- 企业信息清洗后必须重新验证扫描通过，未通过验证前禁止进入 Stage 步骤
- 如果 git 历史中存在企业文件，警告用户并提供清理建议（`git filter-repo`），但不自动执行 force-push