# my-claude-skills

我的 Claude Code 自建 Skills 集合，用于日常开发工作流。

## 使用方式

将需要的 skill 目录复制到 `~/.claude/skills/` 即可：

```bash
cp -r github-push ~/.claude/skills/
cp -r CV-create ~/.claude/skills/
cp -r llm-pipeline-scaffold ~/.claude/skills/
```

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

### `learned`

占位目录，用于积累经验性 prompts。

## 私有 Skills

以下 skills 因包含内部平台信息，存放于私有仓库：

- `dataphin` — Dataphin/MaxCompute 数据开发
- `wohu-knowledge-base` — 外部 RAG 知识库检索
- `eve-*` — EVE 大模型评测平台
- `aistudio-connect-diagnosis` — AIStudio 连接诊断
- `ant-find-skills` — 内部 skill 发现

## 与其他 Skills 库的关系

| 来源 | 安装方式 | 说明 |
|------|---------|------|
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Claude Code 插件管理器 | 81 个通用 skills |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 手动复制 | 工程类 18 个 skills |
| 本仓库 | 手动复制 | 个人自建 |
