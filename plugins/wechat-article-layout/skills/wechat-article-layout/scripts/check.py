#!/usr/bin/env python3
"""公众号正文检查：粘进后台会不会掉格式。

用法：python3 check.py 正文1.html [正文2.html ...]
有“必须改”的问题时退出码为 1。render.py 排完会自动调用这里，平时不用单独跑。
"""
import re
import sys
from html.parser import HTMLParser

# 公众号编辑器会删掉或改写的写法
BANNED = [
    (r"<\s*(style|script|link|iframe|form|input|button)\b", "出现公众号会删掉的标签"),
    (r"<\s*/?\s*div\b", "出现 div（公众号会改写，请用 section）"),
    (r"\s(class|id)\s*=", "出现 class 或 id（会被剥掉，样式要写在 style 里）"),
    (r"position\s*:\s*(fixed|absolute|sticky)", "用了定位（不支持）"),
    (r"(?<![-\w])float\s*:", "用了浮动（不支持）"),
    (r"display\s*:\s*(inline-)?grid", "用了网格布局（不支持，请用 flex）"),
    (r"@(media|keyframes|import|font-face)", "用了 @ 规则（不支持）"),
    (r"var\s*\(\s*--", "用了样式变量（不支持，颜色要写死）"),
    (r"white-space\s*:\s*pre", "用了 white-space:pre（会多出大片空白）"),
]
GRADIENT = re.compile(r"(linear|radial|conic)-gradient\s*\(", re.I)
CJK = "一-鿿㐀-䶿"
HALF = re.compile(f"[{CJK}][,;!?:]|[{CJK}]\\s?[\"']|[\"'][{CJK}]")
CODE = re.compile(r"monospace|consolas|menlo|sf mono", re.I)
VOID = {"img", "br", "hr"}


class Walker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.leafs = 0
        self.bare, self.half, self.img_bare, self.img_wide = [], [], 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        style = a.get("style") or ""
        in_leaf = any(s[1] for s in self.stack)
        if tag == "img":
            if not in_leaf:
                self.img_bare += 1
            if re.search(r"(?<![-\w])width\s*:\s*100%", style) and "max-width" not in style:
                self.img_wide += 1
        if tag in VOID:
            return
        is_leaf = tag == "span" and "leaf" in a
        self.leafs += is_leaf
        self.stack.append((tag, is_leaf, bool(CODE.search(style))))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if not any(s[1] for s in self.stack):
            self.bare.append(text[:20])
        if not any(s[2] for s in self.stack) and HALF.search(text):
            self.half.append(text[:20])


def check(html):
    """返回（必须改列表，建议改列表，span leaf 数量）。"""
    must, should = [], []
    scan = re.sub(r'src="data:[^"]*"', 'src=""', html)  # 内嵌图片的内容不参与检查
    for rx, msg in BANNED:
        n = len(re.findall(rx, scan, re.I))
        if n:
            must.append(f"{msg}，{n} 处")
    if re.search(r"<\s*(!doctype|html|head|body)\b", scan, re.I):
        must.append("带了整页外壳（只要正文片段，从最外层 section 开始）")
    w = Walker()
    w.feed(scan)
    if w.bare:
        must.append(f"{len(w.bare)} 处文字没包 span leaf，粘过去样式会丢。例：" + "；".join(w.bare[:3]))
    if w.img_bare:
        must.append(f"{w.img_bare} 张图片没包 span leaf")
    if w.img_wide:
        should.append(f"{w.img_wide} 张图片写了 width:100%，小图会被拉糊，改成 max-width:100%")
    if w.half:
        should.append(f"{len(w.half)} 处正文疑似半角标点或直引号。例：" + "；".join(w.half[:3]))
    n = len(GRADIENT.findall(scan))
    if n:
        should.append(f"{n} 处渐变背景，深色模式下可能出问题，建议换纯色")
    return must, should, w.leafs


if __name__ == "__main__":
    bad = 0
    for path in sys.argv[1:]:
        must, should, leafs = check(open(path, encoding="utf-8").read())
        state = "不通过" if must else ("通过，有建议" if should else "通过")
        print(f"[{state}] {path}（span leaf {leafs} 处）")
        for m in must:
            print(f"   必须改：{m}")
        for s in should:
            print(f"   建议改：{s}")
        bad += bool(must)
    sys.exit(1 if bad else 0)
