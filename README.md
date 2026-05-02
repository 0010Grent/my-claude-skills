# my-claude-skills

Claude Code 插件包，包含自建 Skills 与 Agents，用于日常开发工作流与学术可视化。

## 安装

```bash
git clone https://github.com/0010Grent/my-claude-skills.git
cd my-claude-skills && bash install.sh
```

重启 Claude Code 即可使用。

### 更新

```bash
cd my-claude-skills
git pull && bash install.sh
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

### `arxiv-paper-reporter`

深度阅读全英文 arxiv 论文，生成面向多人汇报的结构化解读报告。

**触发词**：`/read-paper <链接或路径>`、`论文解读`、`论文汇报`、粘贴 arxiv 链接

**功能**：
- 解析 arxiv 链接或本地 PDF，输出四维分析（问题/算法/实验/结论）
- 按章节难度均衡分配报告人，生成时长标注的分工方案
- 对指定章节深度精读：算法流程 + 数学公式直觉解释
- 生成完整汇报报告，每板块含攻读目标、精读章节、听众检查点

---

### `manimgl-3b1b`

使用 manimgl（3Blue1Brown 个人动画库）制作概念阐释动画。输出 MP4/GIF，用于学术汇报或 PPT 嵌入。

**触发词**：`制作动画`、`manim`、`3b1b 风格`、`概念可视化`

**功能**：
- 将数学公式、算法流程、数据流转化为可视化动画
- 深色背景、LaTeX 公式、ValueTracker 动态数值驱动
- 慢速播放（20~36 秒/场景），适合 PPT 逐步讲解
- 内置色彩系统与几何元素规范（BLUE/YELLOW/GREEN/RED/TEAL 语义映射）

---

## Agents 列表

Agents 存放于 `agents/` 目录，安装时同步到 `~/.claude/agents/`。

### `manimgl-animator`

专门负责编写和渲染 manimgl 动画的 Agent。接收概念描述，输出完整脚本并执行渲染。

**能力**：
- 阅读论文/文档，提取需可视化的核心概念
- 按 3B1B 风格规范编写 manimgl 场景脚本
- 调用 ffmpeg 转码 GIF，验证文件大小与时长

---

## 与其他 Skills 库的关系

| 来源 | 安装方式 | 说明 |
|------|---------|------|
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | `claude /plugin install` | 81 个通用 skills |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 手动复制 | 工程类 18 个 skills |
| 本仓库 | `bash install.sh` | 个人自建 skills + agents |
