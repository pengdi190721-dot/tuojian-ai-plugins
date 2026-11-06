"""风格预览：同一段画面，用四种风格各出一版，给老板挑。
用法：
  python3 style_preview.py 项目 --秒 40 52 58          # 每种风格在这几个时刻各截一张，拼成 out/风格预览.jpg
  python3 style_preview.py 项目 --秒 40 52 --片段 36 60 # 另外把 36–60 秒按四种风格各渲染一遍，接成 out/风格样片.mp4
  加 --竖 出竖版；加 --风格 qingshuang heijin 只出指定的几种。"""
import argparse, asyncio, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from build import build
from render import open_page, render_range

LABEL_JS = """(t)=>{const d=document.createElement('div');d.textContent=t;
d.style.cssText='position:absolute;right:28px;bottom:24px;z-index:99;background:rgba(0,0,0,.72);color:#fff;font:900 30px "Noto Sans CJK SC","PingFang SC",sans-serif;padding:10px 22px;border-radius:12px';
document.getElementById('stage').appendChild(d);}"""


async def shots(d, themes, orient, times):
    from playwright.async_api import async_playwright
    w, h = (1080, 1920) if orient == '竖' else (1920, 1080)
    od = d / 'work' / '风格'; od.mkdir(exist_ok=True)
    res = {}
    async with async_playwright() as p:
        for i, th in enumerate(themes):
            page, _ = build(d, th, orient, out=d / 'work' / f'preview_{th}.html', quiet=True)
            b, pg, errs = await open_page(p, page, w, h)
            await pg.evaluate(LABEL_JS, f'风格{"一二三四五六"[i]}：{THEMES[th]}')
            res[th] = []
            for t in times:
                await pg.evaluate(f'render({t})')
                f = od / f'{th}_{t:07.2f}.jpg'
                await pg.screenshot(path=str(f), type='jpeg', quality=85)
                res[th].append(f)
            await b.close()
    return res, w, h


def grid(res, themes, w, h, out):
    from PIL import Image
    cols = len(next(iter(res.values())))
    tw = 720 if w > h else 360
    th_ = int(tw * h / w)
    sheet = Image.new('RGB', (tw * cols + 10 * (cols - 1), th_ * len(themes) + 10 * (len(themes) - 1)), 'white')
    for r, t in enumerate(themes):
        for c, f in enumerate(res[t]):
            sheet.paste(Image.open(f).resize((tw, th_)), (c * (tw + 10), r * (th_ + 10)))
    sheet.save(out, quality=88)


async def clips(d, themes, orient, a, e):
    from playwright.async_api import async_playwright
    w, h = (1080, 1920) if orient == '竖' else (1920, 1080)
    parts = []
    for i, th in enumerate(themes):
        page = d / 'work' / f'preview_{th}.html'
        # 在页面里加上风格名角标
        html = page.read_text(encoding='utf-8').replace('<script>engineStart();</script>',
            f"<script>engineStart();({LABEL_JS})('风格{'一二三四五六'[i]}：{THEMES[th]}');</script>")
        page.write_text(html, encoding='utf-8')
        outp = d / 'work' / '风格' / f'clip_{th}.mp4'
        print(f'渲染 {THEMES[th]} ……', flush=True)
        await render_range(d, page, w, h, a, e, outp)
        parts.append(outp)
    lst = d / 'work' / '风格' / 'list.txt'
    lst.write_text(''.join(f"file '{p.name}'\n" for p in parts), encoding='utf-8')
    out = d / 'out' / '风格样片.mp4'
    silent = d / 'work' / '风格' / 'all.mp4'
    run_ff(['-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])
    voice = d / 'work' / 'voice_edit.wav'
    if voice.exists():
        # 有录音就配上老板自己的声音：每种风格放同一段
        seg = d / 'work' / '风格' / 'seg.wav'
        run_ff(['-ss', a, '-t', e - a, '-i', voice, '-ac', 2, '-ar', SR, seg])
        al = d / 'work' / '风格' / 'alist.txt'
        al.write_text("file 'seg.wav'\n" * len(parts), encoding='utf-8')
        run_ff(['-i', silent, '-f', 'concat', '-safe', '0', '-i', al, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out])
    else:
        run_ff(['-i', silent, '-c', 'copy', '-movflags', '+faststart', out])
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('项目')
    ap.add_argument('--秒', nargs='+', type=float, required=True)
    ap.add_argument('--片段', nargs=2, type=float)
    ap.add_argument('--风格', nargs='+', default=list(THEMES))
    ap.add_argument('--竖', action='store_true')
    a = ap.parse_args()
    d = proj_dir(a.项目)
    orient = '竖' if a.竖 else load_project(d)['画幅']
    res, w, h = asyncio.run(shots(d, a.风格, orient, a.秒))
    out = d / 'out' / ('风格预览_竖版.jpg' if orient == '竖' else '风格预览.jpg')
    grid(res, a.风格, w, h, out)
    print('风格预览图：', out, '（每一行是一种风格，从上到下：' + '、'.join(THEMES[t] for t in a.风格) + '）')
    if a.片段:
        print('风格样片：', asyncio.run(clips(d, a.风格, orient, *a.片段)))
