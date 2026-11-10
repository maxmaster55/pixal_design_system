/* NixOS Frost scenes for the Ember Cave engine (needs ember.js loaded first).
   Landscape cover: an ice cavern. Focal light is a six-armed frost lattice (a generic snowflake, not a logo),
   a frozen pool runs along the floor, icicles hang from ledges, and warm embers are Nix sigils (λ { } = ; : .).
   Ember.frostCover(canvas,{seed}), Ember.frostBand(canvas,{seed,accent}). Seeds: cover 2605, back 1103. */
(function (E) {
  "use strict";
  const P = E.P, hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
  const F = {
    ice: "#4bc6e9", iceLit: "#bdf0ff", iceDeep: "#2a8fb8", iceEdge: "#17607a",
    foam: "#e6fbff", surf: "#8fe3f7", mid: "#2a7fa6", deep: "#173f5e", glint: "#ffffff"
  };
  Object.assign(E.EMIT, {
    "#bdf0ff": [6, .05], "#2a8fb8": [4, .012], "#e6fbff": [5, .03], "#8fe3f7": [4, .018]
  });
  const SIGIL = {
    "λ": ["110", "010", "010", "101", "101"], "{": ["011", "010", "110", "010", "011"], "}": ["110", "010", "011", "010", "110"],
    "=": ["000", "111", "000", "111", "000"], ";": ["000", "010", "000", "010", "100"], ":": ["000", "010", "000", "010", "000"]
  };
  const KEYS = Object.keys(SIGIL);
  const put = (ctx, x, y, c) => { ctx.fillStyle = c; ctx.fillRect(x | 0, y | 0, 1, 1); };
  const glyph = (ctx, x, y, m, c) => m.forEach((row, j) => [...row].forEach((b, i) => { if (b === "1") put(ctx, x + i, y + j, c); }));

  // six-armed lattice: arms with two pairs of side branches, a hollow hexagon at the core
  function drawFlake(ctx, cx, cy, L, small) {
    const pts = new Map(), set = (x, y, c, pri) => { const k = x + "," + y, o = pts.get(k); if (!o || o[1] < pri) pts.set(k, [c, pri]); };
    const line = (x0, y0, a, len, cFn, pri) => { for (let s = 0; s <= len; s += .5) set(Math.round(x0 + Math.cos(a) * s), Math.round(y0 + Math.sin(a) * s * .92), cFn(s / len), pri); };
    for (let k = 0; k < 6; k++) {
      const a = k * Math.PI / 3 - Math.PI / 2;
      const lit = Math.cos(a + 2.3) > 0; // arms facing the upper left catch the light
      line(cx, cy, a, L, t => t > .92 ? F.glint : (lit ? (t > .5 ? F.iceLit : F.ice) : (t > .6 ? F.ice : F.iceDeep)), 2);
      const br = small ? [[.55, 3]] : [[.42, 4], [.7, 3.5]];
      for (const [f, bl] of br) {
        const bx = cx + Math.cos(a) * L * f, by = cy + Math.sin(a) * L * f * .92;
        for (const s of [-1, 1]) line(bx, by, a + s * Math.PI / 3, bl, t => t > .8 ? F.iceLit : (lit ? F.ice : F.iceDeep), 1);
      }
    }
    if (!small) for (let k = 0; k < 6; k++) { // core hexagon outline
      const a0 = k * Math.PI / 3, a1 = a0 + Math.PI / 3, R = 3.2;
      for (let s = 0; s <= 1; s += .2) set(Math.round(cx + Math.cos(a0) * R * (1 - s) + Math.cos(a1) * R * s), Math.round(cy + Math.sin(a0) * R * (1 - s) + Math.sin(a1) * R * s), F.iceEdge, 3);
    }
    set(cx, cy, F.glint, 4);
    pts.forEach(([c], k) => { const [x, y] = k.split(",").map(Number); put(ctx, x, y, c); });
  }

  function frostScene(seed, W, H) {
    W = W || 170; H = H || 120;
    const gx = Math.round(W * .71), gy = Math.round(H * .41), L = 15, pool = H - 13;
    const g = E.cave(W, H, seed, {
      fill: .48, iter: 5, open: (x, y) => {
        if (((x - gx) / 30) ** 2 + ((y - gy) / 34) ** 2 < 1) return 0;                    // lattice chamber
        if (x > 6 && x < W * .5 + ((y * 7) % 5) && y > 7 && y < H * .66) return 0;         // title chamber
        if (y > H - 26 && y < H - 3 && x > 9 && x < W - 9) return 0;                       // frozen basin
        if (y > H * .5 && y < H - 20 && x > W * .2 && x < W * .9) return 0;                // floor cavern
        return 1;
      }
    });
    const r = E.rng(seed * 7 + 3), embers = [];
    for (let i = 0; i < 260 && embers.length < 15; i++) {
      const x = 6 + Math.floor(r() * (W - 14)), y = 12 + Math.floor(r() * (pool - 22));
      if (Math.hypot(x - gx, y - gy) < 24) continue;                         // keep the lattice clear
      if (x < W * .52 && (y < H * .64 || y > H * .74)) continue;              // keep the title and footer clear
      let ok = true; for (let j = -4; j < 6; j++) for (let k = -1; k < 4; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok && embers.every(e => Math.abs(e.x - x) > 5 || Math.abs(e.y - y) > 8)) embers.push({ x, y, d: KEYS[Math.floor(r() * KEYS.length)], col: r() < .6 ? P.ember : P.emberHot });
    }
    const icicles = []; // hang from ceilings: rock pixel with 3+ air pixels below
    for (let t = 0; t < 900 && icicles.length < 26; t++) {
      const x = 4 + Math.floor(r() * (W - 8)), y = 3 + Math.floor(r() * (H - 34));
      if (!g[y][x] || g[y + 1][x] || g[y + 2][x] || g[y + 3][x]) continue;
      if (x < W * .52 && y > 6 && y < H * .66 && x > 8) continue;           // not over the title text
      if (icicles.some(c => Math.abs(c.x - x) < 3)) continue;
      icicles.push({ x, y: y + 1, h: 2 + Math.floor(r() * 5) });
    }
    const sparks = []; for (let i = 0; i < 24; i++) { const a = r() * 6.283, d = L + 3 + r() * 11; sparks.push({ a, d, c: r() < .55 ? F.iceLit : (r() < .6 ? P.white : P.emberHot) }); }
    const lights = [{ x: gx, y: gy, r: 20, i: 1.2, c: hex(F.ice) }, { x: W / 2, y: pool, r: 34, i: .5, c: hex(F.ice) }, { x: 38, y: 40, r: 30, i: .35, c: hex(P.ember) }]
      .concat(embers.map(e => ({ x: e.x + 1, y: e.y + 2, r: 6, i: .34, c: hex(P.ember) })));
    const base = document.createElement("canvas"); base.width = W; base.height = H;
    E.render(base.getContext("2d"), W, H, g, lights);
    const halos = [{ x: gx, y: gy, r: 36, c: hex(F.ice), a: .2 }, { x: gx, y: gy, r: 12, c: [220, 248, 255], a: .12 },
      { x: W / 2, y: pool + 3, r: 60, c: hex(F.ice), a: .09 }, { x: 34, y: 34, r: 44, c: hex(P.ember), a: .07 }];
    function draw(ctx) {
      ctx.drawImage(base, 0, 0);
      const rr = E.rng(seed * 13 + 1);
      for (let y = pool; y < H - 2; y++) for (let x = 3; x < W - 3; x++) { // frozen pool, dithered depth
        if (g[y][x]) continue; const top = y === pool, dd = BAYER[y & 3][x & 3];
        put(ctx, x, y, top ? F.foam : (y < pool + 2 ? F.surf : (dd > 7 - (y - pool) * .6 ? F.mid : F.deep)));
        if (!top && rr() < .02) put(ctx, x, y, F.surf);
      }
      for (let i = 0; i < 10; i++) { const x = 10 + Math.floor(rr() * (W - 20)); if (!g[pool][x]) { put(ctx, x, pool, F.glint); put(ctx, x + 1, pool + 1, F.iceLit); } }
      for (const c of icicles) for (let k = 0; k < c.h; k++) {
        const w = k < c.h - 2 && c.h > 3 ? 1 : 0;
        put(ctx, c.x, c.y + k, k === c.h - 1 ? F.glint : (k > c.h - 3 ? F.iceLit : F.iceDeep));
        if (w) put(ctx, c.x + 1, c.y + k, F.iceEdge);
      }
      drawFlake(ctx, gx, gy, L, false);
      for (const s of sparks) { const x = Math.round(gx + Math.cos(s.a) * s.d), y = Math.round(gy + Math.sin(s.a) * s.d * .9); if (g[y] && !g[y][x]) put(ctx, x, y, s.c); }
      for (const e of embers) {
        glyph(ctx, e.x, e.y, SIGIL[e.d], e.col);
        for (let k = 1; k <= 4; k++) put(ctx, e.x + 1, e.y - k, [P.ember, P.emberDim, P.emberAsh, P.emberSoot][k - 1]);
      }
    }
    return { W, H, draw, halos };
  }
  function frostCover(canvas, o) {
    o = o || {}; const sc = frostScene(o.seed || 2605, o.W, o.H), art = document.createElement("canvas");
    art.width = sc.W; art.height = sc.H; sc.draw(art.getContext("2d")); E.bloom(art, canvas, o.scale || 8, sc.halos);
  }
  // band for part openers: 170x22, a small lattice as the light, icicles and sigil embers
  function frostBand(canvas, o) {
    o = o || {}; const W = o.W || 170, H = o.H || 22, seed = o.seed || 3, art = document.createElement("canvas"); art.width = W; art.height = H;
    const ctx = art.getContext("2d"), g = E.cave(W, H, seed, { fill: .5, iter: 4, open: (x, y) => (y > 4 && y < H - 5 ? 0 : null) });
    for (let x = 0; x < W; x++) { g[H - 1][x] = 1; g[0][x] = 1; }
    const r = E.rng(seed), lx = Math.round(W * (.62 + r() * .26)), ly = H / 2 | 0, accent = hex(o.accent || P.ember);
    for (let y = ly - 8; y <= ly + 8; y++) for (let x = lx - 9; x <= lx + 9; x++) if (g[y] && y > 0 && y < H - 1) g[y][x] = 0;
    E.render(ctx, W, H, g, [{ x: lx, y: ly, r: 12, i: 1.1, c: hex(F.ice) }, { x: 24, y: H - 5, r: 12, i: .45, c: accent }]);
    for (let x = 3; x < W - 3; x++) for (let y = 1; y < H - 6; y++) if (g[y][x] && !g[y + 1][x] && !g[y + 2][x] && Math.abs(x - lx) > 9 && r() < .22) {
      const h = 1 + Math.floor(r() * 3); for (let k = 1; k <= h; k++) put(ctx, x, y + k, k === h ? F.iceLit : F.iceDeep); break;
    }
    for (let i = 0; i < 8; i++) {
      const x = Math.floor(r() * (W - 6)), y = 5 + Math.floor(r() * (H - 12));
      if (Math.abs(x - lx) < 12) continue; let ok = true; for (let j = 0; j < 5; j++) for (let k = 0; k < 3; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok) glyph(ctx, x, y, SIGIL[KEYS[Math.floor(r() * KEYS.length)]], r() < .5 ? P.emberHot : P.ember);
    }
    drawFlake(ctx, lx, ly, 6, true);
    E.bloom(art, canvas, o.scale || 8, [{ x: lx, y: ly, r: 24, c: hex(F.ice), a: .24 }, { x: 24, y: H - 5, r: 16, c: accent, a: .08 }]);
  }
  E.frostCover = frostCover; E.frostBand = frostBand; E.NIXSIGIL = SIGIL; E.FROST = F;
  E.frostInit = function (scope) {
    (scope || document).querySelectorAll("canvas[data-frost]").forEach(c => {
      const k = c.dataset.frost, seed = +c.dataset.seed || undefined;
      if (k === "cover") frostCover(c, { seed }); else if (k === "band") frostBand(c, { seed, accent: c.dataset.accent });
    });
    E.autoInit(scope);
  };
})(window.Ember);
