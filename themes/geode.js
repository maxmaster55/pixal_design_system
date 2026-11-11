/* Geode theme for Glowgrid (made for the WebAssembly field book) (needs core/glowgrid.js loaded first).
   Landscape cover: a geode cavern. Walls bristle with violet crystal spikes, a pool of liquid violet light
   runs along the floor, and the focal light is one isometric crystal cube (a sealed module) whose top face
   carries a lit grid (linear memory). Warm sparks are hex digits from the module magic (0 6 1 7 3 D A).
   Glowgrid.geodeCover(canvas,{seed}), Glowgrid.geodeBand(canvas,{seed,accent}). Seeds: cover 3141, back 2017. */
(function (E) {
  "use strict";
  const P = E.P, hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
  const G = {
    gem: "#9b7bff", gemLit: "#d9ccff", gemDeep: "#5b3fd1", gemEdge: "#3a2490", gemDark: "#26185e",
    foam: "#efe9ff", surf: "#b9a6ff", mid: "#6a4fd8", deep: "#2b1d6b", glint: "#ffffff"
  };
  Object.assign(E.EMIT, {
    "#9b7bff": [5, .012], "#d9ccff": [6, .03], "#5b3fd1": [4, .01], "#efe9ff": [5, .03], "#b9a6ff": [4, .008]
  });
  const SIGIL = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "3": ["111", "001", "011", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"], "A": ["010", "101", "111", "101", "101"],
    "D": ["110", "101", "101", "101", "110"]
  };
  const KEYS = Object.keys(SIGIL);
  const put = (ctx, x, y, c) => { ctx.fillStyle = c; ctx.fillRect(x | 0, y | 0, 1, 1); };
  const glyph = (ctx, x, y, m, c) => m.forEach((row, j) => [...row].forEach((b, i) => { if (b === "1") put(ctx, x + i, y + j, c); }));
  const inPoly = (x, y, pts) => { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, yi] = pts[i], [xj, yj] = pts[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };

  // isometric cube, edge a: top face lit with a memory grid, left face mid, right face deep, glinting silhouette
  function drawCube(ctx, cx, cy, a, small) {
    const h = a / 2, T = [cx, cy - a], L = [cx - a, cy - h], R = [cx + a, cy - h], C = [cx, cy], BL = [cx - a, cy + h + 2], BR = [cx + a, cy + h + 2], B = [cx, cy + a + 2];
    const top = [T, R, C, L], left = [L, C, B, BL], right = [C, R, BR, B];
    for (let y = Math.floor(cy - a - 1); y <= cy + a + 3; y++) for (let x = Math.floor(cx - a - 1); x <= cx + a + 1; x++) {
      const px = x + .5, py = y + .5, d = BAYER[y & 3][x & 3];
      if (inPoly(px, py, top)) {
        const u = (px - cx) / a + (py - (cy - h)) / h, v = -(px - cx) / a + (py - (cy - h)) / h; // face coords in -1..1
        const grid = !small && (Math.abs(((u + 1) * 2) % 1) < .18 || Math.abs(((v + 1) * 2) % 1) < .18);
        put(ctx, x, y, grid ? G.gemLit : (d > 12 ? G.surf : G.gem));
      } else if (inPoly(px, py, left)) put(ctx, x, y, d > 13 ? G.gem : G.gemDeep);
      else if (inPoly(px, py, right)) put(ctx, x, y, d > 13 ? G.gemDeep : G.gemEdge);
    }
    const seg = (p, q, c) => { const n = Math.max(Math.abs(q[0] - p[0]), Math.abs(q[1] - p[1])) * 2; for (let i = 0; i <= n; i++) put(ctx, Math.round(p[0] + (q[0] - p[0]) * i / n - .25), Math.round(p[1] + (q[1] - p[1]) * i / n - .25), c); };
    seg(L, T, G.gemLit); seg(T, R, G.gemLit); seg(L, C, G.gemLit); seg(C, R, G.gemLit); seg(C, B, G.gem);
    seg(L, BL, G.gemLit); seg(R, BR, G.gemDeep);
    put(ctx, T[0], T[1], G.glint);
  }
  // crystal spike growing from (x,y) in direction dir (+1 down, -1 up)
  function spike(ctx, x, y, len, w, dir) {
    for (let k = 0; k < len; k++) {
      const half = Math.max(0, Math.round(w * (1 - k / len)));
      for (let i = -half; i <= half; i++) put(ctx, x + i, y + dir * k, i === -half ? G.gem : (i === half ? G.gemEdge : G.gemDeep));
    }
    put(ctx, x, y + dir * (len - 1), G.gemLit); if (len > 5) put(ctx, x, y + dir * len, G.glint);
  }

  function geodeScene(seed, W, H) {
    W = W || 170; H = H || 120;
    const gx = Math.round(W * .72), gy = Math.round(H * .42), A = 13, pool = H - 13;
    const g = E.cave(W, H, seed, {
      fill: .48, iter: 5, open: (x, y) => {
        if (((x - gx) / 30) ** 2 + ((y - gy) / 33) ** 2 < 1) return 0;                    // crystal chamber
        if (x > 6 && x < W * .5 + ((y * 7) % 5) && y > 7 && y < H * .66) return 0;         // title chamber
        if (y > H - 26 && y < H - 3 && x > 9 && x < W - 9) return 0;                       // light pool basin
        if (y > H * .5 && y < H - 20 && x > W * .2 && x < W * .9) return 0;                // floor cavern
        return 1;
      }
    });
    const r = E.rng(seed * 7 + 3), sparks = [];
    for (let i = 0; i < 300 && sparks.length < 15; i++) {
      const x = 6 + Math.floor(r() * (W - 14)), y = 12 + Math.floor(r() * (pool - 22));
      if (Math.hypot(x - gx, y - gy) < 24) continue;
      if (x < W * .52 && (y < H * .64 || y > H * .74)) continue;
      let ok = true; for (let j = -4; j < 6; j++) for (let k = -1; k < 4; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok && sparks.every(e => Math.abs(e.x - x) > 5 || Math.abs(e.y - y) > 8)) sparks.push({ x, y, d: KEYS[Math.floor(r() * KEYS.length)], col: r() < .6 ? P.ember : P.emberHot });
    }
    const spikes = []; // from ceilings (down) and floors (up)
    for (let t = 0; t < 1400 && spikes.length < 30; t++) {
      const x = 4 + Math.floor(r() * (W - 8)), y = 3 + Math.floor(r() * (H - 20));
      const down = g[y][x] && !g[y + 1][x] && !g[y + 2][x] && !g[y + 3][x];
      const up = g[y][x] && y > 3 && !g[y - 1][x] && !g[y - 2][x] && !g[y - 3][x] && y < pool - 1;
      if (!down && !up) continue;
      if (x < W * .53 && x > 6 && y > 5 && y < H * .68) continue;          // not over the title text
      if (Math.hypot(x - gx, y - gy) < 20) continue;
      if (spikes.some(c => Math.abs(c.x - x) < 4 && Math.abs(c.y - y) < 6)) continue;
      spikes.push({ x, y: down ? y + 1 : y - 1, dir: down ? 1 : -1, len: 3 + Math.floor(r() * 6), w: 1 + (r() < .5 ? 1 : 0) + (r() < .2 ? 1 : 0) });
    }
    const motes = []; for (let i = 0; i < 24; i++) { const a = r() * 6.283, d = A + 6 + r() * 11; motes.push({ a, d, c: r() < .55 ? G.gemLit : (r() < .6 ? P.white : P.emberHot) }); }
    const lights = [{ x: gx, y: gy, r: 21, i: 1.2, c: hex(G.gem) }, { x: W / 2, y: pool, r: 34, i: .5, c: hex(G.gem) }, { x: 38, y: 40, r: 30, i: .35, c: hex(P.ember) }]
      .concat(sparks.map(e => ({ x: e.x + 1, y: e.y + 2, r: 6, i: .34, c: hex(P.ember) })));
    const base = document.createElement("canvas"); base.width = W; base.height = H;
    E.render(base.getContext("2d"), W, H, g, lights);
    const halos = [{ x: gx, y: gy, r: 36, c: hex(G.gem), a: .22 }, { x: gx, y: gy - 4, r: 12, c: [230, 222, 255], a: .04 },
      { x: W / 2, y: pool + 3, r: 60, c: hex(G.gem), a: .1 }, { x: 34, y: 34, r: 44, c: hex(P.ember), a: .07 }];
    function draw(ctx) {
      ctx.drawImage(base, 0, 0);
      const rr = E.rng(seed * 13 + 1);
      for (let y = pool; y < H - 2; y++) for (let x = 3; x < W - 3; x++) {
        if (g[y][x]) continue; const top = y === pool, dd = BAYER[y & 3][x & 3];
        put(ctx, x, y, top ? G.foam : (y < pool + 2 ? G.surf : (dd > 7 - (y - pool) * .6 ? G.mid : G.deep)));
        if (!top && rr() < .02) put(ctx, x, y, G.surf);
      }
      for (let i = 0; i < 10; i++) { const x = 10 + Math.floor(rr() * (W - 20)); if (!g[pool][x]) { put(ctx, x, pool, G.glint); put(ctx, x + 1, pool + 1, G.gemLit); } }
      for (const s of spikes) spike(ctx, s.x, s.y, s.len, s.w, s.dir);
      drawCube(ctx, gx, gy, A, false);
      for (const m of motes) { const x = Math.round(gx + Math.cos(m.a) * m.d), y = Math.round(gy + Math.sin(m.a) * m.d * .9); if (g[y] && !g[y][x]) put(ctx, x, y, m.c); }
      for (const e of sparks) {
        glyph(ctx, e.x, e.y, SIGIL[e.d], e.col);
        for (let k = 1; k <= 4; k++) put(ctx, e.x + 1, e.y - k, [P.ember, P.emberDim, P.emberAsh, P.emberSoot][k - 1]);
      }
    }
    return { W, H, draw, halos };
  }
  function geodeCover(canvas, o) {
    o = o || {}; const sc = geodeScene(o.seed || 3141, o.W, o.H), art = document.createElement("canvas");
    art.width = sc.W; art.height = sc.H; sc.draw(art.getContext("2d")); E.bloom(art, canvas, o.scale || 8, sc.halos);
  }
  // band for part openers: 170x22, a small cube as the light, spikes and hex sparks
  function geodeBand(canvas, o) {
    o = o || {}; const W = o.W || 170, H = o.H || 22, seed = o.seed || 3, art = document.createElement("canvas"); art.width = W; art.height = H;
    const ctx = art.getContext("2d"), g = E.cave(W, H, seed, { fill: .5, iter: 4, open: (x, y) => (y > 4 && y < H - 5 ? 0 : null) });
    for (let x = 0; x < W; x++) { g[H - 1][x] = 1; g[0][x] = 1; }
    const r = E.rng(seed), lx = Math.round(W * (.62 + r() * .26)), ly = H / 2 | 0, accent = hex(o.accent || P.ember);
    for (let y = ly - 8; y <= ly + 8; y++) for (let x = lx - 9; x <= lx + 9; x++) if (g[y] && y > 0 && y < H - 1) g[y][x] = 0;
    E.render(ctx, W, H, g, [{ x: lx, y: ly, r: 12, i: 1.1, c: hex(G.gem) }, { x: 24, y: H - 5, r: 12, i: .45, c: accent }]);
    for (let x = 3; x < W - 3; x++) {
      if (Math.abs(x - lx) < 11 || r() > .2) continue;
      for (let y = 1; y < H - 6; y++) if (g[y][x] && !g[y + 1][x] && !g[y + 2][x]) { spike(ctx, x, y + 1, 2 + Math.floor(r() * 3), 1, 1); x += 3; break; }
    }
    for (let i = 0; i < 8; i++) {
      const x = Math.floor(r() * (W - 6)), y = 5 + Math.floor(r() * (H - 12));
      if (Math.abs(x - lx) < 12) continue; let ok = true; for (let j = 0; j < 5; j++) for (let k = 0; k < 3; k++) if (!g[y + j] || g[y + j][x + k]) ok = false;
      if (ok) glyph(ctx, x, y, SIGIL[KEYS[Math.floor(r() * KEYS.length)]], r() < .5 ? P.emberHot : P.ember);
    }
    drawCube(ctx, lx, ly, 5, true);
    E.bloom(art, canvas, o.scale || 8, [{ x: lx, y: ly, r: 24, c: hex(G.gem), a: .24 }, { x: 24, y: H - 5, r: 16, c: accent, a: .08 }]);
  }
  E.geodeCover = geodeCover; E.geodeBand = geodeBand; E.GEODE = G; E.HEXSIGIL = SIGIL;
  E.register("geode", { cover: geodeCover, band: geodeBand });
})(window.Glowgrid);
