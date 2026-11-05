#!/usr/bin/env python3
"""直接读抖音分享链接：标题文案、互动数、视频里说的话，加上封面和预览画面的图片地址。不下载视频。"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# 别在技能文件夹里留下缓存文件，免得用户把整个文件夹再上传时被技能市场拒收。
sys.dont_write_bytecode = True
from analyze_video import (  # noqa: E402
    LOCAL_WHISPER_MODEL,
    MINIMUM_NODE,
    TRANSCRIBER_PACKAGE,
    atomic_json_write,
    cache_root,
    node_version,
    use_model_mirror_if_blocked,
)


URL_PATTERN = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
MOBILE_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
# 抖音分享页不带访问凭证只给空页面。这个凭证是匿名发的，不用登录、不用注册。
TTWID_URL = "https://ttwid.bytedance.com/ttwid/union/register/"
TTWID_PAYLOAD = {
    "region": "cn",
    "aid": 1768,
    "needFid": False,
    "service": "www.iesdouyin.com",
    "migrate_info": {"ticket": "", "source": "node"},
    "cbUrlProtocol": "https",
    "union": True,
}
TTWID_TTL = 30 * 60
PLAY_ENDPOINT = "https://aweme.snssdk.com/aweme/v1/play/"
SHARE_TYPES = ("video", "note", "slides")
TIMEOUT = 30
# 网络偶尔断一下很常见，自动再试两次，不让用户手动重来。
RETRIES = 2
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead)
FALLBACK_HINT = (
    "换个办法：在抖音里点“分享”、再点“保存本地”，把视频文件发过来；"
    "没有“保存本地”就用手机录屏发过来。"
)
OTHER_PLATFORM_HINT = (
    "直接读只支持抖音。别的平台的视频，请在App里保存下来或者录屏，把文件发过来；"
    "公众号这类文章，直接打开网页读就行。"
)
TIMESTAMP = re.compile(r"(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}\s*-->")


class Unreadable(Exception):
    """抖音这次没给作品数据，交给上层换办法。"""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None


def extract_url(text: str) -> str:
    # 用户常把整段分享口令粘过来，只取里面第一条链接。
    match = URL_PATTERN.search(text.strip())
    if not match:
        raise SystemExit("没有在内容里找到链接，请把抖音的分享链接或整段分享口令发过来。")
    return match.group(0).rstrip(".,!?;:)]}\"'")


def is_douyin(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host.endswith("douyin.com") or host.endswith("iesdouyin.com")


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


def open_url(
    url: str,
    headers: dict[str, str],
    *,
    data: bytes | None = None,
    follow: bool = True,
):
    # 先直连：走境外线路时抖音常常不给作品数据。直连不通（比如公司网络只能走代理），再按系统代理试一次。
    for direct in (True, False):
        handlers: list[urllib.request.BaseHandler] = [
            urllib.request.HTTPSHandler(context=ssl_context())
        ]
        if not follow:
            handlers.append(NoRedirect())
        if direct:
            handlers.append(urllib.request.ProxyHandler({}))
        opener = urllib.request.build_opener(*handlers)
        method = "POST" if data is not None else "GET"
        for attempt in range(RETRIES + 1):
            try:
                return opener.open(
                    urllib.request.Request(url, data=data, headers=headers, method=method),
                    timeout=TIMEOUT,
                )
            except urllib.error.HTTPError:
                # 跳转和平台明确拒绝不是网络抖动，再试也没用。
                raise
            except NETWORK_ERRORS:
                if attempt == RETRIES:
                    if direct:
                        break
                    raise
                time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def page_headers(cookie: str | None, referer: str = "https://www.iesdouyin.com/") -> dict[str, str]:
    headers = {
        "User-Agent": MOBILE_AGENT,
        "Referer": referer,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if cookie:
        headers["Cookie"] = cookie
    return headers


def ttwid_cache() -> Path:
    return cache_root() / "douyin" / "ttwid.json"


def register_ttwid() -> str | None:
    body = json.dumps(TTWID_PAYLOAD).encode("utf-8")
    headers = {"User-Agent": MOBILE_AGENT, "Content-Type": "application/json"}
    try:
        with open_url(TTWID_URL, headers, data=body) as response:
            cookies = response.headers.get_all("Set-Cookie") or []
    except (urllib.error.HTTPError, *NETWORK_ERRORS):
        return None
    for cookie in cookies:
        if "ttwid=" in cookie:
            return cookie.split("ttwid=", 1)[1].split(";", 1)[0]
    return None


def get_ttwid(refresh: bool = False) -> str | None:
    path = ttwid_cache()
    if not refresh:
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved.get("value") and time.time() < saved.get("expires", 0):
                return saved["value"]
        except (OSError, ValueError):
            pass
    value = register_ttwid()
    if value:
        atomic_json_write(path, {"value": value, "expires": time.time() + TTWID_TTL})
    return value


def item_id_in(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    for key in ("modal_id", "vid", "aweme_id"):
        if query.get(key) and query[key][0].isdigit():
            return query[key][0]
    match = re.search(r"/(?:video|note|slides)/(\d{8,})", urlparse(url).path)
    return match.group(1) if match else None


def resolve_item_id(url: str) -> str | None:
    found = item_id_in(url)
    if found:
        return found
    # 短链要跳几次才到带作品编号的地址，逐跳跟。
    current = url
    for _ in range(5):
        try:
            with open_url(current, page_headers(None, "https://www.douyin.com/"), follow=False):
                return item_id_in(current)
        except urllib.error.HTTPError as error:
            location = error.headers.get("Location")
            if error.code not in {301, 302, 303, 307, 308} or not location:
                raise
            if location.startswith("/"):
                location = f"https://{urlparse(current).hostname}{location}"
            current = location
            found = item_id_in(current)
            if found:
                return found
    return None


def router_data(html: str) -> dict | None:
    marker = html.find("window._ROUTER_DATA")
    if marker == -1:
        return None
    start = html.find("{", marker)
    if start == -1:
        return None
    try:
        payload, _ = json.JSONDecoder().raw_decode(html, start)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def find_item(node: object) -> dict | None:
    if isinstance(node, dict):
        info = node.get("videoInfoRes")
        items = info.get("item_list") if isinstance(info, dict) else None
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]
        for value in node.values():
            found = find_item(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_item(value)
            if found:
                return found
    return None


def share_item(item_id: str, cookie: str | None) -> dict | None:
    missing = 0
    for kind in SHARE_TYPES:
        url = f"https://www.iesdouyin.com/share/{kind}/{item_id}/"
        try:
            with open_url(url, page_headers(cookie)) as response:
                html = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                missing += 1
                continue
            if error.code in {401, 403}:
                return None
            raise
        data = router_data(html)
        item = find_item(data.get("loaderData")) if data else None
        if item:
            return item
    if missing == len(SHARE_TYPES):
        raise SystemExit("这条抖音作品不存在，可能删了或者只有作者自己能看。请换一条，或者让对方把视频文件发过来。")
    return None


def fetch_item(item_id: str) -> tuple[dict, str | None]:
    # 凭证可能过期或被风控，空页面时换一个新凭证再试一次。
    for refresh in (False, True):
        ttwid = get_ttwid(refresh=refresh)
        cookie = f"ttwid={ttwid}" if ttwid else None
        item = share_item(item_id, cookie)
        if item:
            return item, cookie
    raise Unreadable("抖音这次没给作品数据")


def first_url(value: object) -> str:
    if isinstance(value, dict):
        urls = value.get("url_list")
        if isinstance(urls, list) and urls:
            return urls[0]
        return value.get("url") or ""
    return ""


def read_text(url: str, headers: dict[str, str]) -> str:
    with open_url(url, headers) as response:
        return response.read().decode("utf-8", errors="replace")


def subtitle_segments(body: str) -> list[dict]:
    # 字幕文件的格式抖音没公开，JSON、VTT、SRT 都认一下；认不出来就当没有字幕。
    body = body.strip()
    if body[:1] in "[{":
        try:
            payload = json.loads(body)
        except ValueError:
            return []
        rows = payload if isinstance(payload, list) else payload.get("utterances") or payload.get("body") or []
        segments = []
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict):
                text = row.get("text") or row.get("content") or ""
                if text.strip():
                    segments.append({"开始": row.get("start_time") or row.get("start"), "文字": text.strip()})
        return segments
    segments, lines = [], body.splitlines()
    for index, line in enumerate(lines):
        if TIMESTAMP.search(line):
            text = []
            for following in lines[index + 1:]:
                if not following.strip() or TIMESTAMP.search(following):
                    break
                text.append(following.strip())
            if text:
                segments.append({"开始": line.split("-->")[0].strip(), "文字": " ".join(text)})
    return segments


def creator_subtitles(item: dict, headers: dict[str, str]) -> list[dict]:
    tracks = ((item.get("video") or {}).get("cla_info") or {}).get("caption_infos") or []
    for track in tracks if isinstance(tracks, list) else []:
        url = first_url(track)
        if not url:
            continue
        try:
            segments = subtitle_segments(read_text(url, headers))
        except (urllib.error.HTTPError, *NETWORK_ERRORS):
            continue
        if segments:
            return segments
    return []


def video_seconds(item: dict) -> float:
    return ((item.get("video") or {}).get("duration") or 0) / 1000


def own_original_sound(item: dict) -> str:
    # 作者原声就是这条视频里说的话，只取这段声音最省。用的是别人的原声（热门配音）、
    # 或者原声长度跟视频对不上，就不是这条说的话，不用。
    music = item.get("music") or {}
    if not music.get("is_original_sound"):
        return ""
    owner, uid = music.get("owner_id"), (item.get("author") or {}).get("uid")
    if owner and uid and str(owner) != str(uid):
        return ""
    sound_seconds, seconds = music.get("duration") or 0, video_seconds(item)
    if sound_seconds and seconds and abs(sound_seconds - seconds) > 3:
        return ""
    return first_url(music.get("play_url"))


def url_from(value: object) -> str:
    # 抖音有的地方给地址列表，有的给“主地址、备用地址”，两种都认。
    if isinstance(value, list) and value:
        return value[0] if isinstance(value[0], str) else ""
    if isinstance(value, dict):
        return value.get("main_url") or value.get("backup_url") or first_url(value)
    return ""


def audio_sources(item: dict) -> list[str]:
    # 从小到大排：作者原声 → 单独的声音轨 → 最小清晰度的视频 → 低清晰度播放地址 → 原播放地址。
    # 只为听写，越小越快，下到一半断的机会也越小。
    video = item.get("video") or {}
    sources = [own_original_sound(item)]
    for track in video.get("bit_rate_audio") or []:
        if isinstance(track, dict):
            sources.append(url_from((track.get("audio_meta") or {}).get("url_list")))
    variants = [
        variant for variant in video.get("bit_rate") or []
        if isinstance(variant, dict) and first_url(variant.get("play_addr"))
    ]
    if variants:
        smallest = min(variants, key=lambda variant: variant.get("bit_rate") or 0)
        sources.append(first_url(smallest.get("play_addr")))
    address = video.get("play_addr") or {}
    uri = address.get("uri") if isinstance(address, dict) else None
    if uri:
        sources.append(f"{PLAY_ENDPOINT}?video_id={uri}&ratio=360p")
    sources.append(first_url(address))
    if uri:
        sources.append(f"{PLAY_ENDPOINT}?video_id={uri}&ratio=720p")
    unique = []
    for source in sources:
        if source and source not in unique:
            unique.append(source)
    return unique


MEDIA_SUFFIXES = {".mp3": ".mp3", ".m4a": ".m4a", ".aac": ".aac", ".mp4": ".mp4"}
MEDIA_TYPES = {"audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/aac": ".aac", "video/mp4": ".mp4"}


def media_suffix(url: str, content_type: str) -> str:
    # 听写组件靠后缀认格式，按地址或返回的类型给文件起名。
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in MEDIA_SUFFIXES:
        return MEDIA_SUFFIXES[suffix]
    return MEDIA_TYPES.get(content_type.split(";")[0].strip().lower(), ".mp4")


class Truncated(Exception):
    """下到一半断了：拿到的比服务器说的少。"""


def download(url: str, stem: Path, headers: dict[str, str]) -> Path:
    target = stem
    for attempt in range(RETRIES + 1):
        try:
            with open_url(url, headers) as response:
                target = stem.with_suffix(media_suffix(url, response.headers.get("Content-Type", "")))
                expected = response.headers.get("Content-Length")
                with target.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
            # 连接中途断开时 Python 不报错，只是数据少了一截，所以自己对一下大小。
            if expected and expected.isdigit() and target.stat().st_size < int(expected):
                raise Truncated(f"只拿到{target.stat().st_size}字节，应该有{expected}字节")
            break
        except (*NETWORK_ERRORS, Truncated):
            if attempt == RETRIES:
                raise Unreadable("声音下到一半断了，试了几次都没下全")
            time.sleep(2 * (attempt + 1))
    if target.stat().st_size < 1024:
        raise Unreadable("取到的声音是空的")
    return target


def media_seconds(path: Path) -> float | None:
    # 有 ffprobe 就量一下实际有多长，跟作品时长对不上说明没下全。没有就不量。
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    completed = subprocess.run(
        [probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=False,
    )
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return None


def transcriber() -> tuple[str | None, str]:
    node, npx = shutil.which("node"), shutil.which("npx")
    if not node or not npx:
        return None, "要听写视频里说了什么，电脑上要装 Node.js（22.12以上）。说一句“帮我检查一下”，我带你装。"
    if node_version(node) < MINIMUM_NODE:
        return None, "电脑上的 Node.js 版本太旧，要22.12以上。打开 nodejs.org 下载推荐的版本装上，再发一次链接。"
    return npx, ""


def transcribe(media: Path, npx: str, workdir: Path) -> list[dict]:
    use_model_mirror_if_blocked()
    command = [
        npx, "-y", TRANSCRIBER_PACKAGE, str(media),
        "--model", LOCAL_WHISPER_MODEL, "--lang", "zh", "--json",
        "--out-dir", str(workdir), "--force", "--no-color",
    ]
    if shutil.which("ffmpeg"):
        command.extend(["--decoder", "ffmpeg"])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    return [
        {"开始": segment.get("start"), "结束": segment.get("end"), "文字": segment["text"].strip()}
        for segment in payload.get("segments", [])
        if isinstance(segment, dict) and str(segment.get("text", "")).strip()
    ]


def spoken_words(item: dict, item_id: str, cookie: str | None) -> tuple[list[dict], str, str]:
    """返回（分段、来源、提示）。声音只放在临时文件夹里，听写完连文件夹一起删掉。"""
    referer = f"https://www.iesdouyin.com/share/video/{item_id}/"
    headers = page_headers(cookie, referer)
    segments = creator_subtitles(item, headers)
    if segments:
        return segments, "作品自带字幕", ""
    npx, problem = transcriber()
    if not npx:
        return [], "", problem
    expected = video_seconds(item)
    with tempfile.TemporaryDirectory(prefix="douyin-") as folder:
        workdir = Path(folder)
        media, longest, longest_seconds, measured = None, None, 0.0, False
        for index, source in enumerate(audio_sources(item)):
            try:
                candidate = download(source, workdir / f"sound-{index}", headers)
            except (urllib.error.HTTPError, Unreadable):
                continue
            seconds = media_seconds(candidate)
            if seconds is None or not expected or seconds >= expected - 10:
                media, measured = candidate, seconds is not None
                break
            # 比作品短了一大截，多半没下全：先留着，换下一个地址再试。
            if seconds > longest_seconds:
                longest, longest_seconds = candidate, seconds
        short_hint = ""
        if media is None and longest is not None:
            media = longest
            short_hint = (
                f"声音只取到前{int(longest_seconds)}秒（作品有{int(expected)}秒），后面没下全，"
                "文字稿只到这里。换个网络再发一次链接试试。"
            )
        if media is None:
            return [], "", "作品的声音没取到。" + FALLBACK_HINT
        segments = transcribe(media, npx, workdir)
    if not segments:
        return [], "", "这次没听写出说的话（多半是听写组件没下载下来，或者视频里没人说话）。换个网络再发一次链接试试；还不行，" + FALLBACK_HINT
    last = segments[-1].get("结束") or segments[-1].get("开始") or 0
    if not short_hint and not measured and expected > 30 and isinstance(last, (int, float)) and last < expected * 0.6:
        # 量不了声音长度时，看听写停在哪：停得太早，提醒可能没取全（也可能后面只有音乐）。
        short_hint = (
            f"文字稿停在第{int(last)}秒，作品有{int(expected)}秒。后面可能只有音乐，"
            "也可能声音没取全；对不上的话换个网络再发一次链接。"
        )
    return segments, "本地听写（只取声音，用完就删）", short_hint


def preview_sheets(video: dict) -> list[dict]:
    # 抖音给拖进度条用的预览拼图：一张图里按顺序排着很多小画面，看画面不用下视频。
    # 不是每条作品都有，字段名没在公开资料里核实过，有就给，没有就算了。
    sheets = []
    for thumb in video.get("big_thumbs") or []:
        if not isinstance(thumb, dict):
            continue
        urls = thumb.get("img_urls") or ([thumb["img_url"]] if thumb.get("img_url") else [])
        for url in urls if isinstance(urls, list) else []:
            if isinstance(url, str) and url.startswith("http"):
                sheets.append({
                    "图片地址": url,
                    "一张几格": thumb.get("img_num"),
                    "每行几格": thumb.get("img_x_len"),
                    "每格隔几秒": thumb.get("interval"),
                })
    return sheets


def read_douyin(url: str, with_words: bool = True) -> dict:
    item_id = resolve_item_id(url)
    if not item_id:
        raise SystemExit("这条抖音链接没认出是哪条作品。请在抖音里点“分享”，再点“复制链接”，把整段发过来再试。")
    item, cookie = fetch_item(item_id)
    statistics = item.get("statistics") or {}
    video = item.get("video") or {}
    images = item.get("images") or []
    result: dict[str, object] = {
        "平台": "抖音",
        "作品编号": item_id,
        "类型": "图文" if images else "视频",
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
    cover = first_url(video.get("origin_cover")) or first_url(video.get("cover"))
    if cover:
        result["封面图"] = cover
    previews = preview_sheets(video)
    if previews:
        result["预览画面"] = previews
    if images:
        # 图文作品的文案就是标题文字；图片只给地址，要看图里的字再打开，不存到电脑上。
        result["图片地址"] = [first_url(image) for image in images if first_url(image)]
        return result
    if not with_words:
        return result
    segments, source, hint = spoken_words(item, item_id, cookie)
    if segments:
        result["文字稿"] = "\n".join(segment["文字"] for segment in segments)
        result["分段"] = segments
        result["文字稿来源"] = source
    if hint:
        result["提示"] = hint
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="直接读抖音分享链接，只取说的话和封面、预览图地址，不下载视频")
    parser.add_argument("share", help="抖音分享链接，或整段分享口令")
    parser.add_argument("--no-transcript", action="store_true", help="只要标题文案和互动数，不听写说的话")
    parser.add_argument("--json-output", help="把结果另存为JSON文件")
    args = parser.parse_args()

    url = extract_url(args.share)
    if not is_douyin(url):
        raise SystemExit(f"这不是抖音链接。{OTHER_PLATFORM_HINT}")
    try:
        result = read_douyin(url, with_words=not args.no_transcript)
    except Unreadable as error:
        raise SystemExit(f"这条抖音链接没直接读出来（{error}）。{FALLBACK_HINT}")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"抖音这次拒绝了读取（错误码{error.code}）。{FALLBACK_HINT}")
    except NETWORK_ERRORS as error:
        raise SystemExit(f"试了几次还是连不上抖音。先看看网络通不通；开着加速器或翻墙软件的，关掉再发一次。还不行，{FALLBACK_HINT}（技术原因：{error}）")

    if args.json_output:
        atomic_json_write(Path(args.json_output).expanduser().resolve(), result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
