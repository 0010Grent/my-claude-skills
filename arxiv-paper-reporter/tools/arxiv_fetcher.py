"""
arxiv_fetcher.py
获取 arxiv 论文的元数据与正文内容。
支持通过 arxiv ID 或完整链接获取论文。
"""

import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str
    updated: str
    categories: list[str]
    pdf_url: str
    abs_url: str
    affiliations: list[str] = field(default_factory=list)
    full_text: Optional[str] = None


def extract_arxiv_id(input_str: str) -> str:
    """从 URL 或字符串中提取 arxiv ID（如 2401.12345）。"""
    # 匹配常见格式：2401.12345 或 abs/2401.12345v2
    patterns = [
        r"arxiv\.org/abs/([0-9]+\.[0-9]+(?:v\d+)?)",
        r"arxiv\.org/pdf/([0-9]+\.[0-9]+(?:v\d+)?)",
        r"\b([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str, re.IGNORECASE)
        if match:
            return match.group(1)
    raise ValueError(f"无法从输入中提取 arxiv ID：{input_str}")


def fetch_paper_metadata(arxiv_id: str) -> ArxivPaper:
    """通过 arxiv API 获取论文元数据。"""
    # 去掉版本号用于 API 查询
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    api_url = f"https://export.arxiv.org/api/query?id_list={clean_id}&max_results=1"

    with urllib.request.urlopen(api_url, timeout=30) as response:
        content = response.read().decode("utf-8")

    root = ET.fromstring(content)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ValueError(f"未找到论文：{arxiv_id}")

    title = entry.findtext("atom:title", namespaces=ns).strip().replace("\n", " ")
    abstract = entry.findtext("atom:summary", namespaces=ns).strip().replace("\n", " ")
    published = entry.findtext("atom:published", namespaces=ns, default="")[:10]
    updated = entry.findtext("atom:updated", namespaces=ns, default="")[:10]

    authors = [
        a.findtext("atom:name", namespaces=ns)
        for a in entry.findall("atom:author", ns)
    ]

    categories = [
        cat.get("term", "")
        for cat in entry.findall("atom:category", ns)
    ]

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        published=published,
        updated=updated,
        categories=categories,
        pdf_url=pdf_url,
        abs_url=abs_url,
    )


def fetch_paper(input_str: str) -> ArxivPaper:
    """
    主入口：接受 arxiv 链接或 ID，返回 ArxivPaper 对象。

    用法：
        paper = fetch_paper("https://arxiv.org/abs/2401.12345")
        paper = fetch_paper("2401.12345")
    """
    arxiv_id = extract_arxiv_id(input_str)
    paper = fetch_paper_metadata(arxiv_id)
    return paper


def format_paper_info(paper: ArxivPaper) -> str:
    """将论文元数据格式化为可读的文本摘要。"""
    authors_str = ", ".join(paper.authors[:5])
    if len(paper.authors) > 5:
        authors_str += f" 等{len(paper.authors)}人"

    return f"""📄 论文基本信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
标题：{paper.title}
作者：{authors_str}
发表时间：{paper.published}
最后更新：{paper.updated}
arxiv ID：{paper.arxiv_id}
分类：{', '.join(paper.categories[:3])}
链接：{paper.abs_url}
PDF：{paper.pdf_url}

📝 摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{paper.abstract}
"""


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法：python arxiv_fetcher.py <arxiv链接或ID>")
        sys.exit(1)

    paper = fetch_paper(sys.argv[1])
    print(format_paper_info(paper))
