"""出画面。
用法：
  python3 render.py 项目 检查              # 查画面脚本有没有写错（找不到的关键词、行号），并列出音效
  python3 render.py 项目 抽帧 12.5 30 61   # 指定秒数截图，存到 work/抽帧/
  python3 render.py 项目 总览 [段号]        # 每句话截一张，拼成总览图，用来逐句检查画面
  python3 render.py 项目 样片 开始秒 结束秒  # 渲染一小段（有录音就带声音），存到 out/样片.mp4
  python3 render.py 项目 全片              # 逐段渲染全片，存到 work/parts/，然后运行 finish.py 合成
可加 --风格 xxx / --竖 / --横 临时换风格或画幅。"""
import argparse, asyncio, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from build import build


async def open_page(p, page_path, w, h):
    b = await open_browser(p)
    pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(Path(page_path).as_uri())
    await pg.evaluate('document.fonts.ready.then(()=>true)')
    await pg.wait_for_function('Array.from(document.images).every(i=>i.complete)', timeout=30000)
    bad = await pg.evaluate('Array.from(document.images).filter(i=>!i.naturalWidth).map(i=>i.getAttribute("src"))')
    if bad:
        errs.append('这些截图在 assets 里找不到：' + '、'.join(sorted(set(bad))))
    return b, pg, errs


async def check(d, page, w, h):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b, pg, errs = await open_page(p, page, w, h)
        info = await pg.evaluate('window.info ? window.info() : null')
        if info is None:
            print('【出错】页面脚本没跑起来：', errs); await b.close(); return False
        sfx = await pg.evaluate('window.sfxList()')
        (d / 'work' / 'sfx.json').write_text(json.dumps(sfx), encoding='utf-8')
        await b.close()
    todo = [i + 1 for i, l in enumerate((d / 'scenes.html').read_text(encoding='utf-8').splitlines()) if 'TODO' in l] if (d / 'scenes.html').exists() else []
    if todo:
        errs.append(f'scenes.html 还有 {len(todo)} 处 TODO 没写（第 {"、".join(map(str, todo[:8]))} 行……）')
    ok = not info['ERRS'] and not errs
    for e in errs:
        print('【要改】', e)
    for e in info['ERRS']:
        print('【要改】', e)
    print('各段开始时间：', '  '.join(f'第{i + 1}段 {t:.1f}秒' for i, t in enumerate(info['sections'])))
    print(f'总长 {info["END"]:.1f} 秒，音效 {len(sfx)} 个。', '检查通过' if ok else '有问题要改，改完再检查')
    return ok


async def stills(d, page, w, h, times, tag='抽帧'):
    from playwright.async_api import async_playwright
    od = d / 'work' / '抽帧'; od.mkdir(exist_ok=True)
    outs = []
    async with async_playwright() as p:
        b, pg, _ = await open_page(p, page, w, h)
        for t in times:
            await pg.evaluate(f'render({t})')
            f = od / f'{tag}_{t:07.2f}.jpg'
            await pg.screenshot(path=str(f), type='jpeg', quality=82)
            outs.append((t, f))
        await b.close()
    return outs


def contact(items, out, w, h, cols=3):
    """把截图拼成一张总览图，每张左上角标上 段.行 和秒数"""
    from PIL import Image, ImageDraw, ImageFont
    tw = 640; th = int(tw * h / w)
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new('RGB', (tw * cols, th * rows), 'white')
    try:
        font = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 22)
    except Exception:
        try:
            font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 22)
        except Exception:
            font = ImageFont.load_default()
    for i, (label, f) in enumerate(items):
        im = Image.open(f).resize((tw, th))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 190, 34], fill='black'); dr.text((6, 4), label, fill='yellow', font=font)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out, quality=85)
    return out


