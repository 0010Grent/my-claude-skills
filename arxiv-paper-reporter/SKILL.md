---
name: arxiv-paper-reporter
description: "Use this skill whenever the user wants to read, understand, or summarize an arxiv paper, or generate a structured presentation/report from a research paper. Triggers include: any mention of 'arxiv', 'paper report', '论文解读', '论文汇报', 'read paper', 'explain paper', or requests to analyze academic papers, generate presenter assignments, deep-read specific sections, or produce structured reading reports. Use this skill even if the user just pastes an arxiv URL or PDF path without explicit instructions."
---

# arxiv Paper Reporter

帮助用户深度阅读全英文 arxiv 论文，并生成结构化、面向多人汇报讲解的论文解读报告。

## 核心能力

- **论文理解**：解析算法机制、数据集、实证结果，将数学公式转化为直觉性解释
- **汇报报告生成**：面向听众的结构化分工报告，每个板块含攻读目标、精读章节、讲解要点、时长标注
- **章节精读**：针对指定章节深度解析，输出算法流程、关键机制、实验逻辑

## 命令

| 命令 | 功能 |
|------|------|
| `/read-paper <链接或路径>` | 读取并理解论文，输出四维深度分析 |
| `/assign-speakers [--speakers N]` | 智能分配报告人章节与难度热力图 |
| `/explain-section <章节号>` | 对指定章节进行深度精读 |
| `/write-report [--speakers N --duration Xmin]` | 生成完整汇报报告 |

## 工作流

1. 用户提供论文链接或 PDF → `/read-paper`
2. 确认理解框架 → `/assign-speakers`
3. 针对重点章节 → `/explain-section`
4. 生成完整报告 → `/write-report`

## 使用命令

当用户提到论文链接、PDF 路径，或要求生成汇报报告时，按以下步骤执行：

### 读取论文（/read-paper）

1. 若为 arxiv 链接，使用 WebFetch 或 `tools/arxiv_fetcher.py` 获取论文内容
2. 若为 PDF，使用 `tools/pdf_parser.py` 解析
3. 输出结构：论文基本信息 → 核心贡献 → 章节目录 → 四维分析（问题/算法/实验/结论）→ 逻辑框架图 → 推荐精读章节

### 分配报告人（/assign-speakers）

- 按章节内容难度和篇幅均衡分配
- 输出：分工方案表格 + 难度热力图 + 建议讲解时长

### 章节精读（/explain-section）

- 输出：算法流程、关键机制、数学公式直觉解释、实验逻辑

### 生成报告（/write-report）

每个报告人板块必须包含：

```
报告人 [X]：[主题名称] ([时长])

攻读目标：[1-2句话]

精读章节：
● [章节号] [章节名]

汇报讲解板块：
● [要点]（X分钟）：[详细解读]

听众理解检查点：
□ [关键概念] — 听众应能用自己的话复述
```

## 行为准则

- **先理解，再报告**：生成报告前必须完整解析论文
- **双层解释**：每个技术概念给出「白话版」+「技术版」
- **保留原文**：关键术语保留英文，括号内给中文
- **数学公式必须解释**：不允许直接复制，必须解释直觉含义
- **实验数据要解读**：数字背后的意义比数字本身更重要

## 输出目录

报告保存至 `outputs/[论文标题]/`，结构：
- `01_paper_understanding.md`
- `speaker_assignments.md`
- `sections/[章节]_explanation.md`
- `report_[日期].md`
