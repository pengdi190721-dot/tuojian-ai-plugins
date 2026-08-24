#!/usr/bin/env python3
"""检查“自媒体作战室”的本机运行环境。"""

from __future__ import annotations

import argparse
import json
import shutil
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


def inspect_environment() -> dict[str, object]:
    home = Path.home()

    required = {
        name: command_or_path([name], [])
        for name in ("codex", "python3", "git")
    }
    optional_runtime = {
        name: command_or_path([name], [])
        for name in ("node", "npm", "docker", "ffmpeg")
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
        "ready_with_fallbacks" if missing_optional else "ready"
    )

    return {
        "plugin": "自媒体作战室",
        "status": status,
        "required": required,
        "optional_runtime": optional_runtime,
        "external_adapters": adapters,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "notes": [
            "外部能力缺失不会阻止基础的选题、调研、写稿和复盘流程。",
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
