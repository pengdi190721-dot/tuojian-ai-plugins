#!/usr/bin/env python3
"""维护单个内容任务的阶段状态和交付物索引。"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path


STATE_FILE = ".self-media-job.json"
STAGES = (
    "positioning",
    "setup",
    "topic",
    "research",
    "persona",
    "script",
    "production",
    "review",
)
STATUSES = ("pending", "in_progress", "completed", "blocked")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def state_path(directory: str) -> Path:
    return Path(directory).expanduser().resolve() / STATE_FILE


def read_state(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"未找到任务状态文件：{path}。请先运行 init。")
    with path.open("r", encoding="utf-8") as handle:
        state = json.load(handle)

    previous_stages = state.get("stages", {})
    positioning_default = "completed" if previous_stages else "pending"
    state["stages"] = {
        stage: previous_stages.get(
            stage, positioning_default if stage == "positioning" else "pending"
        )
        for stage in STAGES
    }
    state["schema_version"] = 2
    state["current_stage"] = next_stage(state["stages"])
    return state


def atomic_write(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"{STATE_FILE}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def parse_key_value(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"交付物格式应为 名称=路径，收到：{item}")
        key, value = item.split("=", 1)
        if not key.strip() or not value.strip():
            raise SystemExit(f"交付物名称和路径都不能为空：{item}")
        parsed[key.strip()] = value.strip()
    return parsed


def next_stage(stage_status: dict[str, str]) -> str | None:
    for stage in STAGES:
        if stage_status[stage] != "completed":
            return stage
    return None


def init_command(args: argparse.Namespace) -> int:
    path = state_path(args.dir)
    if path.exists() and not args.force:
        raise SystemExit(f"任务已存在：{path}。如需重建，请明确使用 --force。")
    created = now()
    state = {
        "schema_version": 2,
        "title": args.title,
        "created_at": created,
        "updated_at": created,
        "current_stage": "positioning",
        "stages": {
            stage: "in_progress" if stage == "positioning" else "pending"
            for stage in STAGES
        },
        "artifacts": {},
        "assumptions": [],
        "open_questions": [],
    }
    atomic_write(path, state)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def show_command(args: argparse.Namespace) -> int:
    print(json.dumps(read_state(state_path(args.dir)), ensure_ascii=False, indent=2))
    return 0


def set_command(args: argparse.Namespace) -> int:
    path = state_path(args.dir)
    state = read_state(path)
    state["stages"][args.stage] = args.status
    state["artifacts"].update(parse_key_value(args.artifact))

    for assumption in args.assumption:
        if assumption not in state["assumptions"]:
            state["assumptions"].append(assumption)
    for question in args.question:
        if question not in state["open_questions"]:
            state["open_questions"].append(question)

    state["current_stage"] = next_stage(state["stages"])
    state["updated_at"] = now()
    atomic_write(path, state)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="维护自媒体作战室任务状态")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化任务")
    init_parser.add_argument("--dir", required=True, help="任务目录")
    init_parser.add_argument("--title", required=True, help="任务名称")
    init_parser.add_argument("--force", action="store_true", help="明确覆盖已有状态")
    init_parser.set_defaults(handler=init_command)

    show_parser = subparsers.add_parser("show", help="显示任务状态")
    show_parser.add_argument("--dir", required=True, help="任务目录")
    show_parser.set_defaults(handler=show_command)

    set_parser = subparsers.add_parser("set", help="更新任务阶段")
    set_parser.add_argument("--dir", required=True, help="任务目录")
    set_parser.add_argument("--stage", required=True, choices=STAGES)
    set_parser.add_argument("--status", required=True, choices=STATUSES)
    set_parser.add_argument(
        "--artifact", action="append", default=[], help="交付物，格式为 名称=路径"
    )
    set_parser.add_argument("--assumption", action="append", default=[])
    set_parser.add_argument("--question", action="append", default=[])
    set_parser.set_defaults(handler=set_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
