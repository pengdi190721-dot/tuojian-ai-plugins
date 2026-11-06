/* 口播科普动画 · 引擎 v1.0.0
   页面里的每个元素什么时候出现、怎么动、什么时候配音效，都由这里根据口播时间算出来。
   生成页面时，build.py 会先放入 TL（每个字的时间）、SUBS（字幕）、PROJ（段落信息），再放入本文件和画面里的脚本。 */
(function () {
  const PU = '，。、；：？！“”‘’ ,.;:?!"\'★';
  const norm = s => [...s].filter(c => !PU.includes(c)).join('').toLowerCase();
  const ERRS = []; window.ERRS = ERRS;
  const FIRST = PROJ.sections.map(s => s.first);          // 每段第一句的全局行号（从1开始）
  const NL = TL.lines.length;

  /* ---------- 时间函数：写画面时用 ---------- */
  // 行号可以写成数字（全局第几句），也推荐写成 '段.行'，比如 '3.2' = 第3段第2句
  function idx(r) {
    if (typeof r === 'number') { if (r < 1 || r > NL) { ERRS.push('没有第' + r + '句'); return 1; } return r; }
    const m = String(r).match(/^(\d+)\.(\d+)$/);
    if (!m) { ERRS.push('看不懂的行号：' + r); return 1; }
    const k = +m[1], j = +m[2];
    if (k < 1 || k > FIRST.length) { ERRS.push('没有第' + k + '段：' + r); return 1; }
    const g = FIRST[k - 1] + j - 1, next = k < FIRST.length ? FIRST[k] : NL + 1;
    if (j < 1 || g >= next) { ERRS.push('第' + k + '段没有第' + j + '句：' + r); return FIRST[k - 1]; }
    return g;
  }
  const LN = r => TL.lines[idx(r) - 1];
  const ls = r => LN(r).nct[0] - 0.1;                       // 这句话开口前0.1秒
  const le = r => LN(r).ne;                                 // 这句话说完
  function at(r, kw) {                                      // 这句话里说到某个词的那一刻
    const L = LN(r), n = norm(L.text), k = n.indexOf(norm(kw));
    if (k < 0) { ERRS.push(r + ' 里找不到「' + kw + '」'); return L.nct[0] - 0.1; }
    return L.nct[k] - 0.06;
  }
  const END = TL.total;
  const S = k => k <= 1 ? 0 : (k > FIRST.length ? END : ls(FIRST[k - 1]) - 0.45);   // 第k段开始
  Object.assign(window, { at, ls, le, S, END });

  /* ---------- 缓动 ---------- */
  const C = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const P = (t, s, d) => C((t - s) / d);
  const EO = x => 1 - Math.pow(1 - x, 3);
  const EIO = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const BK = x => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  const ev = s => Function('at', 'ls', 'le', 'S', 'END', 'return (' + s + ')')(at, ls, le, S, END);
  const asIv = v => v === null || v === undefined ? null : (typeof v === 'number' ? [[v, 1e9]] : v);

  /* ---------- 截图镜头 ---------- */
  const CAMS = {}; window.CAMS = CAMS;
  window.cam = (id, cfg) => { CAMS[id] = cfg; };

  let ELS = [], DRAWS = [], BOBS = [], BLINKS = [], PULSES = [], SWINGS = [], curSub = -2;

  function setup() {
    // 段落：<section class="sec" data-sec="3"> 自动从第3段开始、第4段开始时结束
    document.querySelectorAll('.sec[data-sec]').forEach(s => {
      const k = +s.dataset.sec; s.classList.add('el');
      if (s.dataset.in === undefined) s.dataset.in = 'S(' + k + ')';
      if (s.dataset.out === undefined) s.dataset.out = 'S(' + (k + 1) + ')';
      if (!s.dataset.a) s.dataset.a = 'fade';
    });
    // 竖版专用位置：元素上写 data-vstyle="left:..;top:.."，竖版时覆盖原来的位置
    if (document.body.classList.contains('V')) document.querySelectorAll('[data-vstyle]').forEach(e => { e.style.cssText += ';' + e.dataset.vstyle; });
    // 画框里的图解：自动包一层 1060×690 的画布，横竖版自动缩放
    document.querySelectorAll('.R-frame:not(.cam)').forEach(f => {
      if (f.querySelector(':scope > .inner')) return;
      const inner = document.createElement('div'); inner.className = 'inner';
      while (f.firstChild) inner.appendChild(f.firstChild);
      f.appendChild(inner);
    });
    document.querySelectorAll('.R-frame > .inner').forEach(i => {
      const w = i.parentElement.clientWidth || 1060; i.style.transform = 'scale(' + (w / 1060) + ')';
    });
    // 镜头
    for (const [id, c] of Object.entries(CAMS)) {
      const el = document.getElementById(id);
      if (!el) { ERRS.push('画面里没有 id 为 ' + id + ' 的镜头'); continue; }
      el.classList.add('el'); if (!el.dataset.a) el.dataset.a = 'zoom';
      const img = document.createElement('img'); img.src = 'assets/' + (c.img || el.dataset.img); el.appendChild(img);
      c.el = el; c.imgEl = img; c.marks = c.marks || [];
      c.mEls = c.marks.map(m => { const d = document.createElement('div'); d.className = 'mk' + (m.kind === 'bar' ? ' bar' : ''); el.appendChild(d); return d; });
    }
    // 进度条
    const chs = document.getElementById('chapters');
    PROJ.chapters.forEach((c, i) => { const d = document.createElement('div'); d.className = 'ch'; d.id = 'ch' + i; d.textContent = c.name; chs.appendChild(d); });
    if (!PROJ.chapters.length) chs.style.display = 'none';
    // 元素
    ELS = [...document.querySelectorAll('.el')];
    for (const el of ELS) {
      const c = Object.values(CAMS).find(c => c.el === el);
      if (c) el._iv = c.show.map(x => x.slice());
      else if (el.dataset.show) el._iv = ev(el.dataset.show);
      else if (el.dataset.in !== undefined) el._iv = [[ev(el.dataset.in), el.dataset.out !== undefined ? ev(el.dataset.out) : 1e9]];
      else el._iv = [[-1, 1e9]];
      el._hl = asIv(el.dataset.hl ? ev(el.dataset.hl) : null);
      el._dim = asIv(el.dataset.dim ? ev(el.dataset.dim) : null);
      el._par = el.parentElement ? el.parentElement.closest('.el') : null;
    }
    DRAWS = [...document.querySelectorAll('.draw')].map(p => ({ p, t: ev(p.dataset.in), L: p.getTotalLength() }));
    DRAWS.forEach(d => { d.p.style.strokeDasharray = d.L; });
    BOBS = [...document.querySelectorAll('.bob')];
    BLINKS = [...document.querySelectorAll('.blink')];
    PULSES = [...document.querySelectorAll('.pulse')];
    SWINGS = [...document.querySelectorAll('.swing')];
  }

  function camRect(c, t) {
    let i = 0; while (i + 1 < c.views.length && t >= c.views[i + 1][0]) i++;
    const v = c.views[i]; if (i === 0) return v[1];
    const pv = c.views[i - 1][1], k = EIO(P(t, v[0], 0.8));
    return pv.map((x, j) => x + (v[1][j] - x) * k);
  }
  function renderCam(c, t) {
    const bw = c.el.clientWidth, bh = c.el.clientHeight, W = c.imgEl.naturalWidth, H = c.imgEl.naturalHeight;
    if (!W) return;
    c.imgEl.style.width = W + 'px'; c.imgEl.style.height = H + 'px';
    const [sx, sy, sw, sh] = camRect(c, t);
    const s = Math.min(bw / sw, bh / sh), ox = (bw - sw * s) / 2 - sx * s, oy = (bh - sh * s) / 2 - sy * s;
    c.imgEl.style.transform = `translate(${ox}px,${oy}px) scale(${s})`;
    c.marks.forEach((m, j) => {
      const d = c.mEls[j];
      if (t < m.in || t > m.out + 0.3) { d.style.visibility = 'hidden'; return; }
      const kin = P(t, m.in, 0.35), kout = EIO(P(t, m.out, 0.3)), pad = m.kind === 'bar' ? 0 : 10;
      const [rx, ry, rw, rh] = m.r, sc = m.kind === 'bar' ? 1 : 1 + 0.25 * (1 - EO(kin));
      const w = rw * s + 2 * pad, h = rh * s + 2 * pad, cx = ox + (rx + rw / 2) * s, cy = oy + (ry + rh / 2) * s;
      Object.assign(d.style, { visibility: 'visible', left: (cx - w * sc / 2) + 'px', top: (cy - h * sc / 2) + 'px', width: (w * sc) + 'px', height: (h * sc) + 'px', opacity: EO(kin) * (1 - kout) });
      if (m.kind !== 'bar') d.style.boxShadow = `0 0 0 ${8 + 5 * Math.sin(t * 6)}px color-mix(in srgb,var(--mk) 20%,transparent)`;
    });
  }

  function ivK(iv, t, din = 0.45, dout = 0.35) {
    for (const [a, b] of iv) if (t >= a && t <= b + dout) return [P(t, a, din), EIO(P(t, b, dout))];
    return null;
  }
  function renderEl(el, t) {
    if (el._par && el._par.style.visibility !== 'visible') { el.style.visibility = 'hidden'; return; }
    const k = ivK(el._iv, t, el.classList.contains('sec') ? 0.4 : 0.45);
    if (!k) { el.style.visibility = 'hidden'; return; }
    el.style.visibility = 'visible';
    const [kin, kout] = k, a = el.dataset.a || 'rise';
    let o = EO(kin) * (1 - kout), x = 0, y = 0, s = 1, clip = '';
    if (a === 'rise') y = (1 - EO(kin)) * 40 - kout * 20;
    else if (a === 'pop') s = .6 + .4 * BK(kin);
    else if (a === 'fade') o = EIO(kin) * (1 - kout);
    else if (a === 'left') x = -(1 - EO(kin)) * 70;
    else if (a === 'right') x = (1 - EO(kin)) * 70;
    else if (a === 'zoom') s = .94 + .06 * EO(kin);
    else if (a === 'wipe') { const kk = P(t, el._iv[0][0], 0.7); clip = `inset(-20% ${(1 - EIO(kk)) * 100}% -20% -5%)`; o = 1 - kout; }
    else if (a === 'none') o = 1 - kout;
    if (el._dim) { const kd = ivK(el._dim, t, 0.4, 0.4); if (kd) o *= 1 - 0.72 * EO(kd[0]) * (1 - kd[1]); }
    if (el._hl) {
      const kh = ivK(el._hl, t, 0.4, 0.4), v = kh ? EO(kh[0]) * (1 - kh[1]) : 0;
      el.style.boxShadow = v > 0 ? `0 0 0 ${7 * v}px color-mix(in srgb,var(--acc) ${Math.round(v * 100)}%,transparent),var(--shadow)` : '';
      el.style.background = v > 0 ? `color-mix(in srgb,var(--acc-s) ${Math.round(v * 100)}%,var(--card))` : '';
    }
    el.style.opacity = o; el.style.transform = `translate(${x}px,${y}px) scale(${s})`; el.style.clipPath = clip;
  }

  function render(t) {
    for (const el of ELS) renderEl(el, t);
    for (const d of DRAWS) d.p.style.strokeDashoffset = d.L * (1 - EIO(P(t, d.t, 0.4)));
    for (const c of Object.values(CAMS)) { if (!c.el) continue; if (c.el.style.visibility === 'visible') renderCam(c, t); else c.mEls.forEach(d => d.style.visibility = 'hidden'); }
    BOBS.forEach((b, i) => { b.style.translate = `0 ${Math.sin(t * 2.2 + i) * 7}px`; });
    BLINKS.forEach((b, i) => { const ph = (t + i * 0.9) % 3.4, closed = ph < 0.13; b.querySelectorAll('.eo').forEach(e => e.style.visibility = closed ? 'hidden' : 'inherit'); b.querySelectorAll('.ec').forEach(e => e.style.visibility = closed ? 'inherit' : 'hidden'); });
    PULSES.forEach((p, i) => { p.style.opacity = 0.55 + 0.45 * Math.sin(t * 5 + i); });
    SWINGS.forEach((w, i) => { w.style.rotate = (Math.sin(t * 5 + i) * 14) + 'deg'; });
    document.getElementById('fade').style.opacity = Math.max(1 - EO(P(t, 0, 0.5)), EIO(P(t, END - 0.6, 0.6)));
    // 进度条
    const chs = document.getElementById('chapters');
    if (PROJ.chapters.length) {
      const firstCh = PROJ.chapters[0].sec;
      chs.style.opacity = EO(P(t, S(firstCh), 0.4));
      let cur = 1; for (let k = 1; k <= FIRST.length; k++) if (t >= S(k)) cur = k;
      PROJ.chapters.forEach((c, i) => { const el = document.getElementById('ch' + i); el.className = 'ch' + (cur > c.sec ? ' done' : cur === c.sec ? ' on' : ''); });
    }
    // 字幕
    let si = -1; for (let i = 0; i < SUBS.length; i++) if (t >= SUBS[i].a && t < SUBS[i].b) { si = i; break; }
    const sub = document.getElementById('sub');
    if (si !== curSub) { sub.innerHTML = si >= 0 ? '<div>' + SUBS[si].h + '</div>' : ''; curSub = si; }
    if (si >= 0) { const q = SUBS[si]; sub.style.opacity = EO(P(t, q.a, 0.12)) * (1 - EIO(P(t, q.b - 0.08, 0.08))); } else sub.style.opacity = 0;
  }

  function sfxList() {
    const out = [];
    for (const el of ELS) if (el.dataset.sfx) for (const [a] of el._iv) if (a >= 0 && a < END) out.push([a, el.dataset.sfx]);
    for (const c of Object.values(CAMS)) for (const m of (c.marks || [])) if (!m.nosfx) out.push([m.in, 'ding']);
    for (let k = 2; k <= FIRST.length; k++) out.push([S(k), 'whoosh']);
    return out.sort((x, y) => x[0] - y[0]);
  }

  window.engineStart = function () {
    try { setup(); } catch (e) { ERRS.push('画面脚本出错：' + e.message); }
    window.render = render; window.sfxList = sfxList;
    window.info = () => ({ ERRS, END, sections: FIRST.map((_, i) => S(i + 1)) });
    try { render(0); } catch (e) { ERRS.push('画面渲染出错：' + e.message); }
  };
})();
