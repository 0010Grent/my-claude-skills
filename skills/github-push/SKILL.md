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
- 描述：基于项目内容自动生成建议，用户可修改

### Step 2.5: Directory Structure Audit（目录结构诊断）

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

### Step 4: Stage & Review

```bash
# 暂存所有文件
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
gh repo view {repo_name} --json url,isPrivate

# 验证推送成功
git log --oneline -3
git status
```

向用户报告：
```
✅ 推送完成

仓库: https://github.com/{username}/{repo_name}
可见性: private
分支: main
提交: {commit_count} 个文件
```

---

## Project Positioning Protocol（项目定位协议）

**推送或重命名时，必须先深入分析项目再撰写 README 标题、仓库描述和项目简介。**

### 核心原则：写本质，不写表象

项目定位不是描述"它做了什么操作"，而是回答"它在更广阔的技术栈/工作流中扮演什么角色"。表面描述只看到功能，本质定位看到工程价值。

**错误示例 → 正确示例**：

| 表象描述（禁止） | 本质定位（必须） |
|---|---|
| "金融考试题目自动生成系统" | "金融垂域合成语料引擎——教师模型蒸馏 + 6维度质控" |
| "批量生成题目的工具" | "大模型训练种子数据的自动化合成管线" |
| "用 AI 出题的脚本" | "基于教师模型的垂域语料蒸馏工厂" |
| "自动化测试工具" | "持续验证管线——代码变更的自动化拦截网" |
| "数据分析脚本集" | "可复现的分析管线——从原始数据到决策洞察" |

### 定位分析四步法

在撰写 README/描述 **之前**，必须执行以下分析：

#### 1. 追问"为什么需要它"

不要停留在"它生成了什么"，追问生成的产物被谁消费、用于什么目的：

```
生成题目 → 谁用这些题目？→ 用于训练金融垂域模型
         → 那它就是 语料合成管线，不是 出题工具
```

#### 2. 识别技术在栈中的位置

将项目放入更广的技术栈中定位：

```
大模型工作流:
  预训练 → SFT微调 → RLHF → 部署
                 ↑
            本项目产出物在此消费
        → 所以本项目是 "微调种子数据合成引擎"
```

#### 3. 用行业术语替代功能描述

| 功能动作 | 行业术语 |
|---------|---------|
| 生成 | 合成 / 蒸馏 |
| 检查 | 质控 / 验证 / 筛选 |
| 改进提示词 | 自优化 / 自动蒸馏 |
| 删除坏数据 | 幻觉拦截 / 纯度过滤 |
| 批量处理 | 管线 / 工厂 |
| 迭代重新生成 | 多轮自优化闭环 |

#### 4. 撰写一行定位公式

格式：**[领域] + [技术本质] + [核心机制]**

```
FinForge = 金融垂域 + 合成语料引擎 + 教师模型蒸馏 × 6维度质控 × 多轮自优化
```

### README 撰写要求

当首次推送或重命名时撰写/重写 README，必须包含以下段落，按此顺序：

#### 1. 标题行

`# ProjectName — [一行定位公式]`

标题必须直接体现本质定位，不写功能描述。

#### 2. 一句话定位（标题下方第一段）

用 2-3 句话说明：
- **本质是什么**（不是"它做什么"，而是"它是什么"）
- **核心机制**（管线的关键技术环节）
- **产出物的消费者是谁**（下游如何使用）

示例：
> 基于教师模型（Claude / Gemini）的金融垂域训练语料自动合成管线。从考点提纲出发，经多维度验证 + 多轮自优化迭代，产出可直接用于模型微调的高纯度种子数据集。

#### 3. "为什么需要这个项目"段落（必须）

直接回答项目存在的技术理由，不是概述功能列表。典型结构：
- 行业痛点 1（为什么现有方案不行）
- 行业痛点 2（如果不用这个会怎样）
- 本项目如何解决

示例：
> 金融垂域模型微调需要大量**可验证、无幻觉**的训练数据。人工标注成本高且难以规模化，而直接用 LLM 生成的数据存在两个根本问题：
> 1. **幻觉污染**：模型会虚构不存在的公司、编造财务数据、混淆行业指标口径
> 2. **质量漂移**：未经验证的合成数据会放大模型自身偏差，"garbage in, garbage out"

#### 4. 架构流程图

按 README 流程图规范（见下文）绘制，阶段命名使用行业术语（合成/质控/蒸馏），不使用功能动词（生成/验证/评估）。

