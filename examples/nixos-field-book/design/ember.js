/* Ember Cave art engine v1
   Procedural pixel art: dithered caverns, emissive pixels, soft bloom, and a 12 fps animation loop.
   Usage: <script src="ember.js"></script> then Ember.cover(canvas,{seed}), Ember.band(canvas,{seed}),
          Ember.icon(canvas,"gear"|"q"|"key"|"chip"|"bug"|"skull", color), Ember.animate(canvas,{seed}).
   All art is drawn on a tiny grid (art pixels) and upscaled with hard edges by S (default 8). */
(function (root) {
  "use strict";
  // ---------- palette ----------
  const P = {
    void: "#0b0714", cave: "#170d24", rock: "#3b2a3f", rockLit: "#8a5a5a",
    ember: "#ff8a2a", emberHot: "#ffd36b", emberDim: "#b24d0a", emberAsh: "#7a3108", emberSoot: "#4a1c06",
    hex: "#e94bd6", hexLit: "#ffb8f4", hexDeep: "#a12f97", hexEdge: "#7a1f73",
    acid: "#7cf36b", acidFoam: "#d8ffc9", acidBubble: "#b8ff9a", acidMid: "#3fae4a", acidDeep: "#2a7c3a",
    frost: "#4bc6e9", white: "#ffffff", ink: "#1c1226"
  };
  const hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const ROCK = ["#120a1a", "#1f1229", "#2c1a35", "#3b2a3f", "#5a3d52", "#8a5a5a", "#c4825f"].map(hex);
  const AIR = ["#0b0714", "#100a1b", "#150c22", "#1b1029", "#241433", "#2f1a44"].map(hex);
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
  // Emissive colors: [glow radius in art pixels, peak alpha]. Only these colors glow.
  const EMIT = {
    "#ff8a2a": [6, .06], "#ffd36b": [6, .07], "#b24d0a": [4, .03], "#7a3108": [3, .015],
    "#e94bd6": [6, .016], "#ffb8f4": [6, .03], "#a12f97": [4, .01], "#ffffff": [7, .1],
    "#d8ffc9": [5, .025], "#7cf36b": [4, .012], "#b8ff9a": [5, .03], "#4bc6e9": [5, .08]
  };
  const GLYPH = { // 3x5 digits for binary embers
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"]
  };
  const ICONS = { // 7x7 one-bit icons
    gear: ["0011100", "0110110", "1101011", "1010101", "1101011", "0110110", "0011100"],
    q: ["0111110", "1100011", "0000011", "0001110", "0011000", "0000000", "0011000"],
    key: ["0111000", "1000100", "1000100", "0111000", "0010000", "0011100", "0010100"],
    chip: ["0101010", "1111111", "0100010", "1101011", "0100010", "1111111", "0101010"],
    bug: ["1000001", "0111110", "1101011", "0111110", "1111111", "0111110", "1000001"],
    skull: ["0111110", "1111111", "1001001", "1111111", "0110110", "0111110", "0101010"],
    warn: ["0001000", "0011100", "0010100", "0110110", "0111110", "1110111", "1111111"],
    book: ["1111110", "1000011", "1011011", "1000011", "1011011", "1000011", "1111111"]
  };

  // ---------- helpers ----------
  function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function ramp(p, v, x, y) {
    const n = p.length - 1, f = Math.max(0, Math.min(1, v)) * n, i = Math.floor(f), t = f - i;
    return p[Math.min(n, i + (t * 16 > BAYER[y & 3][x & 3] + .5 ? 1 : 0))];
  }
  function put(ctx, x, y, c) { ctx.fillStyle = c; ctx.fillRect(x | 0, y | 0, 1, 1); }
  function glyph(ctx, x, y, map, color) { map.forEach((row, j) => [...row].forEach((b, i) => { if (b === "1") put(ctx, x + i, y + j, color); })); }
  // value noise for flicker (smooth, deterministic)
  function noise1(t, seed) { const i = Math.floor(t), f = t - i, h = n => { let x = Math.sin((n + seed * 57.13) * 12.9898) * 43758.5453; return x - Math.floor(x); }; const u = f * f * (3 - 2 * f); return h(i) * (1 - u) + h(i + 1) * u; }

  // ---------- cave generation (cellular automaton) ----------
  function cave(W, H, seed, o) {
    const r = rng(seed), g = [];
    for (let y = 0; y < H; y++) { g[y] = []; for (let x = 0; x < W; x++) { const e = x < 2 || x > W - 3 || y < 1 || y > H - 2; g[y][x] = e || r() < o.fill ? 1 : 0; } }
    const open = () => { if (o.open) for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (o.open(x, y) === 0) g[y][x] = 0; };
    open();
    for (let it = 0; it < o.iter; it++) {
      const n = g.map(a => a.slice());
      for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
        let c = 0; for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) c += g[y + j][x + i];
        n[y][x] = c >= 5 ? 1 : (c <= 3 ? 0 : g[y][x]);
      }
      g.splice(0, H, ...n); open();
    }
    return g;
  }
  // ---------- lit render: dithered ramps + colored light spill ----------
  function render(ctx, W, H, g, lights) {
    const img = ctx.createImageData(W, H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      let s = 0, tr = 0, tg = 0, tb = 0;
      for (const l of lights) { const d = Math.hypot(x - l.x, y - l.y), w = l.i / (1 + (d * d) / (l.r * l.r)); s += w; tr += w * l.c[0]; tg += w * l.c[1]; tb += w * l.c[2]; }
      let c;
      if (g[y][x]) { const na = (g[y - 1] && !g[y - 1][x]) || (g[y + 1] && !g[y + 1][x]) || !g[y][x - 1] || !g[y][x + 1]; c = ramp(ROCK, (na ? .28 : .08) + s * .7, x, y); }
      else c = ramp(AIR, (y / H) * .35 + s * .5, x, y);
      const k = (y * W + x) * 4, m = g[y][x] ? .22 : .16;
      img.data[k] = Math.min(255, c[0] + tr * m); img.data[k + 1] = Math.min(255, c[1] + tg * m); img.data[k + 2] = Math.min(255, c[2] + tb * m); img.data[k + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  }
  // ---------- bloom: hard upscale, then additive soft glow from emissive pixels ----------
  function bloom(src, dst, S, halos, strength) {
    const W = src.width, H = src.height, k1 = strength == null ? 1 : strength;
    if (dst.width !== W * S) { dst.width = W * S; dst.height = H * S; }
    const d = src.getContext("2d").getImageData(0, 0, W, H).data, ctx = dst.getContext("2d");
    ctx.globalCompositeOperation = "source-over"; ctx.imageSmoothingEnabled = false; ctx.drawImage(src, 0, 0, W * S, H * S);
    ctx.globalCompositeOperation = "lighter";
    const glow = (cx, cy, R, rgb, a) => {
      const gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
      gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(.35, `rgba(${rgb},${a * .45})`); gr.addColorStop(1, `rgba(${rgb},0)`);
      ctx.fillStyle = gr; ctx.fillRect(cx - R, cy - R, 2 * R, 2 * R);
    };
    for (const h of halos || []) glow(h.x * S, h.y * S, h.r * S, h.c.join(","), h.a * k1);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4, key = "#" + [d[i], d[i + 1], d[i + 2]].map(v => v.toString(16).padStart(2, "0")).join(""), e = EMIT[key];
      if (e) glow((x + .5) * S, (y + .5) * S, e[0] * S, d[i] + "," + d[i + 1] + "," + d[i + 2], e[1] * k1);
    }
    ctx.globalCompositeOperation = "source-over";
  }

  // ---------- scene: cover ----------
  function coverScene(seed, W, H) {
    W = W || 120; H = H || 170;
    const cx = W / 2 | 0, cy = Math.round(H * .565), pool = H - 14;
    const g = cave(W, H, seed, {
      fill: .47, iter: 5, open: (x, y) => {
        if (((x - cx) / (W * .37)) ** 2 + ((y - cy) / (H * .306)) ** 2 < 1) return 0;
        if (y < H * .27 && Math.abs(x - cx) < W * .33 + ((y * 7) % 5)) return 0; // title chamber
        if (y > H - 34 && y < H - 4 && x > 14 && x < W - 14) return 0;           // pool basin
        return 1;
      }
    });
    const r = rng(seed * 7 + 3), embers = [];
    for (let i = 0; i < 60 && embers.length < 16; i++) {
      const x = 8 + Math.floor(r() * (W - 20)), y = 48 + Math.floor(r() * (pool - 60));
      if (Math.abs(x - cx) < 10 && Math.abs(y - cy) < 16) continue;
      let ok = true; for (let j = -4; j < 5; j++) for (let k = 0; k < 3; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok) embers.push({ x, y, y0: y, d: r() < .5 ? "0" : "1", col: r() < .6 ? P.ember : P.emberHot, ph: r() * 100, sp: .15 + r() * .25 });
    }
    const drips = []; for (let x = 4; x < W - 4; x++) for (let y = 40; y < H - 1; y++) { if (g[y][x] && !g[y + 1][x] && r() < .05) { drips.push({ x, y0: y + 1, y: y + 1, v: 0, wait: r() * 60 }); break; } }
    const sparks = []; for (let i = 0; i < 22; i++) { const a = r() * 6.283, d = 9 + r() * 16; sparks.push({ a, d, c: r() < .5 ? P.emberHot : P.hex, ph: r() * 10 }); }
    const bubbles = []; for (let i = 0; i < 14; i++) bubbles.push({ x: 10 + Math.floor(r() * (W - 20)), y: pool - 1 - Math.floor(r() * 3) });
    const lights = [{ x: cx, y: cy, r: 17, i: 1.15, c: hex(P.hex) }, { x: cx, y: pool, r: 30, i: .6, c: hex(P.acid) }]
      .concat(embers.map(e => ({ x: e.x + 1, y: e.y + 2, r: 6, i: .35, c: hex(P.ember) })));
    const base = document.createElement("canvas"); base.width = W; base.height = H;
    render(base.getContext("2d"), W, H, g, lights);
    const halos = [{ x: cx, y: cy, r: 34, c: hex(P.hex), a: .22 }, { x: cx, y: cy, r: 12, c: [255, 200, 250], a: .1 }, { x: cx, y: pool + 2, r: 46, c: hex(P.acid), a: .12 }, { x: cx, y: 22, r: 40, c: hex(P.ember), a: .1 }];
    function draw(ctx, t) { // t in seconds; t = 0 is the print frame
      ctx.drawImage(base, 0, 0);
      const rr = rng(seed * 13 + Math.floor(t * 12));
      for (let y = pool; y < H - 2; y++) for (let x = 3; x < W - 3; x++) {
        if (g[y][x]) continue; const top = y === pool, dd = BAYER[y & 3][(x + Math.floor(t * 3)) & 3];
        put(ctx, x, y, top ? P.acidFoam : (y < pool + 2 ? P.acid : (dd > 7 ? P.acidMid : P.acidDeep)));
        if (!top && rr() < .03) put(ctx, x, y, P.acidBubble);
      }
      for (const b of bubbles) { const hop = t ? Math.floor((t * 2 + b.x) % 3) : 0; if (!g[b.y - hop][b.x]) put(ctx, b.x, b.y - hop, P.acidBubble); }
      const pulse = t ? .5 + .5 * Math.sin(t * 1.6) : .5;
      for (let j = -14; j <= 14; j++) {
        const w = Math.floor((14 - Math.abs(j)) * .55);
        for (let i = -w; i <= w; i++) { const edge = Math.abs(i) === w, lit = i < 0 && j < 0; put(ctx, cx + i, cy + j, edge ? P.hexEdge : (lit ? P.hexLit : (i < 0 ? P.hex : P.hexDeep))); }
      }
      const tw = t ? Math.floor(t * 4) % 3 : 0; [[-2, -7], [-1, -8], [-3, -5]].forEach((p, i) => { if (i !== tw || !t) put(ctx, cx + p[0], cy + p[1], P.white); });
      for (const s of sparks) {
        const a = s.a + t * .25, x = Math.round(cx + Math.cos(a) * s.d), y = Math.round(cy + Math.sin(a) * s.d * .9);
        if (!g[y] || g[y][x]) continue; if (t && noise1(t * 3 + s.ph, 2) < .35) continue; put(ctx, x, y, s.c);
      }
      for (const e of embers) {
        let y = e.y0, x = e.x;
        if (t) { const span = e.y0 - 46, rise = (t * e.sp * 12 + e.ph) % span; y = Math.round(e.y0 - rise); x = Math.round(e.x + Math.sin(t * 1.3 + e.ph) * 1.2); }
        const fl = t ? noise1(t * 6 + e.ph, 1) : 1, col = fl < .25 ? P.emberDim : e.col;
        glyph(ctx, x, y, GLYPH[e.d], col);
        // trail: above a falling ember in the still frame, below a rising ember when animated
        for (let k = 1; k <= 4; k++) put(ctx, x + 1, t ? y + 4 + k : y - k, [P.ember, P.emberDim, P.emberAsh, P.emberSoot][k - 1]);
      }
      for (const d of drips) {
        let y = d.y0; if (t) { const cyc = (t * 12 + d.wait) % 90; y = cyc < 60 ? d.y0 : Math.round(d.y0 + ((cyc - 60) / 30) ** 2 * (pool - d.y0)); }
        if (y < pool && !(g[y] && g[y][d.x])) put(ctx, d.x, y, P.frost);
      }
      return pulse;
    }
    return { W, H, draw, halos };
  }

  function cover(canvas, o) {
    o = o || {}; const sc = coverScene(o.seed || 1337, o.W, o.H), art = document.createElement("canvas");
    art.width = sc.W; art.height = sc.H; sc.draw(art.getContext("2d"), 0); bloom(art, canvas, o.scale || 8, sc.halos);
  }
  function animate(canvas, o) {
    o = o || {}; const sc = coverScene(o.seed || 1337, o.W, o.H), art = document.createElement("canvas"); art.width = sc.W; art.height = sc.H;
    const ax = art.getContext("2d"), S = o.scale || 4, FPS = o.fps || 12;
    const still = () => { sc.draw(ax, 0); bloom(art, canvas, S, sc.halos); };
    if (root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches) { still(); return { stop() { } }; }
    let raf = 0, last = -1, t0 = performance.now(), running = true;
    function frame(now) {
      if (!running) return; raf = requestAnimationFrame(frame);
      const step = Math.floor((now - t0) / (1000 / FPS)); if (step === last) return; last = step; // hold each frame: pixel-art cadence
      const t = step / FPS + .001, pulse = sc.draw(ax, t);
      const halos = sc.halos.map((h, i) => i < 2 ? Object.assign({}, h, { a: h.a * (.8 + .4 * pulse) }) : h);
      bloom(art, canvas, S, halos);
    }
    raf = requestAnimationFrame(frame);
    return { stop() { running = false; cancelAnimationFrame(raf); still(); } };
  }

  // ---------- scene: band (part openers, headers) ----------
  function band(canvas, o) {
    o = o || {}; const W = o.W || 120, H = o.H || 34, seed = o.seed || 3, art = document.createElement("canvas"); art.width = W; art.height = H;
    const ctx = art.getContext("2d"), g = cave(W, H, seed, { fill: .5, iter: 4, open: (x, y) => (y > 6 && y < H - 7 ? 0 : null) });
    for (let x = 0; x < W; x++) { g[H - 1][x] = 1; g[H - 2][x] = 1; g[0][x] = 1; }
    const r = rng(seed), lx = 20 + Math.floor(r() * (W - 40)), ly = H / 2 | 0, accent = hex(o.accent || P.frost);
    render(ctx, W, H, g, [{ x: lx, y: ly, r: 10, i: 1.1, c: hex(P.ember) }, { x: W - lx, y: H - 6, r: 10, i: .4, c: accent }]);
    for (let i = 0; i < 9; i++) { const x = Math.floor(r() * W), y = 6 + Math.floor(r() * (H - 14)); if (!g[y][x]) put(ctx, x, y, r() < .5 ? P.emberHot : P.ember); }
    put(ctx, lx, ly, P.white); put(ctx, lx - 1, ly + 1, P.emberHot); put(ctx, lx + 1, ly + 1, P.emberHot); put(ctx, lx, ly + 1, P.emberHot); put(ctx, lx, ly + 2, P.ember); put(ctx, lx, ly - 1, P.emberHot);
    bloom(art, canvas, o.scale || 8, [{ x: lx, y: ly, r: 22, c: hex(P.ember), a: .25 }]);
  }
  function icon(canvas, name, color) {
    const m = ICONS[name]; canvas.width = 7; canvas.height = 7; const ctx = canvas.getContext("2d"); ctx.clearRect(0, 0, 7, 7); glyph(ctx, 0, 0, m, color || P.ink);
  }
  function autoInit(scope) {
    (scope || document).querySelectorAll("canvas[data-ember]").forEach(c => {
      const k = c.dataset.ember, seed = +c.dataset.seed || undefined;
      if (k === "cover") cover(c, { seed }); else if (k === "band") band(c, { seed, accent: c.dataset.accent });
      else if (k === "animate") animate(c, { seed }); else if (k === "icon") icon(c, c.dataset.icon, c.dataset.color);
    });
  }
  root.Ember = { P, EMIT, ICONS, GLYPH, rng, cave, render, bloom, cover, band, icon, animate, autoInit, noise1 };
})(typeof window !== "undefined" ? window : this);
