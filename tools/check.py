#!/usr/bin/env python3
"""Check files against the Glowgrid rules. Run it on whatever you just themed.

    python3 tools/check.py PATH [PATH ...]      files or folders (css, scss, html, qml, js, ts, rs, kdl, conf, ini, toml, svg)
    python3 tools/check.py --json PATH          machine-readable findings
    python3 tools/check.py --list-colors        print every colour the palette allows

Exit status: 0 clean, 1 at least one error, 2 bad usage. Warnings do not fail the run.

Rules
  radius      error    a corner radius other than 0
  soft-shadow error    a shadow that is both offset and blurred (shadows are hard; a zero-offset blur is a glow and is allowed)
  blur        error    filter/backdrop-filter blur
  gradient    warning  a CSS gradient (shade with ramps and dither; hard-stop repeats for dashes are fine, silence with the marker)
  color       error    a hex colour that is not in tokens.json (the message names the nearest token)
  font        warning  a font family outside the four faces and their fallbacks
  easing      warning  a transition over 300 ms, a one-shot animation over 1600 ms, or a transition eased without steps()
A line containing `glowgrid-allow` is skipped. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".css", ".scss", ".html", ".htm", ".qml", ".js", ".ts", ".tsx", ".jsx", ".rs", ".lua", ".kdl", ".conf", ".ini", ".toml", ".svg", ".vue", ".svelte"}
FONTS = {"pixelify sans", "silkscreen", "vt323", "ibm plex sans", "noto sans", "courier new", "segoe ui", "jetbrainsmono nerd font", "jetbrains mono",
         "monospace", "sans-serif", "serif", "system-ui", "ui-monospace", "inherit", "initial", "unset"}


def palette():
    """hex (lower case, 6 digits) -> token name, for every colour in tokens.json."""
    t = json.loads((ROOT / "tokens.json").read_text())
    out = {"#000000": "black", "#ffffff": "white"}

    def walk(node, path):
        if isinstance(node, dict):
            if isinstance(node.get("value"), str) and re.fullmatch(r"#[0-9a-fA-F]{6}", node["value"]):
                out.setdefault(node["value"].lower(), path)
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", node):
            out.setdefault(node.lower(), path)

    walk(t, "")
    # tints the kit itself uses that are not named tokens
    for extra, name in (("#241433", "ramp.air[4]"), ("#bfb0c9", "body text on dark (docs)"), ("#cdbfd6", "body text on dark (docs)"), ("#9482ad", "comment violet"),
                        ("#cfc0e6", "property text (editors)"), ("#16261d", "diff added tint (editors)"), ("#2a1220", "diff removed tint (editors)"),
                        ("#ffa565", "string, ember (editors)"), ("#f06fe0", "type, ember (editors)"), ("#ffb38f", "string, frost (editors)")):
        out.setdefault(extra, name)
    return out


def norm(hex_color):
    h = hex_color.lower()
    if len(h) == 4:
        h = "#" + "".join(c * 2 for c in h[1:])
    return h[:7]


def nearest(hex_color, pal):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    best = min(pal, key=lambda p: (int(p[1:3], 16) - r) ** 2 + (int(p[3:5], 16) - g) ** 2 + (int(p[5:7], 16) - b) ** 2)
    return best, pal[best]


LEN = r"-?\d*\.?\d+(?:px|em|rem|cqw|vw|vh|%)?"
RE_RADIUS = re.compile(r"(border(?:-[a-z]+){0,2}-radius|geometry-corner-radius|(?<![a-zA-Z_])radius(?:[A-Z][a-zA-Z]*)?)\s*[:=]?\s*([^;{}\n]*)")
RE_SHADOW = re.compile(r"(box-shadow|text-shadow|-gtk-icon-shadow)\s*:\s*([^;{}]*)")
RE_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])")
RE_FONT = re.compile(r"font-family\s*:\s*([^;{}]*)")
RE_TIME = re.compile(r"(transition|animation)(?:-duration)?\s*:\s*([^;{}]*)")
RE_MS = re.compile(r"(\d*\.?\d+)(ms|s)\b")


def check_text(path, text, pal):
    findings = []

    def add(line, rule, level, msg):
        findings.append({"file": str(path), "line": line, "rule": rule, "level": level, "message": msg})

    is_code = path.suffix in {".rs", ".js", ".ts", ".tsx", ".jsx", ".qml", ".lua"}
    for n, line in enumerate(text.splitlines(), 1):
        if "glowgrid-allow" in line:
            continue
        s = line.strip()

        m = RE_RADIUS.search(line)
        if m and not s.startswith(("//", "#", "*", "/*")):
            val = m.group(2).split("/*")[0].split("//")[0].strip()
            nums = re.findall(r"-?\d*\.?\d+", val)
            # only a literal non-zero number counts; expressions and variables are left alone
            if nums and re.fullmatch(r"[\d.\spxemr%-]+", val) and any(float(x) != 0 for x in nums):
                add(n, "radius", "error", f"corner radius '{val}'. Glowgrid corners are square: use 0.")

        for m in RE_SHADOW.finditer(line):
            for part in re.split(r",(?![^(]*\))", m.group(2)):
                p = re.sub(r"(rgba?|hsla?|color-mix|var)\([^)]*\)", "", part)
                lens = re.findall(LEN, re.sub(r"#[0-9a-fA-F]+", "", p))
                lens = [x for x in lens if re.search(r"\d", x)]
                if len(lens) >= 3:
                    ox, oy, blur = (float(re.match(r"-?\d*\.?\d+", x).group()) for x in lens[:3])
                    if blur != 0 and (ox != 0 or oy != 0):
                        add(n, "soft-shadow", "error", f"shadow '{part.strip()}' is offset and blurred. Use a hard shadow (blur 0); only a zero-offset glow may blur.")

        if re.search(r"(?:backdrop-)?filter\s*:\s*[^;]*blur\(", line):
            add(n, "blur", "error", "blur filter. Glowgrid surfaces are solid; only art glow is soft.")
        if re.search(r"(?<!repeating-)(linear|radial|conic)-gradient\(", line):
            add(n, "gradient", "warning", "gradient. Shade with palette ramps and dither, or a flat token colour.")

        for m in RE_HEX.finditer(line):
            raw = m.group(0)
            # in code, '#' also starts attributes, ids and comments: only quoted values count
            if is_code and not re.search(r"[\"'`]" + re.escape(raw), line):
                continue
            h = norm(raw)
            if h not in pal:
                near, name = nearest(h, pal)
                add(n, "color", "error", f"{raw} is not in the palette. Nearest: {near} ({name}).")

        m = RE_FONT.search(line)
        if m and "var(" not in m.group(1):
            for fam in m.group(1).split(","):
                f = fam.replace("!important", "").strip().strip("\"'").lower()
                if f and f not in FONTS and not f.startswith(("var(", "-apple", "blinkmac")):
                    add(n, "font", "warning", f"font '{fam.strip()}'. The faces are Pixelify Sans, Silkscreen, VT323 and IBM Plex Sans.")

        for m in RE_TIME.finditer(line):
            val = m.group(2)
            if "var(" in val or "infinite" in val:
                continue
            times = [float(a) * (1000 if u == "s" else 1) for a, u in RE_MS.findall(val)]
            limit = 300 if m.group(1) == "transition" else 1600
            if times and max(times) > limit:
                add(n, "easing", "warning", f"{m.group(1)} of {int(max(times))} ms. State changes are 80-300 ms; reveals at most 1600 ms.")
            elif times and m.group(1) == "transition" and "steps(" not in val and re.search(r"\b(ease|ease-in|ease-out|ease-in-out|cubic-bezier)\b", val):
                add(n, "easing", "warning", "eased transition. Use steps(n) so it moves in held frames.")
    return findings


def files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in EXTS and not any(part in {".git", "node_modules", "target", "dist", "build"} for part in f.parts):
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"check.py: no such file or folder: {p}", file=sys.stderr)
            sys.exit(2)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pal = palette()
    if "--list-colors" in sys.argv:
        for h, name in sorted(pal.items(), key=lambda kv: kv[1]):
            print(f"{h}  {name}")
        return 0
    if not args:
        print(__doc__)
        return 2
    found, count = [], 0
    for f in files(args):
        count += 1
        try:
            found += check_text(f, f.read_text(errors="replace"), pal)
        except OSError as e:
            print(f"check.py: {f}: {e}", file=sys.stderr)
    errors = sum(1 for x in found if x["level"] == "error")
    if "--json" in sys.argv:
        print(json.dumps({"files": count, "errors": errors, "warnings": len(found) - errors, "findings": found}, indent=2))
    else:
        for x in found:
            print(f"{x['file']}:{x['line']}: {x['level']} [{x['rule']}] {x['message']}")
        print(f"{count} files checked: {errors} errors, {len(found) - errors} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
