"""A 线第 1 步：收视频 → 统一成工作视频 → 逐字听写 → 找出可以剪的地方 → 抽几帧看画面。
用法：python3 video_prepare.py 项目目录
  - 视频放在项目目录里（几个文件就按文件名顺序拼），或在 project.json 的“视频文件”里按顺序写文件名
输出：
  work/src.mov        工作视频（竖版 1080×1920 或横版 1920×1080，声音和画面对齐到同一个起点）
  work/听写结果.txt    每段话的起止时间（原视频的秒数）和文字
  work/剪辑建议.txt    念错重来、语气词、开头结尾空白的建议，AI 看完写 剪掉.txt
  work/抽帧/          6 张画面，看光线、人脸位置
"""
import json, re, sys, difflib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *
from common import run_ff
from transcribe import model_paths, speech_segments

SR16 = 16000
FILLERS = set('呃嗯啊哦额唉诶')


def find_videos(d, cfg):
    if cfg.get('视频文件'):
        fs = [d / f for f in cfg['视频文件']]
        miss = [str(f.name) for f in fs if not f.exists()]
        if miss:
            sys.exit(f'【出错】project.json 里写的视频找不到：{"、".join(miss)}')
        return fs
    fs = sorted([p for p in d.iterdir() if p.suffix in VIDEO_EXT], key=lambda p: p.name)
    if not fs:
        sys.exit('【出错】项目目录里没有视频（mp4 / mov / m4v）。请把口播视频放进项目目录')
    return fs


def make_src(d, files):
    """统一尺寸、帧率；声音补齐到和画面同一个起点（手机视频的声音常比画面晚零点几秒，不补的话剪辑点会错位）"""
    pr = probe(files[0])
    orient = '竖' if pr['h'] > pr['w'] else '横'
    W, H = (1080, 1920) if orient == '竖' else (1920, 1080)
    fps = pick_fps(pr['fps_src'])
    vf = f'scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={fps},setsar=1'
    af = 'aresample=async=1:first_pts=0'
    parts = []
    for i, f in enumerate(files):
        out = d / 'work' / (f'part{i:02d}.mov' if len(files) > 1 else 'src.mov')
        p = probe(f)
        args = ['-i', f]
        if not p['audio']:
            args += ['-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=mono', '-shortest']
        args += ['-vf', vf, '-af', af, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p',
                 '-c:a', 'pcm_s16le', '-ar', str(SR), '-ac', '1', out]
        print(f'整理视频 {i + 1}/{len(files)}：{f.name}（{p["w"]}×{p["h"]}，{p["dur"]:.1f} 秒）…')
        run_ff(args)
        parts.append(out)
    if len(parts) > 1:
        lst = d / 'work' / 'parts.txt'
        lst.write_text('\n'.join(f"file '{p.as_posix()}'" for p in parts), encoding='utf-8')
        run_ff(['-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', d / 'work' / 'src.mov'])
    dur = probe(d / 'work' / 'src.mov')['dur']
    meta = {'W': W, 'H': H, 'orient': 'V' if orient == '竖' else 'H', '画幅': orient, 'fps': fps, 'dur': dur,
            'files': [f.name for f in files]}
    (d / 'work' / 'video.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return meta


def asr_file(wav16, out_json, out_txt):
    import sherpa_onnx
    y = read_wav_mono(wav16, SR16)
    m, tok = model_paths()
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=str(m), tokens=str(tok), num_threads=4, use_itn=False, language='zh')
    segs = []
    for a, b in speech_segments(y, SR16):
        s = rec.create_stream(); s.accept_waveform(SR16, y[int(a * SR16):int(b * SR16)]); rec.decode_stream(s)
        r = s.result
        toks = [(t.strip(), round(a + ts, 3)) for t, ts in zip(r.tokens, r.timestamps) if t.strip()]
        text = clean_text(''.join(t for t, _ in toks))
        if toks:
            segs.append({'start': round(a, 3), 'end': round(b, 3), 'text': text, 'toks': toks})
    Path(out_json).write_text(json.dumps({'segs': segs, 'dur': len(y) / SR16}, ensure_ascii=False), encoding='utf-8')
    with open(out_txt, 'w', encoding='utf-8') as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i:3d}  {s['start']:7.2f}–{s['end']:7.2f}  {s['text']}\n")
    return segs, len(y) / SR16


