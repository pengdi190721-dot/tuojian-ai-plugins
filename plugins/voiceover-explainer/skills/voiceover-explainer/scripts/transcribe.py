"""听写录音：识别出每个字在第几秒说的（用 SenseVoice 中文识别模型，离线运行）。
用法：python3 transcribe.py 项目 [录音文件]
  - 默认读 project.json 里的“录音文件”，没写就找项目目录里第一个音频/视频文件
  - 如果 work/剪掉.txt 里写了要剪掉的时间段（每行一段，例如 12.3-15.8，按原始录音的秒数），会先剪掉再听写
输出：work/asr.json（逐字时间）、work/voice_clean.wav（剪过的录音，后面对齐用）、work/听写结果.txt（给人看）"""
import json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import *

SR16 = 16000


def model_paths():
    d = next((p for p in MODELS.glob('sherpa-onnx-sense-voice-*') if p.is_dir()), None)
    if not d:
        sys.exit(f'【出错】还没有语音识别模型。请先运行：python3 scripts/check_env.py --download\n（模型放在 {MODELS}）')
    m = d / 'model.int8.onnx'
    if not m.exists():
        m = d / 'model.onnx'
    return m, d / 'tokens.txt'


def apply_cuts(x, sr, cut_file):
    if not cut_file.exists():
        return x, []
    spans = []
    for line in cut_file.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\s*([\d.]+)\s*[-~—到]\s*([\d.]+)', line)
        if m:
            spans.append((float(m.group(1)), float(m.group(2))))
    keep = np.ones(len(x), dtype=bool)
    for a, b in spans:
        keep[int(a * sr):int(b * sr)] = False
    print(f'按 剪掉.txt 剪掉 {len(spans)} 段，共 {sum(b - a for a, b in spans):.1f} 秒')
    return x[keep], spans


def speech_segments(x, sr):
    """按音量找出说话的段落（不用额外模型），太长的在最安静处切开，每段不超过12秒"""
    hop = sr // 100
    e = np.sqrt(np.convolve(x ** 2, np.ones(sr // 40) / (sr // 40), mode='same')[::hop] + 1e-12)
    db = 20 * np.log10(e)
    floor = np.percentile(db, 10)
    sp = db > floor + 10
    # 补上短于0.25秒的停顿，去掉短于0.12秒的杂音
    i, n = 0, len(sp)
    runs = []
    while i < n:
        j = i
        while j < n and sp[j] == sp[i]:
            j += 1
        runs.append([sp[i], i, j]); i = j
    for r in runs:
        if not r[0] and r[2] - r[1] < 25 and r[1] > 0 and r[2] < n:
            sp[r[1]:r[2]] = True
    segs, i = [], 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]:
                j += 1
            if j - i >= 12:
                segs.append((max(0, i - 10) / 100, min(n, j + 10) / 100))
            i = j
        else:
            i += 1

    def split(a, b):
        if b - a <= 12:
            return [(a, b)]
        i0, i1 = int((a + (b - a) * .3) * 100), int((a + (b - a) * .7) * 100)
        k = i0 + int(np.argmin(np.convolve(db[i0:i1], np.ones(20) / 20, mode='same')))
        return split(a, k / 100) + split(k / 100, b)
    out = []
    for a, b in segs:
        out += split(a, b)
    return out


def transcribe(d, src=None):
    import sherpa_onnx
    cfg = load_project(d)
    src = Path(src) if src else find_voice(d, cfg)
    if not src or not Path(src).exists():
        sys.exit('【出错】找不到录音。请把录音放进项目目录，或在 project.json 里写上“录音文件”')
    x = read_wav_mono(src, SR)
    x, spans = apply_cuts(x, SR, d / 'work' / '剪掉.txt')
    write_wav(d / 'work' / 'voice_clean.wav', x, SR)
    y = read_wav_mono(d / 'work' / 'voice_clean.wav', SR16)
    m, tok = model_paths()
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=str(m), tokens=str(tok), num_threads=4, use_itn=False, language='zh')
    out = []
    segs = speech_segments(y, SR16)
    for a, b in segs:
        s = rec.create_stream(); s.accept_waveform(SR16, y[int(a * SR16):int(b * SR16)]); rec.decode_stream(s)
        r = s.result
        out.append({'start': round(a, 3), 'end': round(b, 3), 'text': r.text,
                    'toks': [(t, round(a + ts, 3)) for t, ts in zip(r.tokens, r.timestamps)]})
    dur = len(y) / SR16
    (d / 'work' / 'asr.json').write_text(json.dumps({'segs': out, 'dur': dur, 'src': str(src)}, ensure_ascii=False), encoding='utf-8')
    with open(d / 'work' / '听写结果.txt', 'w', encoding='utf-8') as f:
        for o in out:
            f.write(f"{o['start']:7.2f}–{o['end']:7.2f}  {o['text']}\n")
    print(f'听写完成：录音 {dur:.1f} 秒，{len(out)} 段。结果见 work/听写结果.txt')
    return out


if __name__ == '__main__':
    d = proj_dir(sys.argv[1] if len(sys.argv) > 1 else '.')
    transcribe(d, sys.argv[2] if len(sys.argv) > 2 else None)
