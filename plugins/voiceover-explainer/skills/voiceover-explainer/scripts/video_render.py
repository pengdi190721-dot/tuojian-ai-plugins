"""A 线：渲染包装后的画面。
用法：
  python3 video_render.py 项目 总览            # 每句字幕截一张图，拼成 work/总览_1.jpg…，一张张看
  python3 video_render.py 项目 抽帧 12.5 30     # 看某几秒
  python3 video_render.py 项目 样片 10 20       # 出 10–20 秒带声音的样片 out/样片.mp4
  python3 video_render.py 项目 全片             # 渲染全片画面 work/render.mp4（之后跑 video_finish.py）"""
import asyncio, json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from common import open_browser, run_ff


def page_html():
    try:
        from engine_assets import KOUBO_PAGE
        return KOUBO_PAGE
    except ImportError:
        return (Path(__file__).resolve().parents[3] / 'engine-src' / 'koubo.html').read_text(encoding='utf-8')


def smooth_faces(faces, seg_frames):
    """小窗用的人脸位置：每段内部再平滑，换段重来，小窗不抖"""
    out, k = [], 0
    for n in seg_frames:
        seg = faces[k:k + n]; k += n
        if not seg:
            continue
        s = list(seg[0])
        for f in seg:
            s = [a * 0.92 + b * 0.08 for a, b in zip(s, f)]
            out.append([round(v, 1) for v in s])
    return out


class Renderer:
    def __init__(self, d, tl, faces, framedir):
        self.d, self.tl, self.faces, self.framedir = d, tl, faces, framedir
        self.W, self.H = (1080, 1920) if tl['orient'] == 'V' else (1920, 1080)

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().start()
        self.b = await open_browser(self.pw)
        self.pg = await self.b.new_page(viewport={'width': self.W, 'height': self.H})
        page = self.d / 'work' / 'page.html'
        page.write_text(page_html(), encoding='utf-8')
        await self.pg.goto(page.as_uri())
        await self.pg.wait_for_timeout(300)
        await self.pg.evaluate('([a,b,c]) => init(a,b,c)', [self.tl, self.faces, Path(self.framedir).resolve().as_uri() + '/'])
        return self

    async def shot(self, fi, path=None, quality=92):
        await self.pg.evaluate('f => frame(f)', fi)
        return await self.pg.screenshot(path=str(path) if path else None, type='jpeg', quality=quality)

    async def __aexit__(self, *a):
        await self.b.close(); await self.pw.stop()


def sheet(items, out, W, H, cols=6):
    from PIL import Image, ImageDraw
    w = 270 if W < H else 480
    h = int(w * H / W)
    rows = (len(items) + cols - 1) // cols
    g = Image.new('RGB', (cols * w, rows * h), 'white')
    dr = ImageDraw.Draw(g)
    for i, (t, f) in enumerate(items):
        x, y = (i % cols) * w, (i // cols) * h
        g.paste(Image.open(f).resize((w, h)), (x, y))
        dr.rectangle([x, y, x + 74, y + 24], fill='black'); dr.text((x + 6, y + 6), f'{t:.2f}s', fill='white')
    g.save(out, quality=85)


async def run(d, mode, args):
    tl = json.loads((d / 'work' / 'tl.json').read_text(encoding='utf-8'))
    fj = json.loads((d / 'work' / 'faces.json').read_text(encoding='utf-8'))
    faces = smooth_faces(fj['faces'], fj['seg_frames'])
    fps = tl['fps']
    N = round(tl['end'] * fps)
    async with Renderer(d, tl, faces, d / 'work' / 'frames') as R:
        if mode in ('总览', '抽帧'):
            if mode == '总览':
                times = [0.6] + [round((L['start'] + L['end']) / 2 + 0.25, 2) for L in tl['lines']] + [round(tl['end'] - 0.5, 2)]
            else:
                times = [float(a) for a in args]
            cdir = d / 'work' / '抽帧检查'
            cdir.mkdir(exist_ok=True)
            items = []
            for t in times:
                f = cdir / f'{t:07.2f}.jpg'
                await R.shot(min(N - 1, int(round(t * fps))), f, 85)
                items.append((t, f))
            name = '总览' if mode == '总览' else '抽帧'
            for k in range(0, len(items), 12):
                sheet(items[k:k + 12], d / 'work' / f'{name}_{k // 12 + 1}.jpg', R.W, R.H, cols=6 if R.W < R.H else 4)
            print(f'{name} {len(items)} 张 → work/{name}_*.jpg（一张张打开看）')
            return
        a, b = (0, N) if mode == '全片' else (int(float(args[0]) * fps), min(N, int(float(args[1]) * fps)))
        out = d / 'work' / ('render.mp4' if mode == '全片' else 'sample_v.mp4')
        ff = subprocess.Popen([ffmpeg(), '-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', str(fps), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', str(out)], stdin=subprocess.PIPE)
        t0 = time.time()
        for fi in range(a, b):
            ff.stdin.write(await R.shot(fi))
            if (fi - a) % (fps * 10) == 0:
                print(f'  {fi - a}/{b - a} 帧  {time.time() - t0:.0f} 秒', flush=True)
        ff.stdin.close(); ff.wait()
        print(f'画面渲染完成：{(b - a) / fps:.1f} 秒，用时 {time.time() - t0:.0f} 秒')
    if mode == '样片':
        run_ff(['-i', out, '-ss', f'{a / fps:.3f}', '-t', f'{(b - a) / fps:.3f}', '-i', d / 'work' / 'cut.mov', '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac', '-shortest', d / 'out' / '样片.mp4'])
        print('样片：out/样片.mp4')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    d = proj(sys.argv[1], need_src=True)
    asyncio.run(run(d, sys.argv[2], sys.argv[3:]))
