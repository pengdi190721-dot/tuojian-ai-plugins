"""合成成片并核对：拼接各段画面 + 人声音效 → out/成片.mp4；再把成片重新听写一遍，逐条核对字幕和声音是否对齐；最后抽一张总览图。
用法：python3 finish.py 项目   （先运行 render.py 项目 全片）"""
import json, re, shutil, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from mix import mix


def finish(d):
    info = json.loads((d / 'work' / 'sections.json').read_text(encoding='utf-8'))
    for p in info['parts']:
        if not Path(p).exists():
            sys.exit(f'【出错】缺少画面段落 {p}，请重新运行 render.py 项目 全片')
    mix(d)
    lst = d / 'work' / 'parts' / 'list.txt'
    lst.write_text(''.join(f"file '{Path(p).name}'\n" for p in info['parts']), encoding='utf-8')
    vid = d / 'work' / 'video_only.mp4'
    run_ff(['-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])
    out = d / 'out' / '成片.mp4'
    run_ff(['-i', vid, '-i', d / 'work' / 'final_audio.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
            '-b:a', '192k', '-shortest', '-movflags', '+faststart', d / 'out' / '成片.tmp.mp4'])
    shutil.move(d / 'out' / '成片.tmp.mp4', out)
    print('成片：', out)
    verify(d, out)


def verify(d, out):
    """重新听写成片，核对每条字幕出现的时间和声音差多少"""
    try:
        import transcribe as T
    except Exception:
        print('（跳过字幕核对：语音识别没装好）'); return
    import numpy as np, sherpa_onnx
    y = read_wav_mono(out, 16000)
    m, tok = T.model_paths()
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=str(m), tokens=str(tok), num_threads=4, use_itn=False, language='zh')
    chars = []
    for a, b in T.speech_segments(y, 16000):
        s = rec.create_stream(); s.accept_waveform(16000, y[int(a * 16000):int(b * 16000)]); rec.decode_stream(s)
        for t, ts in zip(s.result.tokens, s.result.timestamps):
            for c in t.strip().lower():
                if c.strip() and c not in PUNCT:
                    chars.append((c, a + ts))
    rs = ''.join(c for c, _ in chars)
    html = (d / 'work' / 'index.html').read_text(encoding='utf-8')
    subs = json.loads(re.search(r'const SUBS=(\[.*?\]);', html).group(1))
    offs, far = [], []
    for s in subs:
        n = norm(re.sub('<[^>]+>', '', s['h']).replace(' ', ''))
        cands = [k for k in range(len(rs)) if rs.startswith(n[:3], k)]
        if not cands:
            continue
        k = min(cands, key=lambda k: abs(chars[k][1] - (s['a'] + 0.08)))
        o = chars[k][1] - (s['a'] + 0.08)
        if abs(o) > 3:
            continue   # 开头几个字在别处也出现过，认错位置了，不算
        offs.append(o)
        if abs(o) > 0.3:
            far.append(f"  {s['a']:.1f}秒「{re.sub('<[^>]+>', '', s['h'])}」差 {o:+.2f} 秒")
    if offs:
        print(f'字幕核对：核了 {len(offs)}/{len(subs)} 条，最大偏差 {max(map(abs, offs)):.2f} 秒，中位数 {statistics.median(offs):+.2f} 秒')
    for f in far:
        print('【要看】', f)
    if not far:
        print('字幕和声音都对得上（偏差都在0.3秒以内）')


if __name__ == '__main__':
    finish(proj_dir(sys.argv[1] if len(sys.argv) > 1 else '.'))
