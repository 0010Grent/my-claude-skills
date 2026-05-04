<div align="center">

<pre align="center">
╔═══════════════════════════════════════════════════════╗
║  ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗         ║
║ ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗        ║
║ ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝        ║
║ ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔═══╝         ║
║ ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║             ║
║  ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝             ║
║                                                       ║
║        ██╗   ██╗██████╗  ██████╗██╗  ██╗               ║
║        ██║   ██║██╔══██╗██╔════╝██║ ██╔╝               ║
║        ██║   ██║██████╔╝██║     █████╔╝                ║
║        ██║   ██║██╔═══╝ ██║     ██╔═██╗                ║
║        ╚██████╔╝██║     ╚██████╗██║  ██╗               ║
║         ╚═════╝ ╚═╝      ╚═════╝╚═╝  ╚═╝               ║
╚═══════════════════════════════════════════════════════╝
</pre>

GitHub Push — Claude Code Skill for Hassle-Free Repository Publishing
---

*One command, zero friction — from local project to private GitHub repository.*

<p>

[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-CC785C?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Shell](https://img.shields.io/badge/Shell-Bash-4EAA25?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)

</p>

**github-push** is a Claude Code skill that automates the entire repository publishing workflow — from pre-flight checks and privacy sanitization to commit, push, and README generation. It handles both brand-new projects and incremental updates to existing repositories with intelligent route branching.

🎯 **One slash command, one complete push.**

<br>

*If you use Claude Code for project management, please ⭐ star & 🍴 fork!*

</div>

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [🗺️ Roadmap](#-roadmap)
- [🚀 Quick Start](#-quick-start)
- [🏗️ Architecture](#-architecture)
- [📋 Command Reference](#-command-reference)
- [🔒 Safety & Privacy Protocols](#-safety--privacy-protocols)
- [📝 Project Positioning Protocol](#-project-positioning-protocol)
- [🔄 Rename Protocol](#-rename-protocol)
- [📂 Directory Structure Standards](#-directory-structure-standards)
- [🛠️ File Structure](#-file-structure)
- [📜 License](#-license)

---

## ✨ Key Features

* **🛡️ Pre-flight Privacy Audit**
    Automatically detects `.env`, API keys, credentials, and local working files (CLAUDE.md, task.txt, tests/) before they ever touch a remote server. Appends missing entries to `.gitignore` without touching existing rules.

* **🧭 Route A/B Smart Branching**
    Distinguishes between existing repositories and brand-new projects. For existing repos, skips redundant diagnostics and goes straight to divergence analysis and incremental push. For new projects, runs the full initialization pipeline including directory structure audit.

* **🧼 Corporate Information Sanitization**
    Mandatory scanning for enterprise-specific keywords and internal identifiers (Ant Group domains, internal emails, proprietary tool names). Classifies matches into three severity tiers: file deletion, inline sanitization, or `.env` placeholder replacement.

* **🎯 Project Positioning Protocol**
    Analyzes project type (CLI tool / library / application / data pipeline) and recommends the most appropriate README style — concise, technical, product-oriented, or pipeline-oriented — instead of forcing generic boilerplate.

* **🔄 Full-Corpus Rename Support**
    Not just GitHub repo renaming. Propagates changes across Python imports, docstrings, CLI descriptions, markdown documents, filenames, and hardcoded configuration variables in a single atomic operation.

* **📊 Fork-Aware Divergence Handling**
    Detects when local history has diverged from remote and presents three resolution strategies: fast-forward push, behind-remote reset with stash recovery, or manual rebase/merge — never forcing an automatic merge.

* **🎨 README Visual Enhancement**
    Bundles badge generation, ASCII/Unicode diagram support, and a social preview generator script for high-quality repository presentation.

---

## 🗺️ Roadmap

- [x] Route A/B path decision for existing vs. new repositories
- [x] Automatic `.gitignore` safety rule completion
- [x] Corporate information sanitization (keyword scan + classification)
- [x] Project Positioning Protocol (4-style README generation)
- [x] Full-corpus rename (code + docs + config + repo + directory)
- [x] Fork-aware divergence strategy (fast-forward / behind / diverged)
- [x] Social preview HTML generator
- [x] Python project directory structure standards
- [ ] Plugin system for custom sanitization rule packs
- [ ] Multi-language `.gitignore` template support (Node.js, Rust, Go)
- [ ] CI/CD template injection (GitHub Actions scaffolding)

---

## 🚀 Quick Start

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- Git configured with a GitHub account
- [GitHub CLI](https://cli.github.com/) (`gh`) authenticated via `gh auth login`

### Installation

Place the skill directory into your Claude Code skills folder:

```bash
# Clone into your skills directory
git clone https://github.com/0010Grent/github-push.git \
  ~/.claude/skills/github-push
```

Claude Code will auto-discover the skill. Verify with:

```claude
/github-push
```

### Usage

**Push a brand-new project:**

```claude
/github-push my-new-repo
```

**Push with current directory name:**

```claude
/github-push
```

**Rename an existing project:**

```claude
/github-push rename better-name
```

**What happens on `/github-push`:**

1. **Step 0** — Route decision (existing repo → Route A, new project → Route B)
2. **Step 1** — Pre-flight checks (git status, `gh` auth, remote status)
3. **Step 2** — Resolve repository name (directory basename or argument)
4. **Step 2.5** *(Route B only)* — Directory structure audit (detect single-level nesting)
5. **Step 3** — Patch `.gitignore` with safety rules
6. **Step 3.5** *(Route B only)* — Corporate information sanitization
7. **Step 4** — Stage files and review
8. **Step 5** — Create GitHub repository via `gh`
9. **Step 6** — Commit with conventional message format
10. **Step 7** — Push to origin
11. **Step 8** — Verify and sync repository description

---

## 🏗️ Architecture

<pre>
<b>用户输入</b>
   │
   ▼
╔══════════════════════════════╗
║  <b>Step 0: Route Decision</b>      ║
║  ├─ 检查 origin 远程是否存在 ║
║  └─ 判定 → Route A 或 Route B ║
╚══════════════════════════════╝
   │
   ├── Route A (已有仓库) ─────────────────────┐
   │                                            │
   │   ╔══════════════════════╗               │
   │   ║  A1: Snapshot & Diff ║               │
   │   ║  A2: Divergence分析   ║               │
   │   ║  A3: Commit & Push     ║               │
   │   ╚══════════════════════╝               │
   │                                            │
   └── Route B (新项目) ───────────────────────┤
                                                │
      ╔═══════════════════════════════╗         │
      ║  B1: Pre-flight Checks        ║         │
      ║  B2: Resolve Repo Name        ║         │
      ║  B3: Directory Structure Audit║         │
      ║  B4: Patch .gitignore         ║         │
      ║  B5: Corp Sanitization        ║         │
      ║  B6: Stage & Review             ║         │
      ║  B7: Create GitHub Repo       ║         │
      ║  B8: Commit & Push            ║         │
      ║  B9: Verify & Sync Desc       ║         │
      ╚═══════════════════════════════╝         │
                                                │
      <b>Project Positioning Protocol</b> ←──────────┘
      (推送后生成 README / 更新仓库描述)
</pre>

**Route A Fork 处理决策树：**

| 场景 | merge-base 结果 | 策略 |
|------|----------------|------|
| 本地领先远程 | `origin/branch` 是 HEAD 祖先 | fast-forward 直接 push |
| 本地落后远程 | HEAD 是 `origin/branch` 祖先 | stash → reset → re-commit → push |
| 已分叉 | 无祖先关系 | 报告用户，等待选择 rebase/merge/exit |

**Divergence 策略代码逻辑：**

```bash
_branch=$(git rev-parse --abbrev-ref HEAD)
if git merge-base --is-ancestor origin/$_branch HEAD; then
  _strategy="fast_forward"
elif git merge-base --is-ancestor HEAD origin/$_branch; then
  _strategy="behind_remote"
else
  _strategy="diverged"
fi
```

---

## 📋 Command Reference

| Command | Action | Route |
|---------|--------|-------|
| `/github-push` | 使用当前目录名作为仓库名，完整推送流程 | B |
| `/github-push <repo-name>` | 指定仓库名，完整推送流程 | B |
| `/github-push rename <new-name>` | 全量重命名：代码引用 + 文档 + GitHub 仓库 + 本地目录 | A/B |

**Trigger words** (Claude Code  slash command auto-detection):
- 上传到 GitHub、推到私有仓库、创建私有仓库并推送
- 改项目名、重命名仓库、rename repo

---

## 🔒 Safety & Privacy Protocols

### `.gitignore` Safety Rules

The skill automatically ensures these patterns are present in `.gitignore` before any push:

**Privacy (never push):**
```gitignore
.env
*.pem
*.key
credentials.json
service-account*.json
```

**Build artifacts:**
```gitignore
node_modules/
__pycache__/
*.pyc
.venv/
venv/
dist/
build/
```

**Local working files (Claude Code specific):**
```gitignore
task.txt
tasks.txt
TODO.txt
NOTES.txt
CLAUDE.md
PLAN.md
ARCHITECTURE.md
记录自建文件/
notes/
私人文件/
```

**Markdown policy:**
```gitignore
*.md
!README.md
```

All rules are **appended, never modified** — existing `.gitignore` entries are preserved.

### Corporate Information Sanitization (Step 3.5)

**Mandatory scan targets:**

| Category | Patterns |
|----------|----------|
| Company names | `蚂蚁`, `蚂蚁集团`, `Ant Group`, `AntGroup` |
| Internal domains | `*.antfin.com`, `*.antgroup.com`, `*.alipay.com`, `*.mybank.cn` |
| Internal platforms | `yuque.antfin`, `aone.alibaba`, `antcode`, `sofa`, `oceanbase` |
| Internal emails | `@antfin.com`, `@antgroup.com`, `@alibaba-inc.com` |

**Three-tier classification:**

| Tier | Condition | Action |
|------|-----------|--------|
| **A — Whole-file deletion** | File name contains enterprise keywords, or >50% content is internal documentation | `git rm --cached` or `rm -f` |
| **B — Inline sanitization** | Core code files with scattered enterprise URLs / emails / comments | `sed` replacement with placeholders |
| **C — `.env` placeholder** | Configuration values pointing to internal endpoints | Replace with generic placeholders |

**Verification loop:**
```bash
# Post-sanitization mandatory re-scan
grep -rni -E "$_pattern" . \
  | grep -v ".git/" | grep -v ".venv/" | grep -v "__pycache__/"
```

No push proceeds until the verification scan returns zero matches.

---

## 📝 Project Positioning Protocol

When pushing or renaming, the skill analyzes the project and selects one of four README positioning styles:

| Style | Suitable For | Template |
|-------|-------------|----------|
| **Concise** | Small utilities, single-purpose scripts | `{Action} {Target}, supports {Feature1} and {Feature2}` |
| **Technical** | Frameworks, libraries, SDKs, middleware | `{Category} for {Platform} — {Core Mechanism}, supports {Features}` |
| **Product** | Applications, services, platforms | `Helps {User} {Solve What}, via {Core Method}` |
| **Pipeline** | Data pipelines, training flows, ETL | `{Domain} Pipeline — {Stage1} → {Stage2} → {Stage3}, yields {Output}` |

**README structure per style:**

```markdown
# ProjectName — {style-appropriate positioning line}

{2-3 sentences: what this is, why use it, who should use it}

## "Why This Exists"
{problem statement based on style}

## Architecture / Flow
{visual diagram (simple → <pre> text → Mermaid)}

## Core Mechanism / Usage
{API design | feature list | command reference | data flow}

## Output Format (pipeline projects)
{data schema, downstream consumption contract}
```

**Forbidden terms** in repository descriptions (without specific metrics):
- "智能" / "intelligent" (what metric proves it?)
- "高效" / "efficient" (compared to what?)
- "全自动" / "fully automatic" (which step still needs human input?)
- "基于 AI" / "AI-based" (which model / algorithm?)

---

## 🔄 Rename Protocol

`/github-push rename <new-name>` performs a full-corpus rename in this order:

```bash
# R1: Detect old name from __init__.py / import statements / directory basename
# R2: Impact analysis — grep across all tracked files
# R3: Execute rename
  3.1  Replace Python imports (find . -name "*.py" -exec sed ...)
  3.2  Replace markdown/doc references
  3.3  Rewrite README positioning
  3.4  Update CLI descriptions (argparse, __doc__)
  3.5  Rename files containing old name
# R4: Verify — grep must return zero matches for old name
# R5: Rename GitHub repository via gh repo rename
# R6: Update remote URL (preserves SSH/HTTPS protocol)
# R7: Commit and push
```

**Remote URL protocol preservation:**

```bash
_current_url=$(git remote get-url origin)
if [[ "$_current_url" == git@* ]]; then
  git remote set-url origin "git@github.com:{user}/{new-name}.git"
else
  git remote set-url origin "https://github.com/{user}/{new-name}.git"
fi
```

---

## 📂 Directory Structure Standards

For Python projects pushed via this skill, the recommended layout (inspired by FinSight) is:

```text
project_name/
├── src/package_name/          # Source code under src/ to avoid namespace collision
│   ├── __init__.py
│   ├── __main__.py            # Supports `python -m package_name`
│   ├── cli.py                 # CLI entry point
│   └── config.py              # Path management & constants
├── tests/                     # At repo root, alongside src/
│   ├── __init__.py
│   └── test_*.py
├── resources/                 # Prompts, templates, non-code assets
│   ├── prompts/
│   └── templates/
├── datasets/                  # User data (input / output)
├── workspace/                 # Runtime artifacts (logs, temp, backups)
├── docs/                      # Extended documentation
├── pyproject.toml             # Modern Python packaging
├── requirements.txt           # Dependency list
├── .env                       # Local secrets (gitignored)
├── .env.example               # Template for other developers
├── .gitignore
└── README.md
```

**Anti-patterns detected during push:**

| Pattern | Detection | Recommendation |
|---------|-----------|----------------|
| Single-level nesting | Root has 1 Python subdir, zero `.py` files at root | Prompt user to lift contents with `git mv` |
| Parent-child name collision | `foo/foo/` structure | Restructure to `foo/src/foo/` |
| Missing tests directory | No `tests/` or `test/` found | Note in push report |
| Symlink to external dir | `.venv` is a symlink | Automatically unstage + gitignore |

---

## 🛠️ File Structure

```text
github-push/
├── SKILL.md                          # Core skill specification (protocols, commands, anti-patterns)
├── README.md                         # This file — project documentation
├── scripts/
│   └── generate_social_preview.py    # 1280×640 Social Preview HTML generator
└── LICENSE                           # MIT License
```

**SKILL.md** (`~/.claude/skills/github-push/SKILL.md`) is the executable specification. It contains:
- Route A/B protocol definitions with shell code snippets
- Full `.gitignore` patch list
- Corporate sanitization keyword list and `sed` commands
- Project Positioning Protocol style matrices and templates
- Rename protocol step-by-step commands
- Anti-patterns checklist (what the skill must NOT do)

**scripts/generate_social_preview.py** generates a self-contained HTML page at `docs/social-preview.html`. Open in browser at 100% zoom, screenshot the 1280×640 region, and upload to GitHub Settings → Social preview.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

</div>
