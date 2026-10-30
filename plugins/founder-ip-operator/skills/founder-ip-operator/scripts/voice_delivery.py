#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播交付体检：用 ffmpeg 算音量包络、停顿和语速曲线，输出人话报告。

不需要任何模型，只用 ffmpeg + numpy（画曲线图另需 matplotlib，没装就只出文字报告）。可选传入转写 JSON 以计算语速。

用法：
    python3 voice_delivery.py 视频.mp4
    python3 voice_delivery.py 视频.mp4 --transcript 转写.json --out 输出目录

输出：
    report.md   人话版体检报告
    data.json   原始数据
    curve.png   音量+语速曲线图
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    # 新手电脑上常见：官网装的 Python 不带 numpy，直接告诉他怎么装，不甩报错。
    print("[voice_delivery] 还缺一个叫 numpy 的小工具。打开终端，输入：python3 -m pip install numpy matplotlib"
          "，装好以后再试一次。", file=sys.stderr)
    raise SystemExit(2)

SR = 16000          # 统一重采样率
WIN = 0.10          # 分析窗 100ms
SILENCE_ABS = -42.0 # 绝对静音阈值 dBFS
SILENCE_REL = 10.0  # 相对噪声底的抬升 dB
MIN_PAUSE = 0.35    # 记为停顿的最短时长（秒）
WEAK_RATIO = 0.55   # 低能量段：低于本段中位数的比例
MIN_WEAK = 1.0      # 低能量段最短时长

PUNCT = re.compile(r"[\s，。！？、；：“”‘’（）()《》…—\-~,.!?;:\"'\[\]{}]")


def die(msg: str, code: int = 2):
    print(f"[voice_delivery] {msg}", file=sys.stderr)
    sys.exit(code)


