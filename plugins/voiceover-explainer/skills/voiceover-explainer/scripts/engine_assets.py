"""动画引擎（自动生成，不要直接改）。
要改样式或动画，改插件目录 engine-src/ 里的文件，再运行 scripts/build_release.py。
项目里想微调，用 project.json 的“自定义样式”加一个 css 文件。"""

BASE_CSS = r'''/* 口播科普动画 · 基础样式 v1.0.0
   颜色、字体全部来自风格表里的变量，这里只管位置和形状。
   横版 body.H = 1920×1080，竖版 body.V = 1080×1920。 */
*{box-sizing:border-box;margin:0;padding:0}
html,body{overflow:hidden;background:var(--bg)}
body.H,body.H #stage{width:1920px;height:1080px}
body.V,body.V #stage{width:1080px;height:1920px}
body{font-family:var(--font);color:var(--ink);-webkit-font-smoothing:antialiased}
#stage{position:relative;overflow:hidden;background:var(--stage-bg)}
.a{position:absolute}
.el{visibility:hidden}
.sec{position:absolute;left:0;top:0;width:100%;height:100%}

/* ---------- 版位（横版） ---------- */
body.H #topbar{left:100px;top:40px}
body.H #chapters{right:60px;top:42px;width:860px}
body.H .R-term{left:100px;top:170px;width:640px}
body.H .R-notes{left:100px;top:500px;width:640px}
body.H .R-frame{left:760px;top:150px;width:1060px;height:690px}
body.H .R-wide,body.H .R-center{left:100px;top:150px;width:1720px;height:710px}
body.H #sub{left:110px;width:1700px;top:892px;height:130px;font-size:58px}
body.H .quote{left:240px;width:1440px;top:290px;font-size:72px}
/* ---------- 版位（竖版） ---------- */
body.V #topbar{left:60px;top:70px}
body.V #chapters{left:40px;top:150px;width:1000px}
body.V .R-term{left:64px;top:250px;width:952px}
body.V .R-frame{left:50px;top:560px;width:980px;height:638px}
body.V .R-notes{left:64px;top:1236px;width:952px}
body.V .R-wide,body.V .R-center{left:40px;top:250px;width:1000px;height:1320px}
body.V #sub{left:60px;width:960px;top:1610px;height:210px;font-size:54px}
body.V .quote{left:60px;width:960px;top:600px;font-size:60px}
body.V .term{font-size:118px}

/* ---------- 顶栏、进度条、字幕、淡入淡出 ---------- */
#topbar{position:absolute;display:flex;align-items:center;gap:18px;z-index:20}
.badge{background:var(--badge-bg);color:var(--badge-fg);border-radius:999px;padding:10px 26px;font-size:30px;font-weight:900;letter-spacing:2px}
.series{font-size:30px;font-weight:700;color:var(--sub)}
#chapters{position:absolute;display:flex;gap:8px;opacity:0;z-index:20}
.ch{flex:1;height:54px;border-radius:27px;background:var(--card);border:2px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:25px;font-weight:800;color:var(--mute);white-space:nowrap}
.ch.done{background:var(--acc-s);border-color:var(--acc-m);color:var(--acc-d)}
.ch.on{background:var(--ch-on-bg);border-color:var(--ch-on-bg);color:var(--ch-on-fg)}
#sub{position:absolute;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:900;line-height:1.3;color:var(--sub-fg);opacity:0;z-index:30}
#sub k{color:var(--sub-k);background:linear-gradient(transparent 62%,var(--sub-kbg) 62%)}
#fade{position:absolute;left:0;top:0;width:100%;height:100%;background:var(--bg);z-index:50}

/* ---------- 主讲词块 ---------- */
.R-term{position:absolute}
.lbl{font-size:36px;font-weight:900;color:var(--acc-d);letter-spacing:3px}
.term{font-family:var(--font-t);font-size:132px;font-weight:900;line-height:1.08;letter-spacing:2px;color:var(--term)}
.eq{font-size:52px;font-weight:900;color:var(--sub);margin-top:6px}
.R-notes{position:absolute;display:flex;flex-direction:column;align-items:flex-start;gap:22px}
body.V .R-notes{gap:18px}

/* ---------- 标签 ---------- */
.note{display:inline-flex;align-items:center;gap:12px;background:var(--note-bg);color:var(--note-fg);border-radius:var(--pill);padding:14px 30px;font-size:36px;font-weight:900;white-space:nowrap;box-shadow:var(--shadow-s)}
.note b{color:var(--note-b)}
.note.w{background:var(--notew-bg);color:var(--notew-fg);border:2px solid var(--line);box-shadow:var(--shadow-s)}
.note.w b{color:var(--acc-d)}
.note.bad{background:var(--danger);color:#fff}
.note.bad b{color:#fff}
.badge2{display:inline-block;background:var(--badge-bg);color:var(--badge-fg);border-radius:999px;padding:10px 24px;font-size:30px;font-weight:900;white-space:nowrap}
.badge2.g{background:var(--acc);color:var(--on-acc)}
.badge2.r{background:var(--danger);color:#fff}
.mark{background-image:linear-gradient(var(--acc-m),var(--acc-m));background-repeat:no-repeat;background-position:0 92%;background-size:100% 34%;color:var(--acc-d);padding:0 6px;white-space:nowrap}

/* ---------- 卡片 ---------- */
.card{background:var(--card);border-radius:var(--radius);border:var(--card-bd);box-shadow:var(--shadow)}
.callout{width:270px;padding:18px 26px 20px}
.callout span{display:block;font-size:28px;font-weight:800;color:var(--sub)}
.callout b{font-size:50px;font-weight:900;color:var(--acc-d)}
.pill{background:var(--card);border:2px solid var(--line);border-radius:999px;padding:16px 30px;font-size:34px;font-weight:800;color:var(--sub);white-space:nowrap}
.pill b{color:var(--ink);font-weight:900}
.chips{display:flex;flex-wrap:wrap;justify-content:center;gap:18px;width:100%}
.chip{display:inline-flex;align-items:baseline;gap:10px;background:var(--card);border:2px solid var(--line);border-radius:999px;padding:20px 34px 22px 28px;font-size:46px;font-weight:900;box-shadow:var(--shadow-s)}
.chip i{width:16px;height:16px;border-radius:50%;background:var(--acc);align-self:center;margin-right:4px;display:block}
.chip small{font-size:28px;font-weight:900;color:var(--acc-d)}
.job{width:300px;height:150px;padding:18px 32px;display:flex;flex-direction:column;justify-content:center}
.job span{font-size:26px;font-weight:800;color:var(--mute)}
.job b{font-size:56px;font-weight:900;line-height:1.2}
.who{width:520px;height:150px;padding:18px 30px;display:flex;align-items:center;gap:22px;background:var(--acc-s);border:2px solid var(--acc-m);border-radius:var(--radius)}
.who span{display:block;font-size:26px;font-weight:800;color:var(--acc-d)}
.who b{font-size:46px;font-weight:900;line-height:1.2}
.item{left:30px;width:1000px;height:72px;border-radius:18px;display:flex;align-items:center;gap:20px;padding:0 24px;font-size:34px;font-weight:800}
.item.msg{background:var(--acc-s)}
.item.doc{background:var(--soft2)}
.item svg{flex:none}
.rl{display:flex;align-items:center;gap:22px;padding:22px 0;border-top:2px dashed var(--line);font-size:44px;font-weight:800}
.rl i{flex:none;width:62px;height:62px;border-radius:50%;background:var(--badge-bg);color:var(--badge-fg);font-style:normal;font-size:32px;font-weight:900;display:flex;align-items:center;justify-content:center}
.node{width:300px;padding:22px 26px;text-align:center;font-size:40px;font-weight:900}
.panel{width:500px;height:600px;padding:30px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px}
.panel h3{font-family:var(--font-t);font-size:64px;font-weight:900}
.panel p{font-size:34px;font-weight:800;color:var(--sub)}
.tiles{position:absolute;left:0;top:100px;width:100%;display:grid;grid-template-columns:repeat(3,1fr);gap:28px 40px}
body.V .tiles{grid-template-columns:repeat(2,1fr);top:120px}
.tile{position:relative;height:240px;padding:30px 36px;display:flex;flex-direction:column;justify-content:center;gap:10px}
.tile span{font-size:32px;font-weight:800;color:var(--sub)}
.tile b{font-family:var(--font-t);font-size:68px;font-weight:900}
.door{display:inline-block;width:24px;height:36px;border:5px solid var(--ink);border-radius:4px;position:relative;margin-right:4px}
.door::after{content:'';position:absolute;right:3px;top:13px;width:5px;height:5px;border-radius:50%;background:var(--ink)}
.center-col{position:absolute;left:0;top:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center}
.h-small{font-size:58px;font-weight:800;color:var(--sub)}
.h-huge{font-family:var(--font-t);font-size:124px;font-weight:900;line-height:1.15;color:var(--term)}
body.V .h-huge{font-size:104px}
.h-mid{font-size:56px;font-weight:900}

/* ---------- 截图镜头 ---------- */
.R-frame,.R-wide,.R-center{position:absolute}
.R-frame>.inner{position:absolute;left:0;top:0;width:1060px;height:690px;transform-origin:0 0}
.cam{border-radius:var(--radius);overflow:hidden;background:#fff;border:var(--cam-bd);box-shadow:var(--shadow)}
.cam img{position:absolute;left:0;top:0;transform-origin:0 0}
.mk{position:absolute;border:6px solid var(--mk);border-radius:18px;visibility:hidden}
.mk.bar{border:none;border-left:10px solid var(--mk);background:color-mix(in srgb,var(--mk) 18%,transparent);border-radius:6px}

/* ---------- 金句卡 ---------- */
.dim{left:0;top:0;width:100%;height:100%;background:var(--dim)}
.quote{position:absolute;background:var(--qbg);color:var(--qfg);border-radius:var(--qradius);border:var(--qbd);padding:52px 70px 60px;font-family:var(--font-q);font-weight:900;line-height:1.38;box-shadow:var(--qshadow);z-index:10}
.quote em{font-style:normal;color:var(--qem)}
.quote small{display:block;font-family:var(--font);font-size:30px;font-weight:800;color:var(--qsub);letter-spacing:5px;margin-bottom:12px}

/* ---------- 角色配色（小机器人、AI员工、老板） ---------- */
.f-ink{fill:var(--bot-ink)}.f-face{fill:var(--bot-face)}.f-eye{fill:var(--bot-eye)}.f-acc{fill:var(--acc)}.f-card{fill:var(--card)}.f-mute{fill:var(--mute)}.f-hi{fill:var(--hi)}.f-skin{fill:var(--skin)}
.s-ink{stroke:var(--bot-ink)}.s-acc{stroke:var(--acc)}.s-face{stroke:var(--bot-face)}.s-eye{stroke:var(--bot-eye)}
.stroke-acc{stroke:var(--line-acc)}
.t-ink{fill:var(--ink)}
.ec{visibility:hidden}
.swing{transform-box:fill-box}
.bubble{position:absolute;background:var(--card);border:var(--card-bd);border-radius:28px;padding:18px 28px;font-size:36px;font-weight:900;box-shadow:var(--shadow-s);white-space:nowrap}
.bubble::after{content:'';position:absolute;left:40px;bottom:-18px;border:12px solid transparent;border-top:18px solid var(--card)}
'''

