"""给截图画坐标网格，方便读出圈注和推近的坐标（原图像素）。
用法：python3 grid.py 项目            # 给 assets 里每张截图各出一张带网格的图，存到 work/网格/
      python3 grid.py 项目 home.png   # 只出一张
红线是横坐标 x（每100一条细线、每500一条粗线），蓝线是纵坐标 y。读法：圈注 r:[左边x, 上边y, 宽, 高]。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import proj_dir
from PIL import Image, ImageDraw, ImageFont


def grid(src, out):
    im = Image.open(src).convert('RGB'); W, H = im.size
    d = ImageDraw.Draw(im)
    fs = max(18, W // 90)
    try:
        f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', fs)
    except Exception:
        try:
            f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
        except Exception:
            f = ImageFont.load_default()
    for x in range(0, W, 100):
        d.line([(x, 0), (x, H)], fill=(230, 0, 0) if x % 500 == 0 else (255, 160, 160), width=3 if x % 500 == 0 else 1)
        if x % 200 == 0:
            d.text((x + 4, 4), str(x), fill=(200, 0, 0), font=f)
    for y in range(0, H, 100):
        d.line([(0, y), (W, y)], fill=(0, 0, 230) if y % 500 == 0 else (160, 160, 255), width=3 if y % 500 == 0 else 1)
        if y % 200 == 0:
            d.text((4, y + 4), str(y), fill=(0, 0, 200), font=f)
    s = 1600 / max(W, H) if max(W, H) > 1600 else 1
    im.resize((int(W * s), int(H * s))).save(out, quality=85)
    print(f'{out}（原图 {W}×{H}）')


if __name__ == '__main__':
    d = proj_dir(sys.argv[1] if len(sys.argv) > 1 else '.')
    od = d / 'work' / '网格'; od.mkdir(exist_ok=True)
    files = [d / 'assets' / sys.argv[2]] if len(sys.argv) > 2 else sorted(p for p in (d / 'assets').iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'))
    for p in files:
        grid(p, od / (p.stem + '_网格.jpg'))
