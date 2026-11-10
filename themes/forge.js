/* Forge theme for Glowgrid (made for the Rust book) (needs core/glowgrid.js loaded first).
   Landscape cover: a cave forge. Focal light is a glowing cog over a dark anvil, a molten pool
   runs along the floor, embers are Rust sigils (& ? ! { } < >), frost shards give a cold accent.
   Ember.forgeCover(canvas,{seed}), Ember.forgeBand(canvas,{seed,accent}). Seeds: cover 1515, back 2024. */
(function (E) {
  "use strict";
  const P = E.P, hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
  const F = { // forge palette: cog faces, molten pool
    cog: "#ff9a3c", cogLit: "#ffc56a", cogDeep: "#c25a12", cogEdge: "#7a3108",
    foam: "#ffe08a", melt: "#f07a22", meltMid: "#a8460a", meltDeep: "#6e2c08", spark: "#fff4c8",
    frostLit: "#bdf0ff", anvilTop: "#c4825f", anvilLit: "#8a5a5a", anvilMid: "#5a3d52", anvilDark: "#3b2a3f"
  };
  Object.assign(E.EMIT, {
    "#ff9a3c": [5, .012], "#ffc56a": [6, .026], "#c25a12": [4, .008],
    "#ffe08a": [5, .022], "#fff4c8": [5, .05], "#bdf0ff": [5, .06]
  });
  const SIGIL = {
    "&": ["010", "101", "010", "101", "011"], "?": ["111", "001", "011", "000", "010"], "!": ["010", "010", "010", "000", "010"],
    "{": ["011", "010", "110", "010", "011"], "}": ["110", "010", "011", "010", "110"], "<": ["001", "010", "100", "010", "001"], ">": ["100", "010", "001", "010", "100"]
  };
  const KEYS = Object.keys(SIGIL);
  const put = (ctx, x, y, c) => { ctx.fillStyle = c; ctx.fillRect(x | 0, y | 0, 1, 1); };
  const glyph = (ctx, x, y, m, c) => m.forEach((row, j) => [...row].forEach((b, i) => { if (b === "1") put(ctx, x + i, y + j, c); }));

  // cog mask: 0 none, 1 body, 2 tooth
  function cogAt(dx, dy, R, teeth, hole) {
    const d = Math.hypot(dx, dy), a = Math.atan2(dy, dx);
    if (d < hole) return 0;
    if (d <= R) {
      // lightening holes in the web
      if (R > 8) for (let k = 0; k < 5; k++) { const ha = k * 1.2566 + .3, hx = Math.cos(ha) * (R * .58), hy = Math.sin(ha) * (R * .58); if (Math.hypot(dx - hx, dy - hy) < R * .13) return 0; }
      return 1;
    }
    if (d <= R + 4 && Math.cos(teeth * a) > .5) return 2;
    return 0;
  }
  function drawCog(ctx, cx, cy, R, teeth, hole) {
    const M = R + 5, m = (x, y) => cogAt(x, y, R, teeth, hole);
    for (let y = -M; y <= M; y++) for (let x = -M; x <= M; x++) {
      if (!m(x, y)) continue;
      const edge = !m(x + 1, y) || !m(x - 1, y) || !m(x, y + 1) || !m(x, y - 1), s = x + y;
      const ring = Math.abs(Math.hypot(x, y) - (R - 1.5)) < .6;
      put(ctx, cx + x, cy + y, edge ? F.cogEdge : (s < -R * .5 ? F.cogLit : (s > R * .45 || ring ? F.cogDeep : F.cog)));
    }
  }

  function forgeScene(seed, W, H) {
    W = W || 170; H = H || 120;
    const gx = Math.round(W * .7), gy = Math.round(H * .4), R = 13, pool = H - 13;
    const ay = gy + R + 7; // anvil face row
    const g = E.cave(W, H, seed, {
      fill: .48, iter: 5, open: (x, y) => {
        if (((x - gx) / 31) ** 2 + ((y - gy - 6) / 38) ** 2 < 1) return 0;                 // forge chamber
        if (x > 6 && x < W * .5 + ((y * 7) % 5) && y > 7 && y < H * .66) return 0;         // title chamber
        if (y > H - 26 && y < H - 3 && x > 9 && x < W - 9) return 0;                       // molten basin
        if (y > H * .5 && y < H - 20 && x > W * .2 && x < W * .9) return 0;                // floor cavern joining them
        return 1;
      }
    });
    // anvil pedestal: solid rock from the anvil base down to the floor
    for (let y = ay + 9; y < H; y++) { const w = 7 + Math.floor((y - ay - 9) * .3); for (let x = gx - w; x <= gx + w; x++) if (g[y] && x > 0 && x < W) g[y][x] = 1; }
    const r = E.rng(seed * 7 + 3), embers = [];
    for (let i = 0; i < 200 && embers.length < 15; i++) {
      const x = 6 + Math.floor(r() * (W - 14)), y = 12 + Math.floor(r() * (pool - 22));
      if (Math.abs(x - gx) < 22 && y > gy - 22 && y < ay + 12) continue;     // keep the cog clear
      if (x < W * .52 && (y < H * .64 || y > H * .74)) continue;              // keep the title and footer clear
      let ok = true; for (let j = -4; j < 6; j++) for (let k = -1; k < 4; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok && embers.every(e => Math.abs(e.x - x) > 5 || Math.abs(e.y - y) > 8)) embers.push({ x, y, d: KEYS[Math.floor(r() * KEYS.length)], col: r() < .6 ? P.ember : P.emberHot });
    }
    const drips = []; for (let x = 4; x < W - 4; x++) for (let y = 4; y < H - 30; y++) { if (g[y][x] && !g[y + 1][x] && r() < .035) { drips.push({ x, y: y + 1 }); break; } }
    const shards = [];
    for (let t = 0; t < 400 && shards.length < 4; t++) { // frost shards growing up from ledges
      const x = 8 + Math.floor(r() * (W - 16)), y = 10 + Math.floor(r() * (H - 40));
      if (x < W * .52 && y < H * .66) continue;
      if (Math.abs(x - gx) < 26 && Math.abs(y - gy) < 30) continue;
      if (g[y][x] || !g[y + 1] || !g[y + 1][x] || g[y - 1][x] || g[y - 2][x] || g[y - 3][x]) continue;
      shards.push({ x, y, h: 3 + Math.floor(r() * 3) });
    }
    const sparks = []; for (let i = 0; i < 24; i++) { const a = r() * 6.283, d = R + 5 + r() * 12; sparks.push({ a, d, c: r() < .65 ? P.emberHot : (r() < .5 ? F.spark : P.frost) }); }
    const lights = [{ x: gx, y: gy, r: 19, i: 1.2, c: hex(P.ember) }, { x: gx - 30, y: pool, r: 30, i: .55, c: hex(P.ember) }, { x: 40, y: pool, r: 26, i: .4, c: hex(P.emberHot) }]
      .concat(embers.map(e => ({ x: e.x + 1, y: e.y + 2, r: 6, i: .32, c: hex(P.ember) })))
      .concat(shards.map(s => ({ x: s.x, y: s.y - 2, r: 6, i: .35, c: hex(P.frost) })));
    const base = document.createElement("canvas"); base.width = W; base.height = H;
    E.render(base.getContext("2d"), W, H, g, lights);
    const halos = [{ x: gx, y: gy, r: 36, c: hex(P.ember), a: .2 }, { x: gx, y: gy, r: 13, c: [255, 214, 140], a: .12 },
      { x: W / 2, y: pool + 3, r: 60, c: hex(P.ember), a: .1 }, { x: 34, y: 34, r: 44, c: hex(P.ember), a: .07 }];
    function draw(ctx) {
      ctx.drawImage(base, 0, 0);
      const rr = E.rng(seed * 13 + 1);
      for (let y = pool; y < H - 2; y++) for (let x = 3; x < W - 3; x++) {
        if (g[y][x]) continue; const top = y === pool, dd = BAYER[y & 3][x & 3];
        put(ctx, x, y, top ? F.foam : (y < pool + 2 ? F.melt : (dd > 7 - (y - pool) * .6 ? F.meltMid : F.meltDeep)));
        if (!top && rr() < .025) put(ctx, x, y, F.foam);
      }
      for (let i = 0; i < 12; i++) { const x = 10 + Math.floor(rr() * (W - 20)), y = pool - 1 - Math.floor(rr() * 3); if (!g[y][x]) put(ctx, x, y, F.spark); }
      // anvil (horn to the left), lit from the cog above
      const A = [[-11, 12, F.anvilTop, -16], [-10, 11, F.anvilLit, -13], [-9, 9, F.anvilMid, 0], [-5, 5, F.anvilMid, 0], [-3, 3, F.anvilDark, 0], [-3, 3, F.anvilDark, 0], [-6, 6, F.anvilMid, 0], [-9, 9, F.anvilDark, 0], [-10, 10, F.anvilDark, 0]];
      A.forEach(([a, b, c, horn], j) => { for (let x = (horn || a); x <= b; x++) put(ctx, gx + x, ay + j, x < a ? F.anvilLit : c); });
      for (let x = -9; x <= 9; x += 3) put(ctx, gx + x, ay, P.emberHot); // hot scale on the face
      // the cog
      drawCog(ctx, gx, gy, R, 9, 4);
      [[-6, -9], [-8, -7], [-9, -5], [-4, -10]].forEach(p => put(ctx, gx + p[0], gy + p[1], P.white));
      // falling spark stream from cog to anvil
      for (let k = 0; k < 4; k++) put(ctx, gx + 2 - k, gy + R + 3 + k, k % 2 ? P.emberHot : F.spark);
      for (const s of sparks) { const x = Math.round(gx + Math.cos(s.a) * s.d), y = Math.round(gy + Math.sin(s.a) * s.d * .85); if (g[y] && !g[y][x] && y < ay - 1) put(ctx, x, y, s.c); }
      for (const e of embers) {
        glyph(ctx, e.x, e.y, SIGIL[e.d], e.col);
        for (let k = 1; k <= 4; k++) put(ctx, e.x + 1, e.y - k, [P.ember, P.emberDim, P.emberAsh, P.emberSoot][k - 1]);
      }
      for (const s of shards) for (let k = 0; k < s.h; k++) { put(ctx, s.x, s.y - k, k === s.h - 1 ? P.white : (k > s.h - 3 ? F.frostLit : P.frost)); if (k < s.h - 2) { put(ctx, s.x - 1, s.y - k + 1, P.frost); put(ctx, s.x + 1, s.y - k, F.frostLit); } }
      for (const d of drips) if (d.y < pool && !g[d.y][d.x]) put(ctx, d.x, d.y, P.frost);
    }
    return { W, H, draw, halos };
  }
  function forgeCover(canvas, o) {
    o = o || {}; const sc = forgeScene(o.seed || 1515, o.W, o.H), art = document.createElement("canvas");
    art.width = sc.W; art.height = sc.H; sc.draw(art.getContext("2d")); E.bloom(art, canvas, o.scale || 8, sc.halos);
  }
  // band for part openers: 170x22, a small cog as the light, sigil embers drifting
  function forgeBand(canvas, o) {
    o = o || {}; const W = o.W || 170, H = o.H || 22, seed = o.seed || 3, art = document.createElement("canvas"); art.width = W; art.height = H;
    const ctx = art.getContext("2d"), g = E.cave(W, H, seed, { fill: .5, iter: 4, open: (x, y) => (y > 4 && y < H - 5 ? 0 : null) });
    for (let x = 0; x < W; x++) { g[H - 1][x] = 1; g[0][x] = 1; }
    const r = E.rng(seed), lx = Math.round(W * (.62 + r() * .26)), ly = H / 2 | 0, accent = hex(o.accent || P.frost);
    for (let y = ly - 7; y <= ly + 7; y++) for (let x = lx - 8; x <= lx + 8; x++) if (g[y] && y > 0 && y < H - 1) g[y][x] = 0;
    E.render(ctx, W, H, g, [{ x: lx, y: ly, r: 12, i: 1.1, c: hex(P.ember) }, { x: 24, y: H - 5, r: 12, i: .45, c: accent }]);
    for (let i = 0; i < 7; i++) {
      const x = Math.floor(r() * (W - 6)), y = 5 + Math.floor(r() * (H - 12));
      if (Math.abs(x - lx) < 12) continue; let ok = true; for (let j = 0; j < 5; j++) for (let k = 0; k < 3; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok) glyph(ctx, x, y, SIGIL[KEYS[Math.floor(r() * KEYS.length)]], r() < .5 ? P.emberHot : P.ember);
    }
    drawCog(ctx, lx, ly, 5, 6, 2); put(ctx, lx - 2, ly - 3, P.white);
    for (let i = 0; i < 3; i++) { const x = 18 + i * 3, y = H - 3; if (!g[y][x]) put(ctx, x, y, o.accent || P.frost); }
    E.bloom(art, canvas, o.scale || 8, [{ x: lx, y: ly, r: 24, c: hex(P.ember), a: .24 }, { x: 24, y: H - 5, r: 16, c: accent, a: .08 }]);
  }
  E.forgeCover = forgeCover; E.forgeBand = forgeBand; E.SIGIL = SIGIL; E.F = F;
  E.forgeInit = function (scope) {
    (scope || document).querySelectorAll("canvas[data-forge]").forEach(c => {
      const k = c.dataset.forge, seed = +c.dataset.seed || undefined;
      if (k === "cover") forgeCover(c, { seed }); else if (k === "band") forgeBand(c, { seed, accent: c.dataset.accent });
    });
    E.autoInit(scope);
  };
  E.register("forge", { cover: forgeCover, band: forgeBand });
})(window.Glowgrid);
