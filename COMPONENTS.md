# Glowgrid components

Every component in the system, what it is for, its states, and how it moves. The web kit
(`kit/web`) implements all of them; the GTK and QML columns say what exists there today.

See them live: open [`kit/web/demo.html`](kit/web/demo.html), or build one shareable file with
`python3 tools/build_single.py`. Motion names refer to [`MOTION.md`](MOTION.md): spatial movement uses springs drawn on the
pixel grid, effects use held steps.

**Reading the tables.** *Class* is the web class; the markup to copy is in `demo.html`.
*Motion* names the primitive and when it plays. GTK: ● styled in `kit/gtk4/glowgrid.css`,
○ a stock widget the stylesheet restyles, blank = build it from `.row`/`.panel`. QML: the
component file in `kit/qml`, or blank.

## Rules every component follows

1. Square corners. `border-radius` is always 0.
2. Shadows are hard: an offset, no blur. Sizes are 3, 4 and 8 px (icon button, text button, panel).
3. Fills are flat token colours. No gradients; shade with a second flat tone or a dither.
4. Emissive colours (accent, accent-hot, glow-1/2/3, alert) mean "this is a light". At rest
   a surface has at most one lit thing competing for the eye.
5. Type: Silkscreen for labels, VT323 for values, IBM Plex Sans for anything a person reads
   as a sentence, Pixelify Sans for one headline per surface.
6. Resting outline is 1 px stone; hover, selection and focus are 2 px accent. Keyboard focus
   is a 2 px glow-3 outline.
7. Motion is primary. Position and size ride springs and are drawn on the 2 px grid; colour
   and opacity change in held steps. Nothing eases smoothly, and everything settles.

## Actions

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Button | `gg-btn` + `primary` / `ghost` / `danger` | rest, hover, pressed, disabled, busy | hover lifts 2 px and the shadow grows to 6 px (press, 80 ms); press sinks 2 px into the shadow; `busy` runs a 5-cell chase | ● `button.text` | `GgButton` |
| Icon button | `gg-iconbtn` | rest, hover, pressed, disabled | hover fills with the accent (press); press sinks 3 px | ● `button.icon` | |
| Segmented control | `gg-segment` | one segment lit | colour steps over 80 ms | | |
| Link | `gg-link` | rest, hover | underline becomes a filled block (press) | | |

## Inputs

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Text field | `gg-input` in `gg-field` | rest, focus, invalid, disabled | focus outline swaps to 2 px accent; `invalid` plays shake once | ○ entry | |
| Launcher input | `gg-input value` | as text field | block cursor blinks at 1 Hz | | |
| Text area | `textarea.gg-input` | as text field | as text field | ○ | |
| Select | `select.gg-input` | closed, open | its menu drops | ○ dropdown | |
| Switch | `gg-switch` (+ `power`) | off, on, disabled | the thumb travels on the fast spring and overshoots its stop (3 held steps without the script); the track colour steps | ○ switch, `switch.power` | `GgSwitch` |
| Checkbox / radio | `gg-check` | off, on | mark appears in one step | ○ | |
| Slider | `gg-range` | rest, dragging | thumb follows the pointer; no easing | ○ scale | |
| Stepper | `gg-stepper` | value, at limit | the value flashes on each change | | |
| Chip | `gg-chip` | rest, removing | removed in one step | | |
| Drop zone | `gg-dropzone` (+ `over`) | rest, drag-over | dashed outline turns glow-1 in one step | ● `.dropzone` | |

## Navigation

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Bar | `gg-bar` | | none; its contents animate | | reference: nixos_conf `Bar.qml` |
| Workspace cells | `gg-cells-ws` | empty, occupied, active | the active cell is lit with a square halo; changes in one step | | |
| Clock | `gg-clock` | | changes on the minute, no animation | | |
| Tabs | `gg-tabs` / `gg-tab` | rest, hover, selected | shared element: one accent bar travels between tabs on the fast spring (`data-gg-indicator`); the new page slides in | ● `.tabs`, `button.tab` | |
| Sidebar | `gg-nav` | rest, hover, current | a 3 px accent rail steps in on the current item | | |
| Breadcrumbs | `gg-crumbs` | | none | | |
| Pagination | `gg-pager` | rest, hover, current | colour steps (press) | | |
| Steps | `gg-steps` | done, now, to do | the current cell breathes | | |
| Menu | `gg-menu` | closed, open, item active | drops in (180 ms), lifts out (120 ms) | ○ popover | |
| Launcher | `gg-launcher` | empty, results, item active | assembles from cells; results rise in | | |
| Key cap | `gg-kbd` | | none | | |

