"""动画引擎（自动生成，不要直接改）。
要改样式或动画，改插件源码里 engine-src 文件夹的文件，再运行插件的打包脚本 build_release。
项目里想微调，用 project.json 的“自定义样式”加一个 css 文件。"""

BASE_CSS = r'''/* 口播剪辑助手 · 基础样式 v1.0.0
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

ENGINE_JS = r'''/* 口播剪辑助手 · 引擎 v1.0.0
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

KOUBO_PAGE = r'''<!doctype html>
<html><head><meta charset="utf-8">
<style>
/* 口播剪辑包装页：人像全屏 / 圆角方形小窗 两种版式，片头、动态字幕、要点卡、三步卡、截图、金句卡、大字、对比字、片尾。
   四种风格写在 body[data-theme] 里，横竖版写在 body.H / body.V 里。 */
:root{--font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;--fontt:var(--font)}
body[data-theme=qingshuang]{
 --stage:radial-gradient(900px 620px at 92% -6%,#DDF6EA 0%,rgba(221,246,234,0) 70%),radial-gradient(900px 700px at -10% 108%,#E9F8F1 0%,rgba(233,248,241,0) 70%),#F4F5F7;
 --ink:#111318;--sub:#6B717B;--acc:#12C08A;--hi:#3EE0A8;--danger:#E5484D;--good:#079A6C;--goodbg:#E4F7EF;--badbg:#FDECEC;--bad:#B4232A;
 --card:#fff;--cardbd:1px solid #EAECEF;--radius:40px;--shadow:0 26px 64px rgba(17,19,24,.10);
 --tagbg:#111318;--tagfg:#fff;--tagdot:#3EE0A8;
 --t1:#fff;--t2:#3EE0A8;--tsh:0 6px 24px rgba(0,0,0,.45);
 --sfg:#fff;--sst:rgba(0,0,0,.55);--sk:#111318;--skbg:#3EE0A8;--sbox:transparent;--sfg2:#111318;
 --ring:#fff;--rowbg:#F4F5F7;--rowon:#111318;--rowonfg:#fff;--num:#12C08A;--numfg:#fff;
 --qbg:#111318;--qfg:#fff;--qem:#3EE0A8;--stbg:#fff;--stfg:#111318;--ctabg:#111318;--ctafg:#fff;--ctai:#3EE0A8;
 --dim:linear-gradient(180deg,rgba(0,0,0,0) 50%,rgba(0,0,0,.58) 100%);}
body[data-theme=heijin]{
 --stage:radial-gradient(900px 640px at 85% -10%,rgba(201,164,92,.22) 0%,rgba(201,164,92,0) 70%),linear-gradient(180deg,#111114,#0A0A0C);
 --ink:#F2EDE3;--sub:#A8A196;--acc:#C9A45C;--hi:#F0D59A;--danger:#D9534F;--good:#E2C58A;--goodbg:#241F15;--badbg:#2A1716;--bad:#E8867F;
 --card:#17171B;--cardbd:1px solid #3A3226;--radius:30px;--shadow:0 30px 70px rgba(0,0,0,.55);
 --tagbg:linear-gradient(135deg,#EBD39C,#B8913F);--tagfg:#141210;--tagdot:#141210;
 --t1:#F2EDE3;--t2:#F0D59A;--tsh:0 6px 30px rgba(0,0,0,.7);
 --sfg:#F2EDE3;--sst:rgba(0,0,0,.7);--sk:#141210;--skbg:#E2C58A;--sbox:transparent;--sfg2:#F2EDE3;
 --ring:#C9A45C;--rowbg:#1F1F24;--rowon:linear-gradient(135deg,#EBD39C,#B8913F);--rowonfg:#141210;--num:#C9A45C;--numfg:#141210;
 --qbg:linear-gradient(160deg,#18181C,#0E0E11);--qfg:#F2EDE3;--qem:#F0D59A;--stbg:#17171B;--stfg:#F2EDE3;--ctabg:linear-gradient(135deg,#EBD39C,#B8913F);--ctafg:#141210;--ctai:#141210;
 --dim:linear-gradient(180deg,rgba(0,0,0,0) 45%,rgba(0,0,0,.75) 100%);
 --fontt:"Noto Serif CJK SC","Songti SC","STSong",serif;}
body[data-theme=baiban]{
 --stage:radial-gradient(#D8D4C8 2px,transparent 2.4px) 0 0/40px 40px,#FBFAF6;
 --ink:#1F2A44;--sub:#5B6478;--acc:#2563EB;--hi:#FFE27A;--danger:#E5484D;--good:#1D4ED8;--goodbg:#E6EEFF;--badbg:#FDECEC;--bad:#C2410C;
 --card:#fff;--cardbd:none;--radius:26px;--shadow:none;
 --tagbg:#FFE27A;--tagfg:#1F2A44;--tagdot:#E5484D;
 --t1:#1F2A44;--t2:#E5484D;--tsh:none;
 --sfg:#1F2A44;--sst:transparent;--sk:#1F2A44;--skbg:#FFE27A;--sbox:#fff;--sfg2:#1F2A44;
 --ring:#1F2A44;--rowbg:#fff;--rowon:#FFE27A;--rowonfg:#1F2A44;--num:#1F2A44;--numfg:#fff;
 --qbg:#fff;--qfg:#1F2A44;--qem:#E5484D;--stbg:#fff;--stfg:#1F2A44;--ctabg:#FFE27A;--ctafg:#1F2A44;--ctai:#1F2A44;
 --dim:linear-gradient(180deg,rgba(0,0,0,0) 60%,rgba(0,0,0,.25) 100%);}
body[data-theme=dazibao]{
 --stage:repeating-linear-gradient(-45deg,rgba(17,17,17,.04) 0 2px,transparent 2px 24px),#FFF6D8;
 --ink:#111;--sub:#4A4A4A;--acc:#FFD400;--hi:#FFD400;--danger:#E63B1F;--good:#111;--goodbg:#FFEFA0;--badbg:#FFE1DA;--bad:#E63B1F;
 --card:#fff;--cardbd:5px solid #111;--radius:20px;--shadow:12px 12px 0 #111;
 --tagbg:#111;--tagfg:#FFD400;--tagdot:#E63B1F;
 --t1:#111;--t2:#E63B1F;--tsh:none;
 --sfg:#111;--sst:transparent;--sk:#111;--skbg:#FFD400;--sbox:#fff;--sfg2:#111;
 --ring:#111;--rowbg:#fff;--rowon:#FFD400;--rowonfg:#111;--num:#111;--numfg:#FFD400;
 --qbg:#FFD400;--qfg:#111;--qem:#E63B1F;--stbg:#fff;--stfg:#111;--ctabg:#111;--ctafg:#FFD400;--ctai:#FFD400;
 --dim:linear-gradient(180deg,rgba(0,0,0,0) 60%,rgba(0,0,0,.25) 100%);}
*{margin:0;padding:0;box-sizing:border-box}
html,body{overflow:hidden;background:#000}
body{font-family:var(--font);color:var(--ink);position:relative}
body.V{width:1080px;height:1920px}
body.H{width:1920px;height:1080px}
#stage{position:absolute;inset:0;background:var(--stage)}
#person{position:absolute;overflow:hidden;background:#000;z-index:2}
#pimg{position:absolute;left:0;top:0;display:block}
#dim{position:absolute;inset:0;background:var(--dim);z-index:3}
#dim2{position:absolute;inset:0;z-index:3;background:linear-gradient(180deg,rgba(10,12,16,0) 38%,rgba(10,12,16,.72) 64%,rgba(10,12,16,.82) 100%)}
.ov{position:absolute;z-index:5}
#tag{display:flex;align-items:center;gap:14px;background:var(--tagbg);color:var(--tagfg);font-size:38px;font-weight:800;padding:14px 30px;border-radius:999px;letter-spacing:2px;box-shadow:0 10px 30px rgba(0,0,0,.18);white-space:nowrap}
#tag i{width:16px;height:16px;border-radius:50%;background:var(--tagdot);display:block}
#title{left:0;right:0;text-align:center;white-space:nowrap}
#title .box{display:inline-block}
#title .t1{font-family:var(--fontt);font-size:68px;font-weight:800;color:var(--t1);text-shadow:var(--tsh);line-height:1.15}
#title .t2{font-family:var(--fontt);font-size:112px;font-weight:900;color:var(--t2);text-shadow:var(--tsh);line-height:1.15}
#pop{left:0;right:0;text-align:center;font-family:var(--fontt);font-size:120px;font-weight:900;color:var(--t2);text-shadow:var(--tsh);white-space:nowrap}
#sub{left:40px;right:40px;text-align:center;white-space:nowrap;z-index:6}
#sub .in{display:inline-block;font-size:58px;font-weight:800;color:var(--sfg);-webkit-text-stroke:10px var(--sst);paint-order:stroke fill;line-height:1.3;background:var(--sbox);padding:6px 26px;border-radius:18px}
#sub span{display:inline-block;opacity:.45}
#sub span.lit{opacity:1}
#sub .kwg{opacity:1!important;display:inline-block;background:var(--skbg);border-radius:12px;padding:0 10px;margin:0 4px;-webkit-text-stroke:0;transform-origin:center 60%}
#sub .kwg span{color:var(--sk);font-size:64px;-webkit-text-stroke:0;opacity:.4}
#sub .kwg span.lit{opacity:1}
#sub .kwg.off{opacity:.55!important}
#sub.onstage .in{color:var(--sfg2);-webkit-text-stroke:0}
#sub.onstage span{opacity:.3}
#sub.onstage .kwg span{opacity:.4}
#sub.onstage span.lit,#sub.onstage .kwg span.lit{opacity:1}
#card{background:var(--card);border:var(--cardbd);border-radius:var(--radius);box-shadow:var(--shadow);padding:50px 50px 32px;z-index:4}
#card h2{font-family:var(--fontt);font-size:62px;font-weight:900;margin-bottom:30px;white-space:nowrap;color:var(--ink)}
.row{display:flex;align-items:center;gap:26px;background:var(--rowbg);border-radius:22px;padding:18px 28px;margin-bottom:16px;line-height:1.3;font-size:50px;font-weight:700;white-space:nowrap;transform-origin:left center;position:relative}
.row b{flex:0 0 64px;height:64px;border-radius:18px;background:var(--num);color:var(--numfg);display:flex;align-items:center;justify-content:center;font-size:40px}
.row.on{background:var(--rowon);color:var(--rowonfg)}
.no{display:flex;align-items:center;gap:20px;font-size:50px;font-weight:800;padding:20px 28px;border-radius:22px;background:var(--badbg);color:var(--bad);margin-bottom:26px;white-space:nowrap}
.no .x{flex:0 0 64px;height:64px;border-radius:50%;background:var(--danger);color:#fff;display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:900}
.no .nt{position:relative}
.no .strike{position:absolute;left:-6px;top:52%;height:6px;background:var(--bad);border-radius:3px}
.lbl{font-size:40px;font-weight:700;color:var(--sub);margin:4px 0 14px 6px}
.steps{display:flex;align-items:center;gap:10px;margin-bottom:24px}
.step{flex:1;text-align:center;background:var(--rowbg);border-radius:22px;padding:24px 8px;font-size:40px;font-weight:800;white-space:nowrap;color:var(--sub);opacity:.6}
.step.lit{background:var(--rowon);color:var(--rowonfg);opacity:1}
.arr{font-size:40px;color:var(--sub);font-weight:900}
.arr.lit{color:var(--acc)}
.yes{display:flex;align-items:center;gap:20px;font-size:50px;font-weight:800;padding:20px 28px;border-radius:22px;background:var(--goodbg);color:var(--good);white-space:nowrap}
.yes .ok{flex:0 0 64px;height:64px;border-radius:50%;background:var(--acc);color:var(--numfg);display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900}
.shot{position:relative;overflow:hidden;border-radius:18px;background:#000}
.shot img{position:absolute;left:0;top:0;display:block}
.shot .mk{position:absolute;border:6px solid var(--danger);border-radius:18px;box-shadow:0 0 0 4000px rgba(0,0,0,.18)}
#quote{background:var(--qbg);border-radius:44px;padding:44px 56px 50px;box-shadow:0 40px 90px rgba(0,0,0,.4)}
#quote p{font-family:var(--fontt);font-size:58px;font-weight:800;color:var(--qfg);line-height:1.45;white-space:nowrap;transform-origin:left center}
#quote p.em{font-size:84px;font-weight:900;color:var(--qem);margin-top:6px}
#quote .bar{width:84px;height:10px;border-radius:5px;background:var(--qem);margin-bottom:24px}
#stamp{left:0;right:0;text-align:center}
#stamp div{display:inline-block;background:var(--stbg);color:var(--stfg);border-radius:28px;padding:22px 44px;font-size:76px;font-weight:900;box-shadow:0 24px 60px rgba(0,0,0,.35);white-space:nowrap}
#stamp em{font-style:normal;color:var(--danger);margin:0 18px}
#cta{left:0;right:0;text-align:center}
#cta div{display:inline-flex;align-items:center;gap:24px;background:var(--ctabg);color:var(--ctafg);border-radius:999px;padding:30px 60px;font-size:72px;font-weight:900;box-shadow:0 30px 70px rgba(0,0,0,.4);white-space:nowrap}
#cta i{display:block;width:72px;height:60px;background:var(--ctai);border-radius:22px 22px 22px 6px;position:relative}
/* 手绘白板：马克笔描边 */
body[data-theme=baiban] :is(#card,#quote,#tag,.row,#stamp div,#cta div,#sub .in){isolation:isolate}
body[data-theme=baiban] :is(#card,#quote,#tag,.row,#stamp div,#cta div,#sub .in)::before{content:'';position:absolute;inset:0;border:4px solid #1F2A44;border-radius:inherit;filter:url(#rough);z-index:-1;background:inherit;pointer-events:none}
body[data-theme=baiban] :is(#stamp div,#cta div,#sub .in){position:relative}
body[data-theme=baiban] #title .box{background:#fff;border-radius:28px;padding:26px 44px 34px;rotate:-1.5deg;position:relative;isolation:isolate}
body[data-theme=baiban] #title .box::before{content:'';position:absolute;inset:0;border:4px solid #1F2A44;border-radius:inherit;filter:url(#rough);z-index:-1;background:inherit}
body[data-theme=baiban] #title .t2,body[data-theme=baiban] #quote p.em{background:linear-gradient(transparent 60%,#FFE27A 60%)}
body[data-theme=baiban] #pop{color:#E5484D;text-shadow:0 0 0 #fff,4px 4px 0 #fff,-4px -4px 0 #fff,4px -4px 0 #fff,-4px 4px 0 #fff}
body[data-theme=baiban] #quote .bar{background:#E5484D}
/* 撞色大字报：粗黑边、硬阴影 */
body[data-theme=dazibao] #title .box{background:#FFD400;border:6px solid #111;box-shadow:14px 14px 0 #111;border-radius:18px;padding:22px 40px 30px;rotate:-2deg}
body[data-theme=dazibao] :is(#title .t1,#title .t2,#pop){letter-spacing:-2px;font-weight:900}
body[data-theme=dazibao] #pop{color:#FFD400;-webkit-text-stroke:8px #111;paint-order:stroke fill;text-shadow:8px 8px 0 #111}
body[data-theme=dazibao] #sub .in{border:5px solid #111;box-shadow:8px 8px 0 #111}
body[data-theme=dazibao] .row{border:4px solid #111}
body[data-theme=dazibao] .row.on{box-shadow:6px 6px 0 #111}
body[data-theme=dazibao] :is(#tag,#stamp div,#cta div){border:4px solid #111}
body[data-theme=dazibao] #quote{border:5px solid #111;box-shadow:16px 16px 0 #111}
body[data-theme=dazibao] #quote .bar{background:#111}
body[data-theme=heijin] :is(#title .t2,#card h2,#quote p.em){background:linear-gradient(180deg,#FFF3D6 0%,#E2C58A 55%,#B8913F 100%);-webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:none}
body[data-theme=heijin] #title .t2{filter:drop-shadow(0 6px 20px rgba(0,0,0,.6))}
/* 标题里的英文、问号大字、身份：只有全屏模版用 */
#title .q,#title .vq,#title .en,#title .id{display:none}
#title .t1>span,#title .t2>span,#title .en>span,#pop>span{display:inline-block}
#sub .en{display:block;font-size:.56em;font-weight:600;line-height:1.3;opacity:1;-webkit-text-stroke-width:6px;margin-top:2px}
#lb{display:none}

/* ===== 模版五到八：人一直全屏，不缩小 ===== */
body.full #title{right:auto;text-align:left}
body.full #title.c{left:0!important;right:0;text-align:center}
body.full #title .tx{display:inline-block}
body.full #title .id{display:block}
body.full #card{width:var(--fw);padding:36px 40px 22px}
body.full #card h2{font-size:50px;margin-bottom:20px}
body.full .row{font-size:44px;padding:14px 24px;margin-bottom:12px}
body.full .row b{flex-basis:54px;height:54px;font-size:34px}
body.full .no,body.full .yes{font-size:42px;padding:14px 24px;margin-bottom:16px}
body.full .steps{flex-direction:column;align-items:stretch;gap:10px}
body.full .step{text-align:left;padding:18px 28px}
body.full .arr{display:none}
body.full #title .en{display:block}
body[data-theme=jiangshi] #title .en,body[data-theme=huazi] #title .en{display:none!important}
/* 五 杂志访谈：衬线大 Q、竖排小字、双语字幕、半透明字幕条 */
body[data-theme=zazhi]{
 --stage:#000;--ink:#fff;--sub:rgba(255,255,255,.7);--acc:#E9CD94;--hi:#E9CD94;--danger:#E9CD94;--good:#E9CD94;--goodbg:rgba(255,255,255,.08);--badbg:rgba(255,255,255,.08);--bad:#fff;
 --card:rgba(16,16,18,.58);--cardbd:1px solid rgba(255,255,255,.28);--radius:6px;--shadow:0 30px 70px rgba(0,0,0,.35);
 --tagbg:rgba(0,0,0,.28);--tagfg:#fff;--tagdot:#E9CD94;
 --t1:#fff;--t2:#fff;--tsh:0 2px 4px rgba(0,0,0,.5),0 4px 22px rgba(0,0,0,.45);
 --sfg:#fff;--sst:transparent;--sk:#F1DDB0;--skbg:transparent;--sbox:rgba(12,12,14,.58);--sfg2:#fff;
 --ring:#fff;--rowbg:transparent;--rowon:rgba(233,205,148,.16);--rowonfg:#F1DDB0;--num:transparent;--numfg:#E9CD94;
 --qbg:transparent;--qfg:#fff;--qem:#F1DDB0;--stbg:rgba(0,0,0,.45);--stfg:#fff;--ctabg:rgba(0,0,0,.35);--ctafg:#fff;--ctai:#E9CD94;
 --dim:linear-gradient(180deg,rgba(0,0,0,.5) 0%,rgba(0,0,0,.22) 22%,rgba(0,0,0,0) 34%,rgba(0,0,0,0) 62%,rgba(0,0,0,.35) 100%);
 --fontt:"Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;--fw:820px}
body[data-theme=zazhi] #title .box{display:flex;align-items:flex-start}
body[data-theme=zazhi] #title .q{display:block;font-family:"Noto Serif","Times New Roman","Georgia",serif;font-size:250px;line-height:.78;color:#fff;text-shadow:0 3px 6px rgba(0,0,0,.45),0 6px 26px rgba(0,0,0,.4);margin-top:6px}
body[data-theme=zazhi] #title .vq{display:block;text-shadow:0 1px 4px rgba(0,0,0,.6);writing-mode:vertical-rl;transform:rotate(180deg);font-family:"Noto Serif","Times New Roman",serif;font-size:26px;letter-spacing:2px;color:#fff;margin:4px 14px 0 4px;white-space:nowrap}
body[data-theme=zazhi] #title .t1{font-size:84px;font-weight:900;line-height:1.08}
body[data-theme=zazhi] #title .en{font-family:"Snell Roundhand","Apple Chancery","Segoe Script","Brush Script MT","URW Chancery L","Noto Serif",serif;font-style:italic;font-size:44px;color:#fff;line-height:1.2;text-shadow:0 1px 3px rgba(0,0,0,.6),0 2px 12px rgba(0,0,0,.45);margin:2px 0 0 6px}
body[data-theme=zazhi] #title .t2{font-family:var(--font);font-size:74px;font-weight:400;line-height:1.25;letter-spacing:2px;text-shadow:0 2px 4px rgba(0,0,0,.55),0 4px 22px rgba(0,0,0,.45)}
body[data-theme=zazhi] #title .id{margin:18px 0 0 6px;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.5)}
body[data-theme=zazhi] #title .id .nm{font-family:var(--fontt);font-size:40px;font-weight:700;letter-spacing:4px}
body[data-theme=zazhi] #title .id .ln{font-size:26px;font-weight:400;opacity:.9;letter-spacing:1px}
body[data-theme=zazhi] #sub .in{font-size:62px;font-weight:400;-webkit-text-stroke:0;text-shadow:0 1px 3px rgba(0,0,0,.5);border-radius:0;padding:8px 30px;letter-spacing:2px}
body[data-theme=zazhi] #sub span{opacity:.7}
body[data-theme=zazhi] #sub .kwg{border-radius:0;padding:0 4px;box-shadow:inset 0 -4px 0 rgba(233,205,148,.75)}
body[data-theme=zazhi] #sub .kwg span{font-size:64px;font-weight:500}
body[data-theme=zazhi] #sub .en{font-size:34px;font-weight:300;letter-spacing:.5px;margin-top:4px;-webkit-text-stroke:0}
body[data-theme=zazhi] #pop{font-weight:900;color:#fff;letter-spacing:14px;text-shadow:0 6px 30px rgba(0,0,0,.45)}
body[data-theme=zazhi] #quote{box-shadow:none;text-align:center;padding:0}
body[data-theme=zazhi] #quote .bar{width:120px;height:3px;margin:0 auto 26px}
body[data-theme=zazhi] #quote p{font-weight:600;text-shadow:0 4px 20px rgba(0,0,0,.45);transform-origin:center}
body[data-theme=zazhi] #card{backdrop-filter:blur(14px)}
body[data-theme=zazhi] #card h2{font-weight:700;color:#fff;font-size:54px}
body[data-theme=zazhi] .row{border-bottom:1px solid rgba(255,255,255,.22);border-radius:0;font-weight:400;color:#fff;font-size:46px}
body[data-theme=zazhi] .row b{font-family:"Noto Serif","Times New Roman",serif;font-weight:400;font-size:44px;flex-basis:54px}
body[data-theme=zazhi] .row.on{color:#F1DDB0}
body[data-theme=zazhi] #tag{font-weight:500;border:1px solid rgba(255,255,255,.6);box-shadow:none;font-size:32px;letter-spacing:4px}
body[data-theme=zazhi] #cta div{border:2px solid rgba(255,255,255,.75);box-shadow:none;font-weight:500;letter-spacing:4px}
/* 六 讲师大标题：粗宋体立体大标题常驻、身份条、白字幕、大字关键词 */
body[data-theme=jiangshi]{
 --stage:#000;--ink:#fff;--sub:rgba(255,255,255,.75);--acc:#FFE7A3;--hi:#FFE7A3;--danger:#FF6B57;--good:#FFE7A3;--goodbg:rgba(255,255,255,.1);--badbg:rgba(255,255,255,.1);--bad:#fff;
 --card:rgba(12,12,14,.5);--cardbd:2px solid rgba(255,255,255,.85);--radius:14px;--shadow:0 26px 60px rgba(0,0,0,.35);
 --tagbg:rgba(0,0,0,.35);--tagfg:#fff;--tagdot:#FFE7A3;
 --t1:#fff;--t2:#fff;--tsh:1px 1px 0 #b3b3b3,2px 2px 0 #9c9c9c,3px 3px 0 #868686,4px 4px 0 #727272,5px 5px 0 #5e5e5e,6px 6px 0 #4c4c4c,7px 8px 0 #3a3a3a,10px 14px 22px rgba(0,0,0,.45);
 --sfg:#fff;--sst:transparent;--sk:#FFE7A3;--skbg:transparent;--sbox:transparent;--sfg2:#fff;
 --ring:#fff;--rowbg:rgba(255,255,255,.08);--rowon:#fff;--rowonfg:#111;--num:transparent;--numfg:#fff;
 --qbg:transparent;--qfg:#fff;--qem:#FFE7A3;--stbg:#fff;--stfg:#111;--ctabg:#fff;--ctafg:#111;--ctai:#111;
 --dim:linear-gradient(180deg,rgba(0,0,0,.42) 0%,rgba(0,0,0,.16) 22%,rgba(0,0,0,0) 34%,rgba(0,0,0,0) 60%,rgba(0,0,0,.3) 100%);
 --fontt:"Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;--fw:820px}
body[data-theme=jiangshi] #title .t1,body[data-theme=jiangshi] #title .t2{font-size:104px;font-weight:900;letter-spacing:8px;line-height:1.24}
body[data-theme=jiangshi] #title .id{margin:26px 0 0 92px;color:#fff;font-family:var(--fontt);text-shadow:1px 1px 0 #777,2px 2px 0 #555,3px 4px 10px rgba(0,0,0,.45)}
body[data-theme=jiangshi] #title .id .nm{font-size:44px;font-weight:900;letter-spacing:6px;margin-bottom:4px}
body[data-theme=jiangshi] #title .id .ln{font-size:28px;font-weight:700;line-height:1.45}
body[data-theme=jiangshi] #sub .in{font-size:62px;font-weight:600;-webkit-text-stroke:8px rgba(0,0,0,.72);paint-order:stroke fill;text-shadow:0 3px 10px rgba(0,0,0,.45)}
body[data-theme=jiangshi] #sub span{opacity:.55}
body[data-theme=jiangshi] #sub .kwg{padding:0 2px;margin:0 2px}
body[data-theme=jiangshi] #sub .kwg span{font-size:68px;font-weight:800;-webkit-text-stroke:8px rgba(0,0,0,.72);paint-order:stroke fill}
body[data-theme=jiangshi] #sub .en{font-size:32px;font-weight:600;-webkit-text-stroke:5px rgba(0,0,0,.72)}
body[data-theme=jiangshi] #pop{font-size:170px;font-weight:900;color:#fff;letter-spacing:44px;text-indent:44px;text-shadow:var(--tsh)}
body[data-theme=jiangshi] #quote{box-shadow:none;padding:0;text-align:center}
body[data-theme=jiangshi] #quote .bar{display:none}
body[data-theme=jiangshi] #quote p{font-weight:900;text-shadow:1px 1px 0 #999,2px 2px 0 #777,3px 3px 0 #555,6px 8px 18px rgba(0,0,0,.45);transform-origin:center}
body[data-theme=jiangshi] #quote p.em{color:#fff;font-size:96px}
body[data-theme=jiangshi] #card h2{font-weight:900;color:#fff}
body[data-theme=jiangshi] .row{color:#fff;font-family:var(--fontt);font-weight:700}
body[data-theme=jiangshi] .row b{border:2px solid #fff;border-radius:50%;font-family:var(--fontt)}
body[data-theme=jiangshi] .row.on{color:#111}
body[data-theme=jiangshi] .row.on b{border-color:#111;color:#111}
body[data-theme=jiangshi] #tag{font-family:var(--fontt);font-weight:700;box-shadow:none}
/* 七 电影宽幕：上下黑边、细字幕、琥珀色重点词 */
body[data-theme=kuanmu]{
 --stage:#000;--ink:#fff;--sub:rgba(255,255,255,.65);--acc:#E8B86B;--hi:#E8B86B;--danger:#E8B86B;--good:#E8B86B;--goodbg:rgba(255,255,255,.06);--badbg:rgba(255,255,255,.06);--bad:rgba(255,255,255,.8);
 --card:rgba(0,0,0,.55);--cardbd:none;--radius:2px;--shadow:none;
 --tagbg:transparent;--tagfg:rgba(255,255,255,.6);--tagdot:#E8B86B;
 --t1:rgba(255,255,255,.72);--t2:#fff;--tsh:none;
 --sfg:#fff;--sst:transparent;--sk:#E8B86B;--skbg:transparent;--sbox:transparent;--sfg2:#fff;
 --ring:#fff;--rowbg:transparent;--rowon:transparent;--rowonfg:#E8B86B;--num:transparent;--numfg:#E8B86B;
 --qbg:transparent;--qfg:#fff;--qem:#E8B86B;--stbg:transparent;--stfg:#fff;--ctabg:transparent;--ctafg:#fff;--ctai:#E8B86B;
 --dim:radial-gradient(ellipse 80% 60% at 50% 50%,rgba(0,0,0,0) 55%,rgba(0,0,0,.42) 100%);
 --fontt:"Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;--fw:800px;--lb:330px}
body[data-theme=kuanmu].H{--lb:132px;--fw:740px}
body[data-theme=kuanmu] #lb{display:block;position:absolute;inset:0;z-index:4;pointer-events:none;background:linear-gradient(#000,#000) top/100% var(--lb) no-repeat,linear-gradient(#000,#000) bottom/100% var(--lb) no-repeat}
body[data-theme=kuanmu] #title .t1{font-size:34px;font-weight:600;letter-spacing:14px;margin-bottom:10px}
body[data-theme=kuanmu] #title .t2{font-size:62px;font-weight:700;letter-spacing:8px}
body[data-theme=kuanmu] #title .en{font-family:"Noto Serif","Georgia",serif;font-style:italic;font-size:26px;color:rgba(255,255,255,.55);letter-spacing:2px;order:3;margin-top:8px}
body[data-theme=kuanmu] #title .tx{display:flex;flex-direction:column;align-items:center}
body[data-theme=kuanmu] #title .id{font-size:26px;color:rgba(255,255,255,.6);letter-spacing:4px;margin-top:10px}
body[data-theme=kuanmu] #title .id .nm{display:inline;color:#E8B86B;margin-right:18px}
body[data-theme=kuanmu] #title .id .ln{display:inline;margin-right:14px}
body[data-theme=kuanmu] #sub .in{font-size:50px;font-weight:300;letter-spacing:4px;-webkit-text-stroke:0;padding:0}
body[data-theme=kuanmu] #sub span{opacity:.5}
body[data-theme=kuanmu] #sub .kwg{padding:0;margin:0 2px}
body[data-theme=kuanmu] #sub .kwg span{font-size:52px;font-weight:500}
body[data-theme=kuanmu] #sub .en{font-size:28px;font-weight:300;color:rgba(255,255,255,.62);letter-spacing:1px;margin-top:10px;-webkit-text-stroke:0}
body[data-theme=kuanmu] #pop{font-size:96px;font-weight:600;color:#fff;letter-spacing:30px;text-indent:30px}
body[data-theme=kuanmu] #pop>span{border-top:2px solid #E8B86B;border-bottom:2px solid #E8B86B;padding:6px 10px}
body[data-theme=kuanmu] #tag{font-size:26px;font-weight:400;letter-spacing:6px;box-shadow:none;padding:0}
body[data-theme=kuanmu] #quote{box-shadow:none;padding:0;text-align:center}
body[data-theme=kuanmu] #quote .bar{width:2px;height:70px;margin:0 auto 26px}
body[data-theme=kuanmu] #quote p{font-weight:500;letter-spacing:6px;transform-origin:center}
body[data-theme=kuanmu] #card{backdrop-filter:blur(10px)}
body[data-theme=kuanmu] #card h2{font-weight:600;color:#fff;letter-spacing:6px;font-size:50px}
body[data-theme=kuanmu] .row{color:rgba(255,255,255,.88);font-weight:300;letter-spacing:3px;padding:14px 8px;font-size:44px}
body[data-theme=kuanmu] .row b{font-family:"Noto Serif","Georgia",serif;font-weight:400;font-size:36px}
body[data-theme=kuanmu] .row.on{color:#E8B86B}
body[data-theme=kuanmu] #cta div{border-top:2px solid #E8B86B;border-bottom:2px solid #E8B86B;border-radius:0;box-shadow:none;font-weight:400;letter-spacing:10px;font-size:56px}
body[data-theme=kuanmu] #stamp div{box-shadow:none;font-family:var(--fontt);font-weight:600}
/* 八 综艺花字：粗描边字幕、黄色重点词弹跳、贴纸标题 */
body[data-theme=huazi]{
 --stage:#000;--ink:#111;--sub:#555;--acc:#FF3D7F;--hi:#FFE600;--danger:#FF3D7F;--good:#111;--goodbg:#FFF6C2;--badbg:#FFE0EA;--bad:#D61F5B;
 --card:#fff;--cardbd:6px solid #111;--radius:28px;--shadow:12px 12px 0 #111;
 --tagbg:#FF3D7F;--tagfg:#fff;--tagdot:#FFE600;
 --t1:#fff;--t2:#FFE600;--tsh:none;
 --sfg:#fff;--sst:#111;--sk:#FFE600;--skbg:transparent;--sbox:transparent;--sfg2:#fff;
 --ring:#111;--rowbg:#FFF6C2;--rowon:#FFE600;--rowonfg:#111;--num:#FF3D7F;--numfg:#fff;
 --qbg:#FFE600;--qfg:#111;--qem:#FF3D7F;--stbg:#fff;--stfg:#111;--ctabg:#FF3D7F;--ctafg:#fff;--ctai:#FFE600;
 --dim:linear-gradient(180deg,rgba(0,0,0,.12) 0%,rgba(0,0,0,0) 28%,rgba(0,0,0,0) 66%,rgba(0,0,0,.2) 100%);
 --font:"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;--fw:800px}
body[data-theme=huazi] #title .tx{display:flex;flex-direction:column;align-items:center}
body[data-theme=huazi] #title .t1{display:inline-block;background:#2D6BFF;color:#fff;font-size:58px;font-weight:900;padding:8px 30px 12px;border:6px solid #fff;border-radius:16px;rotate:-3deg;box-shadow:0 10px 0 rgba(0,0,0,.28)}
body[data-theme=huazi] #title .t2{font-size:108px;font-weight:900;color:#FFE600;-webkit-text-stroke:14px #111;paint-order:stroke fill;text-shadow:0 12px 0 #FF3D7F;rotate:2deg;margin-top:14px;line-height:1.15}
body[data-theme=huazi] #title .id{margin:18px auto 0;display:table;background:#fff;border:5px solid #111;border-radius:999px;padding:6px 28px;rotate:-1.5deg;font-size:30px;font-weight:800;color:#111}
body[data-theme=huazi] #title .id .nm{display:inline;color:#FF3D7F;margin-right:14px}
body[data-theme=huazi] #title .id .ln{display:inline;margin-right:10px}
body[data-theme=huazi] #sub .in{font-size:68px;font-weight:900;-webkit-text-stroke:14px #111;text-shadow:0 7px 0 #111}
body[data-theme=huazi] #sub span{opacity:.5}
body[data-theme=huazi] #sub .kwg{padding:0 2px;margin:0 4px}
body[data-theme=huazi] #sub .kwg span{font-size:80px;-webkit-text-stroke:14px #111;paint-order:stroke fill;color:#FFE600}
body[data-theme=huazi] #sub .en{font-size:34px;-webkit-text-stroke:8px #111;text-shadow:none}
body[data-theme=huazi] #pop{font-size:156px;font-weight:900;color:#FFE600;-webkit-text-stroke:16px #111;paint-order:stroke fill;text-shadow:10px 12px 0 #FF3D7F;rotate:-4deg}
body[data-theme=huazi] #quote{border:6px solid #111;box-shadow:14px 14px 0 #111;rotate:-1.5deg}
body[data-theme=huazi] #quote .bar{background:#111}
body[data-theme=huazi] #card h2{color:#111}
body[data-theme=huazi] .row{border:4px solid #111;font-weight:800}
body[data-theme=huazi] .row.on{box-shadow:6px 6px 0 #111}
body[data-theme=huazi] .step{border:4px solid #111;opacity:.75}
body[data-theme=huazi] .step.lit{opacity:1}
body[data-theme=huazi] :is(#tag,#stamp div,#cta div){border:5px solid #111;box-shadow:8px 8px 0 #111}
body[data-theme=huazi] #stamp div{rotate:-3deg}
/* 横版：字号整体小一点 */
body.H.full #title .t1{font-size:56px}body.H.full #title .t2{font-size:72px}
body.H[data-theme=zazhi] #title .q{font-size:170px}body.H[data-theme=zazhi] #title .vq{font-size:20px}body.H[data-theme=zazhi] #title .en{font-size:32px}
body.H[data-theme=jiangshi] #title .t1,body.H[data-theme=jiangshi] #title .t2{font-size:78px;letter-spacing:6px}body.H[data-theme=jiangshi] #pop{font-size:130px}
body.H[data-theme=kuanmu] #title .t1{font-size:24px;margin-bottom:4px}body.H[data-theme=kuanmu] #title .t2{font-size:44px}body.H[data-theme=kuanmu] #title .en,body.H[data-theme=kuanmu] #title .id{display:none}
body.H[data-theme=kuanmu] #sub .in{font-size:40px}body.H[data-theme=kuanmu] #sub .kwg span{font-size:42px}body.H[data-theme=kuanmu] #sub .en{font-size:22px;margin-top:4px}body.H[data-theme=kuanmu] #pop{font-size:60px;letter-spacing:20px}
body.H[data-theme=huazi] #title .t1{font-size:44px}body.H[data-theme=huazi] #title .t2{font-size:84px}
body.H #sub .in{font-size:50px}body.H #sub .kwg span{font-size:56px}
body.H #title .t1{font-size:56px}body.H #title .t2{font-size:96px}body.H #pop{font-size:104px}
body.H #card{padding:40px 44px 26px}body.H #card h2{font-size:52px;margin-bottom:22px}
body.H .row{font-size:44px;padding:16px 24px;margin-bottom:14px}body.H .row b{flex-basis:56px;height:56px;font-size:34px}
body.H #quote p{font-size:52px}body.H #quote p.em{font-size:74px}
body.H #tag{font-size:32px;padding:12px 26px}
</style></head>
<body class="V" data-theme="qingshuang">
<svg width="0" height="0" style="position:absolute"><filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="6"/></filter></svg>
<div id="stage"></div>
<div id="card" class="ov"></div>
<div id="person"><img id="pimg"></div>
<div id="dim"></div>
<div id="dim2"></div>
<div id="lb"></div>
<div id="tag" class="ov"><i></i><span id="tagtext"></span></div>
<div id="title" class="ov"><div class="box"><div class="q">Q</div><div class="vq">Interview Question</div><div class="tx"><div class="t1"></div><div class="en"></div><div class="t2"></div></div></div><div class="id"></div></div>
<div id="pop" class="ov"></div>
<div id="quote" class="ov"></div>
<div id="stamp" class="ov"></div>
<div id="cta" class="ov"></div>
<div id="sub" class="ov"></div>
<script>
let TL = null, FACES = null, FRAMEDIR = '', LAY = null;
const $ = id => document.getElementById(id);
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = x => { x = clamp(x, 0, 1); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const back = x => { x = clamp(x, 0, 1); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, p) => a + (b - a) * p;
function inout(t, t0, t1, din = .3, dout = .25) { if (t < t0 || t > t1) return 0; return Math.min(clamp((t - t0) / din, 0, 1), clamp((t1 - t) / dout, 0, 1)); }
// 版式坐标：竖版 / 横版
const LAYOUTS = {
  V: {W: 1080, H: 1920, tag: [56, 150], title: 1275, pop: 1300, subFull: 1540, subPip: 1630, card: {l: 64, t: 250, w: 952}, win: {x: 280, y: 1040, w: 520, h: 520},
      quote: {l: 70, t: 1250, w: 940}, stamp: 1290, cta: 1320, shotH: 560},
  H: {W: 1920, H: 1080, tag: [56, 56], title: 610, pop: 640, subFull: 940, subPip: 950, card: {l: 80, t: 150, w: 1200}, win: {x: 1380, y: 300, w: 460, h: 460},
      quote: {l: 360, t: 600, w: 1200}, stamp: 640, cta: 700, shotH: 600},
};
// 模版五到八（人一直全屏）：标题位置（左边距 0 表示居中）、字幕、大字、角标，卡片能放的上下范围
const FULL_LAY = {
  zazhi:    {V: {title: [50, 260], sub: 1460, pop: 1360, tag: [56, 150], area: [215, 1420]}, H: {title: [60, 110], sub: 880, pop: 800, tag: [60, 36], area: [110, 850]}},
  jiangshi: {V: {title: [76, 270], sub: 1460, pop: 1330, tag: [56, 150], area: [215, 1420]}, H: {title: [80, 110], sub: 880, pop: 780, tag: [60, 36], area: [110, 850]}},
  kuanmu:   {V: {title: [0, 150], sub: 1652, pop: 1625, tag: [56, 1850], area: [360, 1560]}, H: {title: [0, 22], sub: 962, pop: 958, tag: [56, 52], area: [160, 920]}},
  huazi:    {V: {title: [0, 250], sub: 1470, pop: 1350, tag: [56, 150], area: [215, 1420]}, H: {title: [0, 70], sub: 880, pop: 790, tag: [60, 36], area: [110, 850]}},
};
let FL = null, TB = 0;
function place(el, x, y, w) { el.style.left = x + 'px'; el.style.top = y + 'px'; if (w) el.style.width = w + 'px'; }
// 一行字放不下就整体缩小字号（不换行、不出画）
function setFit(el, text, maxW) {
  el.innerHTML = ''; if (!text) return;
  const s = document.createElement('span'); s.textContent = text; el.appendChild(s);
  el.style.fontSize = '';
  const w = s.offsetWidth;
  if (w > maxW) el.style.fontSize = (parseFloat(getComputedStyle(el).fontSize) * maxW / w).toFixed(1) + 'px';
}

function init(tl, faces, dir) {
  TL = tl; FACES = faces; FRAMEDIR = dir;
  const full = !!tl.full && FULL_LAY[tl.theme];
  document.body.className = tl.orient + (full ? ' full' : ''); document.body.dataset.theme = tl.theme;
  LAY = LAYOUTS[tl.orient];
  FL = full ? FULL_LAY[tl.theme][tl.orient] : null;
  $('tagtext').textContent = tl.column || '';
  $('tag').style.visibility = tl.column ? 'visible' : 'hidden';
  const T = $('title'), ti = tl.title || {};
  place($('tag'), ...(FL ? FL.tag : LAY.tag));
  T.style.top = (FL ? FL.title[1] : LAY.title) + 'px';
  if (FL) { T.classList.toggle('c', !FL.title[0]); if (FL.title[0]) T.style.left = FL.title[0] + 'px'; }
  $('pop').style.top = (FL ? FL.pop : LAY.pop) + 'px';
  const maxW = LAY.W - (FL && FL.title[0] ? FL.title[0] + 60 : 120) - (tl.theme === 'zazhi' ? (tl.orient === 'V' ? 230 : 160) : 0);
  setFit(T.querySelector('.t1'), ti.l1 || '', maxW);
  setFit(T.querySelector('.t2'), ti.l2 || '', maxW);
  setFit(T.querySelector('.en'), ti.en || '', maxW);
  T.querySelector('.en').style.display = FL && ti.en ? '' : 'none';
  const id = T.querySelector('.id'); id.innerHTML = '';
  (FL ? tl.ident || [] : []).forEach((s, i) => { const e = document.createElement('div'); e.className = i ? 'ln' : 'nm'; e.textContent = s; id.appendChild(e); });
  place($('card'), LAY.card.l, LAY.card.t, FL ? null : LAY.card.w);
  place($('quote'), LAY.quote.l, LAY.quote.t, LAY.quote.w);
  $('stamp').style.top = LAY.stamp + 'px'; $('cta').style.top = LAY.cta + 'px';
  if (FL && tl.theme === 'kuanmu') $('cta').style.top = (tl.orient === 'V' ? 1050 : 520) + 'px';
  const P = $('pimg'); P.width = LAY.W; P.height = LAY.H;
  TB = FL && tl.title && tl.theme !== 'kuanmu' ? T.getBoundingClientRect().bottom : 0;   // 常驻标题的下沿：横版卡片放在它下面，竖版卡片压上来时标题让开
}

// 全屏模版的卡片：人不缩小，卡片放在脸的下面（放不下就放上面），横版放在脸的另一边。一张卡片定一次位置，不跟着晃
function floatCard(el, c) {
  if (c._pos) return c._pos;
  const fi = Math.min(Math.round(c.t0 * TL.fps), FACES.length - 1);
  const f = FACES[Math.max(0, fi)] || [LAY.W * .3, LAY.H * .3, LAY.W * .4, LAY.W * .4];
  const [fx, fy, fw, fh] = f, w = el.offsetWidth, h = el.offsetHeight, [a0, a1] = FL.area;
  let x, y, s = 1, top = false;
  if (TL.orient === 'V') {
    // 脸下面（下巴往下留一点）和脸上面各有多少地方；哪边放得下就放哪边，都放不下就挑地方大的一边、卡片缩小一点
    x = (LAY.W - w) / 2;
    const below = Math.max(fy + fh * 1.15 + 36, a0), roomB = a1 - below;
    const aboveEnd = fy - 40, roomA = aboveEnd - a0;
    if (h <= roomB) y = below;
    else if (h <= roomA) { y = aboveEnd - h; top = true; }
    else if (Math.max(roomA, roomB) >= h * .7) {
      if (roomB >= roomA) { s = roomB / h; y = below; }
      else { s = roomA / h; y = aboveEnd - h * s; top = true; }
    }
    else { s = .7; y = a1 - h * s; }   // 实在放不下：贴着字幕上沿，宁可压到下巴也不压眼睛
    x = (LAY.W - w * s) / 2;
  } else {
    // 横版：放在脸的另一边（脸在中间就放右边），而且放在常驻标题下面
    const ww = Math.min(w, LAY.W / 2 - 120);
    if (ww < w) s = ww / w;
    x = fx + fw / 2 <= LAY.W / 2 ? LAY.W - 80 - w * s : 80;
    const t0 = Math.max(a0, TB ? TB + 30 : 0), room = a1 - t0;
    if (h * s <= room) y = t0 + (room - h * s) / 2;
    else if (room >= h * s * .72) { s *= room / (h * s); y = t0; }
    else { y = clamp(a0 + (a1 - a0 - h * s) / 2, a0, a1 - h * s); top = true; }
  }
  c._pos = {x, y, w, h, s, top};
  return c._pos;
}

function pipP(t) { let p = 0; for (const [a, b] of TL.pip) p = Math.max(p, inout(t, a, b, .5, .5)); return ease(p); }

function layoutPerson(fi, p) {
  const f = FACES[Math.min(fi, FACES.length - 1)] || [LAY.W * .3, LAY.H * .3, LAY.W * .4, LAY.W * .4];
  const [fx, fy, fw, fh] = f;
  const S = Math.min(Math.max(fw * 1.9, 320), LAY.W, LAY.H);
  const cx = fx + fw / 2, cy = fy + fh * 0.6;
  const x0 = clamp(cx - S / 2, 0, LAY.W - S), y0 = clamp(cy - S / 2, 0, LAY.H - S);
  const win = LAY.win;
  const crop = {x: lerp(0, x0, p), y: lerp(0, y0, p), w: lerp(LAY.W, S, p)};
  const rect = {x: lerp(0, win.x, p), y: lerp(0, win.y, p), w: lerp(LAY.W, win.w, p), h: lerp(LAY.H, win.h, p)};
  const k = rect.w / crop.w;
  const P = $('person'), I = $('pimg');
  P.style.left = rect.x + 'px'; P.style.top = rect.y + 'px'; P.style.width = rect.w + 'px'; P.style.height = rect.h + 'px';
  P.style.borderRadius = (48 * p) + 'px';
  P.style.boxShadow = p > 0 ? `0 0 0 ${6 * p}px var(--ring), 0 24px 60px rgba(17,19,24,${.25 * p})` : 'none';
  I.style.width = LAY.W * k + 'px'; I.style.height = LAY.H * k + 'px';
  I.style.left = -crop.x * k + 'px'; I.style.top = -crop.y * k + 'px';
}

function show(el, o, tf) { el.style.opacity = o; el.style.display = o > 0.001 ? '' : 'none'; if (tf !== undefined) el.style.transform = tf; }

function renderSub(t, p) {
  const el = $('sub'), L = TL.lines;
  let cur = null;
  for (let i = 0; i < L.length; i++) {
    const n = i + 1 < L.length ? L[i + 1].start : 1e9;
    if (t >= L[i].start - 0.08 && t < Math.min(n - 0.03, L[i].end + 0.6)) cur = L[i];
  }
  if (!cur || TL.hide_sub.includes(cur.n)) { show(el, 0); return; }
  const k = clamp((t - cur.start + 0.08) / 0.15, 0, 1);
  let h = '', i = 0;
  const C = cur.chars;
  while (i < C.length) {
    if (!C[i][2]) { h += `<span class="${t >= C[i][1] - 0.03 ? 'lit' : ''}">${C[i][0]}</span>`; i++; continue; }
    let j = i; while (j < C.length && C[j][2]) j++;
    const g0 = C[i][1], lit0 = t >= g0 - 0.03;
    const q = clamp((t - g0) / 0.22, 0, 1), sc = lit0 ? 1 + 0.16 * Math.sin(q * Math.PI) : 1;
    h += `<span class="kwg${lit0 ? '' : ' off'}" style="transform:scale(${sc.toFixed(3)})">`;
    for (let m = i; m < j; m++) h += `<span class="${t >= C[m][1] - 0.03 ? 'lit' : ''}">${C[m][0]}</span>`;
    h += '</span>'; i = j;
  }
  const en = cur.en ? `<div class="en">${cur.en.replace(/</g, '&lt;')}</div>` : '';
  el.innerHTML = `<div class="in">${h}${en}</div>`;
  const inn = el.firstChild, mw = LAY.W - 70;   // 一行太长就整体缩小，不出画
  if (inn.offsetWidth > mw) { inn.style.transformOrigin = '50% 0'; inn.style.transform = `scale(${(mw / inn.offsetWidth).toFixed(3)})`; }
  el.className = 'ov' + (p > .5 ? ' onstage' : '');
  el.style.top = (FL ? FL.sub : p > .5 ? LAY.subPip : LAY.subFull) + 'px';
  show(el, k, `translateY(${(1 - k) * 18}px)`);
}

function cardRows(c, t) {
  let h = '', act = -1;
  c.rows.forEach(([r, rt], i) => { if (t >= rt - .05) act = i; });
  c.rows.forEach(([r, rt], i) => {
    if (t < rt - .05) { h += `<div class="row" style="opacity:${FL ? .32 : 0}"><b>${i + 1}</b>${r}</div>`; return; }   // 全屏模版：没说到的先淡淡露着，免得卡片空一大块
    const q = clamp((t - rt + .05) / .25, 0, 1);
    h += `<div class="row${i === act ? ' on' : ''}" style="opacity:${q};transform:translateX(${(1 - q) * -30}px) scale(${i === act ? 1.03 : 1})"><b>${i + 1}</b>${r}</div>`;
  });
  return h;
}

function cardSteps(c, t) {
  let h = '';
  if (c.no) {
    const [nt, ntime] = c.no;
    const q = clamp((t - ntime) / .25, 0, 1), w = clamp((t - ntime - .25) / .3, 0, 1);
    h += `<div class="no" style="opacity:${q};transform:scale(${lerp(.92, 1, back(q))})"><span class="x">✕</span><span class="nt">${nt}<span class="strike" style="width:calc(${(w * 100).toFixed(1)}% + 12px)"></span></span></div>`;
  }
  const any = t >= c.steps[0][1] - .1;
  h += `<div class="lbl" style="opacity:${any ? 1 : 0}">${c.label || '要拆成：'}</div><div class="steps">`;
  c.steps.forEach(([s, st], i) => {
    const lit = t >= st - .05, q = clamp((t - st) / .2, 0, 1);
    if (i) h += `<span class="arr${lit ? ' lit' : ''}" style="opacity:${any ? 1 : 0}">→</span>`;
    h += `<div class="step${lit ? ' lit' : ''}" style="opacity:${any ? 1 : .0};transform:scale(${lit ? lerp(.94, 1, back(q)) : 1})">${s}</div>`;
  });
  h += '</div>';
  if (c.yes) {
    const [yt, ytime] = c.yes, q = clamp((t - ytime) / .25, 0, 1);
    h += `<div class="yes" style="opacity:${q};transform:scale(${lerp(.92, 1, back(q))})"><span class="ok">✓</span>${yt}</div>`;
  }
  return h;
}

function cardShot(c, t) {
  // 截图：先给全貌，到圈注的时间推近到那个位置并圈出来
  const W = (FL ? $('card').clientWidth : LAY.card.w) - 100, H = FL ? (TL.orient === 'V' ? 460 : 400) : LAY.shotH;
  const [iw, ih] = c.size;
  const k0 = Math.min(W / iw, H / ih);
  let k = k0, ox = (W - iw * k0) / 2, oy = (H - ih * k0) / 2, mk = '';
  const m = [...(c.marks || [])].reverse().find(m => t >= m[4] - .05);
  if (m) {
    const [mx, my, mw, mh, mt] = m;
    const q = ease(clamp((t - mt) / .6, 0, 1));
    const kz = Math.min(W / (mw * 1.8), H / (mh * 1.8), k0 * 2.4);
    const k1 = Math.max(k0, kz);
    const cx = mx + mw / 2, cy = my + mh / 2;
    let ox1 = W / 2 - cx * k1, oy1 = H / 2 - cy * k1;
    ox1 = clamp(ox1, W - iw * k1, 0); oy1 = clamp(oy1, H - ih * k1, 0);
    if (iw * k1 < W) ox1 = (W - iw * k1) / 2; if (ih * k1 < H) oy1 = (H - ih * k1) / 2;
    k = lerp(k0, k1, q); ox = lerp(ox, ox1, q); oy = lerp(oy, oy1, q);
    const mq = clamp((t - mt - .45) / .25, 0, 1);
    mk = `<div class="mk" style="left:${ox + mx * k - 8}px;top:${oy + my * k - 8}px;width:${mw * k + 16}px;height:${mh * k + 16}px;opacity:${mq}"></div>`;
  }
  return `<div class="shot" style="width:${W}px;height:${H}px"><img src="${c.src}" style="width:${iw * k}px;height:${ih * k}px;left:${ox}px;top:${oy}px">${mk}</div>`;
}

function renderCard(t, p) {
  const el = $('card');
  const c = TL.cards.find(c => t >= c.t0 && t <= c.t1);
  if (!c || (!FL && p < 0.01)) { show(el, 0); return null; }
  const o = inout(t, c.t0, c.t1, .35, .2) * (FL ? 1 : clamp(p * 1.5, 0, 1));
  if (FL) el.style.display = '';
  let h = c.title ? `<h2>${c.title}</h2>` : '';
  if (c.kind === 'steps') h += cardSteps(c, t);
  else if (c.kind === 'shot') h += cardShot(c, t);
  else h += cardRows(c, t);
  el.innerHTML = h;
  if (FL) {
    el.style.transform = 'none'; el.style.display = '';
    const pos = floatCard(el, c);
    el.style.left = pos.x + 'px'; el.style.top = pos.y + 'px'; el.style.transformOrigin = '0 0';
    show(el, o, `translateY(${(1 - o) * 30}px) scale(${(lerp(.96, 1, o) * pos.s).toFixed(4)})`);
    return {o, pos};
  }
  show(el, o, `translateY(${(1 - o) * 40}px)`);
  return null;
}

function renderQuote(t) {
  const el = $('quote');
  const qd = TL.quotes.find(q => t >= q.t0 && t <= q.t1);
  if (!qd) { show(el, 0); return 0; }
  const o = inout(t, qd.t0, qd.t1, .35, .25);
  let h = '<div class="bar"></div>';
  for (const [txt, pt, em] of qd.parts) {
    const q = clamp((t - pt + .05) / .3, 0, 1);
    h += `<p class="${em ? 'em' : ''}" style="opacity:${q};transform:translateY(${(1 - q) * 16}px) scale(${em ? lerp(.9, 1, back(q)) : 1})">${txt}</p>`;
  }
  el.innerHTML = h;
  show(el, o, `translateY(${(1 - o) * 50}px)`);
  return o;
}

function render(t, fi) {
  const p = FL ? 0 : pipP(t);
  layoutPerson(fi, p);
  show($('stage'), p > 0 ? 1 : 0);
  const tg = clamp((t - .15) / .3, 0, 1);
  show($('tag'), tg, FL ? 'none' : `translateX(${(1 - tg) * -40}px)`);
  const cd = renderCard(t, p);
  if (TL.title) {
    const ti = TL.title;
    let to = inout(t, ti.t0, ti.t1, .35, .25);
    // 卡片放在脸上面、和标题撞上时，标题先让开
    if (cd && cd.pos.top && TB > cd.pos.y - 10) to *= 1 - cd.o;   // 用开头量好的标题下沿，标题藏起来时量不到
    show($('title'), to, `translateY(${(FL ? 1 - clamp((t - ti.t0) / .35, 0, 1) : 1 - to) * 30}px)`);
    const t2 = $('title').querySelector('.t2'), q2 = clamp((t - ti.t0 - .25) / .3, 0, 1);
    t2.style.transform = `scale(${lerp(.7, 1, back(q2))})`; t2.style.opacity = q2;
    const id = $('title').querySelector('.id'), qi = clamp((t - ti.t0 - .6) / .35, 0, 1);
    id.style.opacity = qi; id.style.transform = `translateY(${(1 - qi) * 14}px)`;
  } else show($('title'), 0);
  const pp = TL.pops.find(x => t >= x.t0 && t <= x.t1);
  if (pp) {
    if ($('pop').dataset.text !== pp.text) { setFit($('pop'), pp.text, LAY.W - 100); $('pop').dataset.text = pp.text; }
    show($('pop'), inout(t, pp.t0, pp.t1, .25, .2), `scale(${lerp(.6, 1, back(clamp((t - pp.t0) / .3, 0, 1)))})`);
  }
  else show($('pop'), 0);
  const qo = renderQuote(t);
  const s = TL.stamps.find(x => t >= x.t0 && t <= x.t1);
  if (s) { $('stamp').innerHTML = `<div>${s.a}<em>≠</em>${s.b}</div>`; show($('stamp'), inout(t, s.t0, s.t1, .2, .2), `scale(${lerp(1.5, 1, back(clamp((t - s.t0) / .25, 0, 1)))}) rotate(-4deg)`); }
  else show($('stamp'), 0);
  let co = 0;
  if (TL.cta) {
    const c = TL.cta; co = inout(t, c.t0, c.t1 + 1, .35, .2);
    $('cta').innerHTML = `<div><i></i>${c.text}</div>`;
    show($('cta'), co, `translateY(${(1 - co) * 40}px) scale(${lerp(.9, 1, back(clamp((t - c.t0) / .35, 0, 1)))})`);
  } else show($('cta'), 0);
  show($('dim'), 1 - p);
  show($('dim2'), Math.max(qo, co) * (1 - p));
  renderSub(t, p);
}

async function frame(fi) {
  const t = fi / TL.fps;
  const vf = Math.min(fi, TL.video_frames - 1);
  const I = $('pimg');
  const src = FRAMEDIR + String(vf).padStart(5, '0') + '.jpg';
  if (!I.src.endsWith(src)) { I.src = src; await I.decode(); }
  const imgs = [...document.querySelectorAll('#card img')];
  render(t, vf);
  for (const im of document.querySelectorAll('#card img')) { if (!im.complete) await im.decode().catch(() => 0); }
  return t;
}
</script>
</body></html>
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
