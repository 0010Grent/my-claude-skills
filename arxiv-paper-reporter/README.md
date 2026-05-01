# arxiv Paper Reporter

**一个用于深度解读 arxiv 论文并生成多人汇报报告的 Claude Code Skill。**

---

## 功能概览

| 功能 | 描述 |
|------|------|
| 📄 论文理解 | 从 arxiv 链接或 PDF 文件解析论文，生成四维深度分析 |
| 📊 汇报分工 | 智能分配章节给多位报告人，均衡内容与难度 |
| 🔍 章节精读 | 对指定章节进行深度拆解，含公式解释与讲解建议 |
| 📝 报告生成 | 输出结构化汇报报告，每个板块含攻读目标和时长标注 |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 在 Claude Code 中使用

```bash
# 进入项目目录
cd arxiv-paper-reporter

# 启动 Claude Code
claude
```

### 3. 运行命令

```
# 读取论文（支持 arxiv 链接或 PDF 路径）
/read-paper https://arxiv.org/abs/2310.06825

# 查看章节分配建议
/assign-speakers --speakers 3

# 精读指定章节
/explain-section 3.1,3.2

# 生成完整汇报报告
/write-report --speakers 3 --duration 15min
```

---

## 项目结构

```
arxiv-paper-reporter/
├── CLAUDE.md                      # Skill 主配置（Claude Code 读取）
├── .claude/
│   └── commands/
│       ├── read-paper.md          # /read-paper 命令定义
│       ├── explain-section.md     # /explain-section 命令定义
│       ├── write-report.md        # /write-report 命令定义
│       └── assign-speakers.md     # /assign-speakers 命令定义
├── prompts/
│   ├── paper_reader.py            # 论文解析核心逻辑
│   ├── report_generator.py        # 报告生成核心逻辑
│   └── templates/
│       ├── report_template.md     # 汇报报告 Markdown 模板
│       └── section_template.md    # 章节精读 Markdown 模板
├── tools/
│   ├── arxiv_fetcher.py           # arxiv API 数据获取
│   ├── pdf_parser.py              # PDF 文本与结构提取
│   └── math_explainer.py          # 数学公式识别与解释
├── outputs/                       # 生成报告输出目录（自动创建）
├── requirements.txt
└── README.md
```

---

## 标准工作流

```
用户提供论文链接/PDF
        ↓
   /read-paper
   （解析论文，生成理解框架）
        ↓
  /assign-speakers
   （分配章节给各报告人）
        ↓
  /explain-section
   （对重点章节深度精读）
        ↓
   /write-report
   （生成完整汇报报告）
        ↓
  outputs/ 目录查看报告
```

---

## 命令详解

### `/read-paper`

读取论文并生成深度理解报告。

```
/read-paper https://arxiv.org/abs/2310.06825
/read-paper ./papers/my_paper.pdf
```

输出：
- 论文基本信息（标题/作者/时间）
- 核心贡献（3-5条）
- 章节结构目录
- 四维深度分析（问题/算法/实验/结论）
- 论文逻辑框架 ASCII 图
- 推荐精读章节

### `/assign-speakers`

智能分配报告人章节，输出难度热力图和分工方案。

```
/assign-speakers
/assign-speakers --speakers 4 --total-time 60min
```

### `/explain-section`

对指定章节进行深度精读。

```
/explain-section 3.1
/explain-section 3.1,3.2 --depth deep
```

### `/write-report`

生成完整汇报报告。

```
/write-report --speakers 3 --duration 15min
/write-report --speakers 2 --style academic
```

---

## 报告输出格式

每个报告人板块包含：

```
报告人 [X]：[主题名称] ([时长])

攻读目标：...

精读章节：
● 章节号 章节名

汇报讲解板块：
● 要点1（X分钟）：详细解读
● 要点2（X分钟）：详细解读
● 要点3（X分钟）：详细解读

听众理解检查点：
□ 关键概念 — 听众应能复述
□ 核心机制 — 听众应能描述
```

---

## 设计原则

1. **先理解，再汇报** — 生成报告前必须完整解析论文
2. **双层解释** — 每个技术概念同时给出「白话版」和「技术版」
3. **数学公式必须解释** — 不允许直接复制，必须解释直觉含义
4. **实验数据要解读** — 数字背后的意义比数字本身更重要
5. **时间感** — 每个讲解要点标注建议耗时

---

## 输出目录结构

运行命令后，`outputs/` 目录会按论文标题自动创建子目录：

```
outputs/
└── [论文标题]/
    ├── 01_paper_understanding.md   # 论文理解报告
    ├── speaker_assignments.md      # 分工方案
    ├── sections/
    │   ├── 3.1_explanation.md      # 章节精读
    │   └── 3.2_explanation.md
    └── report_[日期].md            # 最终汇报报告
```

---

## 许可证

MIT License
