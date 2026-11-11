/* Glowgrid UI behaviours. Optional: the CSS works without it. No dependencies.
   Everything is driven by data attributes, so markup alone wires a page up:

     data-gg-tabs                on a container: its .gg-tab[data-panel="#id"] buttons switch panels
     data-gg-open="#id"          a click shows that element (dialog scrim, drawer, menu)
     data-gg-close               a click hides the nearest opened element
     data-gg-menu="#id"          a click toggles a .gg-menu; Esc or an outside click closes it
     data-gg-segment             on a .gg-segment: its buttons act as a radio group
     data-gg-stepper             on a .gg-stepper: [-] and [+] buttons change its <output>
     data-gg-count="1234"        counts up to the number in held steps when it scrolls into view
     data-gg-type                types its text at 10 characters a second
     data-gg-replay="#id"        a click replays the motion class on that element
     data-gg-dismiss             a click removes the nearest .gg-chip / .gg-toast / .gg-banner

   Functions: ggToast(text, kind), ggReplay(el), ggCount(el, to), ggShow(el), ggHide(el).
   Motion honours prefers-reduced-motion: everything jumps to its end state. */
(function (root) {
  "use strict";
  const reduced = () => root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const FRAME = 1000 / 12; // pixel-art cadence: 12 held frames a second
  const MOTION = ["gg-m-rise", "gg-m-drop", "gg-m-slide", "gg-m-wipe", "gg-m-assemble", "gg-m-flash", "gg-m-shake", "gg-m-type"];

  /** Play an element's motion class again from the start. */
  function ggReplay(el) {
    if (!el) return;
    const targets = [el, ...el.querySelectorAll("[class*='gg-m-'], .gg-fresh, .gg-bars, .gg-bar-fill, .gg-accordion[open]")];
    targets.forEach(t => {
      const anim = t.getAnimations ? t.getAnimations({ subtree: true }) : [];
      anim.forEach(a => { a.cancel(); a.play(); });
    });
    el.querySelectorAll("[data-gg-count]").forEach(c => ggCount(c, +c.dataset.ggCount));
    el.querySelectorAll("[data-gg-type]").forEach(type);
  }

  /** Show an element with its entrance motion. Dialog scrims animate their dialog. */
  function ggShow(el, motion) {
    if (!el) return;
    el.hidden = false;
    const body = el.classList.contains("gg-scrim") ? el.firstElementChild : el;
    const cls = motion || body.dataset.ggMotion || (el.classList.contains("gg-scrim") ? "gg-m-assemble" : el.classList.contains("gg-drawer") ? "gg-m-slide" : "gg-m-drop");
    MOTION.concat(["gg-m-lift-out", "gg-m-slide-out"]).forEach(c => body.classList.remove(c));
    void body.offsetWidth; // restart the animation
    body.classList.add(cls);
    const focusable = body.querySelector("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    if (focusable) focusable.focus({ preventScroll: true });
  }

  /** Hide an element, playing the matching exit first. */
  function ggHide(el) {
    if (!el || el.hidden) return;
    const body = el.classList.contains("gg-scrim") ? el.firstElementChild : el;
    const out = el.classList.contains("gg-drawer") || el.classList.contains("gg-toast") ? "gg-m-slide-out" : "gg-m-lift-out";
    if (reduced()) { el.hidden = true; return; }
    MOTION.forEach(c => body.classList.remove(c));
    body.classList.add(out);
    setTimeout(() => { el.hidden = true; body.classList.remove(out); }, 130);
  }

  /** Count up to `to` in held steps (about 10 frames). */
  function ggCount(el, to) {
    const digits = (String(to).split(".")[1] || "").length, steps = 10;
    if (reduced()) { el.textContent = to.toFixed(digits); return; }
    let i = 0;
    clearInterval(el._ggTimer);
    el._ggTimer = setInterval(() => {
      i++;
      el.textContent = (to * i / steps).toFixed(digits);
      if (i >= steps) { clearInterval(el._ggTimer); el.classList.add("gg-m-flash"); setTimeout(() => el.classList.remove("gg-m-flash"), 200); }
    }, FRAME);
  }

  /** Type an element's text at 10 characters a second with a block cursor. */
  function type(el) {
    const text = el.dataset.ggText || (el.dataset.ggText = el.textContent);
    if (reduced()) { el.textContent = text; return; }
    let i = 0;
    clearInterval(el._ggTimer);
    el.textContent = "";
    el._ggTimer = setInterval(() => { el.textContent = text.slice(0, ++i); if (i >= text.length) clearInterval(el._ggTimer); }, 100);
  }

  /** Show a toast for four seconds. kind: "good" (default), "bad", "info". */
  function ggToast(text, kind) {
    let stack = document.querySelector(".gg-toasts");
    if (!stack) { stack = document.createElement("div"); stack.className = "gg gg-toasts"; stack.style.background = "transparent"; document.body.appendChild(stack); }
    const t = document.createElement("div");
    t.className = "gg-toast gg-m-slide";
    t.setAttribute("role", "status");
    const dot = kind === "bad" ? "alert" : kind === "info" ? "focal" : "on";
    t.innerHTML = `<i class="gg-dot ${dot}" style="margin-top:4px"></i><div></div>`;
    t.lastElementChild.textContent = text;
    stack.appendChild(t);
    setTimeout(() => { t.classList.remove("gg-m-slide"); t.classList.add("gg-m-slide-out"); setTimeout(() => t.remove(), 130); }, 4000);
    return t;
  }

  function init(scope) {
    const $$ = (sel, el) => [...(el || scope).querySelectorAll(sel)];

    $$("[data-gg-tabs]").forEach(group => {
      const tabs = $$(".gg-tab[data-panel]", group);
      tabs.forEach(tab => tab.addEventListener("click", () => {
        tabs.forEach(t => {
          const on = t === tab, panel = document.querySelector(t.dataset.panel);
          t.setAttribute("aria-selected", String(on));
          if (panel) { panel.hidden = !on; if (on) { panel.classList.remove("gg-m-slide"); void panel.offsetWidth; panel.classList.add("gg-m-slide"); } }
        });
      }));
    });

    $$("[data-gg-open]").forEach(b => b.addEventListener("click", () => ggShow(document.querySelector(b.dataset.ggOpen))));
    $$("[data-gg-close]").forEach(b => b.addEventListener("click", () => ggHide(b.closest(".gg-scrim, .gg-drawer, .gg-menu, [data-gg-closable]"))));
    $$(".gg-scrim").forEach(s => s.addEventListener("click", e => { if (e.target === s) ggHide(s); }));
    $$("[data-gg-menu]").forEach(b => b.addEventListener("click", e => {
      e.stopPropagation();
      const m = document.querySelector(b.dataset.ggMenu);
      if (m.hidden) ggShow(m, "gg-m-drop"); else ggHide(m);
    }));
    $$("[data-gg-segment]").forEach(seg => $$("button", seg).forEach(b => b.addEventListener("click", () =>
      $$("button", seg).forEach(x => x.setAttribute("aria-pressed", String(x === b))))));
    $$("[data-gg-stepper]").forEach(st => {
      const out = st.querySelector("output"), [minus, plus] = $$("button", st);
      const step = +(st.dataset.step || 1), min = +(st.dataset.min ?? -Infinity), max = +(st.dataset.max ?? Infinity);
      const bump = d => { out.textContent = Math.min(max, Math.max(min, +out.textContent + d)); out.classList.remove("gg-m-flash"); void out.offsetWidth; out.classList.add("gg-m-flash"); };
      if (minus) minus.addEventListener("click", () => bump(-step));
      if (plus) plus.addEventListener("click", () => bump(step));
    });
    $$("[data-gg-replay]").forEach(b => b.addEventListener("click", () => ggReplay(document.querySelector(b.dataset.ggReplay))));
    $$("[data-gg-dismiss]").forEach(b => b.addEventListener("click", () => { const el = b.closest(".gg-chip, .gg-toast, .gg-banner"); if (el) el.remove(); }));

    const seen = new IntersectionObserver(entries => entries.forEach(en => {
      if (!en.isIntersecting) return;
      seen.unobserve(en.target);
      if (en.target.dataset.ggCount !== undefined) ggCount(en.target, +en.target.dataset.ggCount);
      else type(en.target);
    }));
    // the resting text is already the final value, so the page is complete without scripting
    $$("[data-gg-count], [data-gg-type]").forEach(el => seen.observe(el));
  }

  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    document.querySelectorAll(".gg-menu:not([hidden]), .gg-drawer:not([hidden]), .gg-scrim:not([hidden])").forEach(ggHide);
  });
  document.addEventListener("click", e => {
    document.querySelectorAll(".gg-menu:not([hidden])").forEach(m => { if (!m.contains(e.target)) ggHide(m); });
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init(document)); else init(document);

  Object.assign(root, { ggToast, ggReplay, ggCount, ggShow, ggHide, ggInit: init });
})(window);
