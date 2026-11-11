#!/usr/bin/env python3
"""把文字稿排成公众号图文。只用 Python 自带的东西；装了 Pillow 会顺手压缩截图。

用法（Windows 上把 python3 换成 python）：
  python3 render.py --pick                    出选主题的缩略图页（选主题.html，装了 playwright 还会出 选主题.png）
  python3 render.py 文字稿.md                 用设置里的默认主题
  python3 render.py 文字稿.md --theme 3       指定主题（编号、中文名、英文标识都行）
  python3 render.py 文字稿.md --theme all     六套各排一遍，出一个对比页
  python3 render.py --list                    列出全部主题

设置：先读技能里的 settings.md，再读文字稿文件夹里的「公众号设置.md」（有就以它为准）。
输出（和文字稿放在同一个文件夹；--pick 放在当前文件夹，或 --out 指定的文件夹）：
  <稿名>_<主题>_预览.html   浏览器打开，点“复制”，去公众号后台粘贴
  <稿名>_<主题>_正文.html   干净的正文片段（截图是相对路径），给检查和接口发布用
退出码：有“必须改”的问题时为 1。
"""
import argparse
import base64
import html
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
from check import check  # noqa: E402
from themes import THEMES, find_theme, plain  # noqa: E402

META_KEYS = {"标题": "title", "栏目": "kicker", "期数": "issue", "副标题": "sub", "信息": "info",
             "看点": "toc", "署名": "sig", "互动": "cta", "互动尾": "cta2"}
SETTING_KEYS = {"默认主题": "theme", "栏目": "kicker", "署名": "sig", "互动尾": "cta2"}
LAST_RE = re.compile(r"写在最后|最后|总结|结语|收尾")
HAN = "一-鿿㐀-䶿"
CJK = HAN + "　-〿＀-￯"
HALF = {",": "，", ";": "；", "!": "！", "?": "？", ":": "："}
PIPE = re.compile(r"\s*[|｜]\s*")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


# ---------- 设置和文字整理 ----------
USER_SETTINGS = "公众号设置.md"


def read_settings(f):
    out = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):  # 下面是说明文字，不读
                break
            m = re.match(r"^\s*([^：:#\-*\s][^：:#]*?)\s*[：:]\s*(.*)$", line)
            if m and m.group(1) in SETTING_KEYS and m.group(2).strip():
                out.setdefault(SETTING_KEYS[m.group(1)], m.group(2).strip())
    return out


def load_settings(folder=None):
    """技能自带的 settings.md 打底，用户文件夹里的「公众号设置.md」覆盖（技能升级不会冲掉它）。"""
    out = read_settings(SKILL / "settings.md")
    if folder:
        out.update(read_settings(Path(folder) / USER_SETTINGS))
    return out


def fix(text):
    """中文里的半角标点改全角；行内代码和网址不动。"""
    parts = re.split(rf"(`[^`]+`|https?://[^\s{HAN}，。！？；）」]+)", text)
    for i in range(0, len(parts), 2):
        t = parts[i]
        t = re.sub(rf"(?<=[{CJK}])\s*([,;!?:])\s*|\s*([,;!?:])\s*(?=[{CJK}])",
                   lambda m: HALF[m.group(1) or m.group(2)], t)
        t = re.sub(rf"(?<=[{CJK}])\.(?=\s|$|[{CJK}])", "。", t)
        t = re.sub(rf"\(([^()]*[{HAN}][^()]*)\)", r"（\1）", t)
        if re.search(f"[{HAN}]", t) and t.count('"') % 2 == 0:
            n = [0]

            def curly(_):
                n[0] += 1
                return "“" if n[0] % 2 else "”"
            t = re.sub('"', curly, t)
        parts[i] = t
    return "".join(parts)


def join_lines(lines):
    out = ""
    for s in (x.strip() for x in lines):
        if not s:
            continue
        if out and re.match(r"[A-Za-z0-9]", s[0]) and re.match(r"[A-Za-z0-9.,;!?]", out[-1]):
            out += " "
        out += s
    return out