#### 5. 核心机制详解

以数据流为主线，解释每个环节的**技术动机**（为什么这样设计），不列举实现细节。

#### 6. 输出格式说明

明确产出物的数据结构和下游使用方式——这是项目作为"管线"而非"终端工具"的关键证明。

### 仓库描述格式

`gh repo edit` 的 `--description` 必须遵循：

```
[领域] + [技术本质] — [核心机制，用 × 或 + 连接]
```

示例：
```
金融垂域合成语料引擎 — 教师模型蒸馏 × 6维度质控 × 多轮自优化闭环
```

禁止使用以下模式：
- "一个...的工具"
- "基于 AI 的..."
- "自动化...系统"
- "用于...的脚本"

### 重命名时的定位迁移

执行 `/github-push rename` 时，如果新名称暗示了定位变化（如从"lab/工具"改为"引擎/管线"），必须同步执行：

1. **重写 README 标题和一句话定位**——不仅是替换项目名，要根据新名称的语义重新推导定位公式
2. **更新 CLI description**（`argparse.ArgumentParser(description=...)`）——改为本质定位，而非功能描述
3. **更新所有 docstring 中的项目定位句**——搜索第一条 docstring 或模块注释
4. **更新 GitHub 仓库描述**——按上述格式重新撰写
5. **搜索并替换措辞降级**——如"实验"→"生产"、"生成"→"合成"、"验证"→"质控"、"评估"→"蒸馏"、"通过率"→"纯度"

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

同时更新仓库描述（按 Project Positioning Protocol 格式）：

```bash
gh repo edit {new_name} --description "[领域] + [技术本质] — [核心机制]"
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

## Anti-Patterns

- **禁止**在 `.gitignore` 未补全安全规则的情况下推送
- **禁止**推送包含 `.env`、API key、密码等敏感文件的提交
- **禁止** force-push 到已有远程仓库
- **禁止**自动修改用户已有的 `.gitignore` 规则（只追加不修改）
- **禁止** commit message 包含 AI 署名（Co-Authored-By）
- **禁止**修改 `data/` 目录下的运行时输出文件（历史数据不应被重命名影响）
- **禁止**跳过验证步骤直接推送（重命名后必须 grep 确认无残留引用）
- **禁止**用功能动作描述项目定位（"生成题目"/"自动化工具"→ 必须写本质定位）
- **禁止**在 README 标题或仓库描述中使用"一个...的工具"/"基于 AI 的..."/"实验"等降级措辞
- **禁止**推送 CLAUDE.md、task.txt、tests/、记录自建文件/ 等本地私有文件
- **禁止**推送除 README.md 外的其他 Markdown 文件（如 PLAN.md、ARCHITECTURE.md、INFRASTRUCTURE_PATTERNS.md 等）
- **禁止**直接使用中文或含空格的目录名作为 GitHub 仓库名（必须要求用户指定 ASCII 名）
- **禁止**在 Step 2.5 诊断出单层嵌套后跳过警告直接推送（必须告知用户并等待确认）
- **禁止**重命名后硬编码 SSH 或 HTTPS 协议重设 remote URL（必须检测当前协议后保持一致）

## README 流程图规范

**禁止使用 Mermaid**。GitHub 渲染 Mermaid 时，深色背景节点的文字会变成白色，无法通过 themeVariables 可靠修复。

### 使用 `<pre>` + Unicode 制表符

用 HTML `<pre>` 标签包裹纯文本流程图，保证任意 GitHub 主题下文字都可读：

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

### 关键符号

| 符号 | 用途 |
|------|------|
| `╔═╗ ╚═╝` | 阶段容器（双线框） |
| `┌─┐ └─┘` | 条件/分支框（单线框） |
| `│ ▼ ►` | 流向 |
| `├─ └─` | 树形展开 |
| `──→` | 条件分支指向结果 |

### 关键规则

1. **核心节点加粗**：用 `<b>` 标签包裹阶段名、输出文件名、关键判定结果
2. **普通文字不加粗**：维度说明、条件描述保持正常字重
3. **对齐**：中文内容使用全角字符对齐，英文内容用空格对齐
4. **容器内缩进 2 空格**：阶段框内内容统一缩进
5. **阶段命名用行业术语**：合成/质控/蒸馏，不使用生成/验证/评估

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
- 撰写 README 时必须执行 Project Positioning Protocol 的定位分析四步法，确保标题和描述体现工程本质