---
name: manimgl-3b1b
description: 使用 manimgl (3Blue1Brown 库) 制作概念阐释动画，输出 MP4 或 GIF，用于学术汇报/PPT 嵌入。深色背景、LaTeX 公式、ValueTracker 动态数值、慢速播放。
---

# manimgl 3B1B 风格概念动画

用 manimgl（3Blue1Brown 的个人动画库）制作以概念阐释为导向的动画。目标：让复杂的数学和算法原理变得可视化、可理解。

## 何时激活

- 用户需要将数学公式、算法流程、数据流可视化为动画
- 输出用于 PPT/Keynote 嵌入（GIF 或 MP4）
- 用户提到"3Blue1Brown 风格"或"manim 动画"
- 需要慢速逐步展示复杂概念的推导过程

## 环境依赖

| 组件 | 版本 | 位置 | 用途 |
|------|------|------|------|
| manimgl | 1.7.2 | `/Users/fuy/Desktop/manim/manimlib/` | editable install，源码即运行时 |
| TinyTeX | TeX Live 2026 | `~/Library/TinyTeX/bin/universal-darwin/` | LaTeX → DVI → SVG 渲染链 |
| ffmpeg | 7.1.1+ | brew | MP4 → GIF 转换 |
| Python | 3.12 | miniforge conda base | 运行环境 |

**关键**：manimgl 使用 `manimlib`（注意 lib 结尾），社区版使用 `manim`。两者 API 不同，不可混用。

## 渲染命令

```bash
# 必须在每个 bash 命令前 export PATH（Claude Code 子进程不继承 .zshrc）
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"

# 渲染 MP4（--hd = 1920×1080，-w = write to file 不打开窗口）
cd <project_dir>
manimgl animations/<script>.py <SceneName> -w --hd

# MP4 → GIF（15fps，1280px 宽，bayer dithering 减少色带）
ffmpeg -y -i videos/<SceneName>.mp4 \
  -vf "fps=15,scale=1280:-1:flags=lanczos,split[s0][s1];\
[s0]palettegen=stats_mode=diff[p];\
[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 animations/<output>.gif
```

**PPT 嵌入建议**：直接插入 MP4（无 256 色限制），GIF 作为备选。

---

## 视觉风格规范

### 背景与描边
- 背景：manimgl 默认深色 `#1C1C1C`，不修改
- 所有文字和公式必须 `set_backstroke(width=5)`
- 次要标签/注释 `set_backstroke(width=3~4)`

### 色彩系统

| 语义角色 | 颜色常量 | 填充色 | 典型用法 |
|---------|---------|--------|---------|
| 主体/网络 | `BLUE` | `BLUE_E, 0.2~0.3` | Q 网络、Critic、策略执行段 |
| 辅助/对比 | `YELLOW` | `YELLOW_E, 0.1~0.15` | Actor、Demo Buffer、演示数据 |
| 正向/成功 | `GREEN` | `GREEN_E, 0.15` | 奖励、成功率、合并结果 |
| 警告/干预 | `RED` | `RED_E, 0.3` | 人类干预、过估计、风险 |
| 结果/输出 | `TEAL` | `TEAL_E, 0.2` | Q 值显示、最终动作、归纳 |
| 次要元素 | `GREY_A` / `GREY_B` | `GREY_E, 0.3` | 坐标轴、辅助标签、背景框 |

### 字体与字号

| 元素 | 字号 | 字体 |
|------|------|------|
| 场景标题 | 40~42 | `Text("标题", font="Heiti SC")` |
| 核心公式 | 28~36 | `Tex(R"...", t2c={...})` |
| 说明文字 | 20~24 | `Text("说明", font="Heiti SC")` |
| 小标签 | 14~18 | `Text/Tex` |
| 微标注 | 12~14 | `Tex` |

### 几何元素

| 元素 | 参数 |
|------|------|
| 状态节点 | `Circle(radius=0.25~0.4, stroke_width=2~3)` |
| 容器框 | `RoundedRectangle(corner_radius=0.15, stroke_width=3)` |
| 小数据块 | `RoundedRectangle(corner_radius=0.05~0.08, stroke_width=1)` |
| 连接箭头 | `Arrow(stroke_width=2, max_tip_length_to_length_ratio=0.15)` |
| 目标网络标注 | `DashedVMobject(SurroundingRectangle(...), num_dashes=15~20)` |

