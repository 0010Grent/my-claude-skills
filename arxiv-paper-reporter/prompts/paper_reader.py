"""
paper_reader.py
论文解析核心逻辑：协调各工具模块，完成论文理解的完整流程。
输出结构化的论文理解对象，供报告生成器使用。
"""

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.arxiv_fetcher import fetch_paper, ArxivPaper
from tools.pdf_parser import parse_pdf, ParsedPaper
from tools.math_explainer import batch_extract_formulas, classify_formula


@dataclass
class PaperUnderstanding:
    """论文完整理解结果的数据结构。"""

    # 基本信息
    title: str
    authors: list[str]
    arxiv_id: str
    published: str
    source_url: str

    # 结构理解
    abstract: str
    sections: list[dict]       # [{number, title, summary, key_points}]
    glossary: dict[str, str]   # 关键术语 → 中文解释

    # 四维分析
    problem_definition: dict   # 问题定义维度
    algorithm_core: dict       # 算法核心维度
    experiments: dict          # 数据与实验维度
    results: dict              # 结果与意义维度

    # 公式列表
    formulas: list[dict]       # [{raw, type, explanation_prompt}]

    # 报告辅助
    paper_map_ascii: str       # 论文逻辑框架 ASCII 图
    recommended_sections: list[str]  # 推荐精读章节
    difficulty_map: dict[str, str]   # 章节 → 难度评级

    # 元数据
    raw_text_path: Optional[str] = None


def load_paper_from_arxiv(arxiv_input: str) -> tuple[ArxivPaper, str]:
    """从 arxiv 获取论文，返回 (ArxivPaper, 全文摘要文本)。"""
    paper = fetch_paper(arxiv_input)
    # 摘要作为初步文本（全文需要下载 PDF）
    text_content = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
    return paper, text_content


def load_paper_from_pdf(pdf_path: str) -> tuple[ParsedPaper, str]:
    """从 PDF 解析论文，返回 (ParsedPaper, 全文文本)。"""
    parsed = parse_pdf(pdf_path)
    return parsed, parsed.raw_text


def build_section_summaries(sections) -> list[dict]:
    """构建章节摘要列表（占位结构，由 LLM 填充内容）。"""
    result = []
    for s in sections:
        result.append({
            "number": s.number if hasattr(s, "number") else "",
            "title": s.title if hasattr(s, "title") else str(s),
            "summary": "",      # 待 LLM 填充
            "key_points": [],   # 待 LLM 填充
            "word_count": len(getattr(s, "content", "").split()),
        })
    return result


def generate_paper_map_template(title: str) -> str:
    """生成论文逻辑框架 ASCII 图模板。"""
    return f"""
论文逻辑框架：{title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[问题背景]          →    [现有方法的不足]    →    [本文方案]
    │                           │                       │
    ↓                           ↓                       ↓
[应用场景]            [Gap分析/Motivation]      [核心创新点]
                                                        │
                                          ┌─────────────┴─────────────┐
                                          ↓                           ↓
                                    [算法模块1]                  [算法模块2]
                                    （待填充）                   （待填充）
                                          │                           │
                                          └─────────────┬─────────────┘
                                                        ↓
                                              [实验验证框架]
                                    ┌──────────┬─────────┴──────────┐
                                    ↓          ↓                    ↓
                              [主实验]     [消融实验]           [分析实验]
                                    └──────────┴────────────────────┘
                                                        ↓
                                                 [结论与展望]

（此框架为模板，请根据论文具体内容填充各节点内容）
"""


def analyze_section_difficulty(sections: list[dict]) -> dict[str, str]:
    """
    启发式估算各章节阅读难度。
    基于词数和技术词汇密度。
    """
    difficulty_map = {}
    tech_keywords = [
        "algorithm", "gradient", "loss", "attention", "encoder", "decoder",
        "embedding", "transformer", "convolution", "regularization",
        "optimization", "backpropagation", "latent", "distribution",
    ]

    for s in sections:
        content = s.get("content", "")
        word_count = s.get("word_count", 0)
        if not word_count and content:
            word_count = len(content.split())

        # 技术词汇密度
        tech_density = sum(
            1 for kw in tech_keywords if kw.lower() in content.lower()
        )

        if word_count < 300 and tech_density < 3:
            difficulty = "轻量 ⭐"
        elif word_count < 800 or tech_density < 6:
            difficulty = "中等 ⭐⭐⭐"
        else:
            difficulty = "较重 ⭐⭐⭐⭐"

        key = f"{s.get('number', '')} {s.get('title', '')}".strip()
        difficulty_map[key] = difficulty

    return difficulty_map


