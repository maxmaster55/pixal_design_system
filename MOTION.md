# Glowgrid motion

Motion in Glowgrid looks like pixel art moving: **held frames, whole steps, short, and it
settles.** Nothing eases smoothly and nothing loops unless it is a light.

## The four timings

| Name | Duration | Steps | Use it for |
| --- | --- | --- | --- |
| press | 80 ms | 2 | Hover, press, any colour change on a control |
| toggle | 120 ms | 3 | Switches, a progress cell filling, an accordion marker |
| move | 180 ms | 4 to 5 | Things entering or leaving: menus, panels, tab pages, list rows |
| reveal | 280 to 400 ms | 7 to 8 | Windows and dialogs assembling, wipes, charts growing |

Art and spinners run at **12 frames a second** (83 ms a frame). In CSS that is `steps()`;
in code, compute `floor(elapsed / 83)` and redraw only when it changes.

## The primitives

Every animation in the kit is one of these. Web classes are in `kit/web/glowgrid-ui.css`.

| Primitive | Class | What happens | Plays when |
| --- | --- | --- | --- |
| rise | `gg-m-rise`, or `gg-fresh` on a list | Fades in while moving up 8 px, 5 steps, 200 ms. Siblings start 30 ms apart. | A list, card or empty state appears |
| drop | `gg-m-drop` | Fades in while moving down 8 px, 4 steps, 180 ms | A menu, popover or bar panel opens |
| lift-out | `gg-m-lift-out` | The reverse of drop, 3 steps, 120 ms | The same things close |
| slide | `gg-m-slide` / `gg-m-slide-out` | 16 px from the side, 4 steps in, 3 out | Toasts, drawers, tab pages |
| wipe | `gg-m-wipe` | Revealed left to right in 8 steps, 400 ms | Headlines, banners, images |
| assemble | `gg-m-assemble` | 24 px cells grow until they tile the surface, 7 steps, 280 ms | Windows, dialogs, the launcher, hero art |
| flash | `gg-m-flash` | Accent fill for two frames, then back | A value just changed |
| shake | `gg-m-shake` | 4 px left, right, 2 px left, rest: 4 steps, 240 ms | Input rejected |
| type | `data-gg-type` | One character every 100 ms, block cursor | Terminal text, launcher placeholder |
| count | `data-gg-count` | Counts to the value in 10 held frames, then flashes | Stat tiles |
| grow | `gg-bars`, `gg-bar-fill` | Scales from the baseline in 8 steps | Charts and determinate bars appear |
| breathe | `gg-m-breathe` | Two held brightness levels, 1.4 s each way | A lit status cell (ambient) |
| blink | `gg-m-blink` | On and off at 1 Hz | Cursors (ambient) |
| chase | `gg-spinner` | A hot cell and a warm tail move across 8 cells at 12 fps | Something is working (ambient) |
| scan | `gg-skeleton` | One lit cell crosses a row of unlit cells | Content is loading (ambient) |

## Rules

1. **Step, don't tween.** Use `steps(n)`. If a platform only offers eased animation
   (GTK's revealer and stack), keep it at or under 180 ms so it reads as a quick snap.
2. **Enter longer than you leave.** 180 ms in, 120 ms out.
3. **Move on the grid.** Offsets are whole pixels (2, 4, 8, 16). Never scale pixel art or
   text by a fractional factor.
4. **One thing moves at a time** per surface, except a list rising in order.
5. **It settles.** One-shot animations end within 400 ms (reveals of large art may take up
   to 1.6 s). Only lights loop: breathe, blink, chase, scan.
6. **Press feedback is physical.** Buttons lift toward the light on hover and sink into
   their hard shadow on press; nothing glows or fades.
7. **Space uses springs where the platform has them** (compositor window movement, drags).
   Presets from weave-motion, as `[stiffness, damping ratio]`: gentle `[140, 1.0]` for large
   surfaces, default `[300, 0.8]`, fast `[500, 0.85]` for direct manipulation, expressive
   `[220, 0.65]` when a little bounce is wanted. A change of destination keeps the momentum.
8. **Reduced motion.** Under `prefers-reduced-motion: reduce` (or the platform's equivalent)
   show the end state immediately. The kit's CSS and JS already do.

## Per platform

| Platform | How |
| --- | --- |
| Web | The classes above; `glowgrid-ui.js` adds show/hide with the right entrance and exit, replay, toasts, count and type |
| GTK 4 | CSS `transition: ... steps(n)` and `@keyframes` work (see the motion block at the end of `kit/gtk4/glowgrid.css`). Use `GtkRevealer` and `GtkStack` transitions at 180 ms for open/close and tab slides. Drive chases from a 83 ms timer that swaps classes. |
| Qt Quick | A `Timer` that walks an integer step (see `GgSwitch.qml`), or `NumberAnimation` with `easing.type: Easing.Linear` on an integer property. Avoid `Behavior` with default easing. |
| niri | `kit/desktop/niri.kdl`: cell assemble/disassemble shaders for window open/close, Weave springs for movement |
| Terminal | Cursor blink 0.5 s with a stepped curve (`cursor_blink_interval 0.5 steps(1)` in kitty) |