def split_paras(lines):
    paras, buf = [], []
    for line in lines + [""]:
        if line.strip():
            buf.append(line)
        elif buf:
            paras.append(join_lines(buf))
            buf = []
    return paras


def pair(text, default=("", "")):
    bits = PIPE.split(text.strip(), maxsplit=1)
    return (bits + [default[1]])[:2] if bits[0] else list(default)


# ---------- 读文字稿 ----------
def parse(text, notes):
    lines = text.replace("\r\n", "\n").split("\n")
    meta, i = {}, 0
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        if j < len(lines):
            for line in lines[1:j]:
                m = re.match(r"^\s*([^：:]+?)\s*[：:]\s*(.*)$", line)
                if m and m.group(1) in META_KEYS:
                    meta[META_KEYS[m.group(1)]] = m.group(2).strip()
            i = j + 1

    blocks, buf = [], []

    def flush():
        if buf:
            blocks.append(["para", join_lines(buf)])
            buf.clear()

    while i < len(lines):
        s = lines[i].strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("```"):
            flush()
            label, body = s[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i].rstrip())
                i += 1
            i += 1
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            blocks.append(["code", label, body])
            continue
        if s.startswith(":::") and len(s) > 3:
            flush()
            kind, _, arg = s[3:].strip().partition(" ")
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            i += 1
            blocks.extend(make_box(kind, arg.strip(), body, notes))
            continue
        m = re.match(r"^(#{1,4})\s+(.+)$", s)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 1:
                meta.setdefault("title", title)
            else:
                blocks.append([{2: "chapter", 3: "step", 4: "subhead"}[level], title])
            i += 1
            continue
        m = re.match(r"^【图】\s*(.*?)\s*(?:[|｜]\s*(.*))?$", s)
        if m:  # 截图：【图】路径｜说明
            flush()
            blocks.append(["shot", (m.group(2) or "").strip(), m.group(1).strip()])
            i += 1
            continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)$", s)
        if m:  # 也认常见的图片写法
            flush()
            blocks.append(["shot", m.group(1).strip(), m.group(2).strip()])
            i += 1
            continue
        if s.startswith(">"):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:])
                i += 1
            blocks.append(["quote", join_lines(q)])
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            blocks.append(["divider"])
            i += 1
            continue
        for kind, rx in (("olist", r"^\d+(?:(?:\.|．)(?!\d)\s*|(?:\)|）)\s*|、\s*)"), ("ulist", r"^[-*•]\s+")):
            if re.match(rx + r"\S", s):
                flush()
                items = []
                while i < len(lines) and re.match(rx + r"\S", lines[i].strip()):
                    items.append(re.sub(rx, "", lines[i].strip(), count=1))
                    i += 1
                blocks.append([kind, items])
                break
        else:
            buf.append(s)
            i += 1
    flush()
    return meta, blocks


def make_box(kind, arg, body, notes):
    if kind in ("坑", "提醒", "注意"):
        return [["tip", arg, split_paras(body)]]
    if kind == "原话":
        return [["saying", join_lines(body), arg]]
    if kind == "对比":
        left, right = pair(arg, ("之前", "之后"))
        rows = [pair(re.sub(r"^[-*•]\s*", "", x.strip())) for x in body if x.strip()]
        return [["compare", left, right, rows]]
    notes.append(f"不认识的块「:::{kind}」，按普通段落排了")
    return [["para", t] for t in split_paras(body)]


