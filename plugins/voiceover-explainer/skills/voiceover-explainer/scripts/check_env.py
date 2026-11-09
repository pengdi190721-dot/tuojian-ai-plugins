"""检查和安装运行环境。
用法：
  python3 check_env.py              # 只检查，告诉你缺什么
  python3 check_env.py --install    # 安装缺的程序包（自动用国内镜像）
  python3 check_env.py --download   # 下载语音识别模型（约230MB，只要下一次）"""
import importlib, os, shutil, subprocess, sys, tarfile, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import MODELS

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
    try:
        import asyncio
        from playwright.async_api import async_playwright
        from common import open_browser

        async def t():
            async with async_playwright() as p:
                b = await open_browser(p); await b.close()
        asyncio.run(t()); ok_browser = True; print('  ✓ 浏览器能打开')
    except SystemExit:
        print('  ✗ 浏览器打不开（装谷歌浏览器，或运行 --install 自动装）')
    except Exception as e:
        print(f'  ✗ 浏览器打不开：{e}')
    has_model = any(MODELS.glob('sherpa-onnx-sense-voice-*/tokens.txt'))
    print(f'  {"✓" if has_model else "✗"} 语音识别模型（{MODELS}）' + ('' if has_model else '，运行 --download 下载'))
    return miss, ok_browser, has_model


def install(miss, ok_browser):
    if miss:
        cmd = [sys.executable, '-m', 'pip', 'install', '-i', MIRROR] + miss
        print('安装：', ' '.join(cmd))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            subprocess.run(cmd + ['--break-system-packages'])
    if not ok_browser:
        env = dict(os.environ, PLAYWRIGHT_DOWNLOAD_HOST='https://npmmirror.com/mirrors/playwright')
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], env=env)


def download():
    MODELS.mkdir(parents=True, exist_ok=True)
    for url in MODEL_URLS:
        try:
            tgt = MODELS / f'{MODEL_NAME}.tar.bz2'
            print('下载：', url)
            urllib.request.urlretrieve(url, tgt)
            with tarfile.open(tgt) as t:
                t.extractall(MODELS)
            tgt.unlink()
            print('模型下载好了'); return True
        except Exception as e:
            print('  这个地址下载失败：', e)
    d = MODELS / MODEL_NAME; d.mkdir(exist_ok=True)
    try:
        for url, name in HF_FILES:
            print('下载：', url); urllib.request.urlretrieve(url, d / name)
        print('模型下载好了'); return True
    except Exception as e:
        print('  镜像站也下载失败：', e)
    print(f'\n请手动下载：{MODEL_URLS[0]}\n解压后把文件夹放到：{MODELS}')
    return False


if __name__ == '__main__':
    print('检查运行环境：')
    miss, ok_browser, has_model = check()
    if '--install' in sys.argv:
        install(miss, ok_browser); print('\n再检查一遍：'); miss, ok_browser, has_model = check()
    if '--download' in sys.argv and not has_model:
        download()
    if not miss and ok_browser and has_model:
        print('\n环境齐了，可以开工')
