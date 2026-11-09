"""A 线第 2 步：用用户自己视频里的画面，出 4 张模版图（每张 = 人像全屏 + 要点卡加小窗）和一张四合一对比图。
用法：python3 video_templates.py 项目目录
需要：项目目录里的 模版图.json，例如
  {"标题": ["老员工一句", "“这个要看情况”"],
   "字幕": "企业AI落地，【最值钱】的一个数据",
   "要点卡": {"标题": "“看情况”，到底看什么？", "要点": ["看客户类型", "看订单金额", "什么情况直接处理", "什么情况必须找领导"], "亮第几条": 3},
   "小窗字幕": "什么情况可以【直接处理】"}
  栏目取 project.json 的“栏目”（没写就不放角标）
输出：out/模版一.jpg … out/模版四.jpg、out/四个模版对比.jpg"""
import asyncio, json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from video_render import Renderer
from video_build import chars_of

NAMES = ['模版一：清爽薄荷', '模版二：黑金发布会', '模版三：手绘白板', '模版四：撞色大字报']
FILES = ['模版一', '模版二', '模版三', '模版四']


def pick_frames(d, meta, k=2):
    """抽 18 帧，挑脸清楚、睁着眼、在画面中间的两帧（相隔 3 秒以上）"""
    import numpy as np
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
        sys.exit('【出错】抽了 18 帧都没找到人脸：这条可能是录屏，模版图请用全屏版式，或者先确认视频里有人')
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


def line_obj(text, n=1):
    cs = chars_of(text)
    return {'n': n, 'text': re.sub('[【】]', '', text), 'chars': [[c, 0.0, kw] for c, kw, _ in cs], 'start': 0.0, 'end': 100.0}


def fake_tl(meta, cfg, spec, kind):
    tl = {'fps': 24, 'end': 100, 'video_frames': 1, 'orient': meta['orient'], 'theme': 'qingshuang',
          'column': cfg.get('栏目', ''), 'title': None, 'pops': [], 'pip': [], 'cards': [], 'quotes': [], 'stamps': [],
          'cta': None, 'cuts': [], 'hide_sub': [], 'sfx': []}
    if kind == 'full':
        if spec.get('标题'):
            tl['title'] = {'t0': -1, 't1': 100, 'l1': spec['标题'][0], 'l2': spec['标题'][1]}
        tl['lines'] = [line_obj(spec.get('字幕', ''))]
    else:
        card = spec['要点卡']
        act = int(card.get('亮第几条', len(card['要点'])))
        tl['pip'] = [[-1, 100]]
        tl['cards'] = [{'t0': -1, 't1': 100, 'kind': 'rows', 'title': card['标题'],
                        'rows': [[r, -1 if i < act else 99] for i, r in enumerate(card['要点'])]}]
        tl['lines'] = [line_obj(spec.get('小窗字幕', ''))]
    return tl


async def render_all(d, meta, cfg, spec, picked):
    import cv2
    out = {}
    for kind, (score, t, img, box) in zip(('full', 'pip'), picked):
        fdir = d / 'work' / 'tpl' / kind
        fdir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(fdir / '00000.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
        tl = fake_tl(meta, cfg, spec, kind)
        for th in THEMES:
            tl['theme'] = th
            async with Renderer(d, tl, [box], fdir) as R:
                f = d / 'work' / 'tpl' / f'{th}_{kind}.jpg'
                await R.shot(24, f, 90)
                out[(th, kind)] = f
    return out


def compose(d, meta, shots):
    from PIL import Image, ImageDraw, ImageFont
    import glob
    fonts = glob.glob('/usr/share/fonts/**/NotoSansCJK*Bold*', recursive=True) + glob.glob('/System/Library/Fonts/PingFang.ttc') + \
        glob.glob('C:/Windows/Fonts/msyh*.tt*') + glob.glob('/usr/share/fonts/**/*CJK*', recursive=True)
    F = (lambda s: ImageFont.truetype(fonts[0], s)) if fonts else (lambda s: ImageFont.load_default())
    V = meta['orient'] == 'V'
    pw, ph = (540, 960) if V else (960, 540)
    caps = ['人像全屏：片头、金句、结尾', '要点卡 + 圆角小窗：讲要点']

    def tile(f, w, h, r):
        im = Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS)
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
        return im, m
    for i, th in enumerate(THEMES):
        if V:
            cv = Image.new('RGB', (40 + 2 * (pw + 40), 110 + ph + 70), (238, 238, 234))
        else:
            cv = Image.new('RGB', (40 + pw + 40, 110 + 2 * (ph + 70)), (238, 238, 234))
        dr = ImageDraw.Draw(cv)
        dr.text((40, 30), NAMES[i], font=F(44), fill=(30, 30, 30))
        for j, kind in enumerate(('full', 'pip')):
            im, m = tile(shots[(th, kind)], pw, ph, 36)
            X, Y = (40 + j * (pw + 40), 110) if V else (40, 110 + j * (ph + 70))
            cv.paste(im, (X, Y), m)
            f = F(30); w = dr.textlength(caps[j], font=f)
            dr.text((X + (pw - w) / 2, Y + ph + 16), caps[j], font=f, fill=(90, 90, 90))
        cv.save(d / 'out' / f'{FILES[i]}.jpg', quality=88)
    s = 0.62 if V else 0.42
    w, h = int(pw * s), int(ph * s)
    cv = Image.new('RGB', (40 + 4 * (w + 30) + 10, 100 + 2 * (h + 30) + 20), (238, 238, 234))
    dr = ImageDraw.Draw(cv)
    for i, th in enumerate(THEMES):
        X = 40 + i * (w + 30)
        f = F(30 if V else 26); tw = dr.textlength(NAMES[i], font=f)
        dr.text((X + (w - tw) / 2, 36), NAMES[i], font=f, fill=(30, 30, 30))
        for j, kind in enumerate(('full', 'pip')):
            im, m = tile(shots[(th, kind)], w, h, 24)
            cv.paste(im, (X, 100 + j * (h + 30)), m)
    cv.save(d / 'out' / '四个模版对比.jpg', quality=88)


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True)
    p = d / '模版图.json'
    if not p.exists():
        sys.exit('【出错】还没有 模版图.json，写法见本脚本开头的说明')
    spec = json.loads(p.read_text(encoding='utf-8'))
    if not spec.get('要点卡') or len(spec['要点卡'].get('要点', [])) < 2:
        sys.exit('【出错】模版图.json 的“要点卡”至少要 2 条要点')
    meta, cfg = info(d), load_cfg(d)
    picked = pick_frames(d, meta)
    print(f'挑了两帧：{fmt_t(picked[0][1])}（全屏用）、{fmt_t(picked[1][1])}（小窗用）')
    shots = asyncio.run(render_all(d, meta, cfg, spec, picked))
    compose(d, meta, shots)
    print('模版图好了：out/四个模版对比.jpg、out/模版一.jpg…模版四.jpg（发给用户前自己先打开看一遍）')


if __name__ == '__main__':
    main()