def clean_text(s):
    s = re.sub(r'(?i)a\s*i', 'AI', s)
    return s.replace(' ', '')


def norm(s):
    # 同音字当成一样，方便认出念错重来
    return re.sub(r'[^\w]', '', s).lower().translate(str.maketrans('它她地得', '他他的的'))


def suggest(segs, dur):
    """找可以剪的地方：念错重来（后面又说了一遍）、单独的语气词、开头结尾空白"""
    out = []
    if segs and segs[0]['start'] > 0.5:
        out.append((0, max(0, segs[0]['start'] - 0.15), '开头空白'))
    used = set()
    for i, s in enumerate(segs):
        t = norm(s['text'])
        if t and all(c in FILLERS for c in t):
            out.append((s['start'] - 0.05, s['end'] + 0.05, f'语气词“{s["text"]}”'))
            used.add(i)
            continue
        # 整段重来：后面 25 秒内有一段以差不多的话开头 → 剪前面这段（留最后一遍）
        for j in range(i + 1, len(segs)):
            if segs[j]['start'] - s['end'] > 25:
                break
            tj = norm(segs[j]['text'])
            if len(t) < 3 or not tj:
                continue
            head = tj[:len(t) + 2]
            r = difflib.SequenceMatcher(None, t, head).ratio()
            if (r >= 0.62 and t[0] == tj[0]) or (len(t) >= 4 and tj.startswith(t[:4]) and len(t) <= len(tj)):
                out.append((s['start'] - 0.05, segs[i + 1]['start'] - 0.12 if i + 1 < len(segs) else s['end'] + 0.1,
                            f'念错重来：“{s["text"]}”（后面 {fmt_t(segs[j]["start"])} 又说了一遍）'))
                used.add(i)
                break
        # 句尾重来：下一段开头重复了这段结尾的几个字 → 从重复的字开始剪
        if i not in used and i + 1 < len(segs) and segs[i + 1]['start'] - s['end'] < 4:
            nxt = norm(segs[i + 1]['text'])[:8]
            toks = [(norm(c), ts) for c, ts in s['toks'] if norm(c)]
            tail = ''.join(c for c, _ in toks)
            m = difflib.SequenceMatcher(None, tail, nxt).find_longest_match(max(0, len(tail) - 12), len(tail), 0, len(nxt))
            if m.size >= 3 and m.b <= 1 and m.a + m.size >= len(tail) - 2:
                # 找到 tail 第 m.a 个字对应的时间
                acc, ts0 = 0, None
                for c, ts in toks:
                    if acc >= m.a:
                        ts0 = ts; break
                    acc += len(c)
                if ts0:
                    out.append((ts0 - 0.06, segs[i + 1]['start'] - 0.12, f'句尾重来：“{tail[m.a:]}”说了两遍，留后一遍'))
    if segs and dur - segs[-1]['end'] > 2.5:
        out.append((segs[-1]['end'] + 1.5, dur, '结尾空白（留 1.5 秒给片尾卡）'))
    return out


def asr_missing():
    """听写要的东西缺什么；都齐了返回空"""
    try:
        import sherpa_onnx  # noqa: F401
    except Exception:
        return '没装 sherpa-onnx'
    try:
        model_paths()
    except SystemExit:
        return '没有语音识别模型'
    return ''


def no_asr(wav16, out_txt, why):
    """装不上听写时：只按声音找出每段说话的起止时间，照样能看开头结尾空白和长停顿"""
    y = read_wav_mono(wav16, SR16)
    segs = [{'start': round(a, 3), 'end': round(b, 3), 'text': '', 'toks': []} for a, b in speech_segments(y, SR16)]
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(f'# 听写跳过（{why}）。下面只有每段说话的起止时间，没有文字。装好后重跑 video_prepare.py 就会补上听写\n')
        for i, s in enumerate(segs, 1):
            f.write(f"{i:3d}  {s['start']:7.2f}–{s['end']:7.2f}  （没听写）\n")
    return segs, len(y) / SR16


def pauses(segs):
    return [(a['end'], b['start']) for a, b in zip(segs, segs[1:]) if b['start'] - a['end'] > 0.6]


