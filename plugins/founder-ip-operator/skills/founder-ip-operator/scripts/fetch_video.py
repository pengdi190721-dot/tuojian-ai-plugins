#!/usr/bin/env python3
"""把抖音、视频号等分享链接变成本地视频文件，再交给 analyze_video.py 解析文字和画面。"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from analyze_video import atomic_json_write, cache_root


URL_PATTERN = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
ROUTER_PATTERN = re.compile(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", re.S)
MOBILE_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) FxiOS/122.0 Mobile/15E148 Safari/605.1.15"
)
DESKTOP_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
# 开源视频号下载器 wx_channels_download 的本机默认地址。
CHANNELS_DOWNLOADER = "http://127.0.0.1:2022"
TIMEOUT = 30
# 网络偶尔断一下很常见，自动再试两次，不让用户手动重来。
RETRIES = 2
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead)
DOUYIN_EMPTY_HINT = (
    "可以这样办：一、电脑开着代理或VPN软件的全局模式时，抖音只给空页面，把软件切到按规则分流"
    "（国内网站直连）或先关掉，再发一次；二、有得到大脑会员的话，把链接存进得到大脑再读文字稿；"
    "三、在抖音里把视频保存到手机或录屏，直接把视频文件发过来，这样画面也能看。"
    "作品删了或仅自己可见时，只能用第三个办法。"
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None


def extract_url(text: str) -> str:
    # 用户常把整段分享口令粘过来，只取里面第一条链接。
    match = URL_PATTERN.search(text.strip())
    if not match:
        raise SystemExit("没有在内容里找到链接，请把分享链接或整段分享口令发过来。")
    return match.group(0).rstrip(".,!?;:)]}\"'")


def platform_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    path = urlparse(url).path
    if host.endswith("douyin.com") or host.endswith("iesdouyin.com"):
        return "抖音"
    if host == "channels.weixin.qq.com" or (
        host.endswith("weixin.qq.com") and path.startswith("/sph/")
    ):
        return "视频号"
    return "其他"


def ssl_context() -> ssl.SSLContext:
    paths = ssl.get_default_verify_paths()
    if (paths.cafile and Path(paths.cafile).is_file()) or (
        paths.capath and Path(paths.capath).is_dir() and any(Path(paths.capath).iterdir())
    ):
        return ssl.create_default_context()
    # 官网装的 Python 在苹果电脑上默认不带证书，借用 certifi 或系统自带的那份。
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    if Path("/etc/ssl/cert.pem").is_file():
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ssl.create_default_context()


def request(
    url: str, agent: str, *, follow: bool = True, direct: bool = False
) -> urllib.request.addinfourl:
    headers = {"User-Agent": agent, "Accept-Language": "zh-CN,zh;q=0.9"}
    handlers: list[urllib.request.BaseHandler] = [
        urllib.request.HTTPSHandler(context=ssl_context())
    ]
    if not follow:
        handlers.append(NoRedirect())
    if direct or urlparse(url).hostname == "127.0.0.1":
        # 国内平台和本机服务都直连，不走代理软件；走境外线路时抖音不给作品数据。
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)
    for attempt in range(RETRIES + 1):
        try:
            return opener.open(urllib.request.Request(url, headers=headers), timeout=TIMEOUT)
        except urllib.error.HTTPError:
            # 跳转和平台明确拒绝不是网络抖动，再试也没用。
            raise
        except NETWORK_ERRORS:
            if attempt == RETRIES or urlparse(url).hostname == "127.0.0.1":
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def resolve_douyin(url: str) -> str:
    # 短链会跳几次才到 iesdouyin 的分享页，逐跳跟到带作品编号的地址为止。
    current = url
    for _ in range(5):
        try:
            response = request(current, MOBILE_AGENT, follow=False, direct=True)
            response.close()
            return current
        except urllib.error.HTTPError as error:
            location = error.headers.get("Location")
            if error.code not in {301, 302, 303, 307, 308} or not location:
                raise
            if location.startswith("/"):
                location = f"https://{urlparse(current).hostname}{location}"
            current = location
            if "iesdouyin.com/share/" in current:
                return current
    return current


def douyin_item_id(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    for key in ("modal_id", "vid", "aweme_id"):
        if query.get(key):
            return query[key][0]
    match = re.search(r"/(?:video|note|slides)/(\d{8,})", urlparse(url).path)
    return match.group(1) if match else None


def douyin_item(item_id: str) -> dict:
    page_url = f"https://www.iesdouyin.com/share/video/{item_id}"
    with request(page_url, MOBILE_AGENT, direct=True) as response:
        html = response.read().decode("utf-8", errors="replace")
    match = ROUTER_PATTERN.search(html)
    if not match:
        raise SystemExit(f"抖音没有给出这条视频的内容。{DOUYIN_EMPTY_HINT}")
    loader = json.loads(match.group(1).strip()).get("loaderData") or {}
    for key in sorted(loader):
        page = loader[key]
        if not isinstance(page, dict):
            continue
        items = (page.get("videoInfoRes") or {}).get("item_list") or []
        if items:
            return items[0]
    raise SystemExit(f"抖音没有给出这条视频的内容。{DOUYIN_EMPTY_HINT}")


def download(url: str, target: Path, agent: str, *, direct: bool = False) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    for attempt in range(RETRIES + 1):
        try:
            with request(url, agent, direct=direct) as response, temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            break
        except NETWORK_ERRORS:
            # 下到一半断了，从头再下；request 自己已经重试过连接。
            if attempt == RETRIES:
                raise
            time.sleep(2 * (attempt + 1))
    if temporary.stat().st_size < 1024:
        temporary.unlink()
        raise SystemExit("下载到的文件是空的，平台可能限制了这条作品。请在App里把视频保存到手机或录屏，直接把视频文件发过来。")
    temporary.replace(target)
    return target


def first_url(value: object) -> str:
    urls = (value or {}).get("url_list") if isinstance(value, dict) else None
    return urls[0] if urls else ""


def fetch_douyin(url: str, folder: Path) -> dict:
    item_id = douyin_item_id(url) or douyin_item_id(resolve_douyin(url))
    if not item_id:
        raise SystemExit("这条抖音链接没认出是哪条视频。请在抖音里点视频右下角的“分享”，选“复制链接”，把整段复制过来再试。")
    item = douyin_item(item_id)
    statistics = item.get("statistics") or {}
    video = item.get("video") or {}
    result: dict[str, object] = {
        "平台": "抖音",
        "作品编号": item_id,
        "标题文案": (item.get("desc") or "").strip(),
        "作者": (item.get("author") or {}).get("nickname", ""),
        "发布时间": item.get("create_time"),
        "时长秒": round((video.get("duration") or 0) / 1000, 1) or None,
        "点赞": statistics.get("digg_count"),
        "评论": statistics.get("comment_count"),
        "收藏": statistics.get("collect_count"),
        "分享": statistics.get("share_count"),
        "背景音乐": (item.get("music") or {}).get("title", ""),
    }
    images = item.get("images") or []
    if images:
        # 图文作品没有视频，把每张图存下来直接看图。
        paths = []
        for index, image in enumerate(images, start=1):
            image_url = first_url(image)
            if image_url:
                paths.append(
                    str(download(image_url, folder / f"{item_id}-{index:02d}.jpg", MOBILE_AGENT, direct=True))
                )
        result["类型"] = "图文"
        result["图片"] = paths
        return result
    play_url = first_url(video.get("play_addr")).replace("/playwm/", "/play/")
    if not play_url:
        raise SystemExit("这条抖音视频没拿到播放地址。请在抖音里把视频保存到手机或录屏，直接把视频文件发过来。")
    result["类型"] = "视频"
    result["本地视频"] = str(download(play_url, folder / f"{item_id}.mp4", DESKTOP_AGENT, direct=True))
    return result


def channels_downloader_ready() -> bool:
    try:
        with request(f"{CHANNELS_DOWNLOADER}/api/channels/status", DESKTOP_AGENT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return False
    return bool((payload.get("data") or {}).get("available"))


def channels_guide(url: str) -> dict:
    ready = channels_downloader_ready()
    return {
        "平台": "视频号",
        "链接": url,
        "本机视频号下载器": "已连接" if ready else "没有运行或视频号页面没打开",
        "下一步": (
            "用视频号下载器的 MCP 工具 fetch_content 解析这条链接，再用 download_content 存成本地文件，"
            "然后对本地文件运行 analyze_video.py。"
            if ready
            else "视频号链接只能在微信里打开，网页拿不到视频。请对方在手机上录屏后把视频文件发过来；"
            "或按 references/video-analysis.md 的“发来链接时”一节，在电脑上装视频号下载器后再发链接。"
        ),
    }


def fetch_other(url: str, folder: Path) -> dict:
    tool = shutil.which("yt-dlp")
    if not tool:
        raise SystemExit("这个平台的链接暂时读不了。最省事的办法：在App里把视频保存到手机或录屏，直接把视频文件发过来。")
    folder.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [tool, "--no-playlist", "-f", "mp4/best", "-o", str(folder / "%(id)s.%(ext)s"),
         "--print", "after_move:filepath", url],
        capture_output=True, text=True, check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode or not lines:
        raise SystemExit("这个链接没下载下来（可能要登录或有地区限制）。请在App里把视频保存到手机或录屏，直接把视频文件发过来。")
    return {"平台": "其他", "链接": url, "类型": "视频", "本地视频": lines[-1]}


def analyze(video: str, detail: str) -> dict:
    script = Path(__file__).with_name("analyze_video.py")
    completed = subprocess.run(
        [sys.executable, str(script), video, "--detail", detail],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        return {"解析": "没有完成", "原因": completed.stderr.strip()[-500:]}
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="解析抖音、视频号等分享链接，下载后交给视频解析")
    parser.add_argument("share", help="分享链接，或整段分享口令")
    parser.add_argument("--analyze", action="store_true", help="下载后接着解析文字和画面")
    parser.add_argument("--detail", choices=("brief", "standard", "detailed"), default="standard")
    parser.add_argument("--json-output", help="把结果另存为JSON文件")
    args = parser.parse_args()

    url = extract_url(args.share)
    platform_name = platform_of(url)
    folder = cache_root() / "links" / hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    try:
        if platform_name == "抖音":
            result = fetch_douyin(url, folder)
        elif platform_name == "视频号":
            result = channels_guide(url)
        else:
            result = fetch_other(url, folder)
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"{platform_name}这次拒绝了读取（错误码{error.code}）。过几分钟再试一次；"
            "还不行就在App里把视频保存到手机或录屏，直接把视频文件发过来。"
        )
    except NETWORK_ERRORS as error:
        raise SystemExit(
            f"试了三次还是连不上{platform_name}（{error}）。先看看网络通不通；"
            "电脑开着代理或VPN的话，切到按规则分流再试；实在不行，就把视频文件直接发过来。"
        )

    if args.analyze and result.get("本地视频"):
        result["解析结果"] = analyze(str(result["本地视频"]), args.detail)
    if args.json_output:
        atomic_json_write(Path(args.json_output).expanduser().resolve(), result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