# ---------- 整理成主题能直接用的结构 ----------
def build(md_path, settings):
    md_path = Path(md_path)
    notes = []
    raw = md_path.read_text(encoding="utf-8")
    meta, blocks = parse(raw, notes)
    if raw.count("【待补"):
        notes.append(f"稿子里还有 {raw.count('【待补')} 处「【待补：……】」，发之前要换成真实内容")

    for b in blocks:  # 标点统一
        k = b[0]
        if k in ("para", "chapter", "step", "subhead", "quote"):
            b[1] = fix(b[1])
        elif k == "shot":
            b[1] = fix(b[1])
        elif k in ("olist", "ulist"):
            b[1] = [fix(t) for t in b[1]]
        elif k == "tip":
            b[1], b[2] = fix(b[1]), [fix(t) for t in b[2]]
        elif k == "saying":
            b[1], b[2] = fix(b[1]), fix(b[2])
        elif k == "compare":
            b[1], b[2], b[3] = fix(b[1]), fix(b[2]), [[fix(a), fix(c)] for a, c in b[3]]
    meta = {k: fix(v) if k not in ("info", "toc") else v for k, v in meta.items()}

    title = meta.get("title") or md_path.stem
    if not meta.get("title"):
        notes.append(f"文字稿没写标题，先用了文件名「{md_path.stem}」")
    title_parts = [(t[2:-2], True) if t.startswith("==") and t.endswith("==") else (t, False)
                   for t in re.split(r"(==.+?==)", title) if t]
    info = []
    for item in PIPE.split(meta.get("info", "")):
        if item.strip():
            m = re.match(r"^(.*?)\s*[=＝]\s*(.*)$", item.strip())
            k, v = (m.group(1), m.group(2)) if m else ("", item.strip())
            info.append((fix(k), fix(v)))

    # 编号：章节、每章里的步骤、全文的图
    chapters = [i for i, b in enumerate(blocks) if b[0] == "chapter"]
    last_idx = chapters[-1] if chapters and LAST_RE.search(blocks[chapters[-1]][1]) else -1
    ch = st = fig = 0
    images, out = {}, []
    for idx, b in enumerate(blocks):
        k = b[0]
        if k == "chapter":
            ch, st = ch + 1, 0
            out.append(["chapter", ch, b[1], idx == last_idx])
        elif k == "step":
            st += 1
            out.append(["step", st, b[1]])
        elif k == "shot":
            fig += 1
            cap, src = b[1], b[2]
            if not cap:
                notes.append(f"图 {fig} 没写说明")
            mock = re.match(r"^示意图[:：]\s*(\d+)$", src)
            if src in ("", "待补"):
                out.append(["hole", fig, cap])
                notes.append(f"图 {fig} 待补截图：{cap or '（没写说明）'}")
            elif mock:
                images[fig] = (src, "mock", int(mock.group(1)))
                out.append(["shot", fig, cap, f"@@IMG{fig}@@"])
            elif re.match(r"https?://", src):
                images[fig] = (src, "url", src)
                out.append(["shot", fig, cap, f"@@IMG{fig}@@"])
            else:
                f = (md_path.parent / src)
                if f.exists():
                    images[fig] = (src, "file", f)
                    out.append(["shot", fig, cap, f"@@IMG{fig}@@"])
                else:
                    out.append(["hole", fig, cap])
                    notes.append(f"图 {fig} 找不到文件「{src}」，先留了空位")
        else:
            out.append(b)

    lint(out, notes)
    first = next((i for i, b in enumerate(out) if b[0] == "chapter"), len(out))
    if meta.get("toc"):
        toc = [fix(t) for t in PIPE.split(meta["toc"]) if t.strip()]
    else:
        toc = [b[2] for b in out if b[0] == "chapter" and not b[3]][:3]
    cta = meta.get("cta", "")
    if not cta:
        notes.append("文字稿没写「互动」，结尾没有放提问")
    if not meta.get("sig", settings.get("sig", "")):
        notes.append(f"还没设署名，文末没放自我介绍（在稿子文件夹建「{USER_SETTINGS}」写上署名就有了）")
    doc = {
        "kicker": meta.get("kicker", settings.get("kicker", "")), "issue": meta.get("issue", ""),
        "title": title_parts, "sub": meta.get("sub", ""), "info": info, "toc": toc,
        "intro": out[:first], "body": out[first:],
        "sig": meta.get("sig", settings.get("sig", "")), "cta": cta,
        "cta2": meta.get("cta2", settings.get("cta2", "")) if cta else "",
    }
    return doc, images, notes