def sample_frames(d, meta):
    import cv2
    ft = FaceTrack()
    (d / 'work' / '抽帧').mkdir(exist_ok=True)
    n, found, bright = 6, 0, []
    for k in range(n):
        t = meta['dur'] * (0.08 + 0.84 * k / (n - 1))
        img = next(read_frames(d / 'work' / 'src.mov', meta['W'], meta['H'], start=t, n=1))
        box = ft.find(img)
        ft.box = None
        if box is not None:
            found += 1
        bright.append(float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()))
        cv2.imwrite(str(d / 'work' / '抽帧' / f'{fmt_t(t).replace(":", "分")}秒.jpg'), cv2.resize(img, (meta['W'] // 3, meta['H'] // 3)))
    return found / n, float(np.mean(bright))


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.')
    cfg = load_cfg(d)
    files = find_videos(d, cfg)
    meta = make_src(d, files)
    if not cfg.get('画幅'):
        cfg['画幅'] = meta['画幅']
    cfg['视频文件'] = meta['files']
    save_cfg(d, cfg)
    run_ff(['-i', d / 'work' / 'src.mov', '-vn', '-ac', '1', '-ar', SR16, d / 'work' / 'a16.wav'])
    miss = asr_missing()
    if miss:
        print(f'听写跳过（{miss}），先按声音找停顿…')
        segs, dur = no_asr(d / 'work' / 'a16.wav', d / 'work' / '听写结果.txt', miss)
    else:
        print('听写中…')
        segs, dur = asr_file(d / 'work' / 'a16.wav', d / 'work' / 'asr_src.json', d / 'work' / '听写结果.txt')
    sug = suggest(segs, dur)
    ps = pauses(segs)
    with open(d / 'work' / '剪辑建议.txt', 'w', encoding='utf-8') as f:
        f.write('# 剪辑建议（自动找的，AI 必须对照 听写结果.txt 逐条判断，同意的抄进项目目录的 剪掉.txt）\n')
        if miss:
            f.write(f'# 这次听写跳过了（{miss}），只找了开头结尾空白和长停顿；念错重来、语气词要等听写后才找得出来\n')
        f.write('# 剪掉.txt 每行一段：开始秒-结束秒 说明，例如：9.10-13.60 第一遍“这个要看情况”\n')
        f.write('# 时间都是原视频的秒数；超过 0.6 秒的停顿不用写，剪辑时会自动压到 0.3 秒左右\n\n')
        for a, b, why in sug:
            f.write(f'{max(0, a):.2f}-{b:.2f}  {why}\n')
        f.write(f'\n# 另有 {len(ps)} 处超过 0.6 秒的停顿，会自动压短：\n')
        for a, b in ps:
            f.write(f'#   {fmt_t(a)}–{fmt_t(b)}（{b - a:.1f} 秒）\n')
    try:
        face, br = sample_frames(d, meta)
    except ImportError:
        face = br = None
    print(f"\n准备好了：{'、'.join(meta['files'])}，{meta['画幅']}版，{meta['fps']} 帧/秒，{dur:.1f} 秒，"
          + (f'说话 {len(segs)} 段（没听写）' if miss else f'听写 {len(segs)} 段'))
    print(f'剪辑建议 {len(sug)} 条，长停顿 {len(ps)} 处 → 看 work/听写结果.txt 和 work/剪辑建议.txt')
    if face is None:
        print('画面：没装 opencv，没抽帧（运行 check_env.py --install 装上）')
    else:
        print(f'画面：{face:.0%} 的抽帧找到人脸，平均亮度 {br:.0f}（低于 70 偏暗）→ 看 work/抽帧/')
        if face < 0.5:
            print('【注意】很多画面找不到人脸：可能是录屏或者人不在画面里，这条不做人像小窗，只用全屏版式')
        if br < 70:
            print('【注意】画面偏暗，按原样用；太暗的话在定方案时告诉用户可以考虑重拍')
    if miss:
        print(f'【听写跳过】{miss}，剪辑单只能先给开头结尾空白和长停顿。照守则硬规矩第 9 条：先把能定的发给用户'
              '（这部分剪辑单、模版图、画面情况），请他贴口播稿或逐字稿，或者在能联网的电脑上用 WorkBuddy 本地模式再发一次视频；'
              '装好后重跑本脚本就会补上听写。')


if __name__ == '__main__':
    main()
