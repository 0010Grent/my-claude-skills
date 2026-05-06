# paper-talk-script

**Academic Presentation Script Generator — From slides to speaker-ready narration**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" />
  <img src="https://img.shields.io/badge/Claude%20Code-Skill-green" />
  <img src="https://img.shields.io/github/license/0010Grent/paper-talk-script" />
</p>

---

## What It Does

Transforms academic paper presentation materials—PPT slides, PDF papers, analysis reports—into timed, page-by-page speaker scripts for graduate-level classroom presentations.

Given a 10/20/30-minute time constraint, it generates narration that balances technical depth with narrative flow, accounting for slide transitions, animated GIFs, and mathematical explanations.

---

## Why Use This

Preparing presentation scripts by hand is tedious:
- Verifying every number against the original paper
- Timing each slide to hit the deadline exactly
- Writing natural narration that doesn't sound like reading bullet points
- Explaining visual animations while staying synchronized

This skill automates the heavy lifting: fact-checking against source material, allocating time budgets per slide, and producing scripts optimized for spoken delivery.

---

## Workflow

<pre>
<b>Input Materials</b>
    │
    ├── PPT/slides outline ──────┐
    ├── Paper PDF ───────────────┼──→ <b>Structure Analysis</b>
    ├── Analysis report ─────────┤
    └── CLAUDE.md (metadata) ────┘
                        │
                        ▼
            <b>Time Budget Allocation</b>
            (Total duration ÷ slide count,
             weighted by content density)
                        │
                        ▼
            <b>Per-Slide Script Generation</b>
            ├─ Locate source paragraphs
            ├─ Fact-check numbers & formulas
            ├─ Draft narration (narrative-driven)
            ├─ Animation synchronization (if GIFs)
            └─ Time estimate per slide
                        │
                        ▼
            <b>Global Review</b>
            ├─ Duration validation (±10% target)
            ├─ Narrative continuity check
            ├─ Terminology consistency
            └─ Formula cross-verification
                        │
                        ▼
            <b>Output: speaker_script.md</b>
</pre>

---

## Slide Type Time Allocation

| Slide Type | Time Weight | Typical Range |
|------------|-------------|---------------|
| Title/Transition | 0.2x | 5-10 sec |
| Motivation/Background | 1.2x | 45-90 sec |
| Core Algorithm/Formula | 1.5x | 60-120 sec |
| Visualization/Animation | 1.0x | 40-80 sec |
| Experimental Results | 0.8x | 30-60 sec |
| Summary | 0.6x | 20-40 sec |

---

## Key Features

- **Fact-verified narration**: Every number, formula, and claim cross-checked against the original paper
- **Animation-aware scripting**: Timed narration synchronized with GIF playback
- **Mathematical explanation**: Formulas presented on slides, explained in plain language
- **Narrative structure**: Problem → Mechanism → Impact, not bullet-point reading
- **Time-accurate**: Total duration controlled within ±10% of target

---

## Output Format

```markdown
# Speaker Script: <Presentation Topic>

> Presenter: <Name> | Slides: <filename> Slide <range>
> Estimated Duration: <X> minutes | Style: Narrative-driven, technical depth
> Audience: <description>
> Note: All GIFs auto-play in slides; narration guides viewers through them

---

## Slide N — <Title> (<seconds>s)

> [Background GIF: <filename> auto-loops]

<Natural spoken narration, single paragraph, no bullet points>

---
```

---

## Usage

```
/paper-talk-script
```

Or specify duration:

```
Generate a 15-minute speaker script based on slides/ and the paper
```

Required materials in project directory:
- `slides.md` or `slides_outline.md` — slide structure and key points
- Paper PDF (optional but recommended) — fact-checking source
- `CLAUDE.md` — project metadata and verified facts
- `animations/` or `figures/` — GIFs requiring narration sync

---

## Quality Standards

- Duration accuracy: Target time ±10%
- Zero factual errors: All figures match original paper
- Narrative coherence: Logical flow between slides
- Animation sync: Narration length ≥ GIF loop duration
- Appropriate depth: Mechanism-level explanation, not just definitions
- Speakable content: No long sentences, no formula recitation

---

## Project Structure

```
paper-talk-script/
├── SKILL.md              # Skill definition and protocol
├── README.md             # This file
└── .gitignore            # Excludes local/task files
```

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

*A Claude Code skill for academic presentation preparation.*