def lint(blocks, notes):
    bold = 0
    for n, b in enumerate((b for b in blocks if b[0] == "para"), 1):
        text = b[1]
        marks = len(re.findall(r"\[\[.+?\]\]", text))
        bold += len(re.findall(r"\*\*.+?\*\*", text))
        if marks == 0 and len(plain(text)) >= 40:
            notes.append(f"第 {n} 段没标关键词：「{plain(text)[:14]}…」")
        if marks > 3:
            notes.append(f"第 {n} 段标了 {marks} 处关键词，最多 3 处")
    if bold > 5:
        notes.append(f"全文加粗 {bold} 处，最多 5 处，多了就没重点了")
    quotes = [b for b in blocks if b[0] == "quote"]
    if len(quotes) > 2:
        notes.append(f"金句用了 {len(quotes)} 处，最多 2 处")
    for b in quotes:
        if len(plain(b[1])) > 40:
            notes.append(f"金句太长（{len(plain(b[1]))} 字）：「{plain(b[1])[:14]}…」，40 字以内读着有劲")


# ---------- 截图 ----------
def embed(path):
    """本地截图转成内嵌图片；装了 Pillow 就压到宽 1280、1MB 以内。"""
    data = Path(path).read_bytes()
    mime = MIME.get(Path(path).suffix.lower(), "image/png")
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        if mime != "image/gif" and (im.width > 1280 or len(data) > 900_000):
            if im.width > 1280:
                im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)
            buf = io.BytesIO()
            if mime == "image/png":
                im.save(buf, "PNG", optimize=True)
            if mime != "image/png" or buf.tell() > 900_000:
                if im.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", im.size, "#FFFFFF")
                    rgba = im.convert("RGBA")
                    bg.paste(rgba, mask=rgba.split()[-1])
                    im = bg
                buf = io.BytesIO()
                im.convert("RGB").save(buf, "JPEG", quality=85, optimize=True)
                mime = "image/jpeg"
            data = buf.getvalue()
    except ImportError:
        pass
    except Exception:  # 图片读不了就原样放
        pass
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii"), len(data)


def mock_shot(k):
    """样稿用的示意截图（脚本现场画，技能里不放图片文件）。"""
    side = "".join(f'<rect x="20" y="{62 + i * 38}" width="{[96, 120, 84, 110, 72][i]}" height="12" rx="6" fill="#D9DCE1"/>'
                   for i in range(5))
    badge = ('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" stroke="#EF4444" stroke-width="3"/>'
             '<circle cx="{cx}" cy="{y}" r="12" fill="#EF4444"/>'
             '<text x="{cx}" y="{ty}" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle" '
             'font-family="sans-serif">{n}</text>')
    if k % 2:
        body = (badge.format(x=8, y=126, w=154, h=32, cx=162, ty=131, n=k)
                + '<rect x="200" y="64" width="450" height="210" rx="10" fill="#FFFFFF"/>'
                '<rect x="224" y="92" width="180" height="14" rx="7" fill="#D9DCE1"/>'
                + "".join(f'<rect x="224" y="{124 + i * 22}" width="{[380, 340, 360][i]}" height="10" rx="5" fill="#E8EAED"/>'
                          for i in range(3)))
    else:
        body = ('<rect x="390" y="64" width="260" height="40" rx="12" fill="#DDE3EE"/>'
                '<rect x="200" y="124" width="380" height="120" rx="12" fill="#FFFFFF"/>'
                '<rect x="220" y="146" width="150" height="14" rx="7" fill="#C9CED6"/>'
                '<rect x="220" y="176" width="320" height="10" rx="5" fill="#E8EAED"/>'
                '<rect x="220" y="198" width="280" height="10" rx="5" fill="#E8EAED"/>'
                + badge.format(x=212, y=138, w=170, h=30, cx=382, ty=143, n=k))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 380" width="680" height="380">'
           '<rect width="680" height="380" fill="#F3F4F6"/><rect width="680" height="34" fill="#E5E7EB"/>'
           '<circle cx="18" cy="17" r="5" fill="#C4C7CC"/><circle cx="36" cy="17" r="5" fill="#C4C7CC"/>'
           '<circle cx="54" cy="17" r="5" fill="#C4C7CC"/><rect y="34" width="170" height="346" fill="#FFFFFF"/>'
           + side + body
           + '<rect x="200" y="300" width="450" height="44" rx="22" fill="#FFFFFF" stroke="#D9DCE1"/>'
           '<text x="425" y="366" font-size="12" fill="#9CA3AF" text-anchor="middle" font-family="sans-serif">示意截图</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def fill_images(fragment, images, mode, sizes=None):
    for n, (rel, kind, payload) in images.items():
        if kind == "mock":
            value = mock_shot(payload)
        elif kind == "url" or mode == "body":
            value = rel
        else:
            value, size = embed(payload)
            if sizes is not None:
                sizes[n] = size
        fragment = fragment.replace(f"@@IMG{n}@@", html.escape(value, quote=True))
    return fragment


