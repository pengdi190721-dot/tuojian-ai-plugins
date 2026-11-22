"""A 线第 2 步：出模版图给用户挑。一共八个模版：
  一到四（带小窗）：讲要点时人缩到圆角小窗，卡片在旁边
  五到八（全屏口播）：人一直全屏、不缩小，常驻标题、字幕动效，讲要点时卡片浮在人旁边不挡脸
每个模版出一张图（左边“人像全屏”，右边“讲要点时”），再拼一张总览图。

用法：
  python3 video_templates.py 项目目录            # 用用户自己视频里的画面（要先跑 video_prepare.py）
  python3 video_templates.py 项目目录 --示例      # 还没视频：用画好的示意人像出图，先让用户挑模版
  python3 video_templates.py 项目目录 --示例 --横  # 示例出横版
需要：项目目录里的 模版图.json（--示例 没有时用默认的字），例如
  {"标题": ["老员工一句", "“这个要看情况”"],
   "字幕": "企业AI落地，【最值钱】的一个数据",
   "要点卡": {"标题": "“看情况”，到底看什么？", "要点": ["看客户类型", "看订单金额", "什么情况直接处理", "什么情况必须找领导"], "亮第几条": 3},
   "小窗字幕": "什么情况可以【直接处理】",
   "身份": ["彭迪", "拓见AI创始人"]}
  标题可以加第三行英文；字幕后面加“ | 英文”就是双语字幕；身份只在模版五到八显示。栏目取 project.json 的“栏目”
输出：out/模版总览.jpg（八个模版一张图，发给用户挑）、out/模版一.jpg … out/模版八.jpg（单张大图）"""
import asyncio, json, sys, re, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from video_build import chars_of

DEMO_SPEC = {'标题': ['做企业老板IP', '不是让你去做网红', 'Founder IP is not about fame'], '字幕': '是让客户知道，【因为什么】选择你',
             '要点卡': {'标题': '我们看三件事', '要点': ['你的生意', '你这个人', '客户关心什么'], '亮第几条': 3},
             '小窗字幕': '你的生意决定【吸引谁】', '身份': ['彭迪', '拓见AI · 企业AI落地顾问']}
CAPS = {False: ('人像全屏：片头、金句、结尾', '讲要点：人缩到小窗，卡片在旁边'),
        True: ('人一直全屏：常驻标题＋字幕动效', '讲要点：人不缩小，卡片浮在旁边')}
GROUPS = [('带小窗（一到四）：讲要点时人缩到小窗', [k for k in KOUBO_THEMES if k not in FULL_THEMES]),
          ('全屏口播（五到八）：人一直全屏，不缩小', list(FULL_THEMES))]


def pick_frames(d, meta, k=2):
    """抽 18 帧，挑脸清楚、睁着眼、在画面中间的两帧（相隔 3 秒以上）"""
    ft = FaceTrack()
    cands = []
    for i in range(18):
        t = meta['dur'] * (0.08 + 0.84 * i / 17)
        img = next(read_frames(d / 'work' / 'src.mov', meta['W'], meta['H'], start=t, n=1))
        ft.box = None
        box, eyes = ft.find(img, eyes=True)
        if box is None:
            continue
        cx = (box[0] + box[2] / 2) / meta['W']
        score = (2 if eyes >= 2 else 0) + (1 - abs(cx - 0.5) * 2) + box[2] / meta['W']
        cands.append((score, t, img, [float(v) for v in box]))
    if not cands:
        sys.exit('【出错】抽了 18 帧都没找到人脸：这条可能是录屏，可以先用 --示例 出模版图给用户挑，制作时只用全屏版式')
    cands.sort(key=lambda c: -c[0])
    picked = [cands[0]]
    for c in cands[1:]:
        if all(abs(c[1] - p[1]) > 3 for p in picked):
            picked.append(c)
        if len(picked) == k:
            break
    while len(picked) < k:
        picked.append(cands[0])
    return picked


