"""A 线第 3 步之一：按 剪掉.txt 剪视频，自动去掉开头结尾空白、把超过 0.6 秒的停顿压到 0.3 秒左右，
每个剪辑点都挪到没声音的地方；剪完再听写一遍，给出字幕稿草稿。
用法：python3 video_cut.py 项目目录
需要：项目目录里的 剪掉.txt（每行“开始秒-结束秒 说明”，原视频的秒数；没有就只做自动部分）
输出：work/cut.mov、work/cut.json、work/剪后听写.txt、work/字幕稿_草稿.txt、work/剪辑点检查.txt"""
import json, re, sys, os
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from common import run_ff
from video_prepare import asr_file, SR16

PAD = 0.06          # 说话前后再留的余量（听写分段本身已经前后各留了 0.1 秒）
JOIN = 0.28         # 两段之间（加上余量后）不到这么长就不剪开，相当于原停顿不到 0.6 秒
TAIL = 1.5          # 最后一句后面留给片尾卡的时间（有画面的话）


def read_cuts(d):
    p = d / '剪掉.txt'
    spans = []
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            m = re.match(r'\s*([\d.]+)\s*[-~—到]\s*([\d.]+)', line)
            if m:
                a, b = float(m.group(1)), float(m.group(2))
                if b > a:
                    spans.append((a, b))
    return sorted(spans)


def keep_spans(segs, cuts, dur):
    """说话段减去要剪的部分，前后留余量，停顿短的连起来"""
    pieces = []
    for s in segs:
        a, b = s['start'], s['end']
        parts = [(a, b)]
        for ca, cb in cuts:
            nxt = []
            for x, y in parts:
                if cb <= x or ca >= y:
                    nxt.append((x, y))
                else:
                    if ca > x: nxt.append((x, ca))
                    if cb < y: nxt.append((cb, y))
            parts = nxt
        pieces += [p for p in parts if p[1] - p[0] > 0.12]
    pieces.sort()
    keep = []
    for a, b in pieces:
        a2, b2 = max(0, a - PAD), min(dur, b + PAD)
        # 余量不能伸进要剪的部分
        for ca, cb in cuts:
            if ca < a <= cb + PAD: a2 = max(a2, cb)
            if ca - PAD <= b < cb: b2 = min(b2, ca)
        if keep and a2 - keep[-1][1] <= JOIN:
            keep[-1][1] = b2
        else:
            keep.append([a2, b2])
    return keep


