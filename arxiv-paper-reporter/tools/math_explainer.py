"""
math_explainer.py
将论文中的数学公式转化为直觉性解释。
提供公式识别、参数解析和白话解释生成的工具函数。
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FormulaExplanation:
    raw_formula: str           # 原始 LaTeX 公式
    formula_type: str          # 公式类型标签
    plain_description: str     # 白话解释
    intuition: str             # 直觉理解
    parameters: dict[str, str] # 参数 → 含义 映射
    context: str               # 公式在论文中的上下文


# ── 公式类型识别规则 ─────────────────────────────────────────────

FORMULA_TYPE_PATTERNS = {
    "loss_function": [
        r"\\mathcal\{L\}", r"\\text\{Loss\}", r"L\s*=", r"\\ell",
        r"cross.entropy", r"KL\s*\(", r"\\text\{BCE\}",
    ],
    "attention": [
        r"\\text\{Attention\}", r"\\text\{softmax\}.*QK",
        r"QK\^T", r"\\alpha.*v_",
    ],
    "normalization": [
        r"\\text\{LayerNorm\}", r"\\text\{BatchNorm\}",
        r"\\frac\{x.*\\mu\}", r"\\sigma\^2",
    ],
    "probability": [
        r"p\(", r"P\(", r"\\mathbb\{P\}", r"\\Pr\(",
        r"\\sim", r"\\propto",
    ],
    "gradient": [
        r"\\nabla", r"\\frac\{\\partial", r"\\theta.*\\leftarrow",
    ],
    "matrix_operation": [
        r"\\mathbf\{W\}", r"\\mathbf\{A\}", r"\\otimes",
        r"\\cdot", r"\^\{-1\}",
    ],
}


def classify_formula(latex: str) -> str:
    """根据 LaTeX 内容猜测公式类型。"""
    for formula_type, patterns in FORMULA_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, latex, re.IGNORECASE):
                return formula_type
    return "general"


# ── 常见公式组件的中文解释模板 ────────────────────────────────────

COMPONENT_EXPLANATIONS = {
    r"\\text\{softmax\}": "softmax（将向量归一化为概率分布，所有值之和为1）",
    r"\\text\{LayerNorm\}": "层归一化（将每层输出标准化，稳定训练）",
    r"\\mathbb\{E\}": "期望值（对某个分布取平均）",
    r"\\nabla": "梯度（指向函数增长最快的方向）",
    r"\\frac\{\\partial": "偏导数（固定其他变量，对某一变量求导）",
    r"\\sigma": "sigmoid函数 或 标准差（取决于上下文）",
    r"\\mathcal\{L\}": "损失函数（衡量模型预测与真实值的差距）",
    r"\\alpha": "α（通常表示学习率或注意力权重）",
    r"\\theta": "θ（模型参数，训练目标就是找到最优θ）",
    r"\\text\{KL\}": "KL散度（衡量两个概率分布之间的差异）",
}


def explain_components(latex: str) -> list[str]:
    """识别公式中的关键组件并给出中文解释。"""
    explanations = []
    for pattern, explanation in COMPONENT_EXPLANATIONS.items():
        if re.search(pattern, latex, re.IGNORECASE):
            explanations.append(explanation)
    return explanations


def extract_parameters(latex: str) -> dict[str, str]:
    """
    从 LaTeX 公式中提取可能的参数符号。
    返回符号 → 猜测含义的映射（启发式，非精确）。
    """
    # 常见参数含义库
    known_params = {
        "Q": "Query 矩阵（查询向量）",
        "K": "Key 矩阵（键向量）",
        "V": "Value 矩阵（值向量）",
        "d_k": "键向量的维度（用于缩放点积）",
        "W": "可学习权重矩阵",
        "b": "偏置向量",
        "x": "输入向量",
        "y": "输出向量 或 标签",
        "h": "隐藏状态",
        "z": "潜在变量（latent variable）",
        "\\mu": "均值",
        "\\sigma": "标准差",
        "\\lambda": "正则化系数 或 拉格朗日乘数",
        "\\alpha": "学习率 或 注意力权重",
        "\\beta": "动量系数 或 超参数",
        "N": "样本数量 或 序列长度",
        "T": "时间步 或 温度参数",
        "d": "嵌入维度",
        "L": "层数",
        "H": "注意力头数",
    }

    found = {}
    for symbol, meaning in known_params.items():
        # 简单字符串匹配
        if symbol in latex or symbol.replace("\\", "") in latex:
            found[symbol] = meaning
    return found


def generate_explanation_prompt(
    latex: str,
    context: str = "",
    formula_type: str = "",
) -> str:
    """
    生成用于让 LLM 解释公式的提示词模板。
    可直接传递给 Claude API 使用。
    """
    components = explain_components(latex)
    params = extract_parameters(latex)
    ftype = formula_type or classify_formula(latex)

    component_str = "\n".join(f"  - {c}" for c in components) if components else "  （未识别到标准组件）"
    param_str = "\n".join(f"  - {k}：{v}" for k, v in params.items()) if params else "  （请根据论文上下文判断）"

    prompt = f"""请对以下数学公式进行深度解释，面向有一定机器学习基础但不熟悉该论文的读者。

公式（LaTeX）：
{latex}

公式类型（启发式判断）：{ftype}

已识别的公式组件：
{component_str}

已识别的参数：
{param_str}

上下文（来自论文）：
{context if context else "（未提供）"}

请按以下格式输出：

【白话解释】
用一两句话，像对朋友解释一样说明这个公式在做什么。

【直觉理解】
这个公式背后的设计动机是什么？为什么要这样设计而不用更简单的方式？

【参数说明】
逐一说明公式中每个符号/参数的含义及其作用。

【与相关工作的联系】
这个公式是否是某个经典公式的变体或改进？如何理解这种变化？
"""
    return prompt


def batch_extract_formulas(text: str) -> list[str]:
    """从论文文本中批量提取 LaTeX 公式。"""
    patterns = [
        r"\$\$(.+?)\$\$",           # $$...$$
        r"\$([^$\n]+?)\$",          # $...$
        r"\\begin\{equation\}(.+?)\\end\{equation\}",
        r"\\begin\{align\}(.+?)\\end\{align\}",
        r"\\\[(.+?)\\\]",
    ]
    formulas = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        formulas.extend(m.strip() for m in matches if len(m.strip()) > 3)
    return formulas


if __name__ == "__main__":
    # 演示：解释一个注意力机制公式
    demo_formula = r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V"
    demo_context = "We adopt the scaled dot-product attention following Vaswani et al. (2017)."

    print("公式：", demo_formula)
    print("类型：", classify_formula(demo_formula))
    print()
    print("组件：")
    for c in explain_components(demo_formula):
        print(" -", c)
    print()
    print("参数：")
    for k, v in extract_parameters(demo_formula).items():
        print(f"  {k}：{v}")
    print()
    print("── 生成的解释提示词 ──")
    print(generate_explanation_prompt(demo_formula, demo_context))
