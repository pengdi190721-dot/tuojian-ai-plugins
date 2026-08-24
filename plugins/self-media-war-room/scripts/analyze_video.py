#!/usr/bin/env python3
"""自媒体作战室的视频解析适配器；技术细节不直接暴露给学员。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


PACKAGE = "mcp-video-analyzer@0.10.0"
TRANSCRIBER_PACKAGE = "@coroboros/scrybe@0.2.0"
MINIMUM_NODE = (22, 12, 0)
LOCAL_WHISPER_MODEL = "base"


def cache_root() -> Path:
    override = os.environ.get("SELF_MEDIA_VIDEO_CACHE")
    if override:
        return Path(override).expanduser().resolve()
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Caches" / "self-media-war-room"
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "self-media-war-room"
    base = os.environ.get("XDG_CACHE_HOME")
    return Path(base).expanduser() / "self-media-war-room" if base else (
        Path.home() / ".cache" / "self-media-war-room"
    )


def node_version(node: str) -> tuple[int, int, int]:
    completed = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    )
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", completed.stdout.strip())
    if completed.returncode or not match:
        raise SystemExit("视频解析基础组件版本无法识别，请运行作战室体检。")
    return tuple(int(value) for value in match.groups())


def normalized_source(source: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https", "file"}:
        return source
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"没有找到视频文件：{path}")
    return str(path)


def atomic_json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def add_local_transcript(
    payload: dict[str, object],
    source: str,
    npx: str,
    language: str,
    output_dir: Path,
) -> None:
    if payload.get("transcript"):
        payload["warRoomTranscript"] = {
            "source": "视频字幕或本地语音识别",
            "localOnly": True,
        }
        return
    if urlparse(source).scheme in {"http", "https"}:
        payload.setdefault("warnings", []).append(
            "公开链接没有可用字幕；如需完整口播评分，请上传本人有权使用的本地视频。"
        )
        return
    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and metadata.get("hasAudio") is False:
        return

    transcript_dir = output_dir.parent / "transcript"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    command = [
        npx,
        "-y",
        TRANSCRIBER_PACKAGE,
        source,
        "--model",
        LOCAL_WHISPER_MODEL,
        "--lang",
        language,
        "--json",
        "--out-dir",
        str(transcript_dir),
        "--force",
        "--no-color",
    ]
    if shutil.which("ffmpeg"):
        command.extend(["--decoder", "ffmpeg"])

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        payload.setdefault("warnings", []).append(
            "本地语音转写没有完成；当前仍可评价画面和剪辑，但口播表达只能局部评分。"
        )
        return
    try:
        transcript_payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload.setdefault("warnings", []).append(
            "本地语音转写结果格式异常；当前仍可评价画面和剪辑。"
        )
        return

    segments = transcript_payload.get("segments", [])
    if not isinstance(segments, list) or not segments:
        payload.setdefault("warnings", []).append(
            "本地语音转写没有识别出有效内容；请检查音量，或上传更清晰的原始视频。"
        )
        return
    payload["transcript"] = [
        {
            "start": segment.get("start"),
            "end": segment.get("end"),
            "text": segment.get("text", ""),
        }
        for segment in segments
        if isinstance(segment, dict) and segment.get("text")
    ]
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list):
        payload["warnings"] = [
            warning
            for warning in warnings
            if not (
                isinstance(warning, str)
                and (
                    warning.startswith("No speech-to-text backend available")
                    or warning == "No transcript available for this video."
                )
            )
        ]
    payload["warRoomTranscript"] = {
        "source": f"本地语音识别（{LOCAL_WHISPER_MODEL}）",
        "localOnly": True,
        "language": transcript_payload.get("language", language),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="解析用于成片评分或对标拆解的视频")
    parser.add_argument("source", help="本地视频绝对路径或单条公开视频链接")
    parser.add_argument(
        "--detail", choices=("brief", "standard", "detailed"), default="detailed"
    )
    parser.add_argument("--language", default="zh")
    parser.add_argument("--max-frames", type=int, default=40)
    parser.add_argument("--out", help="关键画面输出目录")
    parser.add_argument("--json-output", help="把解析结果另存为JSON文件")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    if not 1 <= args.max_frames <= 60:
        raise SystemExit("关键画面数量必须在1到60之间。")

    node = shutil.which("node")
    npx = shutil.which("npx")
    if not node or not npx:
        raise SystemExit("视频解析基础组件尚未就绪，请先运行作战室体检。")
    installed_version = node_version(node)
    if installed_version < MINIMUM_NODE:
        current = ".".join(str(value) for value in installed_version)
        raise SystemExit(f"视频解析基础组件版本过旧（当前{current}），请先运行作战室体检。")

    source = normalized_source(args.source)
    root = cache_root()
    key = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    output_dir = Path(args.out).expanduser().resolve() if args.out else root / key / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        npx,
        "-y",
        PACKAGE,
        "analyze",
        source,
        "--detail",
        args.detail,
        "--language",
        args.language,
        "--max-frames",
        str(args.max_frames),
        "--ocr-language",
        "eng+chi_sim",
        "--out",
        str(output_dir),
    ]
    if args.force_refresh:
        command.append("--force-refresh")

    environment = os.environ.copy()
    environment["OPENAI_API_KEY"] = ""
    environment.pop("WHISPER_HF_MODEL", None)
    bridge_name = (
        "whisper_bridge.cmd"
        if platform.system() == "Windows"
        else "whisper_bridge.mjs"
    )
    environment["WHISPER_BIN"] = str(Path(__file__).with_name(bridge_name).resolve())
    environment["WHISPER_MODEL"] = LOCAL_WHISPER_MODEL
    environment.setdefault("WHISPER_LANGUAGE", args.language)
    environment.setdefault("MCP_CACHE_DIR", str(root / "engine-cache"))
    environment.setdefault("MCP_WRITE_SIDECARS", "0")

    completed = subprocess.run(
        command, capture_output=True, text=True, env=environment, check=False
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        print("视频解析没有完成。请改用本地原始视频，或运行作战室体检。", file=sys.stderr)
        if detail:
            print(detail, file=sys.stderr)
        return completed.returncode

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        print("视频解析结果格式异常，请运行作战室体检。", file=sys.stderr)
        return 2

    add_local_transcript(payload, source, npx, args.language, output_dir)

    if args.json_output:
        atomic_json_write(Path(args.json_output).expanduser().resolve(), payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
