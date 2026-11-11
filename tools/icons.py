#!/usr/bin/env python3
"""Render the 7x7 icons in kit/icons/icons.json.

    python3 tools/icons.py list
    python3 tools/icons.py svg NAME [--cell 2] [--color '#e9def0']     print one SVG
    python3 tools/icons.py export DIR [--cell 2] [--color currentColor] write every icon as SVG

Standard library only.
"""
import json
import sys
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent.parent / "kit/icons/icons.json").read_text())


def svg(name, cell=2, color="currentColor"):
    rows = DATA["icons"][name]
    size = DATA["size"] * cell
    rects = "".join(
        f'<rect x="{i * cell}" y="{j * cell}" width="{cell}" height="{cell}"/>'
        for j, row in enumerate(rows) for i, bit in enumerate(row) if bit == "1"
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
            f'fill="{color}" shape-rendering="crispEdges">{rects}</svg>\n')


def arg(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print("\n".join(DATA["icons"]))
        return 0
    cell, color = int(arg("--cell", "2")), arg("--color", "currentColor")
    if sys.argv[1] == "svg":
        if len(sys.argv) < 3 or sys.argv[2] not in DATA["icons"]:
            print("unknown icon; try: tools/icons.py list", file=sys.stderr)
            return 1
        sys.stdout.write(svg(sys.argv[2], cell, color))
        return 0
    if sys.argv[1] == "export":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for name in DATA["icons"]:
            (out / f"{name}.svg").write_text(svg(name, cell, color))
        print(f"wrote {len(DATA['icons'])} icons to {out}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
