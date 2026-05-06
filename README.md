<div align="center">

# my-claude-skills — Personal Claude Code skills and agents toolkit

*A curated collection of Claude Code skills and agents for development workflows and academic visualization*

<p>
  <img src="https://img.shields.io/badge/Bash-install%20script-brightgreen" />
  <img src="https://img.shields.io/github/license/0010Grent/my-claude-skills" />
  <img src="https://img.shields.io/github/last-commit/0010Grent/my-claude-skills" />
</p>

</div>

---

## Table of Contents

- [Why Use This](#why-use-this)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Available Skills](#available-skills)
- [File Structure](#file-structure)
- [License](#license)

---

## Why Use This

Manually installing Claude Code skills one by one is tedious:
- Skills from marketplaces cover generic use cases, not your specific workflows
- Writing custom agents from scratch takes time and misses proven patterns
- Academic presentations need specialized tools (arXiv readers, animation pipelines) not bundled in standard skill packs
- Switching machines means re-installing and re-configuring everything

This repository solves that with a single symlink: clone once, run `install.sh`, restart Claude Code, and all skills become immediately available. Each skill is self-contained with its own protocol, prompt templates, and usage guide. Updates propagate instantly through the symlink — no re-installation needed.

---

## Key Features

- GitHub Push — One-click upload local projects to private GitHub repos with auto-generated `README.md`, `.gitignore` patching, and full rename support (code references + docs + repo name + local directory)
- CV Creator — STAR-method resume optimization with quantified bullet generation and cross-bullet duplication checks
- LLM Pipeline Scaffold — Production-grade batch processing skeleton with JSONL checkpoint resume, 5-level JSON error recovery, and tmux/nohup long-running scripts
- ArXiv Paper Reporter — Deep-reading assistant that generates structured presentation reports with speaker allocation from English arXiv papers
- ManimGL 3B1B — Concept visualization animation pipeline outputting MP4/GIF optimized for academic talks and PPT embedding
- Paper Talk Script — Timed, page-by-page speaker script generator from presentation slides and PDF source material
- PPTX Polish — Automated layout fixing for academic/presentation slides: font size unification (≥18pt), line spacing to 1.5x, text overflow auto-expand, and sub-title divider alignment
- Symlink Install — Install once, auto-sync forever. `git pull` updates reflect immediately without re-running the script

---

## Quick Start

### Prerequisites

- Git
- Claude Code
- `gh` CLI (for `github-push` skill)

### Installation

```bash
git clone https://github.com/0010Grent/my-claude-skills.git
cd my-claude-skills && bash install.sh
```

Restart Claude Code. All skills and agents will be available.

### Update

Once installed via symlink, any change in the repository reflects immediately. Just run:

```bash
cd my-claude-skills && git pull
```

---

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `github-push` | `/github-push` | Push local projects to private GitHub repos with auto-generated README and `.gitignore` |
| `CV-create` | `/resume-optimize` | STAR-method resume optimization with quantified bullet generation |
| `llm-pipeline-scaffold` | `scaffold a pipeline` | Production-grade LLM batch processing skeleton with checkpoint resume |
| `arxiv-paper-reporter` | `/read-paper <url>` | Deep-read English arXiv papers and generate structured presentation reports |
| `manimgl-3b1b` | `制作动画` / `manim` | Create 3Blue1Brown-style concept visualization animations |
| `paper-talk-script` | `/paper-talk-script` | Generate timed speaker scripts from slides and PDF papers |
| `pptx-polish` | `/pptx-polish` | Fix PPT layout issues: font size, line spacing, text overflow, divider alignment with python-pptx |

### Agents

| Agent | Description |
|-------|-------------|
| `manimgl-animator` | Specialized agent for writing and rendering manimgl animations |

---

## File Structure

```text
my-claude-skills/
├── agents/                        # Claude Code agents
│   └── manimgl-animator.md       # ManimGL animation agent definition
├── github-push/                   # GitHub upload & rename skill
│   ├── SKILL.md
│   └── scripts/
├── CV-create/                     # Resume optimization skill
│   ├── SKILL.md
│   └── ...
├── llm-pipeline-scaffold/        # LLM batch pipeline scaffolding skill
│   └── SKILL.md
├── arxiv-paper-reporter/         # ArXiv deep-reading skill
│   ├── SKILL.md
│   └── ...
├── manimgl-3b1b/                  # 3B1B animation skill
│   ├── SKILL.md
│   └── ...
├── paper-talk-script/            # Presentation script generator
│   ├── SKILL.md
│   ├── README.md
│   └── .gitignore
├── pptx-polish/                  # PPT layout fixer using python-pptx
│   └── SKILL.md
├── install.sh                     # Symlink installer
├── LICENSE                        # MIT License
└── README.md                      # This file
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
