# Applying Glowgrid: instructions for an agent

You have been asked to make something look like Glowgrid. This file is the fast path.
Read it top to bottom once; it is short on purpose. Deeper references are linked where needed.

## 1. The look in six lines

- A **dark world** (`bg #0b0714`, panels `surface #170d24`) where colour only comes from **lights**:
  `accent`, `accent-hot`, `glow-1`, `glow-2`, `glow-3`, and `alert` for errors.
- **Square corners, hard offset shadows, flat fills.** No radius, no blur, no gradients.
- **Four fonts with fixed jobs:** Silkscreen (labels, upper case, spaced), VT323 (numbers and
  values), IBM Plex Sans (anything read as a sentence), Pixelify Sans (one headline per surface).
- **1 px stone outlines at rest; 2 px accent on hover, selection and the focused thing.**
- **Motion is part of the look.** Things that travel ride springs and are drawn on the 2 px
  grid (whole-pixel hops, with overshoot); colour and opacity change in held steps (80 ms
  presses, 120 ms toggles). Read `MOTION.md` before animating anything.
- Themes change only the lights: **Ember** (default), **Forge**, **Frost**, **Geode**.

## 2. Pick your target and copy

Do not retype colours or invent components. Copy the kit file for your platform.

| You are building | Copy | Then |
| --- | --- | --- |
| A web page or web app | `kit/web/tokens.css`, `kit/web/glowgrid-ui.css`, `glowgrid-ui.js`, `icons.js`; for springs `vendor/weave.js` + `glowgrid-motion.js` | Put class `gg` on `<body>`; copy markup from `kit/web/demo.html` |
| A GTK 4 app | `kit/gtk4/tokens-<theme>.css` + `kit/gtk4/glowgrid.css` | Add class `glowgrid` to the window; use the class names in the file's header. Working example: github.com/maxmaster55/pixelscale |
| Qt Quick / Quickshell | everything in `kit/qml/` | `Glowgrid.name = "frost"` switches theme |
| A Rust program | `kit/rust/tokens.rs` | `palette("ember")` |
| A terminal | `kit/terminal/kitty-<theme>.conf`, or the 16 colours in `kit/terminal/<theme>.json` | VT323 optional; turn its ligatures off |
| The Linux console | `kit/terminal/console-<theme>.txt` (16 hex colours) | |
| niri | `kit/desktop/niri.kdl` | |
| Noctalia shell | `kit/noctalia/glowgrid-<theme>.json` into `~/.config/noctalia/palettes/` | `source = "custom"`, `corner_radius_scale = 0` |
| VS Code | `kit/vscode/` (an extension: themes, defaults, and `ui.css` for shape, fonts and shadows) | Read its README: the UI style is applied by a command, or at build time on NixOS |
| Neovim | `kit/neovim/` (`colors/glowgrid.lua` and an `init.lua` with a bar-style status line) | `:colorscheme glowgrid` |
| A cursor theme | `kit/cursor/` | `python3 build.py` |
| Icons | `kit/icons/icons.json` (32 icons, 7×7 bits) | `python3 tools/icons.py export DIR` for SVGs |
| Anything else | `tokens.json` | Follow section 3 |

Fonts are in `fonts/` (all SIL Open Font License) and on Google Fonts under the same names.

## 3. If there is no kit for your platform

Build from `tokens.json` and these numbers:

- Corner radius 0 everywhere. Shadows: offset equal on x and y, blur 0, colour black:
  3 px for icon buttons, 4 px for buttons, 8 px for panels, cards and windows.
- Panel: `surface` fill. A header strip in `air-3` with a 2 px black line under it. Body
  padding 12 px, rows 8 px apart. A footer in `bg` with a 2 px black line above it.
- Row: `bg` fill, 1 px `stone` outline, padding 9×10 px. Hover or selected: 2 px `accent`.
- Text: names in Plex Sans 600 at 14.5 px; secondary text in `text-soft` at 12.5 px; values in
  VT323 at 18 px in `glow-3`; labels in Silkscreen at 10 to 12 px, upper case, tracking 0.12 to 0.16 em.
- Button: Silkscreen 10.5 px; primary is `accent` with `ink` text; default is `surface` with
  a 1 px `stone` outline and becomes the primary look on hover.
- Switch: a 44×22 track with a 2 px black inset line and a 14 px square thumb; on = `accent`
  track and `ink` thumb.
- Status: a 12 px square. Unlit is `stone`. `glow-1` good, `glow-2` the special one, `alert` bad.
- Progress is a row of cells, never a smooth bar. Loading is an 8-cell chase.
- Icons are 7×7 one-bit bitmaps drawn at 2 px per cell in the text colour.

The full catalogue with states and motion for about 60 components is `COMPONENTS.md`;
motion is `MOTION.md`; the reasoning behind the art side is `RULES.md`.

## 4. Check your work

```sh
python3 tools/check.py path/to/what/you/made
```

It reports rounded corners, soft shadows, blur, gradients, off-palette colours (naming the
nearest token), foreign fonts and motion that is too long or smoothly eased. Fix every error.
Warnings are judgement calls; a line with the comment `glowgrid-allow` is skipped.

Then look at it. Take a screenshot and compare with `kit/web/demo.html`. Check that:

1. only one thing per surface is lit at rest;
2. no sentence is set in a pixel font;
3. nothing letter-spaced is cut off (Pango and some toolkits measure spaced text too narrow);
4. pixel fonts sit on whole pixels (VT323 and Silkscreen blur at odd sizes: prefer 16, 18, 20, 24, 28);
5. it still reads in Forge and Frost.

## 5. Things that go wrong

- **`[hidden]` ignored**: a component sets `display`, so the kit forces `[hidden]` to win. Keep that rule.
- **Emissive colour used as decoration**: if everything is orange, nothing is. Unlit things are `stone`.
- **A red that is not `alert`**: there is exactly one red.
- **VT323 ligatures**: the font merges "fi" into one cell. Disable ligatures where it is used for code.
- **Smooth toolkit defaults**: GTK switches, Qt Behaviors and CSS `ease` all tween. Override them with steps.
- **Rounded leftovers**: scrollbars, sliders, avatars and checkboxes are where radius hides.

## 6. Changing the system itself

Edit `tokens.json`, run `python3 tools/build_tokens.py`, and commit the regenerated files.
`python3 tools/build_tokens.py --check` fails if they are stale. To add a theme, add it under
`themes` with its light colours and a `terminal` block; every platform file picks it up.
