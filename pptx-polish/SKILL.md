---
name: pptx-polish
description: "用 python-pptx 对 .pptx 文件进行排版修复：字号统一、行间距、文本溢出、副标题横线遮挡。触发词：'修复ppt'、'ppt排版'、'pptx字号'、'ppt行间距'、'/pptx-polish'。"
origin: custom
---

# pptx-polish — PPT 排版修复技能

用 python-pptx 对学术/汇报 PPT 进行系统性排版修复。核心能力：字号统一、行间距扩展、文本溢出自动扩高、副标题/分隔线位置修正。

---

## When to Activate

- 用户说"ppt字体太小"、"行间距太窄"、"文字溢出边框"
- 用户说"副标题被横线挡住"、"分隔线盖住文字"
- 用户输入 `/pptx-polish`
- 用户提供 `.pptx` 路径并要求修复排版

---

## 执行顺序约定（不可颠倒）

```
Step 0  备份原文件
Step 1  字号统一（≥ 18pt）
Step 2  行间距 1.5
Step 3  文本溢出扩高 + spAutoFit
Step 4  副标题/分隔线位置修正
验证    几何约束 + 溢出检测
```

**Step 3 必须在 Step 4 之前**：Step 3 扩高副标题框会改变其 bottom，Step 4 必须读到最新 bottom 才能正确定位分隔线。

---

## Step 0：备份

```python
import shutil
shutil.copy(SRC, SRC.replace('.pptx', '.bak.pptx'))
```

---

## Step 1：字号统一（≥ 18pt）

```python
from pptx import Presentation
from pptx.util import Pt

MIN_PT = 18

def is_page_number(shape):
    """页码框：宽度 < 1M EMU 且文本含 '/' + 数字"""
    if not shape.has_text_frame or shape.width >= 1_000_000:
        return False
    t = shape.text_frame.text
    return '/' in t and any(c.isdigit() for c in t)

prs = Presentation(SRC)
for slide in prs.slides:
    for shape in slide.shapes:
        if not shape.has_text_frame or is_page_number(shape):
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                sz = run.font.size
                if sz is None or sz.pt < MIN_PT:
                    run.font.size = Pt(MIN_PT)
prs.save(SRC)
```

> 页码框保留原小字号；标题等已 ≥ 18pt 的不改动。

---

## Step 2：行间距 1.5

```python
prs = Presentation(SRC)
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                para.line_spacing = 1.5
prs.save(SRC)
```

---

## Step 3：文本溢出扩高 + spAutoFit

**高度估算公式**

```
每段高度 = max_font_pt × 1.5 × 12700   (实线段)
每段高度 = max_font_pt × 0.3 × 12700   (空段落)
总需高度 = Σ各段高度 + PADDING(80000)
```

```python
from pptx.util import Emu
from pptx.oxml.ns import qn
from lxml import etree

PADDING    = 80_000
EMPTY_RATIO = 0.3

def para_needed_h(para):
    max_pt = max((r.font.size.pt for r in para.runs if r.font.size), default=18.0)
    ratio  = 1.5 if para.text.strip() else EMPTY_RATIO
    return int(max_pt * ratio * 12700)

def needed_height(shape):
    return PADDING + sum(para_needed_h(p) for p in shape.text_frame.paragraphs)

def set_sp_autofit(shape):
    txBody  = shape.text_frame._txBody
    bodyPr  = txBody.find(qn('a:bodyPr'))
    if bodyPr is None:
        return
    for tag in [qn('a:normAutofit'), qn('a:spAutoFit'), qn('a:noAutofit')]:
        el = bodyPr.find(tag)
        if el is not None:
            bodyPr.remove(el)
    etree.SubElement(bodyPr, qn('a:spAutoFit'))

prs     = Presentation(SRC)
slide_h = prs.slide_height

for slide in prs.slides:
    # ⚠️ 容器过滤条件必须排除细分隔线（height > 100_000）
    containers = [
        s for s in slide.shapes
        if (not s.has_text_frame or not s.text_frame.text.strip())
        and s.width > 500_000
        and s.height > 100_000
    ]

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        set_sp_autofit(shape)

        req = needed_height(shape)
        if shape.height >= req or shape.top + req > slide_h:
            continue

        delta   = req - shape.height
        old_bot = shape.top + shape.height
        shape.height = Emu(req)
        new_bot = shape.top + shape.height

        # 同步扩高真实容器矩形
        for c in containers:
            c_bot    = c.top + c.height
            h_cover  = (c.left <= shape.left + 10_000 and
                        c.left + c.width >= shape.left + shape.width - 10_000)
            contained = c.top <= shape.top and abs(c_bot - old_bot) < 50_000
            if h_cover and contained and c_bot < new_bot:
                c.height = Emu(c.height + delta)

prs.save(SRC)
```

