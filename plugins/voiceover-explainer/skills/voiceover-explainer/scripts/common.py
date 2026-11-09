"""口播剪辑助手 · 公共工具（路径、读项目、读口播稿、找剪辑工具、开浏览器）"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
# 语音识别模型放在用户目录里，技能升级也不用重下
MODELS = Path(os.environ.get('KOUBO_MODELS', Path.home() / '.voiceover-explainer' / 'models'))
THEMES = {'qingshuang': '清爽薄荷', 'heijin': '黑金发布会', 'baiban': '手绘白板', 'dazibao': '撞色大字报'}
PUNCT = '，。、；：？！“”‘’ ,.;:?!"\'★…—'
FPS = 30
SR = 48000


def norm(s):
    return ''.join(c.lower() for c in s if c not in PUNCT)


def ncount(s):
    return sum(1 for c in s if c not in PUNCT)


def proj_dir(arg=None):
    d = Path(arg or '.').resolve()
    if not (d / 'script.txt').exists():
        sys.exit(f'【出错】{d} 里没有 script.txt，请先用 new_project.py 建项目，或者确认项目目录写对了')
    (d / 'work').mkdir(exist_ok=True)
    (d / 'out').mkdir(exist_ok=True)
    return d


def load_project(d):
    p = d / 'project.json'
    cfg = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    cfg.setdefault('栏目标签', '老板问答')
    cfg.setdefault('系列名', '')
    cfg.setdefault('风格', 'qingshuang')
    cfg.setdefault('画幅', '横')
    cfg.setdefault('录音文件', '')
    if cfg['风格'] not in THEMES:
        sys.exit(f"【出错】风格「{cfg['风格']}」不存在，只能是：{'、'.join(f'{k}（{v}）' for k, v in THEMES.items())}")
    return cfg


def parse_script(d):
    """口播稿格式：# 段名（加【章】会显示在顶部进度条），下面每行一句；★开头的是金句；//开头的是备注，不念。"""
    secs = []
    for raw in (d / 'script.txt').read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('//'):
            continue
        if line.startswith('#'):
            name = line.lstrip('#').strip()
            chap = '【章】' in name
            secs.append({'name': name.replace('【章】', '').strip(), 'chapter': chap, 'lines': []})
            continue
        if not secs:
            secs.append({'name': '开头', 'chapter': False, 'lines': []})
        punch = line.startswith('★')
        secs[-1]['lines'].append({'text': line.lstrip('★').strip(), 'punch': punch})
    secs = [s for s in secs if s['lines']]
    if not secs:
        sys.exit('【出错】script.txt 里没有口播内容')
    flat = []
    for si, s in enumerate(secs):
        for j, L in enumerate(s['lines']):
            flat.append({**L, 'sec': si + 1, 'li': j + 1, 'first': j == 0, 'secname': s['name']})
    return secs, flat


def find_voice(d, cfg):
    if cfg.get('录音文件') and (d / cfg['录音文件']).exists():
        return d / cfg['录音文件']
    for ext in ('mp3', 'm4a', 'wav', 'aac', 'mp4', 'mov', 'flac', 'ogg'):
        c = sorted(d.glob(f'*.{ext}'))
        if c:
            return c[0]
    return None


def ffmpeg():
    f = shutil.which('ffmpeg')
    if f:
        return f
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit('【出错】找不到 ffmpeg。请运行：python3 scripts/check_env.py --install')


def run_ff(args):
    r = subprocess.run([ffmpeg(), '-y', '-loglevel', 'error'] + [str(a) for a in args])
    if r.returncode != 0:
        sys.exit('【出错】ffmpeg 运行失败：' + ' '.join(map(str, args[:6])))


def read_wav_mono(path, sr):
    """用 ffmpeg 把任意音频转成单声道浮点数组"""
    import numpy as np
    r = subprocess.run([ffmpeg(), '-loglevel', 'error', '-i', str(path), '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'],
                       stdout=subprocess.PIPE)
    if r.returncode != 0:
        sys.exit(f'【出错】读不了音频：{path}')
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768


def write_wav(path, x, sr, ch=1):
    import numpy as np, wave
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    if ch == 2:
        y = np.repeat(y[:, None], 2, axis=1).reshape(-1)
    with wave.open(str(path), 'w') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


async def open_browser(p):
    """优先用电脑上装好的谷歌浏览器，没有再用自带的"""
    tries = []
    env = os.environ.get('CHROME_PATH')
    if env:
        tries.append({'executable_path': env})
    tries += [{'channel': 'chrome'}, {}]
    for path in ['/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                 r'C:\Program Files\Google\Chrome\Application\chrome.exe', '/usr/bin/chromium']:
        if os.path.exists(path):
            tries.append({'executable_path': path})
    last = None
    for kw in tries:
        try:
            return await p.chromium.launch(args=['--force-color-profile=srgb', '--hide-scrollbars',
                                                 '--disable-lcd-text', '--font-render-hinting=none'], **kw)
        except Exception as e:
            last = e
    sys.exit(f'【出错】打不开浏览器：{last}\n请运行：python3 scripts/check_env.py --install')


def size_of(cfg):
    return (1080, 1920) if cfg.get('画幅') == '竖' else (1920, 1080)
