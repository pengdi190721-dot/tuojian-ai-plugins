#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剧本体检：只量量得准的东西。

查什么：
  1. 台词单句长度（一般不超过20字，超过30字必须拆）
  2. 旁白占比（不超过三成），每句旁白有没有写“必要性”
  3. 动作描写一段有没有超过80字
  4. 套话词命中（和资料《台词与旁白》里的表是同一套）
  5. 有台词的人数（5个以内）、地点数（3到5个）、场次（一集不超过8场）
  6. 按每秒4.5字估算说话时长，加上动作时间，跟目标时长对一对

不查什么：好不好看、有没有戏、钩子强不强。那些靠人和自查表判断，脚本数关键词只会误导。

用法：
  python3 script_check.py 剧本.md
  python3 script_check.py 剧本.md --rate 4.5

剧本格式见资料《剧本格式与统一标准》。
退出码：0 没有必须改的问题；1 有必须改的问题；2 文件读不了。
纯标准库，不联网。
"""

import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------- 统一标准（与资料《剧本格式与统一标准》那张表一致） ----------------
LINE_WARN = 20          # 台词单句超过这个字数提醒
LINE_MUST = 30          # 超过这个字数必须拆
NARRATION_RATIO = 0.30  # 旁白字数占比上限
ACTION_MAX = 80         # 动作描写一段上限
CLICHE_MUST = 3         # 套话词超过这个数必须改
SPEAKERS_MAX = 5        # 有台词的人数上限
PLACES_MIN, PLACES_MAX = 3, 5   # 地点数（同一个地方的多场算一个）
SCENES_MAX = 8          # 一集场次上限
DEFAULT_RATE = 4.5      # 每秒字数
ACTION_SEC = (1, 3)     # 每个无台词动作按1到3秒估

# 套话词表（与资料《台词与旁白》第四节同一套）
CLICHES = [
    ("书面词", r"进行|实现|赋能|基于|从而|予以|值得我们思考|值得思考"),
    ("总结腔", r"这一刻[^。！？]{0,12}(明白|懂得|意识到)|终于明白|原来这就是|的意义"),
    ("金句腔", r"不是[^。！？\n]{1,15}而是|真正的[^。！？\n]{1,12}往往"),
    ("模板表情", r"眼中闪过一丝|嘴角勾起|深吸一口气|瞳孔骤缩|瞳孔猛地一缩"),
    ("情绪直说", r"感到(非常|十分|特别)|五味杂陈|百感交集|心中一暖|心头一震"),
    ("比喻堆砌", r"仿佛|宛如|如同[^。！？\n]{0,12}一般"),
    ("弱动词", r"不禁|不由得"),
]

CJK_OR_ALNUM = re.compile(r"[一-鿿A-Za-z0-9]")
SCENE_RE = re.compile(r"^#{2,3}\s*第\s*[0-9一二三四五六七八九十百]+\s*场")
EPISODE_RE = re.compile(r"^#\s*第\s*[0-9一二三四五六七八九十百]+\s*集")
TARGET_RE = re.compile(r"目标时长[：:]\s*(\d+)")
TAG_RE = re.compile(r"^【([^】]+)】\s*(.*)$")
# 台词：人物名（可带括号提示）+ 冒号 + 内容
DIALOGUE_RE = re.compile(r"^([^\s【#>|`*\-他她它我你][^：:（(\s，,。]{0,5})\s*(?:[（(][^）)]*[）)])?\s*[：:]\s*(.+)$")
NECESSITY_RE = re.compile(r"[（(]\s*必要性[：:][^）)]*[）)]")
SENT_SPLIT = re.compile(r"[。！？!?…]+")


def count(text):
    return len(CJK_OR_ALNUM.findall(text))


def place_of(title):
    """从“第1场　内·车间·深夜”里取出地点“车间”。"""
    parts = re.split(r"[·・•]", title)
    if len(parts) >= 3:
        return parts[1].strip()
    if len(parts) == 2:
        return parts[1].strip()
    return ""


def strip_quotes(text):
    return text.strip().strip("“”\"'「」")


def parse(lines):
    """把剧本拆成：集 → 场 → 行。"""
    episodes = []
    ep = {"title": "（全文）", "target": None, "scenes": [], "loose": []}
    scene = None
    in_fence = False
    scene_in_fence = False
    for no, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            if not in_fence and scene_in_fence:
                scene = None  # 代码块里的剧本到此结束
                scene_in_fence = False
            continue
        if not s:
            continue
        if EPISODE_RE.match(s):
            if ep["scenes"] or ep["loose"]:
                episodes.append(ep)
            ep = {"title": s.lstrip("# ").strip(), "target": None, "scenes": [], "loose": []}
            scene = None
            continue
        m = TARGET_RE.search(s)
        if m and ep["target"] is None:
            ep["target"] = int(m.group(1))
        if SCENE_RE.match(s):
            scene = {"title": s.lstrip("# ").strip(), "items": []}
            scene_in_fence = in_fence
            ep["scenes"].append(scene)
            continue
        if s.startswith("#"):
            scene = None  # 别的标题出现，说明剧本正文结束了
            continue
        if s.startswith((">", "|", "- ", "* ", "**")) or re.match(r"^\d+\.\s", s):
            continue  # 说明、表格、列表、加粗说明不算剧本正文
        if scene is None:
            continue  # 场景之前的内容（说明文字）不计
        tag = TAG_RE.match(s)
        if tag:
            kind, rest = tag.group(1), tag.group(2)
            if kind in ("旁白", "画外"):
                body = rest
                spk = ""
                dm = re.match(r"^([^：:]{1,10})[：:](.*)$", rest)
                if dm:
                    spk, body = dm.group(1).strip(), dm.group(2)
                has_need = bool(NECESSITY_RE.search(body))
                body = NECESSITY_RE.sub("", body)
                scene["items"].append({"kind": kind, "speaker": spk, "text": strip_quotes(body),
                                       "line": no, "need": has_need})
            # 音效、画面文字、连续性、转场：不计入说话和动作
            continue
        dm = DIALOGUE_RE.match(s)
        if dm and count(dm.group(1)) <= 6:
            scene["items"].append({"kind": "台词", "speaker": dm.group(1).strip(),
                                   "text": strip_quotes(dm.group(2)), "line": no})
            continue
        scene["items"].append({"kind": "动作", "text": s, "line": no})
    if ep["scenes"] or ep["loose"]:
        episodes.append(ep)
    return episodes


def check_episode(ep, rate, all_text_lines):
    must, warn, info = [], [], []
    items = [it for sc in ep["scenes"] for it in sc["items"]]
    n_scenes = len(ep["scenes"])

    speakers = sorted({it["speaker"] for it in items
                       if it["kind"] in ("台词", "画外") and it.get("speaker")})
    spoken_chars = sum(count(it["text"]) for it in items if it["kind"] in ("台词", "画外"))
    narr_chars = sum(count(it["text"]) for it in items if it["kind"] == "旁白")
    actions = [it for it in items if it["kind"] == "动作"]

    # 1. 台词单句长度
    for it in items:
        if it["kind"] not in ("台词", "画外", "旁白"):
            continue
        for sent in SENT_SPLIT.split(it["text"]):
            c = count(sent)
            if c > LINE_MUST:
                must.append("第%d行 一句话%d字，超过%d字必须拆：%s" % (it["line"], c, LINE_MUST, sent[:24]))
            elif c > LINE_WARN:
                warn.append("第%d行 一句话%d字，超过%d字，读一遍看能不能一口气说完：%s"
                            % (it["line"], c, LINE_WARN, sent[:24]))

    # 2. 旁白
    total_voice = spoken_chars + narr_chars
    ratio = (narr_chars / total_voice) if total_voice else 0.0
    if ratio > NARRATION_RATIO:
        warn.append("旁白占比%.0f%%，超过三成。先写纯动作和对白版，再看哪句旁白删不掉" % (ratio * 100))
    for it in items:
        if it["kind"] == "旁白" and not it["need"]:
            must.append("第%d行 旁白没写“必要性”，过一遍删除测试：删掉能看懂就删" % it["line"])

    # 3. 动作描写长度
    for it in actions:
        c = count(it["text"])
        if c > ACTION_MAX:
            warn.append("第%d行 动作描写%d字，超过%d字，拆成两段或删掉看不见的部分" % (it["line"], c, ACTION_MAX))

    # 4. 套话词（台词、旁白、动作都查）
    hits = []
    for it in items:
        for name, pat in CLICHES:
            for m in re.finditer(pat, it["text"]):
                hits.append((it["line"], name, m.group(0)))
    if len(hits) > CLICHE_MUST:
        must.append("套话词%d处，超过%d处，必须改" % (len(hits), CLICHE_MUST))
    elif hits:
        warn.append("套话词%d处，目标是0处" % len(hits))

    # 5. 人数、地点数、场次
    places = sorted({place_of(sc["title"]) for sc in ep["scenes"]} - {""})
    if len(speakers) > SPEAKERS_MAX:
        warn.append("有台词的人%d个（%s），超过%d个，看能不能合并" % (len(speakers), "、".join(speakers), SPEAKERS_MAX))
    if places and not (PLACES_MIN <= len(places) <= PLACES_MAX):
        warn.append("地点%d个（%s），统一标准是%d到%d个（单集）" % (len(places), "、".join(places), PLACES_MIN, PLACES_MAX))
    if n_scenes > SCENES_MAX:
        warn.append("一集%d场，超过%d场，节奏会碎，看能不能合并" % (n_scenes, SCENES_MAX))
    if n_scenes == 0:
        must.append("没找到场景标题。场景标题写成“## 第1场　内·地点·时间”")

    # 6. 时长估算
    talk_sec = total_voice / rate if rate else 0
    lo = talk_sec + len(actions) * ACTION_SEC[0]
    hi = talk_sec + len(actions) * ACTION_SEC[1]
    info.append("场次%d场｜地点%d个｜有台词的人%d个（%s）｜动作行%d条"
                % (n_scenes, len(places), len(speakers), "、".join(speakers) or "无", len(actions)))
    info.append("台词%d字，旁白%d字，旁白占比%.0f%%" % (spoken_chars, narr_chars, ratio * 100))
    info.append("说话约%.0f秒（按每秒%.1f字）；加上动作，估算%.0f到%.0f秒" % (talk_sec, rate, lo, hi))
    if ep["target"]:
        if lo > ep["target"] * 1.15:
            warn.append("估算最少%.0f秒，比目标%d秒多出一截。先删重复解释，再合并过场" % (lo, ep["target"]))
        elif hi < ep["target"] * 0.6:
            warn.append("估算最多%.0f秒，比目标%d秒短很多，看看回报和反应有没有留够时间" % (hi, ep["target"]))
    return must, warn, info, hits


def main():
    ap = argparse.ArgumentParser(description="剧本体检：只量量得准的东西")
    ap.add_argument("file", help="剧本文件（.md 或 .txt）")
    ap.add_argument("--rate", type=float, default=DEFAULT_RATE, help="每秒字数，默认4.5")
    args = ap.parse_args()
    try:
        with open(args.file, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        print("读不了文件：%s（%s）" % (args.file, e))
        return 2

    episodes = parse(lines)
    if not episodes:
        print("没找到剧本正文。集标题写成“# 第1集　集名”，场景标题写成“## 第1场　内·地点·时间”。")
        return 1

    any_must = False
    for ep in episodes:
        must, warn, info, hits = check_episode(ep, args.rate, lines)
        print("=" * 60)
        print("剧本体检｜%s%s" % (ep["title"], ("｜目标%d秒" % ep["target"]) if ep["target"] else ""))
        print("=" * 60)
        for s in info:
            print("· " + s)
        if hits:
            print("-" * 60)
            print("套话词明细：")
            for line, name, word in hits:
                print("  第%d行【%s】%s" % (line, name, word))
        print("-" * 60)
        if must:
            any_must = True
            print("必须改：")
            for s in must:
                print("  ✗ " + s)
        if warn:
            print("提醒：")
            for s in warn:
                print("  △ " + s)
        if not must and not warn:
            print("✓ 量得准的几项都没问题。好不好看，接着按《交付前自查》过一遍。")
        print()
    print("说明：脚本只查长度、占比、套话词和时长，不判断有没有戏。")
    return 1 if any_must else 0


if __name__ == "__main__":
    sys.exit(main())