---

## 时长与节奏规范

目标总时长：**20~36 秒/场景**（适合 PPT 嵌入慢速播放）

| 阶段 | run_time | wait |
|------|----------|------|
| 标题出现 | 1.5s | 0.5s |
| 核心公式/结构 | 2.0~2.5s | 0.5~1.0s |
| 关键动画步骤 | 2.0~3.0s | 0.3~0.5s |
| 过渡/标注 | 0.5~1.0s | 0.3s |
| 最终总结 | 1.5~2.0s | 2.0s |
| 全局 FadeOut | 1.5s | 0.5s |

**原则**：宁慢勿快。每个视觉变化后至少 `wait(0.3)`，让观众消化。

---

## 代码结构模板

```python
from manimlib import *
import numpy as np

class ConceptScene(Scene):
    def construct(self):
        # ═══ 1. 标题 ═══
        title = Text("场景标题", font="Heiti SC", font_size=42)
        title.to_edge(UP, buff=0.3)
        title.set_backstroke(width=5)
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)

        # ═══ 2. 核心公式（如有） ═══
        formula = Tex(
            R"y = r + \gamma \, Q_{\hat\phi}(s', a')",
            font_size=32,
            t2c={"r": GREEN, R"\gamma": YELLOW, R"Q_{\hat\phi}": BLUE}
        )
        formula.next_to(title, DOWN, buff=0.4)
        formula.set_backstroke(width=5)
        self.play(Write(formula), run_time=2.0)
        self.wait(1.0)

        # ═══ 3. 主体动画 ═══
        # ... 具体内容 ...

        # ═══ 4. 总结文字 ═══
        summary = Text("一句话总结核心洞察", font="Heiti SC", font_size=26)
        summary.to_edge(DOWN, buff=0.5)
        summary.set_backstroke(width=5)
        self.play(Write(summary), run_time=2.0)
        self.wait(2.0)

        # ═══ 5. 全局淡出 ═══
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
        self.wait(0.5)
```

---

## 核心动画模式（从实践中提炼）

### 1. ValueTracker + always_redraw：动态数值驱动

用于：分布形状变化、进度条、实时 Q 值更新

```python
alpha_tracker = ValueTracker(0.3)

def get_curve():
    val = alpha_tracker.get_value()
    return axes.get_graph(lambda x: func(x, val), color=YELLOW)

curve = always_redraw(get_curve)
self.add(curve)
self.play(alpha_tracker.animate.set_value(0.9), run_time=3.0)
```

### 2. DecimalNumber + updater：实时数字显示

用于：Q 值逐步回传、参数递增

```python
tracker = ValueTracker(0.0)
number = DecimalNumber(0, num_decimal_places=2, font_size=26, color=TEAL)
number.set_backstroke(width=4)
number.add_updater(lambda m: m.set_value(tracker.get_value()))
self.add(number)
self.play(tracker.animate.set_value(0.81), run_time=2.0)
```

### 3. LaggedStartMap：顺序批量出现

用于：状态链、数据块、轨迹线

```python
self.play(LaggedStartMap(ShowCreation, states, lag_ratio=0.15), run_time=2.0)
self.play(LaggedStartMap(FadeIn, blocks, lag_ratio=0.08), run_time=1.5)
```

### 4. FadeTransform：参数演化

用于：φ₀ → φ₁ → φ₂ 的视觉递进

```python
for step in range(1, 4):
    new_label = Tex(f"\\phi_{step}", font_size=24, color=BLUE_B)
    new_label.move_to(old_label.get_center())
    new_label.set_backstroke(width=4)
    self.play(FadeTransform(old_label, new_label), run_time=1.0)
    old_label = new_label
```

### 5. FlashAround：同步高亮强调

用于：并行更新标记、重要区域闪烁

```python
self.play(
    FlashAround(box_a, color=BLUE, buff=0.05),
    FlashAround(box_b, color=YELLOW, buff=0.05),
    run_time=1.5
)
```

### 6. interpolate_color：颜色梯度