---

## Step 4：副标题/分隔线位置修正

**目标布局**（以 16:9 幻灯片，slide_height=6858000 为例）：

```
主标题   top ≈  62880   bottom ≈  703000
副标题   top ≈ 684672   bottom ≈ 1107572
分隔线   top ≈ 1119572  h = 25400
正文区   top ≈ 1143000
```

约束：`line.top > subtitle.bottom`

```python
SHIFT = 120_000  # 主标题/副标题整体上移量

for si, slide in enumerate(prs.slides):
    if si == 0:
        continue   # 封面布局独立，跳过

    title_s = subtitle_s = line_s = None

    for shape in slide.shapes:
        # 主标题：TextBox，top 40k~200k，宽 > 8M
        if (shape.has_text_frame
                and 40_000 < shape.top < 200_000
                and shape.width > 8_000_000):
            title_s = shape
        # 副标题：TextBox，top 650k~900k，宽 > 8M
        elif (shape.has_text_frame
                and 650_000 < shape.top < 900_000
                and shape.width > 8_000_000):
            subtitle_s = shape
        # 分隔线：无文字细矩形，宽 > 10M，高 < 100k，top > 900k
        elif (not (shape.has_text_frame and shape.text_frame.text.strip())
                and shape.width > 10_000_000
                and shape.height < 100_000
                and shape.top > 900_000):
            line_s = shape

    if title_s:
        title_s.top = Emu(title_s.top - SHIFT)
    if subtitle_s:
        subtitle_s.top   = Emu(subtitle_s.top - SHIFT)
        new_sub_bottom   = subtitle_s.top + subtitle_s.height
    else:
        new_sub_bottom   = 1_100_000

    if line_s:
        line_s.height = Emu(25_400)                        # 重置为细线
        line_s.top    = Emu(new_sub_bottom + 12_000)       # 副标题之下 12k

prs.save(SRC)
```

---

## 验证（每步后必跑）

```python
prs = Presentation(SRC)

print("── 几何约束：分隔线 vs 副标题 ──")
all_ok = True
for si, slide in enumerate(prs.slides):
    sub_bot = line_top = None
    for s in slide.shapes:
        if s.has_text_frame and 650_000 < s.top < 900_000 and s.width > 8_000_000:
            sub_bot = s.top + s.height
        if (not (s.has_text_frame and s.text_frame.text.strip())
                and s.width > 10_000_000 and s.height < 100_000
                and s.top > 900_000):
            line_top = s.top
    if sub_bot and line_top:
        gap  = line_top - sub_bot
        mark = "✓" if gap > 0 else "✗ 仍遮挡!"
        if gap <= 0:
            all_ok = False
        print(f"  Slide {si+1:2d}: gap={gap:+d}  {mark}")
if all_ok:
    print("  全部通过")

print("\n── 文本溢出检测 ──")
overflow = 0
for si, slide in enumerate(prs.slides):
    for s in slide.shapes:
        if not s.has_text_frame:
            continue
        req = needed_height(s)
        if s.height < req and s.top + req <= prs.slide_height:
            print(f"  Slide {si+1} {s.name}: h={s.height} need={req}")
            overflow += 1
print(f"  溢出计数: {overflow}")
```

---

## 常见陷阱速查

| 现象 | 根因 | 修复方式 |
|------|------|---------|
| 分隔线扩高后覆盖副标题 | Step 3 容器检测把细线误判为容器 | 容器过滤加 `s.height > 100_000` |
| Step 4 修复后分隔线仍遮挡 | Step 3 扩高了副标题，Step 4 用旧 bottom 定位 | 严格按 Step 3 → Step 4 顺序，Step 4 实时读 `subtitle.top + subtitle.height` |
| 页码框字号 18pt 后溢出 | 框宽 < 1M EMU 容不下大字号 | `is_page_number()` 过滤，保留原字号 |
| 空段落高估导致大量误报 | 空段按 1.5 倍行高计算 | 空段用 `EMPTY_RATIO=0.3` |
| 两步修复互相打架 | 步骤间未交叉校验 | 每步结束后运行验证块，发现冲突立即修复 |
