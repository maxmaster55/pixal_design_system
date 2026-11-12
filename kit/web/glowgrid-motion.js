/* Glowgrid motion: spring physics drawn on the pixel grid.

   Position and size move on springs (momentum, overshoot, interruptible), computed by Weave
   (vendor/weave.js, https://github.com/maxmaster55/weave-motion). What makes it Glowgrid is the
   last step: every value is snapped to the 2 px grid before it reaches the screen, so a bounce
   is a few whole-pixel hops, not a smooth glide. Colour and opacity never spring; they step.

   Load order: vendor/weave.js, then this file. Without Weave everything jumps to its end state.

   Presets (stiffness, damping ratio), from Weave:
     fast        500, 0.85   things under the pointer: switches, presses, the tab indicator
     default     300, 0.80   everyday movement: menus, panels, rows
     expressive  220, 0.65   one hero moment per interaction: a container opening, a drop landing
     gentle      140, 1.00   large surfaces: drawers, full-screen changes. No overshoot.

   API
     ggSpring(el, { x, y, w, h }, { preset, grid })   spring an element's offset or size
     ggEnter(els, { from: { x, y }, stagger, preset })  elements arrive in order
     ggMorph(fromEl, toEl, { preset })                one element becomes another (container transform)
     ggUnmorph(toEl)                                  and back to where it came from
     ggIndicator(tabsEl)                              an accent bar that travels between tabs
     ggSpringSwitches(scope)                          switch thumbs overshoot their stop
     ggDrag(el, { preset })                           drag it; on release it springs home
     ggReorder(listEl, mutate)                        change the order, rows travel to their new places
     ggTicker(el, to, { preset })                     a number settles onto its new value
     ggMotion.grid = 2                                the pixel quantum; set 1 to see the raw springs
   Attributes: data-gg-morph="#target", data-gg-indicator, data-gg-drag, data-gg-enter */