async def overview(d, page, w, h, only_sec=None):
    secs, flat = parse_script(d)
    tl = json.loads((d / 'work' / 'timeline.json').read_text(encoding='utf-8'))
    pts = []
    for L, T in zip(flat, tl['lines']):
        if only_sec and L['sec'] != only_sec:
            continue
        # 每句话说到一半时截一张，这时这句话的画面都已经出来了
        t = T['nct'][len(T['nct']) // 2]
        pts.append((f"{L['sec']}.{L['li']}  {t:.1f}s", t))
    shots = await stills(d, page, w, h, [t for _, t in pts], tag='总览')
    files = []
    for k in range(0, len(pts), 6):
        out = d / 'work' / '抽帧' / f'总览_{k // 6 + 1:02d}.jpg'
        contact([(pts[i][0], shots[i][1]) for i in range(k, min(k + 6, len(pts)))], out, w, h)
        files.append(out)
    print('总览图：'); [print('  ', f) for f in files]
    print('请逐张打开看：字有没有被挡住、圈注是不是圈在对的地方、画面和这句话说的是不是一回事')


async def render_range(d, page, w, h, a, e, outp):
    from playwright.async_api import async_playwright
    f0, f1 = round(a * FPS), round(e * FPS)
    tmp = str(outp) + '.tmp.mp4'
    async with async_playwright() as p:
        b, pg, _ = await open_page(p, page, w, h)
        ff = subprocess.Popen([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg',
                               '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                               '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            await pg.evaluate(f'render({f / FPS})')
            ff.stdin.write(await pg.screenshot(type='jpeg', quality=92))
        ff.stdin.close()
        rc = ff.wait()
        await b.close()
    if rc != 0:
        sys.exit(f'【出错】渲染失败：{outp}')
    os.replace(tmp, outp)


async def full(d, page, w, h):
    info_p = d / 'work' / 'sections.json'
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b, pg, _ = await open_page(p, page, w, h)
        info = await pg.evaluate('window.info()')
        await b.close()
    bounds = info['sections'] + [info['END']]
    pdir = d / 'work' / 'parts'; pdir.mkdir(exist_ok=True)
    parts = []
    for i in range(len(bounds) - 1):
        outp = pdir / f'p{i + 1:02d}.mp4'
        print(f'渲染第{i + 1}段（{bounds[i]:.1f}–{bounds[i + 1]:.1f}秒）……', flush=True)
        await render_range(d, page, w, h, bounds[i], bounds[i + 1], outp)
        parts.append(str(outp))
    info_p.write_text(json.dumps({'parts': parts, 'bounds': bounds}), encoding='utf-8')
    print('全部段落渲染完成，下一步：python3 finish.py 项目')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('项目'); ap.add_argument('命令'); ap.add_argument('参数', nargs='*')
    ap.add_argument('--风格'); ap.add_argument('--竖', action='store_true'); ap.add_argument('--横', action='store_true')
    a = ap.parse_args()
    d = proj_dir(a.项目)
    cfg = load_project(d)
    orient = '竖' if a.竖 else ('横' if a.横 else cfg['画幅'])
    w, h = (1080, 1920) if orient == '竖' else (1920, 1080)
    page, tl = build(d, a.风格, orient, quiet=True)
    if a.命令 == '检查':
        ok = asyncio.run(check(d, page, w, h)); sys.exit(0 if ok else 1)
    elif a.命令 == '抽帧':
        outs = asyncio.run(stills(d, page, w, h, [float(x) for x in a.参数]))
        [print(f) for _, f in outs]
    elif a.命令 == '总览':
        asyncio.run(overview(d, page, w, h, int(a.参数[0]) if a.参数 else None))
    elif a.命令 == '样片':
        s, e = float(a.参数[0]), float(a.参数[1])
        outp = d / 'out' / '样片.mp4'
        asyncio.run(render_range(d, page, w, h, s, e, outp))
        audio = d / 'work' / 'final_audio.wav'
        if not audio.exists() and (d / 'work' / 'voice_edit.wav').exists():
            asyncio.run(check(d, page, w, h))
            from mix import mix
            mix(d)
        if audio.exists():
            tmp = d / 'out' / '样片_带声音.mp4'
            run_ff(['-i', outp, '-ss', s, '-t', e - s, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', tmp])
            os.replace(tmp, outp)
        print('样片：', outp)
    elif a.命令 == '全片':
        asyncio.run(full(d, page, w, h))
    else:
        sys.exit('命令只能是：检查 / 抽帧 / 总览 / 样片 / 全片')
