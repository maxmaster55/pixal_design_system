# Glowgrid motion

Motion is a primary element of Glowgrid, not decoration. A Glowgrid interface is recognisable
by how it moves as much as by how it looks:

> **Springs decide where things are. The pixel grid decides where they are drawn.**

Things that travel through space ride a spring, so they have momentum, can overshoot, and
can be interrupted. Every frame is then snapped to the pixel grid, so an overshoot is a few
whole-pixel hops and nothing ever sits between pixels. Things that change without travelling
(colour, opacity, reveals) move in a few held steps.

The model comes from two sources: [Weave](https://github.com/maxmaster55/weave-motion), which
supplies the spring solver and presets, and Material 3 Expressive, which supplies the split
between *spatial* motion (springs) and *effects* motion (no overshoot), shared elements, and
container transforms. The pixel quantisation and the held steps are Glowgrid's own.

See all of it live in [`kit/web/demo.html`](kit/web/demo.html).

## 1. Principles

1. **Space is sprung.** Position and size are driven by springs. A spring is described by
   stiffness and damping ratio, never by a duration: it takes as long as the distance needs.
2. **Drawn on the grid.** The spring's value is fractional; what reaches the screen is rounded
   to the quantum (2 px for UI, one art pixel for art). Never scale pixel art or text by a
   fractional factor; change size in whole pixels.
3. **Effects step.** Colour, opacity and visibility change in 2 to 8 held steps and never
   overshoot. A colour that bounced would flash.
4. **Interruptible.** Changing the destination keeps position and velocity. Nothing restarts
   from zero, and nothing blocks input while it moves.
5. **One identity.** When something selected moves, it is one object travelling (the tab
   indicator, the highlighted row), not one fading out and another fading in. When a surface
   opens from a control, the control becomes the surface.
6. **Content does not stretch.** A surface may resize on a spring; the text and icons inside
   step in after it lands.
7. **One hero per interaction.** The expressive spring is for the single most important
   movement. Everything else uses default or fast.
8. **It settles.** Springs come to rest; only lights loop (breathe, blink, chase, scan).
9. **Reduced motion is respected.** With the system setting on, springs lose their bounce and
   settle quickly (Weave's policy) and stepped effects jump to their end state.

## 2. Springs

`[stiffness, damping ratio]` at mass 1. Tokens: `ui.motion.springs` in `tokens.json`.

| Preset | Values | Feel | Use it for |
| --- | --- | --- | --- |
| fast | 500, 0.85 | Quick and tight, barely overshoots | Things under the pointer: switch thumbs, the tab indicator, press feedback, drags |
| default | 300, 0.80 | Everyday | Menus, panels, rows reordering, anything closing |
| expressive | 220, 0.65 | A visible, friendly bounce | One hero moment: a container opening, a dropped item landing |
| gentle | 140, 1.00 | Slow, no overshoot | Large surfaces: drawers, workspace changes, full-screen transitions |

How these relate to Material 3 Expressive: its *spatial* tokens (fast, default, slow) map to
fast, default and gentle here; its *expressive* scheme, which lowers damping so movement
overshoots, is the expressive preset; its *effects* tokens, which never overshoot, are the
stepped timings in section 4. The numbers are Weave's, not Google's.

**Choosing:** if the user's finger or pointer is on it, fast. If it is the reason the user
acted, expressive. If it covers most of the screen, gentle. Otherwise default.

## 3. Spatial patterns

| Pattern | What happens | Spring | Web |
| --- | --- | --- | --- |
| Enter | Elements arrive from a 16 px offset, 30 ms apart; opacity steps in | default | `ggEnter(els)` |
| Container transform | A button, row or card becomes a panel or dialog: a square surface travels and resizes from one rectangle to the other, then the content steps in | expressive open, default close | `ggMorph(from, to)`, `ggUnmorph(to)`, `data-gg-morph` |
| Shared element | The selection mark travels between items and resizes to fit | fast | `ggIndicator(tabs)`, `data-gg-indicator` |
| Switch | The thumb travels to its stop and overshoots by a hop | fast | `ggSpringSwitches()` |
| Drag and release | The object follows the pointer exactly, then springs to its resting place with the throw's velocity | expressive | `ggDrag(el)`, `data-gg-drag` |
| Reorder | Rows travel from their old places to their new ones | default | `ggReorder(list, mutate)` |
| Ticker | A number rides to its new value in whole numbers | default | `ggTicker(el, to)` |
| Window movement | Windows and workspaces slide on springs; destination changes keep momentum | gentle for workspaces, default for windows, fast for resize | `kit/desktop/niri.kdl` |
| Cell assembly | A window or dialog is built from 24 px cells, centre first | 280 ms in 7 steps (an effect, not a spring) | `gg-m-assemble`, niri shader |

## 4. Stepped effects

| Name | Duration | Steps | Use it for |
| --- | --- | --- | --- |
| press | 80 ms | 2 | Hover, press, any colour change on a control |
| toggle | 120 ms | 3 | A track changing colour, a progress cell filling, an accordion marker |
| move | 180 ms | 4 to 5 | Entering and leaving when no spring is available |
| reveal | 280 to 400 ms | 7 to 8 | Wipes, cell assembly, charts growing |

Art and spinners run at **12 frames a second** (83 ms a frame).

| Primitive | Class | What happens | Plays when |
| --- | --- | --- | --- |
| rise | `gg-m-rise`, or `gg-fresh` on a list | Fades in while moving up 8 px, 5 steps. Siblings start 30 ms apart. | The CSS-only version of Enter |
| drop / lift-out | `gg-m-drop`, `gg-m-lift-out` | 8 px down in 4 steps; back up in 3 | Menus and popovers without the script |
| slide | `gg-m-slide`, `gg-m-slide-out` | 16 px from the side, 4 steps in, 3 out | Toasts, drawers, tab pages |
| wipe | `gg-m-wipe` | Revealed left to right in 8 steps | Headlines, banners, images |
| assemble | `gg-m-assemble` | 24 px cells grow until they tile the surface | Windows, dialogs, hero art |
| flash | `gg-m-flash` | Accent fill for two frames | A value just changed |
| shake | `gg-m-shake` | 4 px left, right, 2 px left, rest | Input rejected |
| type | `data-gg-type` | One character every 100 ms | Terminal text |
| count | `data-gg-count` | Counts up in 10 held frames, then flashes | Stat tiles without the script |
| grow | `gg-bars`, `gg-bar-fill` | Scales from the baseline in 8 steps | Charts appear |
| breathe | `gg-m-breathe` | Two held brightness levels | A lit status cell (ambient) |
| blink | `gg-m-blink` | On and off at 1 Hz | Cursors (ambient) |
| chase | `gg-spinner` | A hot cell and a warm tail cross 8 cells | Working (ambient) |
| scan | `gg-skeleton` | One lit cell crosses unlit cells | Loading (ambient) |

## 5. Rules of thumb

- Enter on a spring; leave faster than you entered (default to open, a 120 ms step-out or the
  default spring to close).
- Offsets and sizes land on 2, 4, 8 or 16 px.
- Stagger siblings by 30 ms, at most eight; the rest arrive together.
- Do not spring opacity, colour, blur or anything that must stay within a range.
- Press feedback is physical: a button lifts toward the light on hover and sinks into its
  hard shadow on press.
- If a platform cannot do springs, use the stepped move timing. If it cannot do steps either
  (GTK's revealer and stack), keep the eased transition at or under 180 ms.

## 6. Per platform

| Platform | Springs | Steps |
| --- | --- | --- |
| Web | `kit/web/vendor/weave.js` + `kit/web/glowgrid-motion.js` (the functions above). Set `ggMotion.grid` to change the quantum. | The `gg-m-*` classes; `glowgrid-ui.js` for show, hide and replay |
| Rust (any renderer) | The `weave-core` crate: advance springs each frame, round to the quantum before drawing | A timer at 83 ms |
| Qt Quick | `kit/qml/GgSpring.qml`: an analytic spring with a `grid` property | A `Timer` walking an integer step (see `GgSwitch.qml`) |
| GTK 4 | Drive widget positions from a tick callback with `weave-core`, rounding to the quantum; `GtkRevealer`/`GtkStack` at 180 ms where that is too much work | CSS `transition: ... steps(n)` and `@keyframes` (end of `kit/gtk4/glowgrid.css`) |
| niri | `kit/desktop/niri.kdl`: Weave presets for workspace, window and view movement | Cell assemble/disassemble shaders for open and close |
| Terminal | none | `cursor_blink_interval 0.5 steps(1)` in kitty |
