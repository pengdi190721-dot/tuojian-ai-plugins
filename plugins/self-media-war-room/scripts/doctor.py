#!/usr/bin/env python3
"""检查“自媒体作战室”的本机运行环境。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def first_existing_path(paths: list[Path]) -> str | None:
    for path in paths:
        if path.exists():
            return str(path)
    return None


def command_or_path(commands: list[str], paths: list[Path]) -> dict[str, object]:
    for command in commands:
        found = shutil.which(command)
        if found:
            return {"available": True, "location": found}
    found_path = first_existing_path(paths)
    if found_path:
        return {"available": True, "location": found_path}
    return {"available": False, "location": None}


def command_version(command: str) -> tuple[int, int, int] | None:
    found = shutil.which(command)
    if not found:
        return None
    completed = subprocess.run(
        [found, "--version"], capture_output=True, text=True, check=False
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", output)
    if completed.returncode or not match:
        return None
    return tuple(int(value) for value in match.groups())


def inspect_environment() -> dict[str, object]:
    home = Path.home()

    required = {
        "内置创作工作流": {
            "available": True,
            "location": "随插件安装",
        }
    }
    clients = {
        "Codex": command_or_path(["codex"], []),
        "WorkBuddy": command_or_path(
            ["codebuddy", "workbuddy"],
            [Path("/Applications/WorkBuddy.app")],
        ),
    }
    optional_runtime = {
        name: command_or_path([name], [])
        for name in (
            "python3",
            "git",
            "node",
            "npm",
            "npx",
            "yt-dlp",
            "whisper",
            "ffmpeg",
        )
    }
    node_version = command_version("node")
    minimum_node = (22, 12, 0)
    video_analysis_available = bool(
        optional_runtime["npx"]["available"]
        and node_version
        and node_version >= minimum_node
    )
    video_analysis = {
        "available": video_analysis_available,
        "mode": "本地语音识别，不需要付费接口密钥",
        "engine": "mcp-video-analyzer@0.10.0 + scrybe@0.2.0",
        "node_version": (
            ".".join(str(value) for value in node_version) if node_version else None
        ),
        "minimum_node": "22.12.0",
        "public_link_support": bool(optional_runtime["yt-dlp"]["available"]),
    }
    adapters = {
        "Agent Reach": command_or_path(
            ["agent-reach"],
            [
                home / ".agent-reach-venv/bin/agent-reach",
                home / ".codex/skills/agent-reach",
                home / ".agents/skills/agent-reach",
            ],
        ),
        "TrendRadar": command_or_path(
            ["trendradar"],
            [
                home / "TrendRadar",
                home / "trendradar",
                home / "Documents/TrendRadar",
            ],
        ),
        "HyperFrames": command_or_path(
            ["hyperframes"],
            [
                home / ".codex/skills/hyperframes",
                home / ".agents/skills/hyperframes",
                home / ".codex/.tmp/plugins/plugins/hyperframes",
            ],
        ),
        "huashu-design": command_or_path(
            [],
            [
                home / ".codex/skills/huashu-design",
                home / ".agents/skills/huashu-design",
            ],
        ),
        "nuwa-skill": command_or_path(
            [],
            [
                home / ".codex/skills/nuwa-skill",
                home / ".agents/skills/nuwa-skill",
            ],
        ),
        "brand-voice-guard": command_or_path(
            [],
            [
                home / ".codex/skills/brand-voice-guard",
                home / ".agents/skills/brand-voice-guard",
                home / ".codex/skills/brand-voice-enforcement",
                home / ".agents/skills/brand-voice-enforcement",
            ],
        ),
    }

    missing_required = [
        name for name, item in required.items() if not item["available"]
    ]
    missing_optional = [
        name
        for group in (optional_runtime, adapters)
        for name, item in group.items()
        if not item["available"]
    ]
    status = "blocked" if missing_required else (
        "ready" if video_analysis_available else "ready_with_fallbacks"
    )

    return {
        "plugin": "自媒体作战室",
        "status": status,
        "required": required,
        "clients": clients,
        "video_analysis": video_analysis,
        "optional_runtime": optional_runtime,
        "external_adapters": adapters,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "notes": [
            "外部能力缺失不会阻止基础的定位、选题、调研和写稿流程。",
            "视频解析就绪后，成片评分和对标拆解会自动读取转写、关键画面与时间线。",
            "首次解析可能需要联网下载本地识别组件；不会要求提供付费接口密钥。",
            "发现外部工具只代表本机存在；账号登录、渠道权限和接口额度仍需单独验证。",
            "剪辑工具只处理机械工作，发布前必须人工检查事实、画面、字幕、节奏和隐私。",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    status_map = {
        "ready": "完整可用",
        "ready_with_fallbacks": "基础可用，可选增强未全部安装",
        "blocked": "基础环境不完整",
    }
    lines = [
        "# 自媒体作战室环境体检",
        "",
        f"结论：{status_map[str(report['status'])]}",
        "",
        "## 必需环境",
        "",
    ]
    for name, item in report["required"].items():
        mark = "已就绪" if item["available"] else "缺失"
        location = f"（{item['location']}）" if item["location"] else ""
        lines.append(f"- {name}：{mark}{location}")

    lines.extend(["", "## 成片评分与对标拆解", ""])
    video_analysis = report["video_analysis"]
    if video_analysis["available"]:
        lines.append("- 视频解析：已就绪，上传视频后会自动处理")
        lines.append(f"- 语音识别：{video_analysis['mode']}")
        public_link = "可直接处理" if video_analysis["public_link_support"] else "可能需要改为上传本地视频"
        lines.append(f"- 单条公开视频链接：{public_link}")
    else:
        lines.append("- 视频解析：基础组件未就绪，可先用转写和截图做局部分析")
        lines.append("- 下一步：只有需要排障时再查看下面的组件明细")

    lines.extend(["", "## 当前平台", ""])
    for name, item in report["clients"].items():
        mark = "已发现" if item["available"] else "本机未发现"
        lines.append(f"- {name}：{mark}")

    lines.extend(["", "## 可选运行环境", ""])
    for name, item in report["optional_runtime"].items():
        mark = "已就绪" if item["available"] else "未安装"
        location = f"（{item['location']}）" if item["location"] else ""
        lines.append(f"- {name}：{mark}{location}")

    lines.extend(["", "## 外部增强能力", ""])
    for name, item in report["external_adapters"].items():
        mark = "已发现" if item["available"] else "未发现，可使用内置降级流程"
        location = f"（{item['location']}）" if item["location"] else ""
        lines.append(f"- {name}：{mark}{location}")

    lines.extend(["", "## 注意", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查自媒体作战室运行环境")
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="json", dest="output_format"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="缺少必需环境时以非零状态退出",
    )
    args = parser.parse_args()

    report = inspect_environment()
    if args.output_format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and report["missing_required"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