def create_understanding(
    title: str,
    authors: list[str],
    arxiv_id: str,
    published: str,
    source_url: str,
    abstract: str,
    sections: list,
    raw_formulas: list[str],
) -> PaperUnderstanding:
    """
    主函数：创建完整的 PaperUnderstanding 对象。
    内容部分（四维分析等）留待 LLM 调用时填充。
    """
    section_dicts = build_section_summaries(sections)
    formulas = [
        {
            "raw": f,
            "type": classify_formula(f),
            "explanation": "",  # 待 LLM 填充
        }
        for f in raw_formulas[:20]  # 最多处理前20个公式
    ]

    return PaperUnderstanding(
        title=title,
        authors=authors,
        arxiv_id=arxiv_id,
        published=published,
        source_url=source_url,
        abstract=abstract,
        sections=section_dicts,
        glossary={},
        problem_definition={
            "problem": "",
            "existing_limitations": "",
            "importance": "",
        },
        algorithm_core={
            "method_overview": "",
            "key_innovations": [],
            "training_pipeline": "",
            "inference_pipeline": "",
        },
        experiments={
            "datasets": [],
            "baselines": [],
            "ablation_studies": [],
            "evaluation_metrics": [],
        },
        results={
            "main_results": "",
            "significance": "",
            "reliability": "",
            "limitations": "",
            "future_work": "",
        },
        formulas=formulas,
        paper_map_ascii=generate_paper_map_template(title),
        recommended_sections=[],
        difficulty_map=analyze_section_difficulty(section_dicts),
    )


def save_understanding(understanding: PaperUnderstanding, output_dir: str) -> str:
    """将理解结果保存为 JSON 和 Markdown 两种格式。"""
    os.makedirs(output_dir, exist_ok=True)

    # 保存 JSON（供程序读取）
    json_path = os.path.join(output_dir, "understanding.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(understanding), f, ensure_ascii=False, indent=2)

    # 保存 Markdown（供人阅读）
    md_path = os.path.join(output_dir, "01_paper_understanding.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(format_understanding_md(understanding))

    return md_path


def format_understanding_md(u: PaperUnderstanding) -> str:
    """将 PaperUnderstanding 渲染为 Markdown 报告。"""
    authors_str = ", ".join(u.authors[:5])
    if len(u.authors) > 5:
        authors_str += f" 等{len(u.authors)}人"

    lines = [
        f"# 论文理解报告\n",
        f"**标题**：{u.title}",
        f"**作者**：{authors_str}",
        f"**发表时间**：{u.published}",
        f"**来源**：{u.source_url}",
        f"\n---\n",
        f"## 摘要\n",
        u.abstract,
        f"\n---\n",
        f"## 论文逻辑框架\n",
        f"```\n{u.paper_map_ascii}\n```",
        f"\n---\n",
        f"## 章节结构\n",
    ]

    for s in u.sections:
        indent = "  " * (s.get("level", 1) - 1)
        lines.append(f"{indent}- **{s.get('number', '')}** {s.get('title', '')}")

    lines += [
        f"\n---\n",
        f"## 难度分布\n",
    ]
    for section_key, difficulty in u.difficulty_map.items():
        lines.append(f"- {section_key}：{difficulty}")

    if u.formulas:
        lines += [f"\n---\n", f"## 识别到的关键公式（{len(u.formulas)} 个）\n"]
        for i, f in enumerate(u.formulas[:10], 1):
            lines.append(f"**公式{i}** ({f['type']})：`{f['raw'][:80]}...`")

    return "\n".join(lines)
