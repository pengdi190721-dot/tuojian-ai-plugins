"""口播剪辑（A 线）公共工具：项目、读视频信息、人脸检测、按画面切段。"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ffmpeg, THEMES, SR, MODELS, read_wav_mono, write_wav  # noqa

VIDEO_EXT = ('.mp4', '.mov', '.m4v', '.MP4', '.MOV', '.M4V')
DEFAULT = {'类型': '口播剪辑', '风格': 'qingshuang', '画幅': '', '栏目': '', '片尾': '评论区聊聊吧', '视频文件': []}
COLUMNS = ['老板踩坑实录', '老板问答', '部门实测', 'WorkBuddy基础应用']


def proj(arg=None, need_src=False):
    d = Path(arg or '.').resolve()
    d.mkdir(parents=True, exist_ok=True)
    for sub in ('work', 'out', 'assets'):
        (d / sub).mkdir(exist_ok=True)
    if need_src and not (d / 'work' / 'src.mov').exists():
        sys.exit('【出错】还没准备视频。请先运行：python3 scripts/video_prepare.py 项目目录')
    return d


def load_cfg(d):
    p = d / 'project.json'
    cfg = dict(DEFAULT)
    if p.exists():
        cfg.update(json.loads(p.read_text(encoding='utf-8')))
    if cfg['风格'] not in THEMES:
        sys.exit(f"【出错】风格「{cfg['风格']}」不存在，只能是：{'、'.join(f'{k}（{v}）' for k, v in THEMES.items())}")
    return cfg


def save_cfg(d, cfg):
    (d / 'project.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding='utf-8')


def info(d):
    p = d / 'work' / 'video.json'
    if not p.exists():
        sys.exit('【出错】还没准备视频。请先运行：python3 scripts/video_prepare.py 项目目录')
    return json.loads(p.read_text(encoding='utf-8'))


def probe(path):
    """不依赖 ffprobe：读时长、帧率，再解一帧拿到真实宽高（手机竖拍的旋转已经算进去）"""
    r = subprocess.run([ffmpeg(), '-hide_banner', '-i', str(path)], capture_output=True, text=True)
    err = r.stderr
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', err)
    if not m:
        sys.exit(f'【出错】读不了这个视频：{path}')
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    fm = re.search(r'([\d.]+) fps', err)
    fps_src = float(fm.group(1)) if fm else 30.0
    png = subprocess.run([ffmpeg(), '-loglevel', 'error', '-i', str(path), '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                         capture_output=True).stdout
    from PIL import Image
    import io
    w, h = Image.open(io.BytesIO(png)).size
    has_audio = 'Audio:' in err
    return {'dur': dur, 'fps_src': fps_src, 'w': w, 'h': h, 'audio': has_audio}


def pick_fps(f):
    for c in (24, 25, 30):
        if abs(f - c) < 0.6 or abs(f - c * 1000 / 1001) < 0.05:
            return c
    return 30


def face_detector():
    import cv2
    base = Path(getattr(getattr(cv2, 'data', None), 'haarcascades', '') or '')
    f1 = base / 'haarcascade_frontalface_default.xml'
    if not f1.exists():
        sys.exit('【出错】人脸检测文件找不到（新版 opencv 去掉了）。请运行：python3 scripts/check_env.py --install（会装 4.x 版）')
    return cv2.CascadeClassifier(str(f1)), cv2.CascadeClassifier(str(base / 'haarcascade_eye_tree_eyeglasses.xml'))


class FaceTrack:
    """逐帧找人脸，平滑位置，找不到就沿用上一次"""
    def __init__(self):
        self.face, self.eye = face_detector()
        self.box = None

    def find(self, img, eyes=False):
        import cv2, numpy as np
        h, w = img.shape[:2]
        k = 480 / w
        g = cv2.cvtColor(cv2.resize(img, (480, int(h * k)), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        g = cv2.equalizeHist(g)
        fs = self.face.detectMultiScale(g, 1.1, 6, minSize=(40, 40))
        if len(fs) == 0:
            return (self.box, 0) if eyes else self.box
        x, y, fw, fh = max(fs, key=lambda r: r[2] * r[3])
        ne = 0
        if eyes:
            roi = g[y:y + int(fh * 0.6), x:x + fw]
            ne = len(self.eye.detectMultiScale(roi, 1.1, 5, minSize=(max(6, int(fw * .12)),) * 2))
        box = np.array([x, y, fw, fh], dtype=np.float64) / k
        self.box = box if self.box is None else self.box * 0.7 + box * 0.3
        return (self.box, ne) if eyes else self.box


def read_frames(path, w, h, start=None, n=None):
    """逐帧读成 numpy 数组（BGR）"""
    import numpy as np
    cmd = [ffmpeg(), '-loglevel', 'error']
    if start is not None:
        cmd += ['-ss', f'{start:.4f}']
    cmd += ['-i', str(path)]
    if n is not None:
        cmd += ['-frames:v', str(n)]
    cmd += ['-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h * 3
    while True:
        raw = p.stdout.read(size)
        if len(raw) < size:
            break
        yield np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    p.wait()


def energy_db(x, sr, hop=0.01, win=0.02):
    import numpy as np
    n, hh = int(sr * win), int(sr * hop)
    e = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode='same')[::hh] + 1e-12)
    return 20 * np.log10(e)


def fmt_t(t):
    m, s = divmod(max(0, t), 60)
    return f'{int(m)}:{s:04.1f}'