def need_ffmpeg():
    for exe in ("ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            die(f"没找到 {exe}。装好 ffmpeg 再来，或让环境体检脚本检查。")


def probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    raw = subprocess.run(cmd, capture_output=True, text=True)
    if raw.returncode != 0:
        die(f"读不了这个文件：{raw.stderr.strip()[:200]}")
    info = json.loads(raw.stdout)
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    video = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    if not audio:
        die("这个文件没有音轨，没法测语气。请确认导出时勾了音频。")
    dur = float(info.get("format", {}).get("duration") or 0)
    return {
        "duration": dur,
        "has_video": bool(video),
        "video": {
            "width": video[0].get("width"), "height": video[0].get("height"),
            "fps": video[0].get("r_frame_rate"),
        } if video else None,
        "audio": {
            "codec": audio[0].get("codec_name"),
            "sample_rate": audio[0].get("sample_rate"),
            "channels": audio[0].get("channels"),
        },
    }


def decode_pcm(path: Path) -> np.ndarray:
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-",
    ]
    raw = subprocess.run(cmd, capture_output=True)
    if raw.returncode != 0 or not raw.stdout:
        die("音频解码失败，可能是文件损坏或编码不被支持。")
    pcm = np.frombuffer(raw.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if pcm.size == 0:
        die("解出来是空音轨。")
    return pcm


def envelope(pcm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hop = int(SR * WIN)
    n = pcm.size // hop
    frames = pcm[: n * hop].reshape(n, hop)
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-12)
    t = np.arange(n) * WIN
    return t, db


def find_pauses(t: np.ndarray, db: np.ndarray) -> list[dict]:
    floor = float(np.percentile(db, 10))
    thr = max(SILENCE_ABS, floor + SILENCE_REL)
    mask = db < thr
    out, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            dur = (i - start) * WIN
            if dur >= MIN_PAUSE:
                out.append({"start": round(t[start], 2), "end": round(t[i - 1] + WIN, 2),
                            "duration": round(dur, 2)})
            start = None
    if start is not None:
        dur = (len(mask) - start) * WIN
        if dur >= MIN_PAUSE:
            out.append({"start": round(t[start], 2), "end": round(t[-1] + WIN, 2),
                        "duration": round(dur, 2)})
    return out


def find_weak(t: np.ndarray, db: np.ndarray, pauses: list[dict]) -> list[dict]:
    """找“声音明显变小”的段：低于中位数较多，且不是纯静音。"""
    talking = db[db > SILENCE_ABS]
    if talking.size < 10:
        return []
    med = float(np.median(talking))
    thr = med + 20 * math.log10(WEAK_RATIO)
    mask = (db < thr) & (db > SILENCE_ABS)
    out, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            dur = (i - start) * WIN
            if dur >= MIN_WEAK:
                out.append({"start": round(t[start], 2), "end": round(t[i - 1] + WIN, 2),
                            "duration": round(dur, 2),
                            "drop_db": round(float(np.mean(db[start:i]) - med), 1)})
            start = None
    if start is not None:
        dur = (len(mask) - start) * WIN
        if dur >= MIN_WEAK:
            out.append({"start": round(t[start], 2), "end": round(t[-1] + WIN, 2),
                        "duration": round(dur, 2),
                        "drop_db": round(float(np.mean(db[start:]) - med), 1)})
    return out


def hanzi_count(s: str) -> int:
    return len(PUNCT.sub("", s or ""))


def load_segments(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    found = []

    def walk(o):
        if found:
            return
        if isinstance(o, dict):
            segs = o.get("segments")
            if isinstance(segs, list) and segs and isinstance(segs[0], dict) \
                    and "start" in segs[0] and "text" in segs[0]:
                found.extend(segs)
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            if o and isinstance(o[0], dict) and "start" in o[0] and "text" in o[0]:
                found.extend(o)
            else:
                for v in o:
                    walk(v)

    walk(data)
    if not found:
        die("转写文件里没找到 segments（需要含 start、end、text 的数组）。")
    return found


def speed_curve(segments: list[dict], total: float, step: float = 1.0) -> list[dict]:
    bins = int(math.ceil(total / step))
    acc = [[] for _ in range(bins)]
    for s in segments:
        st, en = float(s.get("start", 0)), float(s.get("end", 0))
        n = hanzi_count(s.get("text", ""))
        if n == 0 or en <= st:
            continue
        for b in range(bins):
            lo, hi = b * step, (b + 1) * step
            overlap = max(0.0, min(en, hi) - max(st, lo))
            if overlap > 0:
                acc[b].append(n * overlap / (en - st))
    return [{"t": b * step, "chars_per_sec": round(sum(v), 2) if v else 0.0}
            for b, v in enumerate(acc)]


def plot(t, db, pauses, speeds, out_png: Path, title: str) -> bool:
    try:
        import matplotlib
    except ImportError:
        return False
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=120)
    ax.plot(t, db, lw=0.9, color="#2563eb")
    ax.set_xlabel("seconds")
    ax.set_ylabel("volume (dBFS)", color="#2563eb")
    ax.grid(alpha=0.25, ls="--", lw=0.6)

    for p in pauses:
        ax.axvspan(p["start"], p["end"], color="#f59e0b", alpha=0.22, lw=0)

    if speeds:
        ax2 = ax.twinx()
        xs = [s["t"] + 0.5 for s in speeds]
        ys = [s["chars_per_sec"] for s in speeds]
        ax2.plot(xs, ys, lw=1.4, color="#dc2626", marker="o", ms=2.5)
        ax2.set_ylabel("chars / sec", color="#dc2626")
        ax2.set_ylim(bottom=0)

    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    return True


def verdict(stats: dict, pauses: list[dict], weak: list[dict], speeds: list[dict]) -> list[dict]:
    """把数据翻成人话。每条含：结论、证据、怎么改。"""
    out = []

    if stats["dynamic_range"] < 6:
        out.append({"问题": "整条太平，没有起伏",
                    "证据": f"有效音量动态范围只有 {stats['dynamic_range']} dB",
                    "怎么改": "找出全片最重要的一句，把那句说重一点、前一句刻意压低，做出落差"})

    long_p = [p for p in pauses if p["duration"] >= 1.5]
    if long_p:
        worst = max(long_p, key=lambda x: x["duration"])
        out.append({"问题": "有明显卡壳式停顿",
                    "证据": f"{len(long_p)} 处超过 1.5 秒，最长 {worst['duration']} 秒（第 {int(worst['start'])} 秒）",
                    "怎么改": "这几处要么是忘词，要么是句子太长。把长句拆短，或提前把这几句单独练三遍"})

    if weak:
        worst = max(weak, key=lambda x: x["duration"])
        out.append({"问题": "有段落声音明显变小（像没底气或在念）",
                    "证据": f"{len(weak)} 段，最长 {worst['duration']} 秒（第 {int(worst['start'])} 秒），比中位音量低 {abs(worst['drop_db'])} dB",
                    "怎么改": "把这段单独重录。录音时身体前倾一点、下巴略微向下，声音自然会实"})

    if speeds:
        vals = [s["chars_per_sec"] for s in speeds if s["chars_per_sec"] > 0]
        if vals:
            avg = sum(vals) / len(vals)
            if avg < 4.5:
                out.append({"问题": "整体语速偏慢，听着容易走神",
                            "证据": f"平均 {avg:.1f} 字/秒",
                            "怎么改": "不是加快语速，是删字。把每句压到 15 字以内再录"})
            elif avg > 7.5:
                out.append({"问题": "整体语速偏快，观众跟不上",
                            "证据": f"平均 {avg:.1f} 字/秒",
                            "怎么改": "在每段结论前加一个 0.3 秒的停顿，给他反应时间"})
            if len(vals) >= 4:
                sd = float(np.std(vals))
                if sd > avg * 0.55:
                    gaps = [f"第{int(s['t'])}秒{s['chars_per_sec']:.1f}" for s in speeds
                            if s["chars_per_sec"] == 0][:6]
                    out.append({"问题": "语速忽快忽慢，节奏不稳",
                                "证据": f"标准差 {sd:.1f}，空窗：{('、'.join(gaps) or '无')}",
                                "怎么改": "先把断句定下来再录。每次都在同一批位置停，节奏就稳了"})

    tail = [d for tt, d in zip(stats["_t"], stats["_db"]) if tt >= stats["duration"] * 0.9]
    head = [d for tt, d in zip(stats["_t"], stats["_db"]) if tt <= max(3, stats["duration"] * 0.1)]
    if tail and head:
        drop = float(np.mean(head) - np.mean(tail))
        if drop > 6:
            out.append({"问题": "结尾音量掉下来了，收尾没劲",
                        "证据": f"最后 10% 比开头低 {drop:.1f} dB",
                        "怎么改": "结尾那句单独录。要么站起来说，要么刻意往镜头前凑一点"})

    if not out:
        out.append({"问题": "没发现明显问题", "证据": "音量、停顿、语速都在正常范围",
                    "怎么改": "别改了，可以发"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="口播交付体检：音量包络 + 停顿 + 语速曲线")
    ap.add_argument("media", help="视频或音频文件路径")
    ap.add_argument("--transcript", help="转写 JSON（含 segments 的 start/end/text），不给就只测音量")
    ap.add_argument("--out", help="输出目录，默认与媒体同目录下的 <文件名>-delivery")
    ap.add_argument("--json-output", help="只把 data.json 写到这个路径")
    args = ap.parse_args()

    need_ffmpeg()
    src = Path(args.media).expanduser().resolve()
    if not src.exists():
        die(f"文件不存在：{src}")

    meta = probe(src)
    pcm = decode_pcm(src)
    t, db = envelope(pcm)
    pauses = find_pauses(t, db)
    weak = find_weak(t, db, pauses)

    talking = db[db > SILENCE_ABS]
    dyn = float(np.percentile(talking, 95) - np.percentile(talking, 10)) if talking.size else 0.0

    stats = {
        "duration": round(meta["duration"], 2),
        "dynamic_range": round(dyn, 1),
        "median_db": round(float(np.median(talking)), 1) if talking.size else None,
        "speech_ratio": round(float(np.mean(db > SILENCE_ABS)) * 100, 1),
        "pause_count": len(pauses),
        "pause_total": round(sum(p["duration"] for p in pauses), 2),
        "_t": t, "_db": db,
    }

    speeds = []
    if args.transcript:
        segs = load_segments(Path(args.transcript).expanduser().resolve())
        speeds = speed_curve(segs, meta["duration"])

    problems = verdict(stats, pauses, weak, speeds)
    clean = {k: v for k, v in stats.items() if not k.startswith("_")}
    clean["weak_segments"] = len(weak)

    out_dir = Path(args.out).expanduser().resolve() if args.out else src.parent / f"{src.stem}-delivery"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "data.json").write_text(json.dumps({
        "source": str(src), "meta": meta, "stats": clean,
        "pauses": pauses, "weak": weak, "speed": speeds, "problems": problems,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    has_plot = plot(t, db, pauses, speeds, out_dir / "curve.png",
         f"{src.name}  |  {clean['duration']}s  |  dynamics {clean['dynamic_range']}dB")

    lines = [f"# 口播交付体检：{src.name}", "",
             f"- 时长：{clean['duration']} 秒",
             f"- 有人声占比：{clean['speech_ratio']}%",
             f"- 音量动态范围：{clean['dynamic_range']} dB"
             + ("（偏平）" if clean["dynamic_range"] < 6 else "（有起伏）"),
             f"- 停顿：{clean['pause_count']} 处，共 {clean['pause_total']} 秒",
             f"- 音量偏小段：{len(weak)} 段", ""]

    if not args.transcript:
        lines += ["> 没给转写，这次只测了音量、停顿和起伏，**没有语速数据**。",
                  "> 想看语速，先跑 `scripts/analyze_video.py` 拿到转写 JSON，再用 `--transcript` 传进来。", ""]

    lines += ["## 发现", "", "| 问题 | 证据 | 怎么改 |", "|---|---|---|"]
    for p in problems:
        lines.append(f"| {p['问题']} | {p['证据']} | {p['怎么改']} |")
    lines.append("")

    if pauses:
        lines += ["## 停顿清单", "", "| 开始 | 结束 | 时长 |", "|---|---|---|"]
        for p in pauses[:20]:
            lines.append(f"| {p['start']}s | {p['end']}s | {p['duration']}s |")
        if len(pauses) > 20:
            lines.append(f"| … | 另有 {len(pauses) - 20} 处 | |")
        lines.append("")

    if speeds:
        lines += ["## 语速曲线（每秒）", "", "| 秒 | 字/秒 |", "|---|---|"]
        for s in speeds:
            if s["chars_per_sec"] > 0:
                lines.append(f"| {int(s['t'])} | {s['chars_per_sec']} |")
        lines.append("")

    lines += ["## 说明", "",
              "- 这是**可量化指标**，不是情绪判断。声音里“有没有劲儿”只能靠你自己听，这份报告帮你定位到具体第几秒。",
              "- 音量小 ≠ 一定不好。有时是故意的压低，看上下文再定。",
              ("- 曲线图在 `curve.png`：蓝线是音量，红线是语速，黄色区间是停顿。" if has_plot
               else "- 这台电脑没装 matplotlib，这次没出曲线图；想要图，在终端输入 python3 -m pip install matplotlib 再跑一次。"),
              ""]

    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")

    if args.json_output:
        Path(args.json_output).expanduser().resolve().write_text(
            json.dumps({"stats": clean, "problems": problems}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    print(f"[voice_delivery] 完成 → {out_dir}")
    for p in problems:
        print(f"  - {p['问题']}：{p['证据']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
