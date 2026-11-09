"""检查和安装运行环境。只有真要处理视频或录音时才需要跑；写口播稿、出剪辑单和包装方案不用装任何东西。
用法：
  python3 check_env.py              # 只检查，告诉你缺什么（几秒钟）
  python3 check_env.py --install    # 安装缺的程序包（自动用国内镜像）
  python3 check_env.py --download   # 下载语音识别模型（约230MB，只要下一次）
网络不通时 20 秒内给结论，不会卡住。最后一行是“结论：……”，照着做就行。"""
import importlib, os, shutil, socket, subprocess, sys, tarfile, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import MODELS

try:
    sys.stdout.reconfigure(line_buffering=True)   # 被别的程序调用时也一行行马上显示
except Exception:
    pass

PKGS = {'numpy': 'numpy', 'PIL': 'pillow', 'playwright': 'playwright', 'sherpa_onnx': 'sherpa-onnx', 'imageio_ffmpeg': 'imageio-ffmpeg',
        'cv2': 'opencv-python-headless<5'}   # 剪真人口播（A 线）要用 opencv 找人脸；5.x 去掉了人脸检测文件，所以装 4.x
MIRROR = 'https://pypi.tuna.tsinghua.edu.cn/simple'
MODEL_NAME = 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17'
MODEL_URLS = [
    f'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL_NAME}.tar.bz2',
    f'https://ghfast.top/https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL_NAME}.tar.bz2',
]
HF_FILES = [  # 备用：从镜像站逐个下载两个文件
    ('https://hf-mirror.com/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/model.int8.onnx', 'model.int8.onnx'),
    ('https://hf-mirror.com/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/tokens.txt', 'tokens.txt'),
]
PROBE = [MIRROR + '/pip/', 'https://hf-mirror.com/', 'https://github.com/']
IDLE = 20          # 下载时超过这么多秒一点数据都没来，就算这个地址不通
PIP_LIMIT = 600    # 装程序包最多等 10 分钟
BROWSER_LIMIT = 600


def net_ok():
    """同时试三个地址，有一个通就算能联网；最多等 8 秒"""
    def one(url):
        try:
            urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=6).close()
            return True
        except urllib.error.HTTPError:
            return True          # 服务器回了话（哪怕是错误码），说明网是通的
        except Exception:
            return False
    with ThreadPoolExecutor(len(PROBE)) as ex:
        futs = [ex.submit(one, u) for u in PROBE]
        end = time.time() + 8
        for f in futs:
            try:
                if f.result(timeout=max(0.1, end - time.time())):
                    return True
            except Exception:
                pass
    return False


def check():
    miss = []
    for mod, pkg in PKGS.items():
        try:
            m = importlib.import_module(mod)
            if mod == 'cv2':
                face = Path(getattr(getattr(m, 'data', None), 'haarcascades', '') or '.') / 'haarcascade_frontalface_default.xml'
                if not face.exists():
                    raise ImportError('opencv 里没有人脸检测文件')
            print(f'  ✓ {pkg}')
        except Exception:
            print(f'  ✗ {pkg}（没装）'); miss.append(pkg)
    ff = shutil.which('ffmpeg')
    if ff:
        print(f'  ✓ ffmpeg（{ff}）')
    else:
        try:
            import imageio_ffmpeg; print(f'  ✓ ffmpeg（用 imageio-ffmpeg 自带的）')
        except Exception:
            print('  ✗ ffmpeg（没装，装上 imageio-ffmpeg 就有）')
    ok_browser = False
    if 'playwright' in miss:
        print('  ✗ 浏览器（要先装 playwright）')
    else:
        try:
            import asyncio
            from playwright.async_api import async_playwright
            from common import open_browser

            async def t():
                async with async_playwright() as p:
                    b = await open_browser(p); await b.close()
            asyncio.run(asyncio.wait_for(t(), 60)); ok_browser = True; print('  ✓ 浏览器能打开')
        except SystemExit:
            print('  ✗ 浏览器打不开（装谷歌浏览器，或运行 --install 自动装）')
        except Exception as e:
            print(f'  ✗ 浏览器打不开：{str(e)[:120]}')
    has_model = any(MODELS.glob('sherpa-onnx-sense-voice-*/tokens.txt'))
    print(f'  {"✓" if has_model else "✗"} 语音识别模型（{MODELS}）' + ('' if has_model else '，运行 --download 下载'))
    return miss, ok_browser, has_model