(function (root) {
  "use strict";
  const W = root.Weave;
  const ggMotion = { grid: 2, available: !!W };
  const snap = (v, g) => { g = g || ggMotion.grid; return Math.round(v / g) * g; };
  const els = t => typeof t === "string" ? [...document.querySelectorAll(t)] : t instanceof Element ? [t] : [...t];
  const state = new WeakMap(); // element -> { x, y, w, h springs }

  function springs(el) {
    let s = state.get(el);
    if (!s) { s = { v: { x: 0, y: 0 }, sp: {} }; state.set(el, s); }
    return s;
  }
  function paint(el, s) {
    el.style.transform = (s.v.x || s.v.y) ? `translate(${snap(s.v.x)}px, ${snap(s.v.y)}px)` : "";
    if (s.v.w != null) el.style.width = Math.max(0, snap(s.v.w)) + "px";
    if (s.v.h != null) el.style.height = Math.max(0, snap(s.v.h)) + "px";
  }

  /** Spring an element's offset (x, y) and/or size (w, h), in pixels. Call again mid-flight to
      change destination: position and velocity carry over. Resolves when everything rests. */
  function ggSpring(el, to, opts) {
    opts = opts || {};
    const s = springs(el), waits = [];
    for (const k of Object.keys(to)) {
      if (!W) { s.v[k] = to[k]; continue; }
      if (!s.sp[k]) {
        if (s.v[k] == null) s.v[k] = k === "w" ? el.offsetWidth : k === "h" ? el.offsetHeight : 0;
        s.sp[k] = W.spring(s.v[k], v => { s.v[k] = v; paint(el, s); }, { preset: opts.preset || "default" });
      }
      if (opts.from && opts.from[k] != null) s.sp[k].set(opts.from[k]);
      waits.push(s.sp[k].to(to[k]));
    }
    paint(el, s);
    return Promise.all(waits);
  }

  /** Elements arrive one after another from an offset. Opacity steps in; it does not spring. */
  function ggEnter(targets, opts) {
    opts = Object.assign({ from: { y: 16 }, stagger: 0.03, preset: "default" }, opts);
    return Promise.all(els(targets).map((el, i) => new Promise(done => {
      el.style.opacity = "0";
      setTimeout(() => {
        el.style.transition = "opacity 120ms steps(3)";
        el.style.opacity = "1";
        ggSpring(el, { x: 0, y: 0 }, { from: { x: opts.from.x || 0, y: opts.from.y || 0 }, preset: opts.preset }).then(done);
      }, i * opts.stagger * 1000);
    })));
  }

  // ---- container transform: one surface becomes another ----
  const morphs = new WeakMap(); // target -> { from, ghost }
  function rectOf(el) { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }

  /** `from` (a button, a row, a card) grows into `to` (a panel, a dialog). A square ghost in the
      panel's colours travels and resizes on a spring; when it lands, the real content steps in. */
  function ggMorph(from, to, opts) {
    opts = Object.assign({ preset: "expressive" }, opts);
    const a = rectOf(from);
    to.hidden = false;
    const b = rectOf(to);
    if (!W) return Promise.resolve();
    const ghost = document.createElement("div");
    ghost.className = "gg-ghost";
    ghost.style.cssText = `position:fixed;left:0;top:0;z-index:60;pointer-events:none;background:var(--surface);box-shadow:0 0 0 2px var(--accent),8px 8px 0 #000;width:${a.w}px;height:${a.h}px;transform:translate(${a.x}px,${a.y}px)`;
    document.body.appendChild(ghost);
    to.style.visibility = "hidden";
    from.style.visibility = "hidden";
    morphs.set(to, { from: from });
    const s = { x: a.x, y: a.y, w: a.w, h: a.h };
    const draw = () => { ghost.style.transform = `translate(${snap(s.x)}px,${snap(s.y)}px)`; ghost.style.width = snap(s.w) + "px"; ghost.style.height = snap(s.h) + "px"; };
    const sp = {};
    return Promise.all(Object.keys(s).map(k => { sp[k] = W.spring(s[k], v => { s[k] = v; draw(); }, { preset: opts.preset }); return sp[k].to(b[k]); })).then(() => {
      Object.values(sp).forEach(x => x.destroy());
      ghost.remove();
      to.style.visibility = "";
      // content does not stretch with the surface; it steps in once the surface has landed
      [...to.children].forEach((c, i) => { c.style.animation = `gg-rise 160ms steps(4) ${i * 30}ms both`; });
    });
  }

  /** The reverse: `to` shrinks back into whatever it grew from. */
  function ggUnmorph(to, opts) {
    opts = Object.assign({ preset: "default" }, opts);
    const m = morphs.get(to);
    if (!m || !W) { to.hidden = true; if (m) m.from.style.visibility = ""; return Promise.resolve(); }
    const b = rectOf(to);
    m.from.style.visibility = "";
    const a = rectOf(m.from);
    m.from.style.visibility = "hidden";
    to.hidden = true;
    const ghost = document.createElement("div");
    ghost.style.cssText = "position:fixed;left:0;top:0;z-index:60;pointer-events:none;background:var(--surface);box-shadow:0 0 0 2px var(--accent),8px 8px 0 #000";
    document.body.appendChild(ghost);
    const s = { x: b.x, y: b.y, w: b.w, h: b.h }, sp = {};
    const draw = () => { ghost.style.transform = `translate(${snap(s.x)}px,${snap(s.y)}px)`; ghost.style.width = snap(s.w) + "px"; ghost.style.height = snap(s.h) + "px"; };
    draw();
    return Promise.all(Object.keys(s).map(k => { sp[k] = W.spring(s[k], v => { s[k] = v; draw(); }, { preset: opts.preset }); return sp[k].to(a[k]); })).then(() => {
      Object.values(sp).forEach(x => x.destroy());
      ghost.remove();
      m.from.style.visibility = "";
      morphs.delete(to);
    });
  }

  /** A 3 px accent bar that travels between the tabs of a .gg-tabs strip and resizes to fit:
      the selected state is one object that moves, not two that swap. */
  function ggIndicator(tabs) {
    if (tabs._ggIndicator) return tabs._ggIndicator;
    tabs.style.position = "relative";
    tabs.classList.add("gg-has-indicator");
    const bar = document.createElement("i");
    bar.style.cssText = "position:absolute;top:0;left:0;height:3px;background:var(--accent);pointer-events:none";
    tabs.appendChild(bar);
    const s = { x: 0, w: 0 }, draw = () => { bar.style.transform = `translateX(${snap(s.x)}px)`; bar.style.width = snap(s.w) + "px"; };
    const sx = W && W.spring(0, v => { s.x = v; draw(); }, { preset: "fast" });
    const sw = W && W.spring(0, v => { s.w = v; draw(); }, { preset: "fast" });
    const go = jump => {
      const t = tabs.querySelector('.gg-tab[aria-selected="true"], .gg-tab.active');
      if (!t) return;
      if (!W || jump) { s.x = t.offsetLeft; s.w = t.offsetWidth; if (W) { sx.set(s.x); sw.set(s.w); } draw(); }
      else { sx.to(t.offsetLeft); sw.to(t.offsetWidth); }
    };
    tabs.addEventListener("click", () => requestAnimationFrame(() => go(false)));
    root.addEventListener("resize", () => go(true));
    go(true);
    return (tabs._ggIndicator = { update: go });
  }

  /** Switch thumbs travel on the fast spring and overshoot their stop by a pixel hop or two. */
  function ggSpringSwitches(scope) {
    if (!W) return;
    (scope || document).querySelectorAll(".gg-switch").forEach(sw => {
      if (sw._ggSpring) return;
      const input = sw.querySelector("input"), track = sw.querySelector("i");
      if (!input || !track) return;
      const power = sw.classList.contains("power"), travel = power ? 32 : 22;
      const thumb = document.createElement("b");
      thumb.style.cssText = `position:absolute;top:4px;left:4px;width:${power ? 24 : 14}px;height:${power ? 24 : 14}px;pointer-events:none`;
      sw.appendChild(thumb);
      sw.classList.add("gg-sprung"); // CSS hides the ::after thumb while this one is in charge
      const paintThumb = () => { thumb.style.background = input.checked ? "var(--ink)" : "var(--text-soft)"; };
      const sp = W.spring(input.checked ? travel : 0, v => { thumb.style.transform = `translateX(${snap(v)}px)`; }, { preset: "fast" });
      thumb.style.transform = `translateX(${input.checked ? travel : 0}px)`;
      paintThumb();
      input.addEventListener("change", () => { paintThumb(); sp.to(input.checked ? travel : 0); });
      sw._ggSpring = sp;
    });
  }

  /** Drag an element anywhere; on release it springs back to where it lives. */
  function ggDrag(el, opts) {
    opts = Object.assign({ preset: "expressive" }, opts);
    let start = null;
    el.style.touchAction = "none";
    el.style.cursor = "grab";
    el.addEventListener("pointerdown", e => {
      const s = springs(el);
      Object.values(s.sp).forEach(sp => sp.stop());
      start = { px: e.clientX, py: e.clientY, x: s.v.x || 0, y: s.v.y || 0 };
      el.setPointerCapture(e.pointerId);
      el.style.cursor = "grabbing";
    });
    el.addEventListener("pointermove", e => {
      if (!start) return;
      const s = springs(el);
      s.v.x = start.x + e.clientX - start.px; s.v.y = start.y + e.clientY - start.py;
      if (s.sp.x) s.sp.x.set(s.v.x);
      if (s.sp.y) s.sp.y.set(s.v.y);
      paint(el, s);
    });
    const release = () => { if (!start) return; start = null; el.style.cursor = "grab"; ggSpring(el, { x: 0, y: 0 }, { preset: opts.preset }); };
    el.addEventListener("pointerup", release);
    el.addEventListener("pointercancel", release);
  }

  /** Change a list's order inside `mutate`; each row then travels from where it was to where it is. */
  function ggReorder(list, mutate, opts) {
    opts = Object.assign({ preset: "default" }, opts);
    const before = new Map([...list.children].map(c => [c, c.getBoundingClientRect()]));
    mutate();
    [...list.children].forEach(c => {
      const a = before.get(c), b = c.getBoundingClientRect();
      if (!a) return;
      const s = springs(c), dx = a.left - b.left + (s.v.x || 0), dy = a.top - b.top + (s.v.y || 0);
      if (dx || dy) ggSpring(c, { x: 0, y: 0 }, { from: { x: dx, y: dy }, preset: opts.preset });
    });
  }

  /** A number rides a spring to its new value, shown as whole numbers (or `digits` decimals). */
  function ggTicker(el, to, opts) {
    opts = Object.assign({ preset: "default", digits: 0 }, opts);
    if (!W) { el.textContent = to.toFixed(opts.digits); return; }
    if (!el._ggTicker) el._ggTicker = W.spring(parseFloat(el.textContent) || 0, v => { el.textContent = v.toFixed(opts.digits); }, { preset: opts.preset });
    return el._ggTicker.to(to);
  }

  function init(scope) {
    scope = scope || document;
    scope.querySelectorAll("[data-gg-indicator]").forEach(ggIndicator);
    scope.querySelectorAll("[data-gg-drag]").forEach(el => ggDrag(el, { preset: el.dataset.ggDrag || "expressive" }));
    scope.querySelectorAll("[data-gg-morph]").forEach(b => b.addEventListener("click", () => ggMorph(b, document.querySelector(b.dataset.ggMorph))));
    scope.querySelectorAll("[data-gg-unmorph]").forEach(b => b.addEventListener("click", () => ggUnmorph(b.closest(b.dataset.ggUnmorph || "[data-gg-morph-target]"))));
    if (scope.querySelector && scope.querySelector("[data-gg-spring-switches]")) ggSpringSwitches(scope);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init(document)); else init(document);

  Object.assign(root, { ggMotion, ggSpring, ggEnter, ggMorph, ggUnmorph, ggIndicator, ggSpringSwitches, ggDrag, ggReorder, ggTicker, ggMotionInit: init });
})(window);
