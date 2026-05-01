#!/usr/bin/env python3
"""Generate a GitHub Social Preview HTML page for screenshot.

Usage:
    python generate_social_preview.py "ProjectName" "一句话副标题" [tag1] [tag2] [tag3]

Example:
    python generate_social_preview.py "csv-merge" "智能合并 CSV 文件" Python CLI MIT

The output HTML is self-contained. Open it in a browser at 100% zoom,
screenshot the viewport (1280x640), and upload to GitHub repo settings.
"""

import sys
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title} — Social Preview</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1280px;
      height: 640px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-start;
      padding: 0 100px;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #f8fafc;
      overflow: hidden;
    }}
    .accent {{
      position: absolute;
      top: -200px;
      right: -100px;
      width: 600px;
      height: 600px;
      background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%);
      pointer-events: none;
    }}
    .accent2 {{
      position: absolute;
      bottom: -150px;
      left: -100px;
      width: 400px;
      height: 400px;
      background: radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, transparent 70%);
      pointer-events: none;
    }}
    h1 {{
      font-size: 72px;
      font-weight: 800;
      letter-spacing: -2px;
      line-height: 1.1;
      margin-bottom: 20px;
      background: linear-gradient(90deg, #f8fafc 0%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .subtitle {{
      font-size: 32px;
      color: #cbd5e1;
      font-weight: 400;
      max-width: 900px;
      line-height: 1.4;
      margin-bottom: 40px;
    }}
    .tag-row {{ display: flex; gap: 14px; flex-wrap: wrap; }}
    .tag {{
      padding: 10px 24px;
      border-radius: 8px;
      font-size: 18px;
      font-weight: 600;
      color: #e2e8f0;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(10px);
    }}
    .tag.primary {{ background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #7dd3fc; }}
    .footer {{
      position: absolute;
      bottom: 30px;
      right: 50px;
      font-size: 16px;
      color: #475569;
    }}
  </style>
</head>
<body>
  <div class="accent"></div>
  <div class="accent2"></div>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="tag-row">
    {tags_html}
  </div>
  <div class="footer">github.com/0010Grent/{repo_name}</div>
</body>
</html>"""


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_social_preview.py <title> <subtitle> [tag ...]")
        sys.exit(1)

    title = sys.argv[1]
    subtitle = sys.argv[2]
    tags = sys.argv[3:] if len(sys.argv) > 3 else []
    repo_name = title.lower().replace(" ", "-")

    if not tags:
        tags = ["Python", "CLI"]

    tags_html = "\n    ".join(
        f'<div class="tag{" primary" if i == 0 else ""}">{t}</div>'
        for i, t in enumerate(tags[:4])
    )

    html = TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        tags_html=tags_html,
        repo_name=repo_name,
    )

    out_dir = Path("docs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "social-preview.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"Generated: {out_path}")
    print("Open this file in a browser at 100% zoom, then screenshot the viewport.")
    print("Target size: 1280x640 (GitHub Social Preview dimensions)")
    print("Upload the screenshot to: Settings -> Social preview")


if __name__ == "__main__":
    main()