# ---------- 预览页 ----------
PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
body{margin:0;background:#EEF0EC;color:#1B1D1C;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:14px;line-height:1.7}
.wrap{max-width:__MAX__;margin:0 auto;padding:24px 16px 56px;display:flex;flex-direction:column;gap:18px}
h1{margin:0;font-size:20px;line-height:1.4}
.how{margin:0;color:#4B524E}
.notes{background:#FFF8E6;border:1px solid #F1DFAE;border-radius:10px;padding:12px 14px}
.notes b{display:block;margin-bottom:4px}
.notes ul{margin:0;padding-left:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,360px),1fr));gap:18px;align-items:start}
.card{background:#FFFFFF;border:1px solid #D9DCD6;border-radius:12px;min-width:0}
.top{padding:14px 14px 12px;border-bottom:1px solid #E4E6E2;display:flex;flex-direction:column;gap:8px}
.name{margin:0;font-size:17px;font-weight:800}
.name span{color:#7A817C;margin-right:6px}
.btns{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
button{font:inherit;font-size:13px;font-weight:600;border-radius:8px;padding:7px 12px;cursor:pointer;border:1px solid #1B1D1C}
.b1{background:#1B1D1C;color:#FFFFFF}.b2{background:#FFFFFF;color:#1B1D1C}
button:focus-visible{outline:2px solid #2563EB;outline-offset:2px}
.say{font-size:12px;color:#1F7A4D}
.screen{padding:20px 16px 28px}
.frag{max-width:375px;margin:0 auto}
</style></head><body>
<div class="wrap">
<h1>__TITLE__</h1>
<p class="how">点「复制（带截图）」，去公众号后台新建图文，在正文里粘贴。截图没跟着进去，就回来点「复制（截图留空位）」重新粘，再照图号把截图插进空位。</p>
__NOTES__
<div class="grid">__CARDS__</div>
</div>
<script>
function copyCard(btn, keepImg){
  var card=btn.closest('.card'), src=card.querySelector('.frag').firstElementChild, say=card.querySelector('.say');
  var clone=src.cloneNode(true);
  if(!keepImg){
    [].slice.call(clone.querySelectorAll('img')).forEach(function(im){
      var host=(im.parentNode&&im.parentNode.tagName==='SPAN')?im.parentNode:im;
      var ph=document.createElement('section');
      ph.setAttribute('style','padding:36px 12px;background:#F3F4F6;border:1.5px dashed #D4D4D8;text-align:center;font-size:13px;color:#6B7280;line-height:1.6;');
      ph.innerHTML='<span leaf="">在这里插入截图（看下面的图号）</span>';
      host.parentNode.replaceChild(ph,host);
    });
  }
  var html=clone.outerHTML, text=clone.textContent, done=false;
  function onCopy(e){ try{ e.clipboardData.setData('text/html',html); e.clipboardData.setData('text/plain',text); e.preventDefault(); done=true; }catch(_){} }
  var sel=window.getSelection(), r=document.createRange();
  r.selectNodeContents(src); sel.removeAllRanges(); sel.addRange(r);
  document.addEventListener('copy',onCopy);
  try{ document.execCommand('copy'); }catch(_){}
  document.removeEventListener('copy',onCopy);
  if(done){ sel.removeAllRanges(); say.textContent=keepImg?'已复制，去公众号后台粘贴':'已复制（截图留了空位），粘贴后照图号补图'; }
  else{ say.textContent='已选中全文，按 Ctrl 或 ⌘ 加 C 复制'; }
}
</script>
</body></html>
"""


def page(title, cards, notes, wide):
    note_html = ""
    if notes:
        note_html = ('<div class="notes"><b>排版提示（不影响粘贴，能改就改）</b><ul>'
                     + "".join(f"<li>{html.escape(n)}</li>" for n in notes) + "</ul></div>")
    card_html = "".join(
        f'<div class="card"><div class="top"><p class="name"><span>{t.no}</span>{html.escape(t.name)}</p>'
        '<div class="btns"><button class="b1" type="button" onclick="copyCard(this,true)">复制（带截图）</button>'
        '<button class="b2" type="button" onclick="copyCard(this,false)">复制（截图留空位）</button>'
        '<span class="say" role="status"></span></div></div>'
        f'<div class="screen"><div class="frag">{frag}</div></div></div>'
        for t, frag in cards)
    return (PAGE.replace("__TITLE__", html.escape(title)).replace("__MAX__", "1240px" if wide else "460px")
            .replace("__NOTES__", note_html).replace("__CARDS__", card_html))


# ---------- 选主题的缩略图页 ----------
PICK = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>选一套主题</title>
<style>
body{margin:0;background:#EEF0EC;color:#1B1D1C;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif;font-size:14px;line-height:1.7}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 36px;display:flex;flex-direction:column;gap:16px}
h1{margin:0;font-size:24px;line-height:1.4}
.sub{margin:-6px 0 4px;font-size:15px;color:#5B625E}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:18px;align-items:start}
.tile{background:#FFFFFF;border:1px solid #D9DCD6;border-radius:14px;overflow:hidden;min-width:0}
.head{display:flex;align-items:center;gap:10px;padding:14px 14px 0}
.head b{flex-shrink:0;width:30px;height:30px;line-height:30px;text-align:center;border-radius:50%;background:#1B1D1C;color:#FFFFFF;font-size:16px}
.head span{font-size:20px;font-weight:800}
.head em{margin-left:auto;display:flex;gap:4px}
.head i{width:14px;height:14px;border-radius:50%;border:1px solid #D9DCD6;display:block}
.fit{margin:4px 14px 12px;font-size:13px;color:#5B625E;line-height:1.6}
.pic{border-top:1px solid #E4E6E2;height:470px;overflow:hidden;padding:16px 16px 0}
.tile.open .pic{height:auto;padding-bottom:20px}
.more{display:block;width:100%;border:0;border-top:1px solid #E4E6E2;background:#F7F8F6;font:inherit;font-size:13px;padding:9px;cursor:pointer;color:#1B1D1C}
.more:focus-visible{outline:2px solid #2563EB;outline-offset:-2px}
</style></head><body><div class="wrap">
<h1>公众号排版 · 选一套主题</h1>
<p class="sub">回编号就行，比如“用 3”。点“看全文”能看到整篇的样子。</p>
<div class="grid">__TILES__</div></div>
<script>
[].slice.call(document.querySelectorAll('.more')).forEach(function(b){b.addEventListener('click',function(){
  var t=b.closest('.tile');t.classList.toggle('open');b.textContent=t.classList.contains('open')?'收起':'看全文';});});
</script></body></html>
"""


def pick_page(doc, images):
    tiles = []
    for t in THEMES:
        dots = "".join(f'<i style="background:{c}"></i>' for c in t.swatch)
        frag = fill_images(t.render(doc), images, "preview")
        tiles.append(f'<div class="tile"><div class="head"><b>{t.no}</b><span>{html.escape(t.name)}</span><em>{dots}</em></div>'
                     f'<p class="fit">{html.escape(t.fit)}</p><div class="pic">{frag}</div>'
                     '<button class="more" type="button">看全文</button></div>')
    return PICK.replace("__TILES__", "".join(tiles))


def snapshot(html_path, png_path, width=1180):
    """装了 playwright 就把页面截成一张图；没装就跳过。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception:
                browser = pw.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": width, "height": 800}, device_scale_factor=1.5)
            page.goto(Path(html_path).resolve().as_uri())
            page.add_style_tag(content=".more{display:none}")
            page.wait_for_timeout(300)
            page.screenshot(path=str(png_path), full_page=True)
            browser.close()
        return True
    except Exception:
        return False


def make_pick(out_dir, settings):
    doc, images, _ = build(SKILL / "assets" / "sample.md", settings)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path, png_path = out_dir / "选主题.html", out_dir / "选主题.png"
    html_path.write_text(pick_page(doc, images), encoding="utf-8")
    return html_path, (png_path if snapshot(html_path, png_path) else None)


# ---------- 入口 ----------
def main():
    ap = argparse.ArgumentParser(description="把文字稿排成公众号图文")
    ap.add_argument("draft", nargs="?", help="文字稿（.md）")
    ap.add_argument("--theme", help="主题：编号、中文名、英文标识，或 all")
    ap.add_argument("--pick", action="store_true", help="出选主题的缩略图页")
    ap.add_argument("--out", help="--pick 的输出文件夹（默认当前文件夹）")
    ap.add_argument("--list", action="store_true", help="列出全部主题")
    a = ap.parse_args()

    if a.pick:
        out = Path(a.out or ".").resolve()
        html_path, png_path = make_pick(out, load_settings(out))
        print(f"缩略图页：{html_path}")
        print(f"缩略图：{png_path}" if png_path else "缩略图：没装 playwright，只出了网页，让用户打开网页看")
        return 0

    if a.list or not a.draft:
        for t in THEMES:
            print(f"{t.no}  {t.name}（{t.id}）  适合：{t.fit}  推荐：{t.recommend}")
        return 0

    settings = load_settings(Path(a.draft).resolve().parent)
    key = a.theme or settings.get("theme", "1")
    md = Path(a.draft).resolve()
    if not md.exists():
        print(f"找不到文字稿：{md}")
        return 1
    doc, images, notes = build(md, settings)
    stem = md.stem

    if key == "all":
        cards = [(t, fill_images(t.render(doc), images, "preview")) for t in THEMES]
        out = md.parent / f"{stem}_六套对比.html"
        out.write_text(page(f"{stem} · 六套主题对比", cards, notes, True), encoding="utf-8")
        must, should = [], []
        for t, frag in cards:
            m, s, _ = check(frag)
            must += [f"{t.name}：{x}" for x in m]
            should += [f"{t.name}：{x}" for x in s]
        print(f"对比页：{out}")
    else:
        theme = find_theme(key)
        if not theme:
            print(f"没有这个主题：{key}。可选：" + "、".join(f"{t.no} {t.name}" for t in THEMES))
            return 1
        frag = theme.render(doc)
        body = fill_images(frag, images, "body")
        sizes = {}
        preview = fill_images(frag, images, "preview", sizes)
        for n, size in sizes.items():
            if size > 1_000_000:
                notes.append(f"图 {n} 压缩后还有 {size // 1024} KB，超过 1MB 可能传不上去，建议先裁小")
        body_path = md.parent / f"{stem}_{theme.name}_正文.html"
        prev_path = md.parent / f"{stem}_{theme.name}_预览.html"
        body_path.write_text(body, encoding="utf-8")
        prev_path.write_text(page(f"{stem} · {theme.name}", [(theme, preview)], notes, False), encoding="utf-8")
        must, should, _ = check(body)
        print(f"主题：{theme.no} {theme.name}")
        print(f"预览页：{prev_path}")
        print(f"正文：{body_path}")

    print("检查：" + ("不通过" if must else "通过，粘进公众号不会掉格式"))
    for m in must:
        print(f"  必须改：{m}")
    for s in should:
        print(f"  建议改：{s}")
    if notes:
        print("排版提示：")
        for n in notes:
            print(f"  - {n}")
    return 1 if must else 0


if __name__ == "__main__":
    sys.exit(main())
