"""A 线收尾：人声拉平到 -16、配音效（不加背景音乐）、合成成片、出字幕文件，再把成片重新听写一遍核对字幕。
用法：python3 video_finish.py 项目目录
输出：out/成片.mp4、out/字幕.srt；核对结果打印出来，“【要看】”的地方去对应秒数看一眼"""
import json, re, sys, difflib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from common import run_ff
from mix import bank, VOL
from video_prepare import asr_file, SR16

GAIN = {'pop': 0.55, 'ding': 0.6, 'whoosh': 0.5, 'thud': 0.45}
OFFSET = {'whoosh': -0.18}


def mix(d, tl):
    run_ff(['-i', d / 'work' / 'cut.mov', '-vn', '-ac', '1', '-ar', SR, d / 'work' / 'voice48.wav'])
    v = read_wav_mono(d / 'work' / 'voice48.wav', SR)
    N = int(tl['end'] * SR) + SR // 2
    voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]
    fx = np.zeros(N, np.float32)
    B = bank()
    for name, t in tl['sfx']:
        s = B[name] * GAIN.get(name, .5) * VOL.get(name, 1)
        i = int((t + OFFSET.get(name, 0)) * SR)
        if i < 0: s = s[-i:]; i = 0
        j = min(N, i + len(s)); fx[i:j] += s[:j - i]
    write_wav(d / 'work' / 'voice_pad.wav', voice, SR); write_wav(d / 'work' / 'fx.wav', fx, SR)
    run_ff(['-i', d / 'work' / 'voice_pad.wav', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', SR, d / 'work' / 'voice_norm.wav'])
    run_ff(['-i', d / 'work' / 'voice_norm.wav', '-i', d / 'work' / 'fx.wav', '-filter_complex',
            '[0:a][1:a]amix=inputs=2:normalize=0,volume=1dB,alimiter=limit=0.89[a]', '-map', '[a]', '-ar', SR,
            '-t', f"{tl['end']:.3f}", d / 'work' / 'final_audio.wav'])


def srt(d, tl):
    L = tl['lines']

    def ts(x):
        ms = int(round(max(0, x) * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    out = []
    for i, l in enumerate(L):
        st = l['start'] - 0.05
        en = min(L[i + 1]['start'] - 0.07 if i + 1 < len(L) else tl['end'], l['end'] + 0.5)
        out.append(f"{i + 1}\n{ts(st)} --> {ts(en)}\n{l['text']}\n")
    (d / 'out' / '字幕.srt').write_text('\n'.join(out), encoding='utf-8')


def verify(d, tl, out):
    run_ff(['-i', out, '-vn', '-ac', '1', '-ar', SR16, d / 'work' / 'final16.wav'])
    segs, _ = asr_file(d / 'work' / 'final16.wav', d / 'work' / 'asr_final.json', d / 'work' / '成片听写.txt')
    canon = lambda s: re.sub(r'[^\w]', '', s).lower().translate(str.maketrans('地得它她', '的的他他'))
    heard = canon(''.join(s['text'] for s in segs))
    bad = 0
    for l in tl['lines']:
        t = canon(l['text'])
        if not t:
            continue
        m = difflib.SequenceMatcher(None, t, heard, autojunk=False).find_longest_match(0, len(t), 0, len(heard))
        if m.size / len(t) < 0.85:
            bad += 1
            print(f"【要看】{fmt_t(l['start'])} 字幕「{l['text']}」和成片声音只对上 {m.size / len(t):.0%}（多半是同音字听错，确认一下）")
    print('字幕核对：' + ('全部对上' if not bad else f'{bad} 条要看'))


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True)
    tl = json.loads((d / 'work' / 'tl.json').read_text(encoding='utf-8'))
    if not (d / 'work' / 'render.mp4').exists():
        sys.exit('【出错】还没渲染画面。先运行：python3 scripts/video_render.py 项目 全片')
    mix(d, tl)
    out = d / 'out' / '成片.mp4'
    run_ff(['-i', d / 'work' / 'render.mp4', '-i', d / 'work' / 'final_audio.wav', '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out])
    srt(d, tl)
    print(f'成片：out/成片.mp4（{tl["end"]:.1f} 秒）、字幕：out/字幕.srt')
    verify(d, tl, out)


if __name__ == '__main__':
    main()