def demo_svg(W, H):
    """还没视频时用的示意人像（画出来的，不是真人照片）。返回 svg 文字和脸的位置"""
    V = H > W
    cx, cy, rx, ry = (W / 2, H * .37, W * .135, H * .098) if V else (W / 2, H * .36, W * .058, H * .128)
    sh = cy + ry * 1.55
    sw = W * .40 if V else W * .17
    bokeh = ''.join(f'<circle cx="{W * x:.0f}" cy="{H * y:.0f}" r="{W * r:.0f}" fill="{c}" opacity="{o}"/>' for x, y, r, c, o in [
        (.12, .14, .07, '#F6D9A8', .45), (.86, .1, .05, '#FFE7C4', .5), (.78, .3, .09, '#E9C38F', .35), (.08, .42, .05, '#FBE3BE', .4),
        (.92, .52, .06, '#F3CF9C', .35), (.2, .25, .03, '#FFF1DA', .6), (.66, .06, .03, '#FFF1DA', .6)])
    shelves = ''.join(f'<rect x="0" y="{H * y:.0f}" width="{W}" height="{H * .008:.0f}" fill="#5A3E2B" opacity=".55"/>' for y in (.2, .33, .46))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7A5A40"/><stop offset=".55" stop-color="#9B7653"/><stop offset="1" stop-color="#3F2E22"/></linearGradient>
