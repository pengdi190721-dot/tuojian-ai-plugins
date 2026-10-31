#!/usr/bin/env python3
"""检查并构建真实故事短剧化的插件包与独立技能包；不联网。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

NAME = "true-story-drama"
DISPLAY = "真实故事短剧化"
ALLOWED = {".md", ".yaml", ".py"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(plugin):
    skill = plugin / "skills" / NAME
    codex = read_json(plugin / ".codex-plugin/plugin.json")
    buddy = read_json(plugin / ".codebuddy-plugin/plugin.json")
    require(codex["name"] == buddy["name"] == NAME == plugin.name, "插件名称不一致")
    require(codex["version"] == buddy["version"], "双平台版本不一致")
    version = codex["version"]
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version), "版本须为三段数字")
    require(codex["skills"] == buddy["skills"] == "./skills/", "技能入口错误")
    require(codex["interface"]["displayName"] == DISPLAY, "中文展示名称错误")
    front = (skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", front, re.S)
    require(match is not None, "缺少技能元数据")
    header = match.group(1)
    require(re.search(r"(?m)^name: " + re.escape(NAME) + r"$", header), "技能名称不一致")
    require(re.search(r'(?m)^  version: "' + re.escape(version) + r'"$', header), "技能版本不一致")
    require(re.search(r"(?m)^description: \S.+", header), "技能缺少描述")
    require((skill / "agents/openai.yaml").is_file(), "缺少技能界面配置")
    # 版本号三处要一起改：安装页、更新记录、仓库首页
    readme = (plugin / "README.md").read_text(encoding="utf-8")
    require("版本：" + version + " ·" in readme, "安装页的版本号没跟着改")
    require("- **" + version + "**" in readme, "更新记录里没有写本版")

    files = []
    for path in sorted(skill.rglob("*")):
        require(not path.is_symlink(), "技能包含符号链接：" + path.name)
        if "__pycache__" in path.parts:
            continue
        if path.is_file():
            require(path.suffix in ALLOWED or path.name == "LICENSE", "技能含有非交付文件：" + path.name)
            text = path.read_text(encoding="utf-8")
            require("[TODO:" not in text, "仍有未完成脚手架")
            if path.suffix == ".md":
                for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    if href.startswith(("https://", "http://", "#")):
                        continue
                    dest = (path.parent / href.split("#")[0]).resolve()
                    require(dest.is_relative_to(skill.resolve()), "技能引用越出自身目录：" + href)
                    require(dest.is_file(), "引用文件不存在：" + href)
            if path.suffix == ".py":
                compile(text, str(path), "exec")
            files.append(path)
    require(len(files) >= 20, "技能资源不完整")

    # 两个检查脚本用自带示范跑一遍，确认能用
    for script, target in (("script_check.py", "references/example.md"),
                           ("prompt_check.py", "references/example.md")):
        result = subprocess.run([sys.executable, "-I", str(skill / "scripts" / script), str(skill / target)],
                                capture_output=True, text=True, encoding="utf-8")
        require(result.returncode == 0, script + " 用示范跑没有通过：\n" + result.stdout[-800:])

    # 在完整源码仓库中构建时，同时核对两个市场入口。
    repo = plugin.parent.parent
    top = repo / "README.md"
    if top.is_file() and (repo / ".codebuddy-plugin").is_dir():
        lines = [l for l in top.read_text(encoding="utf-8").splitlines()
                 if l.startswith("- ") and "(plugins/" + NAME + "/README.md)" in l]
        require(len(lines) == 1 and "当前版本" + version in lines[0], "仓库首页的版本号没跟着改")
    for prefix in (".agents/plugins", ".codebuddy-plugin"):
        path = repo / prefix / "marketplace.json"
        if path.is_file():
            market = read_json(path)
            entries = [e for e in market["plugins"] if e["name"] == NAME]
            require(len(entries) == 1, "市场入口缺失或重复")
            source = entries[0]["source"]
            source_path = source["path"] if isinstance(source, dict) else source
            require((repo / source_path).resolve() == plugin.resolve(), "市场指向错误")
            if isinstance(source, str):
                require(entries[0]["version"] == version, "市场版本不一致")
    return skill, version, files


def pack(target, members):
    expected = {}
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, name in sorted(members, key=lambda pair: pair[1]):
            require(not source.is_symlink(), "不打包符号链接")
            data = source.read_bytes()
            expected[name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if name.endswith(".py") else 0o100644) << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        require(archive.testzip() is None, "压缩包完整性检查失败")
        actual = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist()}
        require(actual == expected, "包内文件与源码不一致")
    return {"file": target.name, "files": len(expected), "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    plugin = Path(__file__).resolve().parents[1]
    out = args.output_dir.resolve()
    require(not out.is_relative_to(plugin), "输出目录不能在插件目录内")
    skill, version, files = validate(plugin)
    out.mkdir(parents=True, exist_ok=True)
    plugin_files = [plugin / p for p in
                    (".codex-plugin/plugin.json", ".codebuddy-plugin/plugin.json", "README.md", "LICENSE",
                     "THIRD_PARTY_NOTICES.md", "assets/dependencies.json",
                     "licenses/zenstory-ai-drama-skills/LICENSE")]
    require(all(p.is_file() for p in plugin_files), "插件发行文件不完整")
    skill_members = [(p, NAME + "/" + p.relative_to(skill).as_posix()) for p in files]
    plugin_members = [(p, NAME + "/" + p.relative_to(plugin).as_posix()) for p in plugin_files + files]
    results = [
        pack(out / f"{NAME}-skill-v{version}.zip", skill_members),
        pack(out / f"{NAME}-plugin-v{version}.zip", plugin_members),
    ]
    report = {"name": NAME, "version": version, "package_validation": "passed",
              "scripts_self_test": "passed", "media_generation_tested": False, "artifacts": results}
    (out / "release-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
