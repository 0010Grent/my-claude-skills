"""
manimgl 3B1B 风格场景模板

渲染:
  export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"
  manimgl assets/scene_template.py TemplateScene -w --hd

转 GIF:
  ffmpeg -y -i videos/TemplateScene.mp4 \
    -vf "fps=15,scale=1280:-1:flags=lanczos,split[s0][s1];\
  [s0]palettegen=stats_mode=diff[p];\
  [s1][p]paletteuse=dither=bayer:bayer_scale=5" \
    -loop 0 output.gif
"""
from manimlib import *
import numpy as np


class TemplateScene(Scene):
    def construct(self):
        # ═══════════════════════════════════════
        # 1. 标题
        # ═══════════════════════════════════════
        title = Text("场景标题", font="Heiti SC", font_size=42)
        title.to_edge(UP, buff=0.3)
        title.set_backstroke(width=5)
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)

        # ═══════════════════════════════════════
        # 2. 核心公式
        # ═══════════════════════════════════════
        formula = Tex(
            R"y = r + \gamma \, \mathbb{E}[Q(s', a')]",
            font_size=32,
            t2c={
                "r": GREEN,
                R"\gamma": YELLOW,
                "Q": BLUE,
            }
        )
        formula.next_to(title, DOWN, buff=0.4)
        formula.set_backstroke(width=5)
        self.play(Write(formula), run_time=2.0)
        self.wait(1.0)

        # ═══════════════════════════════════════
        # 3. 主体动画区域
        # ═══════════════════════════════════════

        # --- 示例: 状态链 ---
        states = VGroup()
        for i in range(5):
            c = Circle(radius=0.4, stroke_color=BLUE, stroke_width=3)
            c.set_fill(BLUE_E, opacity=0.3)
            c.move_to(LEFT * 4.8 + RIGHT * 2.4 * i + DOWN * 1.2)
            states.add(c)

        labels = VGroup()
        for i in range(5):
            lab = Tex(f"s_{i+1}", font_size=28)
            lab.move_to(states[i].get_center())
            lab.set_backstroke(width=4)
            labels.add(lab)

        arrows = VGroup()
        for i in range(4):
            arr = Arrow(
                states[i].get_right(), states[i + 1].get_left(),
                buff=0.1, stroke_color=WHITE, stroke_width=2,
                max_tip_length_to_length_ratio=0.15
            )
            arrows.add(arr)

        self.play(
            LaggedStartMap(ShowCreation, states, lag_ratio=0.15),
            LaggedStartMap(Write, labels, lag_ratio=0.15),
            run_time=2.0
        )
        self.play(
            LaggedStartMap(ShowCreation, arrows, lag_ratio=0.2),
            run_time=1.5
        )
        self.wait(0.5)

        # --- 示例: ValueTracker 驱动的动态数值 ---
        trackers = [ValueTracker(0.0) for _ in range(5)]
        displays = VGroup()
        for i in range(5):
            d = DecimalNumber(0, num_decimal_places=2, font_size=26, color=TEAL)
            d.next_to(states[i], DOWN, buff=0.3)
            d.set_backstroke(width=4)
            d.add_updater(lambda m, t=trackers[i]: m.set_value(t.get_value()))
            displays.add(d)
        self.add(displays)

        for i in range(4, -1, -1):
            target_val = 0.9 ** (4 - i)
            self.play(trackers[i].animate.set_value(target_val), run_time=1.5)
            self.wait(0.3)

        # ═══════════════════════════════════════
        # 4. 总结
        # ═══════════════════════════════════════
        summary = Text(
            "一句话总结核心洞察",
            font="Heiti SC", font_size=26
        )
        summary.to_edge(DOWN, buff=0.5)
        summary.set_backstroke(width=5)
        self.play(Write(summary), run_time=2.0)
        self.wait(2.0)

        # ═══════════════════════════════════════
        # 5. 全局淡出
        # ═══════════════════════════════════════
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
        self.wait(0.5)