<linearGradient id="suit" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A3F4A"/><stop offset="1" stop-color="#20242B"/></linearGradient>
<radialGradient id="skin" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="#F6D2BC"/><stop offset="1" stop-color="#E2A98C"/></radialGradient>
<filter id="blur"><feGaussianBlur stdDeviation="{W * .012:.0f}"/></filter></defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/><g filter="url(#blur)">{shelves}{bokeh}</g>
<path d="M{cx - sw} {H} L{cx - sw * .96} {sh + ry * .5} Q{cx - sw * .9} {sh} {cx - sw * .45} {sh - ry * .12} L{cx + sw * .45} {sh - ry * .12} Q{cx + sw * .9} {sh} {cx + sw * .96} {sh + ry * .5} L{cx + sw} {H} Z" fill="url(#suit)"/>
<path d="M{cx - rx * .62} {sh - ry * .14} L{cx} {sh + ry * 1.05} L{cx + rx * .62} {sh - ry * .14} Z" fill="#F4F1EC"/>
<rect x="{cx - rx * .42}" y="{cy + ry * .55}" width="{rx * .84}" height="{ry * .9}" rx="{rx * .3}" fill="#E6AF92"/>
<path d="M{cx - rx * 1.12} {cy + ry * .5} Q{cx - rx * 1.3} {cy - ry * 1.25} {cx} {cy - ry * 1.2} Q{cx + rx * 1.3} {cy - ry * 1.25} {cx + rx * 1.12} {cy + ry * .5} Q{cx + rx * 1.25} {cy + ry * 1.25} {cx + rx * .9} {cy + ry * 1.45} L{cx - rx * .9} {cy + ry * 1.45} Q{cx - rx * 1.25} {cy + ry * 1.25} {cx - rx * 1.12} {cy + ry * .5} Z" fill="#3B2418"/>
<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#skin)"/>
<path d="M{cx - rx * 1.02} {cy - ry * .15} Q{cx - rx * .75} {cy - ry * 1.15} {cx + rx * .2} {cy - ry * 1.02} Q{cx + rx * 1.0} {cy - ry * .9} {cx + rx * 1.02} {cy - ry * .1} Q{cx + rx * .55} {cy - ry * .7} {cx - rx * .1} {cy - ry * .62} Q{cx - rx * .7} {cy - ry * .55} {cx - rx * 1.02} {cy - ry * .15} Z" fill="#3B2418"/>
<g fill="#2B1B14"><ellipse cx="{cx - rx * .38}" cy="{cy + ry * .02}" rx="{rx * .085}" ry="{ry * .06}"/><ellipse cx="{cx + rx * .38}" cy="{cy + ry * .02}" rx="{rx * .085}" ry="{ry * .06}"/></g>
<g stroke="#3B2418" stroke-width="{rx * .06:.1f}" stroke-linecap="round" fill="none"><path d="M{cx - rx * .55} {cy - ry * .17} Q{cx - rx * .38} {cy - ry * .25} {cx - rx * .2} {cy - ry * .17}"/><path d="M{cx + rx * .2} {cy - ry * .17} Q{cx + rx * .38} {cy - ry * .25} {cx + rx * .55} {cy - ry * .17}"/></g>
<path d="M{cx} {cy + ry * .08} Q{cx - rx * .08} {cy + ry * .3} {cx + rx * .02} {cy + ry * .33}" stroke="#C98B70" stroke-width="{rx * .04:.1f}" fill="none" stroke-linecap="round"/>
<path d="M{cx - rx * .22} {cy + ry * .52} Q{cx} {cy + ry * .64} {cx + rx * .22} {cy + ry * .52}" stroke="#B5584A" stroke-width="{rx * .07:.1f}" fill="none" stroke-linecap="round"/>
</svg>'''
    return svg, [cx - rx, cy - ry, rx * 2, ry * 2]


def line_obj(text, n=1):
    zh, _, en = text.partition('|') if '|' in text else text.partition('｜')
    cs = chars_of(zh.strip())
    return {'n': n, 'text': re.sub('[【】]', '', zh.strip()), 'en': en.strip(), 'chars': [[c, 0.0, kw] for c, kw, _ in cs], 'start': 0.0, 'end': 100.0}


def fake_tl(meta, cfg, spec, kind, theme='qingshuang'):
    """kind：full 人像全屏（片头加一句字幕）；pip 讲要点（一到四缩小窗，五到八卡片浮在旁边）"""
    full = theme in FULL_THEMES
    tl = {'fps': 24, 'end': 100, 'video_frames': 1, 'orient': meta['orient'], 'theme': theme, 'full': full,
          'column': cfg.get('栏目', ''), 'title': None, 'ident': spec.get('身份', []) if full else [], 'pops': [], 'pip': [], 'cards': [],
          'quotes': [], 'stamps': [], 'cta': None, 'cuts': [], 'hide_sub': [], 'sfx': []}
    h = spec.get('标题') or []
    if kind == 'full' or full:
        if len(h) >= 2:
            tl['title'] = {'t0': -1, 't1': 100, 'l1': h[0], 'l2': h[1], 'en': h[2] if len(h) > 2 else ''}
    if kind == 'full':
        tl['lines'] = [line_obj(spec.get('字幕', ''))]
    else:
        card = spec['要点卡']
        act = int(card.get('亮第几条', len(card['要点'])))
        if not full:
            tl['pip'] = [[-1, 100]]
        tl['cards'] = [{'t0': -1, 't1': 100, 'kind': 'rows', 'title': card['标题'],
                        'rows': [[r, -1 if i < act else 99] for i, r in enumerate(card['要点'])]}]
        tl['lines'] = [line_obj(spec.get('小窗字幕', ''))]
    return tl


async def render_all(d, meta, cfg, spec, picked):
    from playwright.async_api import async_playwright
    from common import open_browser
    from video_render import page_html
    W, H = meta['W'], meta['H']
    out = {}
    async with async_playwright() as pw:
        b = await open_browser(pw)
        pg = await b.new_page(viewport={'width': W, 'height': H})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        page = d / 'work' / 'tpl' / 'page.html'
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(page_html(), encoding='utf-8')
        for kind, (score, t, img, box) in zip(('full', 'pip'), picked):
            fdir = d / 'work' / 'tpl' / kind
            fdir.mkdir(parents=True, exist_ok=True)
            if isinstance(img, str):
                (fdir / 'frame.svg').write_text(img, encoding='utf-8')
                await pg.set_viewport_size({'width': W, 'height': H})
                await pg.goto((fdir / 'frame.svg').as_uri())
                await pg.screenshot(path=str(fdir / '00000.jpg'), type='jpeg', quality=93)
            else:
                import cv2
                cv2.imwrite(str(fdir / '00000.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
            for th in KOUBO_THEMES:
                await pg.goto(page.as_uri())
                await pg.wait_for_timeout(150)
                tl = fake_tl(meta, cfg, spec, kind, th)
                await pg.evaluate('([a,b,c]) => init(a,b,c)', [tl, [box], fdir.resolve().as_uri() + '/'])
                await pg.evaluate('f => frame(f)', 24)
                f = d / 'work' / 'tpl' / f'{th}_{kind}.jpg'
                await pg.screenshot(path=str(f), type='jpeg', quality=90)
                out[(th, kind)] = f
        if errs:
            sys.exit('【出错】模版页面报错：' + '；'.join(errs[:3]))
        await compose(pg, d, meta, out)
        await b.close()
    return out


SHEET_CSS = '''*{margin:0;padding:0;box-sizing:border-box}body{background:#EEEEEA;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC","Source Han Sans SC",sans-serif;color:#1E1E1E;padding:36px 40px 44px}
h1{font-size:40px;font-weight:800;margin-bottom:6px}.tip{font-size:24px;color:#666;margin-bottom:26px}
h2{font-size:30px;font-weight:800;margin:22px 0 16px;padding-left:14px;border-left:8px solid #1E1E1E}
.row{display:flex;gap:26px}.cell{display:flex;flex-direction:column;align-items:center}
.name{font-size:28px;font-weight:800;margin-bottom:12px;white-space:nowrap}.pair{display:flex;gap:10px}
img{display:block;border-radius:18px}.cap{font-size:20px;color:#666;margin-top:10px;text-align:center;white-space:nowrap}'''


async def compose(pg, d, meta, shots):
    """拼图用浏览器排字：中文字体由系统自己找，Mac、Windows、Linux 上都不会变成方块"""
    V = meta['orient'] == 'V'
    tw = 200 if V else 330
    th_ = int(tw * meta['H'] / meta['W'])
    u = lambda p: p.resolve().as_uri()
    # 总览：两组，每组四个，每个模版两张（人像全屏 / 讲要点）
    parts = [f'<h1>选一个模版，回我编号就行</h1><div class="tip">每个模版两张：左边是平时说话的样子，右边是讲要点的时候。五到八人一直全屏，不缩小。</div>']
    for gname, keys in GROUPS:
        parts.append(f'<h2>{html.escape(gname)}</h2><div class="row">')
        for k in keys:
            full = k in FULL_THEMES
            parts.append(f'<div class="cell"><div class="name">{html.escape(theme_label(k))}</div><div class="pair">'
                         f'<img src="{u(shots[(k, "full")])}" width="{tw}" height="{th_}"><img src="{u(shots[(k, "pip")])}" width="{tw}" height="{th_}"></div>'
                         f'<div class="cap">{"人一直全屏" if full else "讲要点时缩小窗"}</div></div>')
        parts.append('</div>')
    await sheet(pg, d / 'work' / 'tpl' / '总览.html', ''.join(parts), d / 'out' / '模版总览.jpg')
    # 单张大图
    bw = 480 if V else 860
    bh = int(bw * meta['H'] / meta['W'])
    for k in KOUBO_THEMES:
        caps = CAPS[k in FULL_THEMES]
        inner = (f'<h1>{html.escape(theme_label(k))}</h1><div class="row" style="margin-top:20px;{"" if V else "flex-direction:column"}">' +
                 ''.join(f'<div class="cell"><img src="{u(shots[(k, kind)])}" width="{bw}" height="{bh}"><div class="cap" style="font-size:24px">{html.escape(c)}</div></div>'
                         for kind, c in zip(('full', 'pip'), caps)) + '</div>')
        await sheet(pg, d / 'work' / 'tpl' / f'{k}.html', inner, d / 'out' / f'{TEMPLATE_NAMES[k]}.jpg')


async def sheet(pg, page, body, out):
    page.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{SHEET_CSS}</style></head><body><div id="w" style="display:inline-block">{body}</div></body></html>', encoding='utf-8')
    await pg.goto(page.as_uri())
    await pg.wait_for_load_state('load')
    await pg.wait_for_timeout(100)
    box = await pg.evaluate('(() => { const r = document.getElementById("w").getBoundingClientRect(); return [Math.ceil(r.width) + 80, Math.ceil(r.height) + 80]; })()')
    await pg.set_viewport_size({'width': box[0], 'height': box[1]})
    await pg.screenshot(path=str(out), type='jpeg', quality=88, full_page=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    demo = '--示例' in sys.argv
    d = proj(args[0] if args else '.', need_src=not demo)
    p = d / '模版图.json'
    if p.exists():
        spec = json.loads(p.read_text(encoding='utf-8'))
    elif demo:
        spec = DEMO_SPEC
    else:
        sys.exit('【出错】还没有 模版图.json，写法见本脚本开头的说明（还没视频就加 --示例）')
    if not spec.get('要点卡') or len(spec['要点卡'].get('要点', [])) < 2:
        sys.exit('【出错】模版图.json 的“要点卡”至少要 2 条要点')
    cfg = load_cfg(d)
    if demo:
        horiz = '--横' in sys.argv or cfg.get('画幅') == '横'
        W, H = (1920, 1080) if horiz else (1080, 1920)
        meta = {'W': W, 'H': H, 'orient': 'H' if horiz else 'V'}
        svg, box = demo_svg(W, H)
        picked = [(1, 0, svg, box), (1, 0, svg, box)]
        print('用示意人像出图（还没有视频）')
    else:
        meta = info(d)
        picked = pick_frames(d, meta)
        print(f'挑了两帧：{fmt_t(picked[0][1])}（人像全屏用）、{fmt_t(picked[1][1])}（讲要点用）')
    asyncio.run(render_all(d, meta, cfg, spec, picked))
    print('模版图好了：out/模版总览.jpg（八个模版一张图），单张大图 out/模版一.jpg … 模版八.jpg（发给用户前自己先打开看一遍）')


if __name__ == '__main__':
    main()
