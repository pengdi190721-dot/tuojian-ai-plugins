#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频提示词校验：查AI最容易写错、而脚本查得最准的几样。

查什么（每一段带【总设定】的提示词都查）：
  1. 时间段：从0秒开始、一段接一段、不重叠、不留空、结束在总时长
  2. 时长：单段不超过上限（默认15秒，LibTV里Seedance 2.0）
  3. 时间段个数：2到4个
  4. 参考图：正文里提到的“图几”，【参考】里有没有交代
  5. 人物外形锁定串：同一个人物在各段里是不是一字不差；
     给了人物小传文件的，再和小传里的锁定串比一遍
  6. 台词量：引号里的台词字数，有没有超过“秒数×4.5”
  7. 禁止项：有没有写“不出现字幕/文字”“不要背景音乐”（只提醒）

用法：
  python3 prompt_check.py 视频提示词.md
  python3 prompt_check.py 视频提示词.md --max-seconds 15 --bible 人物小传.md

提示词格式见资料《LibTV视频提示词写法》。
退出码：0 没有错；1 有错；2 文件读不了。纯标准库，不联网。
"""

import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RATE = 4.5
SEG_MIN, SEG_MAX = 2, 4
NUM = r"(\d+(?:\.\d+)?)"
DASH = r"\s*[—–\-~～到至]+\s*"
SEG_RE = re.compile(r"【\s*" + NUM + DASH + NUM + r"\s*秒\s*】")
TOTAL_RE = re.compile(r"【总设定】[^\n]*?时长\s*" + NUM + r"\s*秒")
IMG_RE = re.compile(r"@?图(?:片)?\s*(\d+)")
SECTION_RE = re.compile(r"【([^】]+)】")
SHOT_WORDS = ("远景", "全景", "中景", "中近景", "近景", "特写")
CJK = re.compile(r"[一-鿿A-Za-z0-9]")


def fmt(x):
    return ("%g" % x)


def sections(block):
    """把一段提示词按【标题】切开，返回 [(标题, 内容)]。"""
    out = []
    marks = list(SECTION_RE.finditer(block))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(block)
        out.append((m.group(1).strip(), block[m.end():end].strip()))
    return out


def blocks_of(text):
    """找出所有带【总设定】的提示词块（代码块里的优先，没有代码块就整篇找）。"""
    fenced = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    found = [b for b in fenced if "【总设定】" in b]
    if found:
        return found
    parts = re.split(r"(?=【总设定】)", text)
    return [p for p in parts if p.startswith("【总设定】")]


def parse_people(body):
    """【人物】里每行“名字：锁定串”。"""
    people = {}
    for line in body.splitlines():
        m = re.match(r"^\s*([^：:\s]{1,10})\s*[：:]\s*(.+?)\s*$", line)
        if m:
            people[m.group(1)] = m.group(2).rstrip("。")
    return people


def bible_strings(paths):
    """从人物小传里取“外形锁定串”：标题后第一段正文；名字取文件第一个“# 人物小传｜名字”。"""
    result = {}
    for p in paths or []:
        try:
            t = open(p, "r", encoding="utf-8-sig").read()
        except OSError as e:
            print("读不了人物小传：%s（%s）" % (p, e))
            continue
        for chunk in re.split(r"(?=^#\s*人物小传)", t, flags=re.M):
            nm = re.search(r"^#\s*人物小传[｜|]\s*(\S+)", chunk, re.M)
            lk = re.search(r"^##\s*外形锁定串\s*\n+(.+?)\s*$", chunk, re.M)
            if nm and lk:
                result[nm.group(1)] = lk.group(1).strip().rstrip("。")
    return result


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def check_block(idx, block, max_sec, seen_people, bible):
    errs, warns = [], []
    m = TOTAL_RE.search(block)
    total = float(m.group(1)) if m else None
    if total is None:
        errs.append("【总设定】里没写“时长X秒”")
    elif total > max_sec:
        errs.append("时长%s秒，超过单段上限%s秒，拆成两段" % (fmt(total), fmt(max_sec)))

    # 1-3 时间段
    segs = [(float(a), float(b), mm.start()) for mm in SEG_RE.finditer(block) for a, b in [mm.groups()]]
    if not segs:
        errs.append("没找到时间段，写成【0—4秒】【4—8秒】这样")
    else:
        if segs[0][0] != 0:
            errs.append("第一个时间段没从0秒开始（从%s秒开始）" % fmt(segs[0][0]))
        for i, (a, b, _) in enumerate(segs):
            if b <= a:
                errs.append("时间段【%s—%s秒】结束不晚于开始" % (fmt(a), fmt(b)))
            if i > 0:
                pa, pb, _ = segs[i - 1]
                if a > pb:
                    errs.append("【%s—%s秒】和【%s—%s秒】之间空了%s秒" % (fmt(pa), fmt(pb), fmt(a), fmt(b), fmt(a - pb)))
                elif a < pb:
                    errs.append("【%s—%s秒】和【%s—%s秒】重叠了%s秒" % (fmt(pa), fmt(pb), fmt(a), fmt(b), fmt(pb - a)))
        if total is not None and segs[-1][1] != total:
            errs.append("最后一个时间段结束在%s秒，和总时长%s秒对不上" % (fmt(segs[-1][1]), fmt(total)))
        if not (SEG_MIN <= len(segs) <= SEG_MAX):
            warns.append("分了%d个时间段，统一标准是%d到%d个" % (len(segs), SEG_MIN, SEG_MAX))

    secs = sections(block)
    names = [s for s, _ in secs]
    body_of = {s: b for s, b in secs}

    # 每个时间段有没有写景别；最后一个时间段有没有写“最后停在”
    seg_secs = [(t, b) for t, b in secs if SEG_RE.match("【" + t + "】")]
    for title, body in seg_secs:
        if not any(w in body for w in SHOT_WORDS):
            warns.append("【%s】没写景别（远景、全景、中景、中近景、近景、特写）" % title)
    if seg_secs and "最后停在" not in seg_secs[-1][1]:
        warns.append("最后一个时间段【%s】没写“最后停在”什么样，下一段不好接" % seg_secs[-1][0])

    # 4 参考图
    ref = body_of.get("参考", "")
    defined = set(IMG_RE.findall(ref))
    if not ref:
        errs.append("缺【参考】：写清图1、图2……各管什么")
    used = set(IMG_RE.findall(block))
    missing = sorted(used - defined, key=int)
    if missing:
        errs.append("正文提到了图%s，但【参考】里没交代它管什么" % "、图".join(missing))

    # 5 人物锁定串
    people = parse_people(body_of.get("人物", ""))
    if "人物" not in body_of:
        warns.append("缺【人物】：出场人物的外形锁定串要照抄进来")
    for name, s in people.items():
        if name in bible and bible[name] != s:
            k = first_diff(bible[name], s)
            errs.append("“%s”的锁定串和人物小传不一致，从第%d个字开始不同：小传是“…%s”，这里是“…%s”"
                        % (name, k + 1, bible[name][k:k + 12], s[k:k + 12]))
        if name in seen_people and seen_people[name][1] != s:
            k = first_diff(seen_people[name][1], s)
            errs.append("“%s”的锁定串和第%d段不一致，从第%d个字开始不同：第%d段是“…%s”，这里是“…%s”"
                        % (name, seen_people[name][0], k + 1, seen_people[name][0],
                           seen_people[name][1][k:k + 12], s[k:k + 12]))
        seen_people.setdefault(name, (idx, s))

    # 6 台词量
    lines = re.findall(r"[“\"]([^”\"]+)[”\"]", block)
    talk = sum(len(CJK.findall(x)) for x in lines)
    if total and talk > total * RATE:
        warns.append("引号里的台词共%d字，%s秒按每秒%.1f字最多说%d字，说不完" % (talk, fmt(total), RATE, int(total * RATE)))

    # 7 禁止项和声音
    ban = body_of.get("禁止", "")
    if not ban:
        warns.append("缺【禁止】")
    elif not re.search(r"字幕|文字", ban):
        warns.append("【禁止】里没写“不出现字幕、文字”，模型生成的中文字经常错")
    sound = body_of.get("声音", "")
    if not sound:
        warns.append("缺【声音】：环境声、音效、有没有人说话，都要写")
    elif "背景音乐" not in sound and "配乐" not in sound:
        warns.append("【声音】没交代背景音乐。默认写“不要背景音乐”，配乐留给后期")
    if "结束状态" not in names:
        warns.append("缺【结束状态】")
    return total, len(segs), errs, warns


