"""
pdf_parser.py
解析 PDF 格式的学术论文，提取文本、章节结构和图表标题。
依赖：pdfminer.six 或 pymupdf（fitz）
"""

import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Section:
    number: str          # 如 "3.1"
    title: str           # 如 "Attention Mechanism"
    content: str         # 章节正文
    level: int           # 标题层级（1=一级，2=二级）
    page_start: int = 0


@dataclass
class ParsedPaper:
    title: str
    authors: list[str]
    abstract: str
    sections: list[Section]
    figures: list[str]    # 图标题列表
    tables: list[str]     # 表标题列表
    references: list[str]
    raw_text: str
    file_path: str


# ── 尝试导入 PDF 解析库 ──────────────────────────────────────────

def _try_import_fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        return None

def _try_import_pdfminer():
    try:
        from pdfminer.high_level import extract_text
        return extract_text
    except ImportError:
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 文件提取全文文本。"""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{pdf_path}")

    # 优先使用 PyMuPDF（更快、保留布局更好）
    fitz = _try_import_fitz()
    if fitz:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return "\n".join(pages)

    # 回退到 pdfminer
    extract_text = _try_import_pdfminer()
    if extract_text:
        return extract_text(pdf_path)

    raise ImportError(
        "未安装 PDF 解析库。请运行：\n"
        "  pip install pymupdf\n"
        "或：\n"
        "  pip install pdfminer.six"
    )


def detect_sections(text: str) -> list[Section]:
    """启发式识别论文章节结构。"""
    sections = []
    # 匹配常见章节格式：
    #   "1 Introduction"  "2.1 Related Work"  "A Appendix"
    section_pattern = re.compile(
        r"^(\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\s{1,4}([A-Z][^\n]{2,80})\s*$",
        re.MULTILINE,
    )

    matches = list(section_pattern.finditer(text))
    for i, match in enumerate(matches):
        number = match.group(1)
        title = match.group(2).strip()
        level = number.count(".") + 1

        # 提取本章节内容（到下一章节开始前）
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        sections.append(Section(
            number=number,
            title=title,
            content=content,
            level=level,
        ))

    return sections


def extract_abstract(text: str) -> str:
    """提取摘要部分。"""
    # 匹配 Abstract 到第一个章节标题之间的文本
    match = re.search(
        r"(?:Abstract|ABSTRACT)\s*\n(.*?)(?=\n\s*(?:1\s|Introduction|INTRODUCTION))",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip().replace("\n", " ")
    return ""


def extract_figures_tables(text: str) -> tuple[list[str], list[str]]:
    """提取图表标题。"""
    figure_pattern = re.compile(r"(?:Figure|Fig\.?)\s+(\d+)[.:]?\s*([^\n]+)", re.IGNORECASE)
    table_pattern = re.compile(r"Table\s+(\d+)[.:]?\s*([^\n]+)", re.IGNORECASE)

    figures = [f"Figure {m.group(1)}: {m.group(2).strip()}" for m in figure_pattern.finditer(text)]
    tables = [f"Table {m.group(1)}: {m.group(2).strip()}" for m in table_pattern.finditer(text)]

    return figures, tables


def parse_pdf(pdf_path: str) -> ParsedPaper:
    """
    主入口：解析 PDF 论文，返回结构化的 ParsedPaper 对象。

    用法：
        paper = parse_pdf("/path/to/paper.pdf")
        print(paper.abstract)
        for section in paper.sections:
            print(f"{section.number} {section.title}")
    """
    raw_text = extract_text_from_pdf(pdf_path)
    abstract = extract_abstract(raw_text)
    sections = detect_sections(raw_text)
    figures, tables = extract_figures_tables(raw_text)

    # 简单提取标题（通常在第一页最顶部）
    first_page_lines = raw_text.split("\n")[:20]
    title_candidates = [l.strip() for l in first_page_lines if len(l.strip()) > 20]
    title = title_candidates[0] if title_candidates else os.path.basename(pdf_path)

    return ParsedPaper(
        title=title,
        authors=[],  # 作者提取较复杂，留给 LLM 处理
        abstract=abstract,
        sections=sections,
        figures=figures,
        tables=tables,
        references=[],
        raw_text=raw_text,
        file_path=pdf_path,
    )


def format_structure(paper: ParsedPaper) -> str:
    """将解析结果格式化为章节目录。"""
    lines = [f"📚 论文章节结构（共 {len(paper.sections)} 节）", "━" * 40]
    for s in paper.sections:
        indent = "  " * (s.level - 1)
        lines.append(f"{indent}{s.number}  {s.title}  ({len(s.content.split())} 词)")
    lines.append("")
    lines.append(f"图：{len(paper.figures)} 个  表：{len(paper.tables)} 个")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法：python pdf_parser.py <PDF路径>")
        sys.exit(1)

    paper = parse_pdf(sys.argv[1])
    print(f"标题：{paper.title}")
    print(f"摘要：{paper.abstract[:200]}...")
    print()
    print(format_structure(paper))
