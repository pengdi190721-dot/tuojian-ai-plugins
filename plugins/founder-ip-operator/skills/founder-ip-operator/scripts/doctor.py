#!/usr/bin/env python3
"""检查“创始人IP操盘手”的本机运行环境。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
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


def python_module(name: str) -> bool:
    # 口播体检用的是用户自己的 python3，不一定是跑体检的这个解释器，所以去问 python3 本身。
    python = shutil.which("python3")
    if not python:
        return False
    completed = subprocess.run(
        [python, "-c", f"import {name}"], capture_output=True, check=False
    )
    return completed.returncode == 0


def douyin_reachable() -> bool:
    # 只试一下能不能领到抖音的匿名访问凭证：领得到说明网络通，真能不能读要发一条链接试。
    sys.dont_write_bytecode = True
    try:
        import read_douyin_link as reader
    except ImportError:
        return False
    reader.RETRIES = 0
    reader.TIMEOUT = 8
    return bool(reader.register_ttwid())


def inspect_environment(check_network: bool = True) -> dict[str, object]:
    home = Path.home()

    required = {
        "核心策划方法": {
            "available": True,
            "location": "随技能安装",
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
        "voice_check_support": bool(optional_runtime["ffmpeg"]["available"] and python_module("numpy")),
        "voice_check_plot": python_module("matplotlib"),
    }
    douyin_direct = {
        "script": "scripts/read_douyin_link.py",
        "checked": check_network,
        "reachable": douyin_reachable() if check_network else None,
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
        "plugin": "创始人IP操盘手",
        "status": status,
        "required": required,
        "clients": clients,
        "video_analysis": video_analysis,
        "douyin_direct": douyin_direct,
        "optional_runtime": optional_runtime,
        "external_adapters": adapters,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "notes": [
            "外部增强能力没装也不影响访谈、定位、选题、写稿和复盘。",
            "视频解析就绪后，成片评分、对标拆解和视频复盘会自动读取转写、关键画面与时间线。",
            "首次解析可能需要联网下载本地识别组件；不会要求提供付费接口密钥。",
            "发现外部工具只代表本机存在；账号登录、渠道权限和接口额度仍需单独验证。",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    status_map = {
        "ready": "完整可用",
        "ready_with_fallbacks": "基础可用，可选增强未全部安装",
        "blocked": "基础环境不完整",
    }
    lines = [
        "# 创始人IP操盘手环境体检",
        "",
        f"结论：{status_map[str(report['status'])]}",
        "",
        "## 不用装就能用的",
        "",
    ]
    for name, item in report["required"].items():
        mark = "已就绪" if item["available"] else "缺失"
        location = f"（{item['location']}）" if item["location"] else ""
        lines.append(f"- {name}：{mark}{location}")

    lines.append("- 定位、选题、写稿、看截图复盘、投流教学：都能用，不用装任何东西")

    lines.extend(["", "## 读视频（成片打分、拆对标、视频复盘）", ""])
    video_analysis = report["video_analysis"]
    if video_analysis["available"]:
        lines.append("- 读视频：能用，发视频文件过来就会自动处理")
        lines.append(f"- 听写说话内容：{video_analysis['mode']}")
    else:
        node = video_analysis["node_version"]
        reason = f"电脑上的 Node.js 版本太旧（现在是{node}，要22.12以上）" if node else "电脑上还没装 Node.js"
        lines.append(f"- 读视频：还不能用，因为{reason}")
        lines.append("- 下一步：打开 nodejs.org，下载页面上推荐的那个版本，双击安装，装完再说一句“帮我检查一下”")
        lines.append("- 装好之前：可以先把视频里说的话（文字稿）和几张截图发过来，能做一部分分析")
    if video_analysis["voice_check_support"]:
        plot = "会出曲线图" if video_analysis["voice_check_plot"] else "只出文字报告；想要曲线图，在终端输入 python3 -m pip install matplotlib"
        lines.append(f"- 口播体检：能用，{plot}")
    else:
        lines.append("- 口播体检：还不能用。要装 ffmpeg，再在终端输入 python3 -m pip install numpy matplotlib")

    lines.extend(["", "## 发抖音链接（直接读，不用注册，不下载视频）", ""])
    douyin = report["douyin_direct"]
    if not douyin["checked"]:
        lines.append("- 发抖音链接：这次没联网检查，直接发一条链接试试")
    elif douyin["reachable"]:
        lines.append("- 发抖音链接：能连上抖音，直接发一条链接试试")
    else:
        lines.append("- 发抖音链接：这台电脑现在连不上抖音。开着加速器或翻墙软件的，关掉再查一次")
    if video_analysis["available"]:
        lines.append("- 听写视频里说了什么：能用，只取声音在本机听写，听完就删")
    else:
        lines.append("- 直接读能拿到标题文案、互动数和封面；要听写视频里说了什么，要装好上面说的 Node.js")
    lines.append("- 读不出来，或者是小红书、B站、视频号的视频：在App里把视频保存下来发过来（抖音是点“分享”、再点“保存本地”；要上面的“读视频”能用）")

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
        mark = "已发现" if item["available"] else "没装，不影响，用技能自带的做法"
        location = f"（{item['location']}）" if item["location"] else ""
        lines.append(f"- {name}：{mark}{location}")

    lines.extend(["", "## 注意", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查创始人IP操盘手运行环境")
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="json", dest="output_format"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="缺少必需环境时以非零状态退出",
    )
    parser.add_argument("--offline", action="store_true", help="不联网检查能不能连上抖音")
    args = parser.parse_args()

    report = inspect_environment(check_network=not args.offline)
    if args.output_format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and report["missing_required"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
