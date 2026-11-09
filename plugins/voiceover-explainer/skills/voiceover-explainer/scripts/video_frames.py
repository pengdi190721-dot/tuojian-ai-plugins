"""A 线第 3 步之二：把剪好的视频拆成一帧帧图片，同时记下人脸位置（小窗跟着脸走），
剪辑点后面交替推近 8%，把跳剪藏起来。不做美颜，画面按原样用。
用法：python3 video_frames.py 项目目录
输出：work/frames/00000.jpg…、work/faces.json"""
import json, sys, time, os
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *

ZOOM = 1.08


def work(job):
    d, i, start, n, z = job
    import cv2, numpy as np
    d = Path(d)
    meta = info(d)
    W, H = meta['W'], meta['H']
    ft = FaceTrack()
    faces, cxy = [], None
    for k, img in enumerate(read_frames(d / 'work' / 'cut.mov', W, H, start=start, n=n)):
        box = ft.find(img)
        bx = box if box is not None else np.array([W * .3, H * .3, W * .4, W * .4])
        c = np.array([bx[0] + bx[2] / 2, bx[1] + bx[3] / 2])
        cxy = c if cxy is None else cxy * 0.9 + c * 0.1
        if z != 1.0:
            cw, ch = W / z, H / z
            x0 = float(np.clip(cxy[0] - cw / 2, 0, W - cw)); y0 = float(np.clip(cxy[1] - ch * 0.42, 0, H - ch))
            M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
            img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC)
            fb = [(bx[0] - x0) * z, (bx[1] - y0) * z, bx[2] * z, bx[3] * z]
        else:
            fb = [float(v) for v in bx]
        cv2.imwrite(str(d / 'work' / 'frames' / f'{i + k:05d}.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
        faces.append([round(float(v), 1) for v in fb])
    return i, faces


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True)
    meta = info(d)
    cut = json.loads((d / 'work' / 'cut.json').read_text(encoding='utf-8'))
    out = d / 'work' / 'frames'
    out.mkdir(exist_ok=True)
    for f in out.glob('*.jpg'):
        f.unlink()
    jobs, acc = [], 0
    for si, n in enumerate(cut['seg_frames']):
        jobs.append((str(d), acc, acc / meta['fps'], n, 1.0 if si % 2 == 0 else ZOOM))
        acc += n
    t = time.time()
    with Pool(max(1, min(4, (os.cpu_count() or 2)))) as pool:
        res = dict(pool.map(work, jobs))
    faces = []
    for _, i, *_ in jobs:
        faces += res[i]
    json.dump({'faces': faces, 'seg_frames': cut['seg_frames']}, open(d / 'work' / 'faces.json', 'w'))
    print(f'拆帧完成：{len(faces)} 帧，用时 {time.time() - t:.0f} 秒')
    if len(faces) != cut['frames']:
        print(f'【注意】帧数 {len(faces)} 和剪辑记录 {cut["frames"]} 不一致，重新运行一次 video_cut.py')


if __name__ == '__main__':
    main()
