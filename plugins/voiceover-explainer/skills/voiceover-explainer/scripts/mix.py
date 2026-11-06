"""音效：现场合成四种音效（不用网上素材，没有版权问题），按画面放好，压在人声下面。
  pop 啵（卡片、标签弹出）  ding 嘀（圈注出现）  whoosh 嗖（换段）  thud 咚（金句）
用法：python3 mix.py 项目   （先运行 render.py 项目 检查，生成 work/sfx.json）
输出：work/final_audio.wav（人声+音效，不含背景音乐）"""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import *

VOL = {'pop': 1.0, 'ding': 1.0, 'whoosh': 1.0, 'thud': 1.0}   # 想整体调大调小音效，改这里


def bank():
    rng = np.random.default_rng(7)
    env = lambda n, tau: np.exp(-np.arange(n) / (tau * SR))

    def pop():
        n = int(0.09 * SR); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * np.cumsum(320 + 700 * np.exp(-t / 0.018)) / SR) * env(n, 0.028)
        y[:96] *= np.linspace(0, 1, 96); return y * 0.11

    def ding():
        n = int(0.6 * SR); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1568 * t) + 0.35 * np.sin(2 * np.pi * 2349 * t) + 0.15 * np.sin(2 * np.pi * 3136 * t)
        e = env(n, 0.16); e[:192] *= np.linspace(0, 1, 192); return y * e * 0.05

    def whoosh():
        n = int(0.55 * SR); x = rng.standard_normal(n); t = np.arange(n) / n
        a = np.exp(-2 * np.pi * (300 + 2600 * t ** 1.5) / SR)
        y = np.zeros(n); prev = 0.0
        for i in range(n):
            prev = (1 - a[i]) * x[i] + a[i] * prev; y[i] = prev
        hp = (y - np.concatenate([[0], y[:-1]]) * 0.97) * np.sin(np.pi * t) ** 2
        return hp / (np.abs(hp).max() + 1e-9) * 0.13

    def thud():
        n = int(0.5 * SR); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * np.cumsum(52 + 70 * np.exp(-t / 0.05)) / SR) * env(n, 0.16)
        c = int(0.006 * SR); y[:c] += rng.standard_normal(c) * np.linspace(1, 0, c) * 0.25
        y[:144] *= np.linspace(0, 1, 144); return y * 0.34
    return {'pop': pop(), 'ding': ding(), 'whoosh': whoosh(), 'thud': thud()}


def mix(d):
    vp = d / 'work' / 'voice_edit.wav'
    if not vp.exists():
        sys.exit('【出错】还没有调好的人声，请先运行 align_edit.py')
    sp = d / 'work' / 'sfx.json'
    if not sp.exists():
        sys.exit('【出错】还没有音效清单，请先运行：python3 render.py 项目 检查')
    v = read_wav_mono(vp, SR)
    ev = json.loads(sp.read_text(encoding='utf-8'))
    B = bank()
    last, kept = {}, []
    for t, kind in ev:
        if kind in B and t - last.get(kind, -9) >= 0.15:
            last[kind] = t; kept.append((t, kind))
    fx = np.zeros(len(v) + SR, dtype=np.float32)
    for t, kind in kept:
        s = B[kind] * VOL.get(kind, 1.0); p = int(max(0, t + (-0.18 if kind == 'whoosh' else 0)) * SR)
        fx[p:p + len(s)] += s[:len(fx) - p]
    write_wav(d / 'work' / 'mix_raw.wav', v + fx[:len(v)], SR)
    run_ff(['-i', d / 'work' / 'mix_raw.wav', '-af', 'alimiter=limit=0.89:level=disabled', '-ac', 2, '-ar', SR, d / 'work' / 'final_audio.wav'])
    print('音效：', dict(Counter(k for _, k in kept)), '→ work/final_audio.wav')


if __name__ == '__main__':
    mix(proj_dir(sys.argv[1] if len(sys.argv) > 1 else '.'))