def main():
    ap = argparse.ArgumentParser(description="视频提示词校验")
    ap.add_argument("file", help="视频提示词文件（.md）")
    ap.add_argument("--max-seconds", type=float, default=15, help="单段时长上限，默认15秒")
    ap.add_argument("--bible", nargs="*", help="人物小传文件，用来核对外形锁定串")
    args = ap.parse_args()
    try:
        text = open(args.file, "r", encoding="utf-8-sig").read()
    except (OSError, UnicodeDecodeError) as e:
        print("读不了文件：%s（%s）" % (args.file, e))
        return 2

    blocks = blocks_of(text)
    if not blocks:
        print("没找到带【总设定】的视频提示词。格式见资料《LibTV视频提示词写法》。")
        return 1
    bible = bible_strings(args.bible)
    seen = {}
    total_err = 0
    grand = 0.0
    skipped = 0
    for i, b in enumerate(blocks, 1):
        if "__" in b or re.search(r"<[^>\n]{1,30}>", b):
            skipped += 1
            print("=" * 60)
            print("第%d段｜这是还没填的模板（有__或<>占位），跳过" % i)
            continue
        total, nseg, errs, warns = check_block(i, b, args.max_seconds, seen, bible)
        grand += total or 0
        print("=" * 60)
        print("第%d段｜时长%s｜时间段%d个" % (i, (fmt(total) + "秒") if total else "未写", nseg))
        print("-" * 60)
        for e in errs:
            print("  ✗ " + e)
        for w in warns:
            print("  △ " + w)
        if not errs and not warns:
            print("  ✓ 时间段、时长、参考图、人物锁定串都对得上")
        total_err += len(errs)
    print("=" * 60)
    print("共%d段（跳过模板%d段），合计%s秒；错误%d处。人物：%s" % (len(blocks), skipped, fmt(grand), total_err,
                                                   "、".join(seen) if seen else "未识别"))
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
