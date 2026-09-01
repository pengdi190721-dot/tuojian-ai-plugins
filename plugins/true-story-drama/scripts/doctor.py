#!/usr/bin/env python3
"""检查“真实故事短剧化”插件包与本机客户端。"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ".codex-plugin/plugin.json",
    ".codebuddy-plugin/plugin.json",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "assets/dependencies.json",
    "scripts/doctor.py",
    "scripts/build_release.py",
    "skills/true-story-drama/SKILL.md",
    "skills/true-story-drama/agents/openai.yaml",
    "skills/true-story-drama/references/material-understanding-and-confirmation.md",
    "skills/true-story-drama/references/truth-contract.md",
    "skills/true-story-drama/references/dramatic-development.md",
    "skills/true-story-drama/references/script-and-shot-format.md",
    "skills/true-story-drama/references/image2-seedance-workflow.md",
    "skills/true-story-drama/references/review-rubric.md",
    "skills/true-story-drama/assets/story-intake-template.md",
    "skills/true-story-drama/assets/story-confirmation-template.md",
    "skills/true-story-drama/assets/adaptation-ledger-template.md",
    "skills/true-story-drama/assets/script-package-template.md",
    "skills/true-story-drama/assets/review-template.md",
    "licenses/zenstory-ai-drama-skills/LICENSE",
)


def load_json(relative_path: str) -> dict[str, Any]:
    path = PLUGIN_ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_package() -> dict[str, Any]:
    missing = [item for item in REQUIRED_FILES if not (PLUGIN_ROOT / item).is_file()]
    errors: list[str] = []
    manifests: dict[str, Any] = {}

    for label, relative_path in (
        ("Codex", ".codex-plugin/plugin.json"),
        ("WorkBuddy", ".codebuddy-plugin/plugin.json"),
    ):
        if relative_path in missing:
            continue
        try:
            manifests[label] = load_json(relative_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{label}清单无法读取：{exc}")

    if len(manifests) == 2:
        names = {item.get("name") for item in manifests.values()}
        versions = {item.get("version") for item in manifests.values()}
        if names != {"true-story-drama"}:
            errors.append("双平台插件名称不一致")
        if len(versions) != 1:
            errors.append("双平台插件版本不一致")

    skill_path = PLUGIN_ROOT / "skills/true-story-drama/SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        if "[TODO:" in skill_text:
            errors.append("技能入口仍有未完成占位内容")
        if "name: true-story-drama" not in skill_text:
            errors.append("技能名称与插件名称不一致")

    status = "ready" if not missing and not errors else "blocked"
    version = None
    if manifests.get("Codex"):
        version = manifests["Codex"].get("version")

    return {
        "plugin": "真实故事短剧化",
        "version": version,
        "status": status,
        "plugin_root": str(PLUGIN_ROOT),
        "missing_files": missing,
        "errors": errors,
        "clients": {
            "Codex": shutil.which("codex") is not None,
            "WorkBuddy": bool(
                shutil.which("codebuddy")
                or shutil.which("workbuddy")
                or Path("/Applications/WorkBuddy.app").exists()
            ),
        },
        "notes": [
            "基础创作不需要付费接口密钥或外部模型服务。",
            "收到故事或采访后先确认故事大意和主题，再进入短剧化。",
            "图片未确认前，Seedance提示词只能标为草案。",
            "插件默认只生成可编辑文本，不会自动生成或发布图片、视频和配音。",
            "客户端未在本机发现不代表插件包不兼容；应在目标电脑完成安装测试。",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    conclusion = "插件包结构完整" if report["status"] == "ready" else "插件包需要修复"
    lines = [
        "# 真实故事短剧化体检",
        "",
        f"结论：{conclusion}",
        f"版本：{report['version'] or '未知'}",
        "",
        "## 双平台入口",
        "",
    ]
    for name, available in report["clients"].items():
        lines.append(f"- {name}：{'本机已发现' if available else '本机未发现'}")

    lines.extend(["", "## 插件包", ""])
    if report["missing_files"]:
        lines.append("- 缺少文件：")
        lines.extend(f"  - {item}" for item in report["missing_files"])
    else:
        lines.append("- 必需文件：完整")

    if report["errors"]:
        lines.append("- 结构问题：")
        lines.extend(f"  - {item}" for item in report["errors"])
    else:
        lines.append("- 双平台名称与版本：一致")

    lines.extend(["", "## 注意", ""])
    lines.extend(f"- {item}" for item in report["notes"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查真实故事短剧化插件包")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    report = inspect_package()
    if args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
