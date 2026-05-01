"""
report_generator.py
汇报报告生成核心逻辑：将论文理解结果转化为多报告人格式的汇报文档。
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SpeakerSection:
    """单个报告人的板块内容。"""
    speaker_id: str             # "A", "B", "C"...
    topic: str                  # 板块主题
    chapters: list[str]         # 负责的章节列表
    duration_min: int           # 建议时长（分钟）
    study_goal: str             # 攻读目标
    key_points: list[dict]      # 讲解要点列表 [{title, content, duration_min}]
    comprehension_checks: list[str]  # 听众理解检查点
    difficulty: str = "中等"


@dataclass
class ReportConfig:
    """报告生成配置。"""
    num_speakers: int = 3
    duration_per_speaker: int = 15    # 每人分钟数
    style: str = "mixed"              # academic / casual / mixed
    output_path: str = ""
    custom_assignments: dict = field(default_factory=dict)  # 自定义分配


@dataclass
class FinalReport:
    """最终汇报报告。"""
    paper_title: str
    paper_url: str
    report_date: str
    speakers: list[str]
    total_duration_min: int
    overview: str
    sections: list[SpeakerSection]
    discussion_questions: list[str]
    related_papers: list[str]
    config: ReportConfig


def estimate_duration(chapter_count: int, difficulty: str = "中等") -> int:
    """根据章节数和难度估算讲解时长。"""
    base = chapter_count * 5
    multiplier = {"轻量": 0.7, "中等": 1.0, "较重": 1.4, "专家": 1.8}.get(difficulty, 1.0)
    return max(10, int(base * multiplier))


def split_chapters_evenly(
    all_sections: list[dict],
    num_speakers: int,
    difficulty_map: dict,
) -> list[list[dict]]:
    """
    将章节均匀分配给报告人，尽量保证内容量和难度均衡。
    简单策略：按权重轮流分配。
    """
    # 计算每个章节的权重（词数 + 难度加成）
    def section_weight(s: dict) -> float:
        wc = s.get("word_count", 500)
        key = f"{s.get('number', '')} {s.get('title', '')}".strip()
        diff = difficulty_map.get(key, "中等")
        multiplier = {"轻量": 0.6, "中等": 1.0, "较重": 1.5}.get(diff, 1.0)
        return wc * multiplier

    # 按贪心策略分配：总是将下一章节分给当前负担最轻的报告人
    speaker_loads = [0.0] * num_speakers
    assignments = [[] for _ in range(num_speakers)]

    for section in all_sections:
        min_speaker = speaker_loads.index(min(speaker_loads))
        assignments[min_speaker].append(section)
        speaker_loads[min_speaker] += section_weight(section)

    return assignments


def build_speaker_section(
    speaker_id: str,
    assigned_chapters: list[dict],
    config: ReportConfig,
    difficulty_map: dict,
) -> SpeakerSection:
    """为单个报告人构建板块结构（内容占位符，由 LLM 填充）。"""
    chapter_nums = [s.get("number", "") for s in assigned_chapters]
    chapter_titles = [s.get("title", "") for s in assigned_chapters]
    topic = _infer_topic(chapter_titles)

    # 估算难度
    difficulties = []
    for s in assigned_chapters:
        key = f"{s.get('number', '')} {s.get('title', '')}".strip()
        difficulties.append(difficulty_map.get(key, "中等"))
    avg_difficulty = max(set(difficulties), key=difficulties.count) if difficulties else "中等"

    # 占位讲解要点（由 LLM 根据论文实际内容替换）
    key_points = [
        {
            "title": f"讲解要点{i+1}（待填充）",
            "content": "根据论文实际内容填充",
            "duration_min": config.duration_per_speaker // 3,
        }
        for i in range(3)
    ]

    return SpeakerSection(
        speaker_id=speaker_id,
        topic=topic,
        chapters=chapter_nums,
        duration_min=config.duration_per_speaker,
        study_goal=f"理解{topic}的核心思路，能够向听众清晰解释",
        key_points=key_points,
        comprehension_checks=[
            "（根据论文内容填充关键概念检查点）",
            "（根据论文内容填充核心机制检查点）",
        ],
        difficulty=avg_difficulty,
    )


def _infer_topic(titles: list[str]) -> str:
    """根据章节标题推断板块主题（简单关键词匹配）。"""
    all_titles = " ".join(titles).lower()
    if any(w in all_titles for w in ["introduction", "related", "background", "motivation"]):
        return "研究背景与动机"
    if any(w in all_titles for w in ["method", "model", "architecture", "approach", "framework"]):
        return "方法与模型架构"
    if any(w in all_titles for w in ["experiment", "evaluation", "result", "performance"]):
        return "实验设计与结果分析"
    if any(w in all_titles for w in ["analysis", "ablation", "discussion"]):
        return "深入分析与讨论"
    if any(w in all_titles for w in ["conclusion", "future", "limitation"]):
        return "结论与展望"
    return "论文核心内容"


def generate_report(
    paper_title: str,
    paper_url: str,
    sections: list[dict],
    difficulty_map: dict,
    config: ReportConfig,
) -> FinalReport:
    """
    主函数：生成完整汇报报告结构。
    """
    speaker_ids = [chr(65 + i) for i in range(config.num_speakers)]  # A, B, C...

    # 分配章节
    if config.custom_assignments:
        # 用户自定义分配
        assignments = [
            [s for s in sections if s.get("number", "") in config.custom_assignments.get(sid, [])]
            for sid in speaker_ids
        ]
    else:
        assignments = split_chapters_evenly(sections, config.num_speakers, difficulty_map)

    # 构建各报告人板块
    speaker_sections = [
        build_speaker_section(speaker_ids[i], assignments[i], config, difficulty_map)
        for i in range(config.num_speakers)
    ]

    total_duration = sum(s.duration_min for s in speaker_sections) + 5  # +5分钟开场

    return FinalReport(
        paper_title=paper_title,
        paper_url=paper_url,
        report_date=datetime.now().strftime("%Y年%m月%d日"),
        speakers=speaker_ids,
        total_duration_min=total_duration,
        overview="（待 LLM 根据论文内容填充论文概述）",
        sections=speaker_sections,
        discussion_questions=[
            "（待 LLM 根据论文内容生成讨论问题1）",
            "（待 LLM 根据论文内容生成讨论问题2）",
            "（待 LLM 根据论文内容生成讨论问题3）",
        ],
        related_papers=[],
        config=config,
    )


def render_report_markdown(report: FinalReport) -> str:
    """将 FinalReport 渲染为完整的 Markdown 汇报文档。"""
    speakers_str = "、".join(f"报告人{s}" for s in report.speakers)
    lines = [
        "━" * 56,
        "# 论文解读汇报报告",
        "",
        f"**论文标题**：{report.paper_title}",
        f"**论文来源**：{report.paper_url}",
        f"**报告日期**：{report.report_date}",
        f"**报告人**：{speakers_str}",
        f"**预计总时长**：约 {report.total_duration_min} 分钟",
        "━" * 56,
        "",
        "## 📋 开场概述（5分钟）",
        "",
        report.overview,
        "",
        "---",
        "",
    ]

    for section in report.sections:
        lines += [
            f"## 报告人{section.speaker_id}：{section.topic}（{section.duration_min}分钟）",
            "",
            f"**攻读目标**：{section.study_goal}",
            "",
            "**精读章节**：",
        ]
        for ch in section.chapters:
            lines.append(f"● 章节 {ch}")

        lines += ["", "**汇报讲解板块**：", ""]
        for kp in section.key_points:
            lines += [
                f"### ● {kp['title']}（约 {kp['duration_min']} 分钟）",
                "",
                kp["content"],
                "",
            ]

        lines += ["**听众理解检查点**：", ""]
        for check in section.comprehension_checks:
            lines.append(f"□ {check}")

        lines += ["", "---", ""]

    lines += [
        "## ❓ 推荐讨论问题",
        "",
    ]
    for i, q in enumerate(report.discussion_questions, 1):
        lines.append(f"{i}. {q}")

    if report.related_papers:
        lines += ["", "## 📎 相关资源", ""]
        for ref in report.related_papers:
            lines.append(f"- {ref}")

    return "\n".join(lines)


def save_report(report: FinalReport, output_dir: str) -> str:
    """保存报告到文件。"""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    md_path = os.path.join(output_dir, f"report_{date_str}.md")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_report_markdown(report))

    return md_path
