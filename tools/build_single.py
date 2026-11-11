#!/usr/bin/env python3
"""Inline the web kit into one self-contained HTML file, for sharing or hosting.

    python3 tools/build_single.py [OUT]     default OUT: dist/glowgrid-components.html

Takes kit/web/demo.html and replaces its local <link> and <script src> with the files' contents.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "kit/web"


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist/glowgrid-components.html"
    html = (WEB / "demo.html").read_text()
    html = re.sub(r'<link rel="stylesheet" href="(?!https?:)([^"]+)">', lambda m: "<style>\n" + (WEB / m.group(1)).read_text() + "</style>", html)
    html = re.sub(r'<script src="(?!https?:)([^"]+)"></script>', lambda m: "<script>\n" + (WEB / m.group(1)).read_text().replace("</script", "<\\/script") + "</script>", html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
