#!/usr/bin/env python3
"""Glowgrid pixel cursor theme generator.

Every cursor is drawn as a small text grid of art pixels (at most 14x14),
gets a 1-art-pixel dark outline added automatically, is placed on a 16x16
canvas and scaled up with nearest neighbour. Standard library only.

    build.py --out DIR     build an X cursor theme into DIR (needs xcursorgen)
    build.py --sheet PNG   write a 4x contact sheet (dark half, light half)

Grid legend
    .  transparent (becomes outline when it touches a body pixel)
    #  text         d  text-soft     x  forced outline (bg)
    h  accent-hot   o  accent        e  accent-deep     s  stone
    g  glow-1       m  glow-2        c  glow-3          r  alert
"""
import argparse
import os
import struct
import subprocess
import sys
import zlib

PALETTE = {
    "#": (0xE9, 0xDE, 0xF0),  # text
    "d": (0xA4, 0x93, 0xB0),  # text-soft
    "x": (0x0B, 0x07, 0x14),  # bg (outline)
    "h": (0xFF, 0xD3, 0x6B),  # accent-hot
    "o": (0xFF, 0x8A, 0x2A),  # accent
    "e": (0xB2, 0x4D, 0x0A),  # accent-deep
    "s": (0x5A, 0x3D, 0x52),  # stone ramp
    "g": (0x7C, 0xF3, 0x6B),  # glow-1
    "m": (0xE9, 0x4B, 0xD6),  # glow-2
    "c": (0x4B, 0xC6, 0xE9),  # glow-3
    "r": (0xFF, 0x5F, 0x5F),  # alert
}
OUTLINE = "x"
CANVAS = 16
# nominal cursor size -> integer scale of the 16x16 canvas. The image is a
# third larger than the nominal size (24 -> 32 px) because the art leaves
# room around the shape, the same way other themes pad theirs.
SIZES = {24: 2, 32: 3, 48: 4, 64: 5, 96: 8}
STEP_MS = 1000 // 12  # one 12 fps step


# --------------------------------------------------------------- helpers

def G(text):
    rows = [r.strip() for r in text.strip().splitlines()]
    w = max(len(r) for r in rows)
    assert all(len(r) == w for r in rows), "ragged grid:\n" + text
    return rows


def mirror_h(c):
    g, (hx, hy) = c
    return [r[::-1] for r in g], (len(g[0]) - 1 - hx, hy)


def mirror_v(c):
    g, (hx, hy) = c
    return g[::-1], (hx, len(g) - 1 - hy)


def transpose(c):
    g, (hx, hy) = c
    return ["".join(col) for col in zip(*g)], (hy, hx)


def overlay(base, badge, at):
    """Paste grid `badge` onto grid `base` with its top-left at `at`."""
    bx, by = at
    w = max(len(base[0]), bx + len(badge[0]))
    h = max(len(base), by + len(badge))
    out = [list(r.ljust(w, ".")) for r in base] + [["."] * w for _ in range(h - len(base))]
    for y, row in enumerate(badge):
        for x, ch in enumerate(row):
            if ch != ".":
                out[by + y][bx + x] = ch
    return ["".join(r) for r in out]