ENGINE_JS = r'''/* 口播科普动画 · 引擎 v1.0.0
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
'''

THEMES_CSS = {
    'baiban': r'''/* 风格三：手绘白板 —— 点阵白板、马克笔线条、便利贴，像老师在白板上讲，亲切好懂 */
:root{
 --bg:#FBFAF6;
 --stage-bg:radial-gradient(#D8D4C8 1.5px,transparent 1.7px) 0 0/36px 36px,#FBFAF6;
 --ink:#1F2A44;--term:#1F2A44;--sub:#5B6478;--mute:#9AA1AE;--line:#C9CDD6;--soft2:#EEF1F6;
 --card:#FFFFFF;--card-bd:none;--radius:22px;--pill:16px;
 --shadow:none;--shadow-s:none;
 --acc:#2563EB;--acc-d:#1D4ED8;--acc-s:#E6EEFF;--acc-m:#FFE27A;--on-acc:#fff;--hi:#FFE27A;--line-acc:#E5484D;
 --badge-bg:#1F2A44;--badge-fg:#fff;--ch-on-bg:#1F2A44;--ch-on-fg:#fff;
 --note-bg:#FFE27A;--note-fg:#1F2A44;--note-b:#C2410C;--notew-bg:#fff;--notew-fg:#1F2A44;
 --danger:#E5484D;--mk:#E5484D;--cam-bd:none;
 --qbg:#FFFFFF;--qfg:#1F2A44;--qem:#E5484D;--qsub:#9AA1AE;--qradius:22px;--qbd:none;--qshadow:none;
 --dim:rgba(251,250,246,.84);
 --sub-fg:#1F2A44;--sub-k:#1F2A44;--sub-kbg:#FFE27A;
 --bot-ink:#1F2A44;--bot-face:#FFFFFF;--bot-eye:#1F2A44;--skin:#F2D2B6;
 --font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
 --font-t:var(--font);--font-q:var(--font);
}
/* 马克笔边框：用一层抖动的描边代替直线边框，文字本身不抖 */
:where(.card,.quote,.note.w,.pill,.chip,.cam,.who,.ch){isolation:isolate;position:relative}
:where(.quote){position:absolute}
.card::before,.quote::before,.note.w::before,.pill::before,.chip::before,.cam::after,.who::before,.ch::before{content:'';position:absolute;inset:0;border:3.5px solid #1F2A44;border-radius:inherit;filter:url(#rough);pointer-events:none}
.card::before,.quote::before,.note.w::before,.pill::before,.chip::before,.who::before,.ch::before{z-index:-1;background:inherit}
.card,.quote,.note.w,.pill,.chip,.who,.ch{border:none!important}
.cam::after{z-index:5;border-width:4px}
.quote::before{border-width:5px}
.note{transform-origin:left center;box-shadow:3px 4px 0 rgba(31,42,68,.12);border-radius:6px}
.R-notes .note:nth-child(odd){rotate:-1.2deg}.R-notes .note:nth-child(even){rotate:.8deg}
.mk{filter:url(#rough);border-width:6px;border-radius:28px}
.mk.bar{filter:none;background:rgba(255,226,122,.55);border-left:10px solid #E5484D}
.ch.done{background:#E6EEFF;color:#1D4ED8}
.term,.h-huge{text-decoration:underline;text-decoration-color:#FFE27A;text-decoration-thickness:22px;text-underline-offset:-8px;text-decoration-skip-ink:none}
.quote em{background:linear-gradient(transparent 62%,#FFE27A 62%);color:#C2410C}
''',
    'dazibao': r'''/* 风格四：撞色大字报 —— 黄黑撞色、粗黑边、硬阴影，冲击力强，适合短视频抓眼球 */
:root{
 --bg:#FFF6D8;
 --stage-bg:repeating-linear-gradient(-45deg,rgba(17,17,17,.035) 0 2px,transparent 2px 22px),#FFF6D8;
 --ink:#111111;--term:#111111;--sub:#4A4A4A;--mute:#8A8A8A;--line:#111111;--soft2:#FFF0B3;
 --card:#FFFFFF;--card-bd:4px solid #111;--radius:18px;--pill:14px;
 --shadow:10px 10px 0 #111;--shadow-s:6px 6px 0 #111;
 --acc:#FFD400;--acc-d:#E63B1F;--acc-s:#FFEFA0;--acc-m:#FFD400;--on-acc:#111;--hi:#FFD400;--line-acc:#111111;
 --badge-bg:#111;--badge-fg:#FFD400;--ch-on-bg:#111;--ch-on-fg:#FFD400;
 --note-bg:#111;--note-fg:#fff;--note-b:#FFD400;--notew-bg:#fff;--notew-fg:#111;
 --danger:#E63B1F;--mk:#E63B1F;--cam-bd:4px solid #111;
 --qbg:#FFD400;--qfg:#111;--qem:#E63B1F;--qsub:#5A4A00;--qradius:18px;--qbd:5px solid #111;--qshadow:16px 16px 0 #111;
 --dim:rgba(255,246,216,.84);
 --sub-fg:#111;--sub-k:#111;--sub-kbg:#FFD400;
 --bot-ink:#111111;--bot-face:#FFD400;--bot-eye:#111111;--skin:#F5C9A0;
 --font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
 --font-t:var(--font);--font-q:var(--font);
}
.term,.h-huge{letter-spacing:-2px;font-weight:900}
.lbl{display:inline-block;background:#111;color:#FFD400;padding:4px 16px;border-radius:8px}
.note.w,.pill,.chip,.ch{border:3px solid #111}
.ch.done{background:#FFEFA0;color:#111}
.who{border:4px solid #111;box-shadow:6px 6px 0 #111;background:#FFEFA0}
.who b{color:#111}
.mk{border-width:8px;border-radius:12px}
.chip i{background:#E63B1F}
.mark{color:#111}
#sub k{padding:0 4px}
''',
    'heijin': r'''/* 风格二：黑金发布会 —— 深色底、金色点缀、标题用宋体，适合投大屏、发布会、高端分享 */
:root{
 --bg:#0C0C0E;
 --stage-bg:radial-gradient(1000px 640px at 85% -12%,rgba(201,164,92,.20) 0%,rgba(201,164,92,0) 70%),radial-gradient(900px 600px at -10% 112%,rgba(201,164,92,.12) 0%,rgba(201,164,92,0) 70%),linear-gradient(180deg,#111114,#0A0A0C);
 --ink:#F2EDE3;--term:#F5E6C4;--sub:#A8A196;--mute:#6E685F;--line:#2E2B26;--soft2:#1F1F24;
 --card:#17171B;--card-bd:1px solid #3A3226;--radius:26px;--pill:999px;
 --shadow:0 30px 70px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.04);--shadow-s:0 12px 30px rgba(0,0,0,.45);
 --acc:#C9A45C;--acc-d:#E2C58A;--acc-s:#241F15;--acc-m:rgba(201,164,92,.38);--on-acc:#141210;--hi:#F0D59A;--line-acc:#C9A45C;
 --badge-bg:linear-gradient(135deg,#EBD39C,#B8913F);--badge-fg:#141210;--ch-on-bg:#C9A45C;--ch-on-fg:#141210;
 --note-bg:linear-gradient(135deg,#EBD39C,#B8913F);--note-fg:#141210;--note-b:#000;--notew-bg:#17171B;--notew-fg:#F2EDE3;
 --danger:#D9534F;--mk:#E2C58A;--cam-bd:2px solid #8A7140;
 --qbg:linear-gradient(160deg,#18181C,#0E0E11);--qfg:#F2EDE3;--qem:#F0D59A;--qsub:#8C8578;--qradius:28px;--qbd:2px solid #B8913F;--qshadow:0 40px 100px rgba(0,0,0,.7);
 --dim:rgba(8,8,10,.78);
 --sub-fg:#F2EDE3;--sub-k:#F0D59A;--sub-kbg:rgba(201,164,92,.35);
 --bot-ink:#EDE6D6;--bot-face:#141210;--bot-eye:#F0D59A;--skin:#E8C9A8;
 --font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
 --font-t:"Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;--font-q:var(--font-t);
}
.badge,.badge2{background:var(--badge-bg)}
.term,.h-huge,.tile b,.panel h3{background:linear-gradient(180deg,#FFF3D6 0%,#E2C58A 55%,#B8913F 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.mark{color:#F0D59A}
.quote em{background:linear-gradient(180deg,#FFF0C8,#D9B26A);-webkit-background-clip:text;background-clip:text;color:transparent}
.ch{background:#141417}
''',
    'qingshuang': r'''/* 风格一：清爽薄荷 —— 白底、薄荷绿，干净耐看，适合日常科普、讲软件界面 */
:root{
 --bg:#F4F5F7;
 --stage-bg:radial-gradient(1100px 620px at 92% -10%,#DDF6EA 0%,rgba(221,246,234,0) 70%),radial-gradient(900px 600px at -8% 110%,#E9F8F1 0%,rgba(233,248,241,0) 70%),#F4F5F7;
 --ink:#111318;--term:#111318;--sub:#6B717B;--mute:#A3A8B0;--line:#E6E8EC;--soft2:#F1F3F6;
 --card:#FFFFFF;--card-bd:1px solid #EAECEF;--radius:32px;--pill:999px;
 --shadow:0 26px 64px rgba(17,19,24,.09),0 3px 8px rgba(17,19,24,.04);--shadow-s:0 12px 28px rgba(17,19,24,.10);
 --acc:#12C08A;--acc-d:#079A6C;--acc-s:#E4F7EF;--acc-m:#C8EFDD;--on-acc:#fff;--hi:#3EE0A8;--line-acc:#12C08A;
 --badge-bg:#111318;--badge-fg:#fff;--ch-on-bg:#111318;--ch-on-fg:#fff;
 --note-bg:#111318;--note-fg:#fff;--note-b:#3EE0A8;--notew-bg:#fff;--notew-fg:#111318;
 --danger:#E5484D;--mk:#12C08A;--cam-bd:1px solid #E5E7EA;
 --qbg:#111318;--qfg:#fff;--qem:#3EE0A8;--qsub:#8C929B;--qradius:44px;--qbd:none;--qshadow:0 40px 90px rgba(17,19,24,.28);
 --dim:rgba(244,245,247,.80);
 --sub-fg:#111318;--sub-k:#079A6C;--sub-kbg:#C8EFDD;
 --bot-ink:#111318;--bot-face:#FFFFFF;--bot-eye:#111318;--skin:#F2D2B6;
 --font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
 --font-t:var(--font);--font-q:var(--font);
}
''',
}