用于：Q 值沿链条递减的视觉编码

```python
colors = [interpolate_color(GREEN, BLUE_E, alpha) for alpha in np.linspace(0, 1, 5)]
for i, color in enumerate(colors):
    self.play(states[i].animate.set_fill(color, opacity=0.5), run_time=1.0)
```

### 7. DashedVMobject：虚线框（目标网络标注）

```python
dashed_box = DashedVMobject(
    SurroundingRectangle(target_group, buff=0.2, stroke_color=GREY_A),
    num_dashes=20
)
```

### 8. 填充进度条（ValueTracker 驱动 Rectangle）

用于：Buffer 填充量可视化

```python
fill_tracker = ValueTracker(0)
fill_bar = always_redraw(lambda: Rectangle(
    width=3.3,
    height=max(0.01, fill_tracker.get_value() * 2.3),
    stroke_width=0,
).set_fill(YELLOW, opacity=0.3).move_to(
    container.get_bottom() + UP * max(0.01, fill_tracker.get_value() * 2.3) / 2 + UP * 0.1
))
self.add(fill_bar)
self.play(fill_tracker.animate.set_value(0.5), run_time=2.0)
```

---

## 场景类型速查

| 概念类型 | 推荐模式 | 参考脚本 |
|---------|---------|---------|
| 链式传播（Bellman、梯度回传） | Circle 链 + Arrow + DecimalNumber 逐步更新 | g1_bellman_backup.py |
| 双网络并行（Actor-Critic） | 左右 RoundedRectangle + FlashAround 同步 | g2_actor_critic.py |
| 参数敏感性（α、γ 调节） | Axes + always_redraw 曲线 + 滑块控件 | g3_entropy.py |
| 多模块级联（双 MDP） | Step 1/2 标签 + 箭头串联 + 底部拼接框 | g4_dual_mdp.py |
| 数据路由/分发 | 时间线 + 颜色段 + ✓/✗ 标记 + 填充进度条 | g5_data_routing.py |
| 采样/批次构成 | 数据块 + MoveToTarget 采样动画 | g6_rlpd_sampling.py |
| 对比分析（好 vs 坏） | 上下分栏 + 状态链 + 涟漪/级联效应 | g7_overestimation.py |
| 多阶段流程 | 顺序框 + 箭头 + 内容依次展开 | g8_training_pipeline.py |

---

## 设计原则

1. **一个场景证明一个观点**：不要在一个动画里塞多个独立概念
2. **渐进揭示**：先结构后细节，先整体后局部
3. **运动即含义**：每个动画动作对应一个概念变化，不做无意义的装饰运动
4. **公式即锚点**：先展示公式，再用动画解释公式各项的含义
5. **颜色即语义**：同一概念在所有场景中用同一颜色，跨场景保持一致
6. **文字即桥梁**：中文说明连接公式和直觉，放在关键转折点

## 质量检查清单

- [ ] 所有 Text 使用 `font="Heiti SC"`
- [ ] 所有文字/公式有 `set_backstroke(width=5)`
- [ ] 没有 `sys.path.insert`（manimgl editable install 不需要）
- [ ] 关键动画 `run_time >= 2.0`，无 < 0.5 的极快动画
- [ ] 每步之间有 `wait(0.3~1.0)`
- [ ] 末尾有 `wait(2.0)` + 全局 FadeOut
- [ ] 总时长 20~36 秒
- [ ] `t2c` 颜色映射与场景语义一致
- [ ] GIF 文件 < 3MB（否则降 fps 或分辨率）

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| 使用 `from manim import *` | ImportError 或 API 不兼容 | 改为 `from manimlib import *` |
| 忘记 `set_backstroke` | 文字在深色背景上模糊 | 全局搜索 Text/Tex，补 backstroke |
| `run_time` 过小（< 0.5） | 观众看不清 | 最小 0.8，关键步骤 2.0+ |
| 不 export TinyTeX PATH | LaTeX 编译失败 | bash 开头加 export |
| `Tex` 中 `\text{}` 嵌套中文 | 编译失败（默认模板不含 CJK 包） | 中文用 `Text(font="Heiti SC")`，LaTeX 公式用 `Tex` |