def run(cmd, limit, env=None):
    try:
        return subprocess.run(cmd, timeout=limit, env=env).returncode
    except subprocess.TimeoutExpired:
        print(f'  超过 {limit // 60} 分钟没装完，先停下')
        return 1


def install(miss, ok_browser):
    if miss:
        cmd = [sys.executable, '-m', 'pip', 'install', '--timeout', '15', '--retries', '1', '-i', MIRROR] + miss
        print('安装：', ' '.join(cmd))
        if run(cmd, PIP_LIMIT) != 0:
            run(cmd + ['--break-system-packages'], PIP_LIMIT)
    if not ok_browser:
        env = dict(os.environ, PLAYWRIGHT_DOWNLOAD_HOST='https://npmmirror.com/mirrors/playwright')
        run([sys.executable, '-m', 'playwright', 'install', 'chromium'], BROWSER_LIMIT, env)


def fetch(url, tgt):
    """边下边存；超过 IDLE 秒没收到数据就放弃这个地址"""
    with urllib.request.urlopen(url, timeout=IDLE) as r, open(tgt, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        got, last = 0, time.time()
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk); got += len(chunk)
            if total and time.time() - last > 15:
                print(f'  已下载 {got * 100 // total}%'); last = time.time()


def download():
    MODELS.mkdir(parents=True, exist_ok=True)
    tgt = MODELS / f'{MODEL_NAME}.tar.bz2'
    for url in MODEL_URLS:
        try:
            print('下载：', url)
            fetch(url, tgt)
            with tarfile.open(tgt) as t:
                try:
                    t.extractall(MODELS, filter='data')   # 只解出普通文件，安全
                except TypeError:
                    t.extractall(MODELS)                  # 老版本 Python 没有 filter 参数
            tgt.unlink()
            print('模型下载好了'); return True
        except Exception as e:
            print('  这个地址下载失败：', str(e)[:120])
            tgt.unlink(missing_ok=True)
    d = MODELS / MODEL_NAME; d.mkdir(exist_ok=True)
    try:
        for url, name in HF_FILES:
            print('下载：', url); fetch(url, d / name)
        print('模型下载好了'); return True
    except Exception as e:
        print('  镜像站也下载失败：', str(e)[:120])
    print(f'\n请手动下载：{MODEL_URLS[0]}\n解压后把文件夹放到：{MODELS}')
    return False


if __name__ == '__main__':
    socket.setdefaulttimeout(IDLE)
    want_net = '--install' in sys.argv or '--download' in sys.argv
    print('检查运行环境：')
    miss, ok_browser, has_model = check()
    need = bool(miss) or not ok_browser or ('--download' in sys.argv and not has_model)
    net = None
    if want_net and need:
        print('\n检查网络……')
        net = net_ok()
        print('  ✓ 能联网' if net else '  ✗ 连不上网（试了国内镜像、模型镜像站、GitHub）')
    if net and '--install' in sys.argv and (miss or not ok_browser):
        install(miss, ok_browser); print('\n再检查一遍：'); miss, ok_browser, has_model = check()
    if net and '--download' in sys.argv and not has_model:
        has_model = download()
    print()
    if not miss and ok_browser and has_model:
        print('结论：环境齐了，可以开工')
        sys.exit(0)
    lack = '、'.join(miss + ([] if ok_browser else ['浏览器']) + ([] if has_model else ['语音识别模型']))
    if net is False:
        print(f'结论：网络不通，装不上（还缺：{lack}）。先把不靠脚本的部分交给用户：口播稿、剪辑单、包装方案、字幕稿；'
              '出成片要在能联网的电脑上，用 WorkBuddy 本地模式再跑一次。')
    elif want_net:
        print(f'结论：还缺 {lack}，没装成。先把不靠脚本的部分交给用户，再照上面的提示处理（或请用户用 WorkBuddy 本地模式在自己电脑上跑）。')
    else:
        print(f'结论：还缺 {lack}。要处理视频或录音时，运行 --install 和 --download 装上；只写稿、出方案不用装。')
    sys.exit(2)
