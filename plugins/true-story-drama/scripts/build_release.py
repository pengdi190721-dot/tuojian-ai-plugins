#!/usr/bin/env python3
"""生成不含缓存文件的可分享插件压缩包。"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_NAMES = {".DS_Store", "__pycache__"}


def plugin_version() -> str:
    manifest_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return str(manifest["version"])


def should_include(path: Path) -> bool:
    if any(part in EXCLUDED_NAMES for part in path.parts):
        return False
    return path.suffix != ".pyc"


def build(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"true-story-drama-v{plugin_version()}.zip"

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(PLUGIN_ROOT.rglob("*")):
            relative = source.relative_to(PLUGIN_ROOT)
            if not source.is_file() or not should_include(relative):
                continue
            data = source.read_bytes()
            info = zipfile.ZipInfo(
                filename=f"true-story-drama/{relative.as_posix()}",
                date_time=(2026, 9, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="打包真实故事短剧化插件")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PLUGIN_ROOT.parents[1] / "output",
    )
    args = parser.parse_args()
    print(build(args.output_dir).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