def snap(keep, db, fps, dur):
    """剪辑点挪到最安静的地方，再对齐到整帧"""
    def quiet(t0, t1):
        i0, i1 = max(0, int(t0 * 100)), min(len(db) - 1, int(t1 * 100))
        if i1 <= i0:
            return t0
        return (i0 + int(np.argmin(db[i0:i1 + 1]))) / 100
    out = []
    for a, b in keep:
        a = quiet(a - 0.08, a + 0.03)
        b = quiet(b - 0.03, b + 0.08)
        a, b = round(a * fps) / fps, round(b * fps) / fps
        if b - a >= 2 / fps:
            out.append([a, min(b, dur)])
    return out


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True)
    meta = info(d)
    fps = meta['fps']
    asr = json.loads((d / 'work' / 'asr_src.json').read_text(encoding='utf-8'))
    segs, dur = asr['segs'], asr['dur']
    x = read_wav_mono(d / 'work' / 'a16.wav', SR16)
    db = energy_db(x, SR16)
    speech = float(np.percentile(db[db > np.percentile(db, 60)], 50))
    cuts = read_cuts(d)
    keep = keep_spans(segs, cuts, dur)
    if not keep:
        sys.exit('【出错】剪完什么都不剩了，检查 剪掉.txt')
    # 片尾：最后一句后面留一点画面给片尾卡（原视频有的话）
    keep[-1][1] = min(dur - 0.05, keep[-1][1] + TAIL)
    keep = snap(keep, db, fps, dur)
    # 剪辑点检查：切点前后 40 毫秒的音量，接近说话音量说明切到字了
    rep, warn = [], 0
    for i, (a, b) in enumerate(keep):
        ea = db[max(0, int(a * 100) - 4):int(a * 100) + 4].max()
        eb = db[max(0, int(b * 100) - 4):int(b * 100) + 4].max()
        flag = ''
        if (i > 0 and ea > speech - 15) or (i < len(keep) - 1 and eb > speech - 15):
            flag = '  【要听】切点附近有声音，可能切到字'; warn += 1
        rep.append(f'{i + 1:2d}  {fmt_t(a)} – {fmt_t(b)}   起点音量 {ea:5.0f}  终点音量 {eb:5.0f}（说话约 {speech:.0f}）{flag}')
    (d / 'work' / '剪辑点检查.txt').write_text('\n'.join(rep), encoding='utf-8')
    # 逐段剪出来再拼（每段帧数和声音长度严格一样，拼起来不会音画错位）
    segdir = d / 'work' / 'seg'
    segdir.mkdir(exist_ok=True)
    for f in segdir.glob('*.mov'):
        f.unlink()
    lst, frames, acc, cuts_at = [], [], 0, []
    for i, (a, b) in enumerate(keep):
        n = round((b - a) * fps); dd = n / fps
        f = segdir / f'{i:03d}.mov'
        run_ff(['-ss', f'{a:.4f}', '-i', d / 'work' / 'src.mov', '-frames:v', n, '-t', f'{dd:.4f}',
                '-af', f'apad,atrim=0:{dd:.4f},afade=t=in:d=0.012,afade=t=out:st={dd - 0.012:.4f}:d=0.012',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', fps,
                '-c:a', 'pcm_s16le', '-ar', SR, f])
        lst.append(f"file '{f.as_posix()}'"); frames.append(n); acc += n; cuts_at.append(round(acc / fps, 3))
    (segdir / 'list.txt').write_text('\n'.join(lst), encoding='utf-8')
    run_ff(['-f', 'concat', '-safe', '0', '-i', segdir / 'list.txt', '-c', 'copy', d / 'work' / 'cut.mov'])
    json.dump({'keep': keep, 'seg_frames': frames, 'frames': acc, 'cuts_at': cuts_at[:-1], 'dur': acc / fps},
              open(d / 'work' / 'cut.json', 'w'), indent=1)
    run_ff(['-i', d / 'work' / 'cut.mov', '-vn', '-ac', '1', '-ar', SR16, d / 'work' / 'cut16.wav'])
    print('剪完了，重新听写…')
    segs2, _ = asr_file(d / 'work' / 'cut16.wav', d / 'work' / 'asr_cut.json', d / 'work' / '剪后听写.txt')
    draft(d, segs2)
    print(f'剪完：原视频 {dur:.1f} 秒 → {acc / fps:.1f} 秒，{len(keep)} 段，剪辑点 {len(keep) - 1} 个')
    print('剪辑点检查见 work/剪辑点检查.txt' + (f'，有 {warn} 处【要听】' if warn else '，都落在没声音的地方'))
    print('下一步：照 work/字幕稿_草稿.txt 改出 字幕稿.txt，再写 包装.json')


def draft(d, segs):
    """按停顿把听写断成一行一句（每行不超过 14 个字），给 AI 改成字幕稿"""
    out = []
    for s in segs:
        toks = [(t if t.lower() not in ('a', 'i') else t.upper(), ts) for t, ts in s['toks']]
        cur, last = [], None
        for t, ts in toks:
            n = len(''.join(c for c, _ in cur))
            gap = ts - last if last is not None else 0
            if cur and ((gap > 0.24 and n >= 4) or n >= 14):
                out.append(''.join(c for c, _ in cur)); cur = []
            cur.append((t, ts)); last = ts
        if cur:
            out.append(''.join(c for c, _ in cur))
    text = '\n'.join(out).replace('AI', 'AI')
    (d / 'work' / '字幕稿_草稿.txt').write_text(
        '// 按停顿自动断的行，AI 要改：听错的字、标点、的地得、指东西用“它”；重点词用【】括起来（每行最多一处）；一行不超过 14 个字\n'
        '// 不许增删说的话：字幕要和声音一字一字对得上\n' + text + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
