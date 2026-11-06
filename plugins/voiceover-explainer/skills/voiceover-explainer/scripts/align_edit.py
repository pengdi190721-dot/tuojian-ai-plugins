"""对稿 + 调节奏：把口播稿和录音一句一句对上，按画面节奏重排停顿，输出新的人声和逐字时间表。
用法：python3 align_edit.py 项目 [--强制]
先运行 transcribe.py。输出：
  work/对稿报告.txt   —— 哪些句子念得和稿子不一样、哪些地方多说了话（必须看）
  work/timeline.json —— 每句话每个字在新人声里的时间（画面和字幕都靠它）
  work/voice_edit.wav —— 调好节奏、音量拉平的人声
节奏规则：内容不剪、语速不动；句间停顿压到0.22–0.55秒；换段前停1.05秒；★金句前至少停0.55秒；片头留0.8秒，片尾留2.2秒。"""
import difflib, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import *

LEAD, TAIL = 0.8, 2.2


def align(d, force=False):
    secs, lines = parse_script(d)
    asr = json.loads((d / 'work' / 'asr.json').read_text(encoding='utf-8'))
    rec = []
    for s in asr['segs']:
        for tok, t in s['toks']:
            for ch in tok.strip().lower():
                if ch.strip() and ch not in PUNCT:
                    rec.append((ch, t))
    rs = ''.join(c for c, _ in rec)
    scr, owner = '', []
    for li, L in enumerate(lines):
        n = norm(L['text']); L['n0'] = len(scr); L['n'] = len(n); scr += n; owner += [li] * len(n)
    sm = difflib.SequenceMatcher(None, scr, rs, autojunk=False)
    m = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            m[a + k] = b + k
    tt = np.full(len(scr), np.nan)
    for a, b in m.items():
        tt[a] = rec[b][1]
    known = ~np.isnan(tt)
    if known.sum() < len(scr) * 0.5:
        sys.exit('【出错】录音和口播稿对上的字不到一半，可能录音文件放错了，或者口播稿不是这一版')
    tt = np.interp(np.arange(len(scr)), np.arange(len(scr))[known], tt[known])

    # ---------- 对稿报告 ----------
    report, bad = [], []
    for li, L in enumerate(lines):
        ks = [k for k in range(L['n0'], L['n0'] + L['n']) if k in m]
        L['ms'] = len(ks) / max(L['n'], 1)
        L['ct'] = tt[L['n0']:L['n0'] + L['n']].tolist()
        heard = rs[m[ks[0]]:m[ks[-1]] + 1] if ks else ''
        if L['ms'] < 0.85:
            report.append(f"{L['sec']}.{L['li']}  对上{L['ms']:.0%}\n   稿子：{L['text']}\n   听到：{heard or '（没听到）'}")
        if L['ms'] < 0.3:
            bad.append(f"{L['sec']}.{L['li']}")
    used = set(m.values())
    # 一句话中间识别不一样的字（比如英文名被听成同音字）不算多出来的话，只报句子和句子之间多出来的
    spans = []
    for L in lines:
        ks = [m[k] for k in range(L['n0'], L['n0'] + L['n']) if k in m]
        if ks:
            spans.append((ks[0], ks[-1]))
    inside = lambda a, b: any(s0 <= a and b <= s1 for s0, s1 in spans)
    extra, k = [], 0
    while k < len(rs):
        if k not in used:
            j = k
            while j < len(rs) and j not in used:
                j += 1
            if j - k >= 4 and not inside(k, j - 1):
                extra.append(f"  {rec[k][1]:.1f}–{rec[j - 1][1] + 0.3:.1f}秒：{rs[k:j]}")
            k = j
        else:
            k += 1
    with open(d / 'work' / '对稿报告.txt', 'w', encoding='utf-8') as f:
        f.write('一、和稿子差得比较多的句子（只列对上不到85%的。识别会把英文名、产品名听成同音字，比如 WorkBuddy 听成“乌克巴德”，这种不用管）\n')
        f.write('   处理办法：如果是真念得不一样，把 script.txt 改成实际念的，再重新运行 align_edit.py\n\n')
        f.write('\n'.join(report) if report else '   没有\n')
        f.write('\n\n二、录音里多出来、稿子里没有的话（可能是念错重来、口误、多说的）\n')
        f.write('   处理办法：要剪掉的，把时间段写进 work/剪掉.txt（每行一段，如 12.3-15.8），重新运行 transcribe.py 和 align_edit.py\n')
        f.write('   注意：这里的秒数是 voice_clean.wav 里的秒数；剪掉.txt 要写原始录音的秒数，第一次剪的时候两者一样\n\n')
        f.write('\n'.join(extra) if extra else '   没有\n')
    print(f'对稿报告：work/对稿报告.txt（{len(report)} 句和稿子不完全一样，{len(extra)} 处多出来的话）')
    if bad and not force:
        sys.exit(f'【出错】这几句好像没念：{"、".join(bad)}。请改稿子或补录，确认没问题再加 --强制 运行')

    # ---------- 找每句话的真实起止 ----------
    x = read_wav_mono(d / 'work' / 'voice_clean.wav', SR)
    x = x - np.mean(x)
    hop = SR // 100
    env = np.sqrt(np.convolve(x ** 2, np.ones(SR // 50) / (SR // 50), mode='same')[::hop] + 1e-12)
    db = 20 * np.log10(env)
    thr = np.percentile(db, 8) + 12

    def speech_end(t, limit):
        i, lim = int(t * 100), int(limit * 100)
        while i < lim:
            if np.all(db[i:i + 8] < thr):
                return i / 100
            i += 1
        return limit

    def speech_start(t, limit):
        i, lim = int(t * 100), int(limit * 100)
        while i > lim:
            if np.all(db[max(i - 8, 0):i] < thr):
                return i / 100
            i -= 1
        return limit

    N, dur = len(lines), len(x) / SR
    for i, L in enumerate(lines):
        prev_last = lines[i - 1]['ct'][-1] + 0.12 if i else 0
        nxt_first = lines[i + 1]['ct'][0] - 0.02 if i < N - 1 else dur
        L['s'] = speech_start(L['ct'][0] + 0.02, prev_last)
        L['e'] = speech_end(L['ct'][-1] + 0.14, nxt_first)
    cuts = [max(0, lines[0]['s'] - 0.06)]
    for i in range(N - 1):
        a, b = lines[i]['e'], lines[i + 1]['s']
        if b - a >= 0.16:
            cuts.append((a + 0.05, b - 0.05))
        else:  # 连着说的：在下一句开口前找最靠后的安静点（识别时间常偏早，避免切掉上一句尾字）
            lo, hi = int((lines[i]['ct'][-1] + 0.08) * 100), int((lines[i + 1]['ct'][0] + 0.08) * 100)
            hi = max(hi, lo + 1)
            win = db[lo:hi]
            k = lo + int(np.where(win < win.min() + 6)[0][-1])
            cuts.append((k / 100, k / 100))
    cuts.append(min(dur, lines[-1]['e'] + 0.12))

    # ---------- 重排停顿 ----------
    t_new, segs = LEAD, []
    for i, L in enumerate(lines):
        if i:
            g = min(max(L['s'] - lines[i - 1]['e'], 0.22), 0.55)
            if L['first']:
                g = 1.05
            if L['punch']:
                g = max(g, 0.55)
            t_new += g
        a = cuts[0] if i == 0 else cuts[i][1]
        b = cuts[i + 1][0] if i < N - 1 else cuts[-1]
        off = t_new - a
        L['nct'] = [round(t + off, 3) for t in L['ct']]
        L['ns'], L['ne'] = round(L['s'] + off, 3), round(L['e'] + off, 3)
        segs.append((a, b, t_new))
        t_new += b - a
    total = round(t_new + TAIL, 3)
    out = np.zeros(int(total * SR) + SR, dtype=np.float32)
    fade = int(0.012 * SR)
    for a, b, tn in segs:
        seg = x[int(a * SR):int(b * SR)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        p = int(tn * SR); out[p:p + len(seg)] += seg
    write_wav(d / 'work' / 'voice_edit_pre.wav', out[:int(total * SR)], SR)
    run_ff(['-i', d / 'work' / 'voice_edit_pre.wav', '-af', 'highpass=f=70,afftdn=nf=-30,loudnorm=I=-16:TP=-1.5:LRA=9',
            '-ar', SR, '-ac', 1, d / 'work' / 'voice_edit.wav'])
    tl = {'total': total, 'lines': [{'text': L['text'], 'nct': L['nct'], 'ns': L['ns'], 'ne': L['ne'], 'sec': L['sec'],
                                     'punch': L['punch']} for L in lines]}
    (d / 'work' / 'timeline.json').write_text(json.dumps(tl, ensure_ascii=False), encoding='utf-8')
    for f in ('final_audio.wav',):
        (d / 'work' / f).unlink(missing_ok=True)
    print(f'节奏调整完成：原录音 {dur:.1f} 秒 → 新人声 {total:.1f} 秒（work/voice_edit.wav）')
    return tl


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    align(proj_dir(args[0] if args else '.'), force='--强制' in sys.argv)