def to_canvas(grid, hot, anchor):
    """Outline the grid and put it on the 16x16 canvas.

    Returns (canvas rows, hotspot in canvas art pixels)."""
    w, h = len(grid[0]), len(grid)
    assert w <= CANVAS - 2 and h <= CANVAS - 2, f"grid {w}x{h} too big"
    ox, oy = (1, 1) if anchor == "tl" else ((CANVAS - w) // 2, (CANVAS - h) // 2)
    cv = [["."] * CANVAS for _ in range(CANVAS)]
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            assert ch == "." or ch in PALETTE, f"unknown pixel {ch!r}"
            cv[oy + y][ox + x] = ch
    out = [r[:] for r in cv]
    for y in range(CANVAS):
        for x in range(CANVAS):
            if cv[y][x] != ".":
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < CANVAS and 0 <= xx < CANVAS and cv[yy][xx] != ".":
                        out[y][x] = OUTLINE
    return out, (hot[0] + ox, hot[1] + oy)


def rgba(canvas, scale):
    rows = []
    for row in canvas:
        line = b"".join(
            (bytes(PALETTE[ch]) + b"\xff" if ch != "." else b"\0\0\0\0") * scale for ch in row
        )
        rows.extend([line] * scale)
    return rows


def write_png(path, rows):
    """rows: list of RGBA byte strings, one per scanline."""
    w, h = len(rows[0]) // 4, len(rows)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    raw = b"".join(b"\0" + r for r in rows)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


# ------------------------------------------------------------------- art

ARROW = G("""
h.......
##......
###.....
####....
#####...
######..
#######.
########
#####...
##.##...
#...##..
....##..
""")

HAND = G("""
...hh......
...##......
...##......
...##......
...##.#.#..
...##x#x#x#
##.##x#x#x#
###########
.##########
..#########
..#########
...#######.
...#######.
""")

OPEN_HAND = G("""
....#.#....
..#.#.#.#..
..#.#.#.#..
..#.#.#.#..
#.#x#x#x#..
##########.
.#########.
.#########.
..########.
..#######..
...######..
""")

FIST = G("""
..#.#.#.#..
..#x#x#x#..
##########.
.#########.
.#########.
..########.
..#######..
...######..
""")

IBEAM = G("""
##.##
..#..
..#..
..#..
..#..
..#..
..#..
..#..
..#..
..#..
..#..
..#..
..#..
##.##
""")

MOVE = G("""
......#......
.....###.....
....#####....
......#......
..#...#...#..
.##...#...##.
######h######
.##...#...##.
..#...#...#..
......#......
....#####....
.....###.....
......#......
""")

ALL_SCROLL = G("""
......#......
.....###.....
....#####....
.............
..#.......#..
.##...h...##.
###..hhh..###
.##...h...##.
..#.......#..
.............
....#####....
.....###.....
......#......
""")

EW = G("""
...#......#...
..##......##..
.###......###.
##############
.###......###.
..##......##..
...#......#...
""")

NWSE = G("""
#####......
####.......
###........
##.#.......
#...#......
.....#.....
......#...#
.......#.##
........###
.......####
......#####
""")

# single arrow pushing against a bar: the edge being dragged
W_SIDE = G("""
hh....#.....
hh...##.....
hh..###.....
hh.#########
hh..###.....
hh...##.....
hh....#.....
""")

NW_CORNER = G("""
hhhhhhhhh
h........
h.#####..
h.####...
h.###....
h.##.#...
h.#...#..
h......#.
h.......#
""")

CROSSHAIR = G("""
......#......
......#......
......#......
......#......
......#......
.............
#####.h.#####
.............
......#......
......#......
......#......
......#......
......#......
""")

CROSS = G("""
......#......
......#......
......#......
......#......
......#......
......#......
#############
......#......
......#......
......#......
......#......
......#......
......#......
""")

CELL = G("""
....###....
....###....
....###....
....###....
###########
###########
###########
....###....
....###....
....###....
....###....
""")

NOT_ALLOWED = G("""
....rrrr....
..rrrrrrrr..
.rrrxxxxrrr.
.rrrrxxxxrr.
rrxrrrxxxxrr
rrxxrrrxxxrr
rrxxxrrrxxrr
rrxxxxrrrxrr
.rrxxxxrrrr.
.rrrxxxxrrr.
..rrrrrrrr..
....rrrr....
""")

ZOOM = G("""
...####......
..#xxxx#.....
.#xxxxxx#....
#xxxxxxxx#...
#xxxxxxxx#...
#xxxxxxxx#...
#xxxxxxxx#...
.#xxxxxx#....
..#xxxx###...
...####.###..
.........###.
..........###
...........##
""")
ZOOM_PLUS = G("""
..hh..
..hh..
hhhhhh
hhhhhh
..hh..
..hh..
""")
ZOOM_MINUS = G("""
hhhhhh
hhhhhh
""")

X_CURSOR = G("""
rr.....rr
rrr...rrr
.rrr.rrr.
..rrrrr..
...rrr...
..rrrrr..
.rrr.rrr.
rrr...rrr
rr.....rr
""")

PENCIL = G("""
.........oo.
........oooo
.......#xooo
......###xo.
.....#####..
....#####...
...#####....
..#####.....
.d####......
.dd##.......
hdd#........
hh..........
""")

UP_ARROW = G("""
....h....
...###...
..#####..
.#######.
#########
...###...
...###...
...###...
...###...
...###...
...###...
""")

DOTBOX = G("""
###########
#.........#
#.........#
#.........#
#....h....#
#...hhh...#
#....h....#
#.........#
#.........#
#.........#
###########
""")

BADGE_HELP = G("""
.cc.
c..c
...c
..c.
.c..
....
.c..
""")

BADGE_MENU = G("""
#####
.....
#####
.....
#####
""")

BADGE_PLUS = G("""
..g..
..g..
ggggg
..g..
..g..
""")

BADGE_LINK = G("""
.cccc
...cc
..c.c
.c..c
c....
""")

# The 8-cell spark chase: cells clockwise from the top-left.
CHASE = ["h", "o", "e", "s", "s", "s", "s", "s"]  # head, trail, idle


def chase_colors(frame):
    """Colour of each of the 8 ring cells on a given frame."""
    return [CHASE[(frame - i) % 8] for i in range(8)]


def wait_frame(frame):
    ring = [(0, 0), (4, 0), (8, 0), (8, 4), (8, 8), (4, 8), (0, 8), (0, 4)]
    g = [["."] * 11 for _ in range(11)]
    for (cx, cy), col in zip(ring, chase_colors(frame)):
        for y in range(3):
            for x in range(3):
                g[cy + y][cx + x] = col
    return ["".join(r) for r in g]


def progress_frame(frame):
    ring = [(0, 0), (2, 0), (4, 0), (4, 2), (4, 4), (2, 4), (0, 4), (0, 2)]
    g = [["."] * 5 for _ in range(5)]
    for (cx, cy), col in zip(ring, chase_colors(frame)):
        g[cy][cx] = col
    return overlay(ARROW, ["".join(r) for r in g], (9, 9))


def cursors():
    """name -> (anchor, [(grid, hotspot, ms)]) ; ms is 0 for still cursors."""
    c = {}

    def still(name, grid, hot, anchor="center"):
        c[name] = (anchor, [(grid, hot, 0)])

    def still_c(name, cur, anchor="center"):
        still(name, cur[0], cur[1], anchor)

    still("left_ptr", ARROW, (0, 0), "tl")
    still_c("right_ptr", mirror_h((ARROW, (0, 0))))
    still("center_ptr", UP_ARROW, (4, 0))
    still("hand2", HAND, (3, 0))
    still("hand1", OPEN_HAND, (5, 5))
    still("grabbing", FIST, (5, 3))
    still("xterm", IBEAM, (2, 7))
    still_c("vertical-text", transpose((IBEAM, (2, 7))))
    still("move", MOVE, (6, 6))
    still("all-scroll", ALL_SCROLL, (6, 6))

    ew = (EW, (7, 3))
    still_c("sb_h_double_arrow", ew)
    still_c("sb_v_double_arrow", transpose(ew))
    nwse = (NWSE, (5, 5))
    still_c("bd_double_arrow", nwse)
    still_c("fd_double_arrow", mirror_h(nwse))

    w = (W_SIDE, (0, 3))
    still_c("left_side", w)
    still_c("right_side", mirror_h(w))
    still_c("top_side", transpose(w))
    still_c("bottom_side", mirror_v(transpose(w)))
    nw = (NW_CORNER, (0, 0))
    still_c("top_left_corner", nw)
    still_c("top_right_corner", mirror_h(nw))
    still_c("bottom_left_corner", mirror_v(nw))
    still_c("bottom_right_corner", mirror_v(mirror_h(nw)))

    still("crosshair", CROSSHAIR, (6, 6))
    still("cross", CROSS, (6, 6))
    still("plus", CELL, (5, 5))
    still("crossed_circle", NOT_ALLOWED, (6, 6))
    still("zoom-in", overlay(ZOOM, ZOOM_PLUS, (2, 2)), (4, 4))
    still("zoom-out", overlay(ZOOM, ZOOM_MINUS, (2, 4)), (4, 4))
    still("X_cursor", X_CURSOR, (4, 4))
    still("pencil", PENCIL, (0, 11))
    still("dotbox", DOTBOX, (5, 5))

    up = (UP_ARROW, (4, 0))
    still_c("sb_up_arrow", up)
    still_c("sb_down_arrow", mirror_v(up))
    still_c("sb_left_arrow", transpose(up))
    still_c("sb_right_arrow", mirror_h(transpose(up)))

    still("question_arrow", overlay(ARROW, BADGE_HELP, (10, 0)), (0, 0), "tl")
    still("context-menu", overlay(ARROW, BADGE_MENU, (9, 1)), (0, 0), "tl")
    still("copy", overlay(ARROW, BADGE_PLUS, (9, 8)), (0, 0), "tl")
    still("link", overlay(ARROW, BADGE_LINK, (9, 8)), (0, 0), "tl")

    # held for two 12 fps steps per cell: one lap takes 1.33 s
    c["wait"] = ("center", [(wait_frame(f), (5, 5), STEP_MS * 2) for f in range(8)])
    c["left_ptr_watch"] = ("tl", [(progress_frame(f), (0, 0), STEP_MS * 2) for f in range(8)])
    return c


# Alternative names -> the cursor file that serves them. Covers the CSS /
# freedesktop names, the legacy X11 core names and the hashed names old
# toolkits ask for.
LINKS = {
    # CSS / freedesktop
    "default": "left_ptr", "arrow": "left_ptr", "top_left_arrow": "left_ptr",
    "wayland-cursor": "left_ptr",
    "pointer": "hand2", "pointing_hand": "hand2",
    "text": "xterm", "ibeam": "xterm",
    "grab": "hand1", "openhand": "hand1",
    "closedhand": "grabbing", "dnd-move": "grabbing", "dnd-none": "grabbing",
    "fleur": "move", "size_all": "move", "pointer-move": "move",
    "help": "question_arrow", "left_ptr_help": "question_arrow",
    "whats_this": "question_arrow", "dnd-ask": "question_arrow",
    "progress": "left_ptr_watch", "half-busy": "left_ptr_watch",
    "watch": "wait",
    "not-allowed": "crossed_circle", "forbidden": "crossed_circle",
    "circle": "crossed_circle", "no-drop": "crossed_circle",
    "dnd_no_drop": "crossed_circle", "dnd-no-drop": "crossed_circle",
    "alias": "link", "dnd-link": "link",
    "dnd-copy": "copy",
    "cell": "plus",
    "tcross": "cross", "cross_reverse": "cross", "diamond_cross": "cross",
    "color-picker": "crosshair",
    "pirate": "X_cursor", "x-cursor": "X_cursor",
    "draft": "pencil",
    "draft_large": "right_ptr", "draft_small": "right_ptr",
    "icon": "dotbox", "target": "dotbox", "dot_box_mask": "dotbox", "draped_box": "dotbox",
    # resize
    "ew-resize": "sb_h_double_arrow", "col-resize": "sb_h_double_arrow",
    "h_double_arrow": "sb_h_double_arrow", "size_hor": "sb_h_double_arrow",
    "size-hor": "sb_h_double_arrow", "split_h": "sb_h_double_arrow",
    "ns-resize": "sb_v_double_arrow", "row-resize": "sb_v_double_arrow",
    "v_double_arrow": "sb_v_double_arrow", "size_ver": "sb_v_double_arrow",
    "size-ver": "sb_v_double_arrow", "split_v": "sb_v_double_arrow",
    "double_arrow": "sb_v_double_arrow",
    "nwse-resize": "bd_double_arrow", "size_fdiag": "bd_double_arrow",
    "nesw-resize": "fd_double_arrow", "size_bdiag": "fd_double_arrow",
    "w-resize": "left_side", "e-resize": "right_side",
    "n-resize": "top_side", "s-resize": "bottom_side",
    "nw-resize": "top_left_corner", "ne-resize": "top_right_corner",
    "sw-resize": "bottom_left_corner", "se-resize": "bottom_right_corner",
    "left_tee": "left_side", "right_tee": "right_side",
    "top_tee": "top_side", "bottom_tee": "bottom_side",
    "ul_angle": "top_left_corner", "ur_angle": "top_right_corner",
    "ll_angle": "bottom_left_corner", "lr_angle": "bottom_right_corner",
    "up-arrow": "sb_up_arrow", "down-arrow": "sb_down_arrow",
    "left-arrow": "sb_left_arrow", "right-arrow": "sb_right_arrow",
    # hashed names (from libXcursor's shape hashing, used by old Qt/GTK)
    "00000000000000020006000e7e9ffc3f": "left_ptr_watch",
    "08e8e1c95fe2fc01f976f1e063a24ccd": "left_ptr_watch",
    "3ecb610c1bf2410f44200f48c40d3599": "left_ptr_watch",
    "00008160000006810000408080010102": "sb_v_double_arrow",
    "2870a09082c103050810ffdffffe0204": "sb_v_double_arrow",
    "028006030e0e7ebffc7f7070c0600140": "sb_h_double_arrow",
    "14fef782d02440884392942c1120523": "sb_h_double_arrow",
    "03b6e0fcb3499374a867c041f52298f0": "crossed_circle",
    "1081e37283d90000800003c07f3ef6bf": "copy",
    "6407b0e94181790501fd1e167b474872": "copy",
    "b66166c04f8c3109214a4fbd64a50fc8": "copy",
    "3085a0e285430894940527032f8b26df": "link",
    "640fb0e74195791501fd1ed57b41487f": "link",
    "a2a266d0498c3104214a47bd64ab0fc8": "link",
    "4498f0e0c1937ffe01fd06f973665830": "move",
    "9081237383d90e509aa00f00170e968f": "move",
    "5c6cd98b3f3ebcb1f9c7f1c204630408": "question_arrow",
    "d9ce0ab605698f320427677b458ad60b": "question_arrow",
    "9d800788f1b08800ae810202380a0822": "hand2",
    "e29285e634086352946a0e7090d73106": "hand2",
    "c7088f0f3e6c8088236ef8e1e3e70000": "bd_double_arrow",
    "fcf1c3c7cd4491d801f1e1c78f100000": "fd_double_arrow",
    "fcf21c00b30f7e3f83fe0dfd12e71cff": "grabbing",
}

INDEX_THEME = """[Icon Theme]
Name=Glowgrid
Comment=Glowgrid pixel cursors: hard pixels lit from within
"""


# ----------------------------------------------------------------- build

def build_theme(out, xcursorgen):
    cdir = os.path.join(out, "cursors")
    work = os.path.join(out, ".work")
    os.makedirs(cdir, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    defs = cursors()
    for name, (anchor, frames) in sorted(defs.items()):
        lines = []
        for size, scale in SIZES.items():
            for i, (grid, hot, ms) in enumerate(frames):
                canvas, (hx, hy) = to_canvas(grid, hot, anchor)
                png = os.path.join(work, f"{name}-{size}-{i}.png")
                write_png(png, rgba(canvas, scale))
                # middle of the hot art pixel, except tips: their top-left
                off = 0 if anchor == "tl" else scale // 2
                line = f"{size} {hx * scale + off} {hy * scale + off} {png}"
                lines.append(line + (f" {ms}" if ms else ""))
        cfg = os.path.join(work, name + ".cursor")
        with open(cfg, "w") as f:
            f.write("\n".join(lines) + "\n")
        subprocess.run([xcursorgen, cfg, os.path.join(cdir, name)], check=True)
    for link, target in sorted(LINKS.items()):
        assert target in defs, f"{link} -> {target}: no such cursor"
        assert link not in defs, f"{link} is both a cursor and a link"
        os.symlink(target, os.path.join(cdir, link))
    for f in os.listdir(work):
        os.remove(os.path.join(work, f))
    os.rmdir(work)
    with open(os.path.join(out, "index.theme"), "w") as f:
        f.write(INDEX_THEME)
    print(f"{len(defs)} cursors, {len(LINKS)} links -> {out}")


def build_sheet(path, scale=4, cols=10):
    """Every cursor (animations: every frame) on a dark and a light half."""
    tiles = []
    for name, (anchor, frames) in cursors().items():
        for grid, hot, _ in frames:
            tiles.append(to_canvas(grid, hot, anchor)[0])
    cell = CANVAS + 2
    nrows = -(-len(tiles) // cols)
    w, h = cols * cell, nrows * cell
    rows = []
    for bg in ((0x17, 0x0D, 0x24), (0xF4, 0xEF, 0xF6)):
        img = [[bg] * w for _ in range(h)]
        for i, cv in enumerate(tiles):
            ox, oy = (i % cols) * cell + 1, (i // cols) * cell + 1
            for y in range(CANVAS):
                for x in range(CANVAS):
                    if cv[y][x] != ".":
                        img[oy + y][ox + x] = PALETTE[cv[y][x]]
        for r in img:
            line = b"".join((bytes(p) + b"\xff") * scale for p in r)
            rows.extend([line] * scale)
    write_png(path, rows)
    print(f"{len(tiles)} tiles -> {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="theme directory to build (…/share/icons/Glowgrid)")
    ap.add_argument("--sheet", help="write a contact sheet PNG")
    ap.add_argument("--xcursorgen", default="xcursorgen")
    a = ap.parse_args()
    if not (a.out or a.sheet):
        ap.error("give --out and/or --sheet")
    if a.sheet:
        build_sheet(a.sheet)
    if a.out:
        build_theme(a.out, a.xcursorgen)


if __name__ == "__main__":
    sys.exit(main())
