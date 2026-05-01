# my-claude-skills

Claude Code 插件包，包含 3 个自建 Skills，用于日常开发工作流。

## 安装

需要 Claude Code CLI（`claude` 命令可用）。

### 1. 克隆仓库

```bash
git clone https://github.com/0010Grent/my-claude-skills.git
```

### 2. 注册 Plugin

进入仓库目录后执行：

```bash
cd my-claude-skills
claude /plugin install .
```

安装成功后，Claude Code 会话内即可直接使用以下触发词。

### 更新

Skill 内容迭代后，拉取最新代码即可，无需重新注册：

```bash
git pull
```

---

## Skills 列表

### `github-push`

将本地项目一键上传到 GitHub 私有仓库，或对已有仓库进行改名。

**触发词**：`/github-push`、`上传到 GitHub`、`/github-push rename <new-name>`

**功能**：
- 自动补全 `.gitignore`
- 创建 GitHub 私有仓库（`gh` CLI）
- 提交并推送
- 支持全量重命名（代码引用 + 文档 + GitHub 仓库 + 本地目录）

---

### `CV-create`

互联网大厂简历优化助手，基于 STAR 法则生成高质量 bullet。

**触发词**：`/resume-optimize`

**功能**：
- 从项目代码/文档提炼量化成果
- 强制格式：`关键词（3-8字）: 应用场景 → 痛点 → 方案 → 结果`
- 内置禁用词表：去除 AI 味套语
- 自动检查跨 bullet 重复句式

---

### `llm-pipeline-scaffold`

LLM 批量流水线脚手架，提炼自三个生产项目的设计模式。

**触发词**：`scaffold a pipeline`、`新建一个流水线项目`

**适用场景**：批量内容生成/标注/评估，需要断点续传、长时间无人值守运行。

**生成内容**：
- 完整目录骨架（`main.py`、`config.py`、`core/`、`prompts/`）
- 断点续传（JSONL 追加式）
- 5 级容错 JSON 解析
- tmux/nohup 长任务启动脚本
- 可选：自动提示词迭代优化模块（`optimizer/`）

---

## 与其他 Skills 库的关系

| 来源 | 安装方式 | 说明 |
|------|---------|------|
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | `claude /plugin install` | 81 个通用 skills |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 手动复制 | 工程类 18 个 skills |
| 本仓库 | `claude /plugin install` | 个人自建 |