## Containers

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Panel | `gg-panel` (+ `lit` / `framed`) with `gg-head`, `gg-body`, `gg-foot` | | drops from a bar, or assembles | ● `.panel`, `.head`, `.page`, `.foot` | `GgPanel` |
| Card | `gg-card` (+ `interactive`) | rest, hover, pressed | interactive: lifts 2 px and gains the accent outline; sinks 4 px on press | | `GgPanel` |
| Row | `gg-row` (+ `selected`) | rest, hover, selected | outline steps to 2 px accent (press); lists enter on the default spring, 30 ms apart; reordering travels (`ggReorder`) | ● `.row`, `.row.me` | |
| Group heading | `gg-group` | | rises with its list | ● `.group` | `GgLabel` |
| Window frame | `gg-window` (+ `focused`) | focused, unfocused | assembles on open, disassembles on close (280 / 220 ms) | reference: `kit/desktop/niri.kdl` | |
| Dialog | `gg-scrim` + `gg-dialog` | closed, open | container transform from the control that opened it (expressive spring), or cell assembly; the scrim (a 2 px dither, never a blur) appears in one step | | |
| Drawer | `gg-drawer` | closed, open | slides in from the edge; its rows rise | | |
| Accordion | `details.gg-accordion` | closed, open | the marker cell lights (toggle); content rises | | |
| Tooltip | `gg-tooltip[data-tip]` | hidden, shown | appears in 2 steps | ○ tooltip | |
| Divider | `gg-divider` (+ `dashed`) | | none | | |

## Feedback

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Toast | `gg-toast` in `gg-toasts`; `ggToast()` | entering, shown, leaving | slides in, stays 4 s, slides out | ● `.toast` (footer line) | |
| Banner | `gg-banner` + `good` / `warn` / `bad` | | wipes in when it appears | | |
| Progress cells | `gg-cells` with `full` / `done` / `failed` | running, done, failed | cells fill one at a time (toggle); all turn glow-1 when done | ● `.cell` | `GgCells` |
| Stepped bar | `gg-bar-fill` | | fills in 8 steps when it appears | | |
| Spinner | `gg-spinner` | | 8-cell spark chase at 12 frames a second | ● `.spark` | |
| Skeleton | `gg-skeleton` | | one lit cell scans across, 12 steps a second | | |
| Status cell | `gg-dot` + `on` / `focal` / `alert` | unlit, lit | lit cells breathe between two levels (alert faster) | ● `.dot` | |
| Pill | `gg-pill` (+ `ghost`) | | none | ● `.pill` | |
| Badge | `gg-badge` (+ `quiet`) | | flashes when the count changes | ● `.count` | |
| On-screen display | `gg-osd` | | drops in; cells follow the value in whole cells | | |
| Empty state | `gg-empty` | | rises in | ● `.message` | |

## Data

| Component | Class | States | Motion | GTK | QML |
| --- | --- | --- | --- | --- | --- |
| Stat tile | `gg-stat` | | the value rides a spring to its new number (`ggTicker`), or counts up in 10 held steps, then flashes | | `GgPanel` + `GgValue` |
| Key and value | `dl.gg-kv` | | a changed value flashes | | `GgLabel` + `GgValue` |
| Bar chart | `gg-bars` | | columns grow from the baseline in 8 steps, 30 ms apart | | |
| Meter | `gg-meter` | | columns change in whole steps | | `GgCells { rising: true }` |
| Table | `gg-table` | | rows rise on first load | | |
| Calendar | `gg-calendar` | today, other month | none | | reference: nixos_conf `Widgets.qml` |
| Timeline | `gg-timeline` | done, now, to do | the current cell breathes | | |
| Avatar | `gg-avatar` | | none | | |
| Terminal block | `gg-term`, `gg-cursor` | | text types at 10 characters a second; cursor blinks at 1 Hz | | |

## Desktop pieces

| Component | Class | Motion | Reference implementation |
| --- | --- | --- | --- |
| Lock screen clock | `gg-bigclock` | none | nixos_conf `noctalia/config.toml` |
| Login box | `gg-login` | pins light one per key; shake on a wrong password | |
| Notification | `gg-toast` | slides in from the screen edge | |
| Tray icon | 3×3 lattice on a 16×16 grid | cells change in one step | pixelscale `src/icons.rs` |
| Cursor | 16×16 art pixels | busy cursor is the 8-cell chase | `kit/cursor` |
| Wallpaper | 192×108 art pixels, seeded | 12 frames a second; must settle | nixos_conf `glowgrid/wallpaper`, `Background.qml` |

## Foundations

| Thing | Where |
| --- | --- |
| Colour and size tokens | `tokens.json`, generated into every `kit/*/tokens*` file |
| Type roles | `gg-display`, `gg-label`, `gg-value`, `gg-name`, `gg-hint` |
| Icons | 32 one-bit 7×7 icons in `kit/icons/icons.json`; `tools/icons.py` exports SVG |
| Heading marker | `gg-heading`: an accent square with a hard shadow before the text |
