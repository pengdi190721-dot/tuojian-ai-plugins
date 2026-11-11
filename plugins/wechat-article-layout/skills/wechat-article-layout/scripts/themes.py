"""六套公众号主题。每套主题实现同一组组件，长相各写各的。

粘进公众号不掉格式的规矩，每套主题都必须守：
- 只用 section / p / span / strong / img 这几种标签
- 样式全部写在元素自己的 style 里，颜色写死，不用渐变、不用样式变量
- 每一段文字都包在 <span leaf=""> 里（用下面的 leaf() 就行）

加新主题：复制一个主题类，改编号、名字、颜色和组件，加进文件末尾的 THEMES，
再跑插件的打包脚本（plugins/wechat-article-layout/scripts/build_release.py）更新主题清单和预览图。
详见 references/add-theme.md。
"""
import html
import re

FONT = "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
MONO = "'SF Mono',Consolas,Menlo,monospace"
CN = "一二三四五六七八九十"
INLINE = re.compile(r"(\[\[.+?\]\]|\*\*.+?\*\*|==.+?==|`[^`]+`)")


# ---------- 基础积木 ----------
def esc(text):
    return html.escape(str(text), quote=False)


def leaf(text):
    return f'<span leaf="">{esc(text)}</span>'


def tag(name, style, *inner):
    return f'<{name} style="{style}">' + "".join(inner) + f"</{name}>"


def sec(style, *inner):
    return tag("section", style, *inner)


def p(style, *inner):
    return tag("p", style, *inner)


def sp(style, text):
    return tag("span", style, leaf(text))


def bar(style):
    """纯装饰的线条或色块（里面没有文字）。"""
    return sec(style + "font-size:0;line-height:0;")


def img(src):
    return ('<span leaf=""><img src="' + html.escape(src, quote=True)
            + '" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>')


def plain(text):
    """去掉行内标记，只留文字（用在金句这类不需要再划重点的地方）。"""
    return re.sub(r"\[\[(.+?)\]\]|\*\*(.+?)\*\*|==(.+?)==|`([^`]+)`",
                  lambda m: next(g for g in m.groups() if g is not None), text)


def cn_num(n):
    return CN[n - 1] if 1 <= n <= len(CN) else str(n)


def code_line(text):
    """代码行：开头的空格换成全角空格，空行留一个全角空格占高度。"""
    if not text.strip():
        return "　"
    return re.sub(r"^ +", lambda m: "　" * max(1, len(m.group()) // 2), text)


class Theme:
    no = 0
    id = name = fit = look = recommend = ""
    swatch = ()
    # 设计变量
    accent = "#1D4ED8"      # 主色
    soft = "#EFF4FF"        # 主色的浅底
    ink = "#1F2937"         # 正文字色
    head = "#111827"        # 标题字色
    muted = "#6B7280"       # 次要文字
    line = "#E5E7EB"        # 分割线
    mark = ""               # 小标题竖条颜色（不填就用主色）
    bold_bg = ""            # 对比表“之后”一栏的表头底色（不填就用主色）
    bold_fg = "#FFFFFF"
    radius = "6px"
    ul = strong = hi = ""   # 行内样式：下划线关键词、加粗、高亮
    code = "background:#F1F5F9;color:#334155;padding:1px 5px;border-radius:4px;font-family:" + MONO + ";font-size:13px;"
    prompt_label = "发给 AI 的话"
    tip_label = "踩坑提醒"

    # ---- 文字 ----
    def rich(self, text):
        out = []
        for part in INLINE.split(text):
            if not part:
                continue
            if part.startswith("[[") and part.endswith("]]"):
                out.append(tag("span", self.ul, leaf(part[2:-2])))
            elif part.startswith("**") and part.endswith("**"):
                out.append(tag("strong", self.strong, leaf(part[2:-2])))
            elif part.startswith("==") and part.endswith("=="):
                out.append(tag("span", self.hi, leaf(part[2:-2])))
            elif part.startswith("`") and part.endswith("`"):
                out.append(tag("span", self.code, leaf(part[1:-1])))
            else:
                out.append(leaf(part))
        return "".join(out)

    def title_html(self, parts, hi_style=""):
        return "".join(tag("span", hi_style, leaf(t)) if (h and hi_style) else leaf(t) for t, h in parts)

    def para(self, text):
        return p(f"margin:0 0 16px;font-size:15px;line-height:1.85;color:{self.ink};text-align:justify;",
                 self.rich(text))

    def wrap(self, blocks):
        return sec(f"max-width:677px;margin:0 auto;background:#FFFFFF;font-family:{FONT};color:{self.ink};"
                   "line-height:1.75;letter-spacing:0.5px;", *blocks)

    # ---- 整篇装配 ----
    def render(self, doc):
        out = [self.cover(doc)]
        out += [self.block(b) for b in doc["intro"]]
        if len(doc["toc"]) >= 2:
            out.append(self.toc(doc["toc"]))
        out += [self.block(b) for b in doc["body"]]
        if doc["sig"] or doc["cta"]:
            out.append(self.footer(doc["sig"], doc["cta"], doc["cta2"]))
        return self.wrap(out) + "\n"

    def block(self, b):
        kind, args = b[0], b[1:]
        if kind == "code":
            return self.prompt(args[0] or self.prompt_label, args[1])
        if kind == "tip":
            return self.tip(args[0] or self.tip_label, args[1])
        return getattr(self, {"hole": "placeholder"}.get(kind, kind))(*args)

    # ---- 各主题通用的组件（主题可以自己重写） ----
    def subhead(self, title):
        return p(f"margin:24px 0 10px;font-size:15px;font-weight:800;line-height:1.6;color:{self.head};"
                 f"border-left:3px solid {self.mark or self.accent};padding-left:10px;", leaf(title))

    def ulist(self, items):
        return sec("margin:0 0 20px;", *[
            sec("display:flex;align-items:flex-start;margin:0 0 6px;",
                sp(f"flex-shrink:0;width:16px;color:{self.accent};font-weight:800;font-size:15px;line-height:1.85;", "•"),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.85;color:{self.ink};", self.rich(t)))
            for t in items])

    def saying(self, text, who):
        rows = [p(f"margin:0 0 2px;font-size:30px;line-height:1;font-weight:800;color:{self.accent};"
                  "font-family:Georgia,serif;", leaf("“")),
                p(f"margin:0;font-size:15px;line-height:1.85;font-weight:600;color:{self.head};", leaf(plain(text)))]
        if who:
            rows.append(p(f"margin:10px 0 0;font-size:13px;line-height:1.6;color:{self.muted};text-align:right;",
                          leaf("—— " + who)))
        return sec(f"margin:4px 0 22px;padding:14px 18px 16px;background:{self.soft};border-radius:{self.radius};", *rows)

    def compare(self, left, right, rows):
        cell = "flex:1;min-width:0;padding:8px 12px;font-size:13px;font-weight:700;line-height:1.6;"
        head = sec("display:flex;",
                   sp(cell + f"background:#F3F4F6;color:{self.muted};", left),
                   sp(cell + f"background:{self.bold_bg or self.accent};color:{self.bold_fg};", right))
        body = [sec(f"display:flex;border-top:1px solid {self.line};",
                    tag("span", f"flex:1;min-width:0;padding:10px 12px;font-size:14px;line-height:1.7;color:{self.muted};",
                        self.rich(a)),
                    tag("span", f"flex:1;min-width:0;padding:10px 12px;font-size:14px;line-height:1.7;color:{self.head};"
                                f"font-weight:600;background:{self.soft};", self.rich(b)))
                for a, b in rows]
        return sec(f"margin:4px 0 24px;border:1px solid {self.line};border-radius:{self.radius};overflow:hidden;",
                   head, *body)

    def divider(self):
        return bar(f"width:48px;height:1px;background:{self.line};margin:30px auto;")

    def placeholder(self, n, cap):
        rows = [p(f"margin:0;font-size:14px;font-weight:700;color:{self.muted};line-height:1.6;", leaf(f"图 {n} · 待补截图"))]
        if cap:
            rows.append(p("margin:6px 0 0;font-size:13px;color:#9CA3AF;line-height:1.7;", leaf(cap)))
        return sec(f"margin:4px 0 22px;padding:26px 16px;border:1.5px dashed #D4D4D8;border-radius:{self.radius};"
                   "background:#FAFAFA;text-align:center;", *rows)

    def caption(self, n, cap, num_style, text_style="", align="center"):
        parts = [sp(num_style, f"图 {n}")]
        if cap:
            parts.append(leaf(cap))
        return p(f"font-size:12px;color:{self.muted};text-align:{align};line-height:1.6;{text_style}", *parts)

    def code_rows(self, lines, color):
        return "".join(p(f"margin:0;font-family:{MONO};font-size:13px;line-height:1.7;color:{color};word-break:break-all;",
                         leaf(code_line(t))) for t in lines)


# ============ 1. 手册蓝 ============
class ManualBlue(Theme):
    no, id, name = 1, "manual-blue", "手册蓝"
    fit = "一步一步的操作教程，截图多、步骤多"
    look = "方块章节号、圆圈步骤、深色命令框，最像说明书"
    recommend = "软件实操、操作教程"
    swatch = ("#1D4ED8", "#EFF4FF", "#0F172A")
    accent, soft, ink, head, muted, line, radius = "#1D4ED8", "#EFF4FF", "#1F2937", "#111827", "#6B7280", "#E5E7EB", "6px"
    ul = "border-bottom:2px solid #BFD3FE;font-weight:600;"
    strong = "color:#1D4ED8;font-weight:700;"
    hi = "background:#DBE6FE;color:#111827;padding:0 3px;border-radius:2px;"

    def cover(self, d):
        top = []
        if d["kicker"]:
            top.append(sp(f"display:inline-block;background:{self.accent};color:#FFFFFF;font-size:11px;font-weight:700;"
                          "padding:5px 8px;border-radius:3px;letter-spacing:1px;margin-right:8px;", d["kicker"]))
        if d["issue"]:
            top.append(sp(f"font-size:12px;color:{self.muted};", d["issue"]))
        rows = [p("margin:0 0 14px;line-height:1;", *top)] if top else []
        rows.append(p(f"margin:0 0 10px;font-size:24px;font-weight:800;line-height:1.4;color:{self.head};",
                      self.title_html(d["title"], f"color:{self.accent};")))
        if d["sub"]:
            rows.append(p(f"margin:0 0 16px;font-size:14px;color:{self.muted};line-height:1.7;", leaf(d["sub"])))
        if d["info"]:
            cells = []
            for k, v in d["info"]:
                inner = [p(f"margin:0;font-size:11px;color:{self.muted};line-height:1.5;", leaf(k))] if k else []
                inner.append(p(f"margin:0;font-size:13px;font-weight:700;color:{self.ink};line-height:1.5;", leaf(v)))
                cells.append(sec("flex:1;min-width:0;padding:10px 8px 10px 0;", *inner))
            rows.append(sec(f"display:flex;border-top:2px solid {self.head};border-bottom:1px solid {self.line};", *cells))
        else:
            rows.append(bar(f"height:2px;background:{self.head};"))
        return sec("margin:0 0 24px;", *rows)

    def toc(self, items):
        rows = [p("margin:0;font-size:14px;line-height:2;color:#374151;",
                  sp(f"color:{self.accent};font-weight:800;margin-right:10px;font-family:{MONO};", str(i + 1)), leaf(t))
                for i, t in enumerate(items)]
        return sec(f"margin:8px 0 28px;padding:14px 16px;background:{self.soft};border-radius:6px;",
                   p(f"margin:0 0 4px;font-size:12px;font-weight:700;color:{self.accent};letter-spacing:2px;", leaf("本篇目录")),
                   *rows)

    def chapter(self, n, title, last):
        return sec(f"display:flex;align-items:center;margin:40px 0 20px;padding-bottom:10px;border-bottom:2px solid {self.accent};",
                   sp(f"display:inline-block;flex-shrink:0;width:34px;height:34px;line-height:34px;text-align:center;"
                      f"background:{self.accent};color:#FFFFFF;font-size:15px;font-weight:800;border-radius:4px;"
                      f"margin-right:12px;font-family:{MONO};", f"{n:02d}"),
                   sp(f"flex:1;min-width:0;font-size:19px;font-weight:800;color:{self.head};line-height:1.4;", title))

    def step(self, n, title):
        return sec("display:flex;align-items:center;margin:26px 0 10px;",
                   sp(f"display:inline-block;flex-shrink:0;width:24px;height:24px;line-height:24px;text-align:center;"
                      f"border:2px solid {self.accent};color:{self.accent};font-size:13px;font-weight:800;border-radius:50%;"
                      "margin-right:10px;", str(n)),
                   sp(f"flex:1;min-width:0;font-size:16px;font-weight:700;color:{self.head};line-height:1.5;", title))

    def shot(self, n, cap, src):
        return (sec("margin:4px 0 8px;padding:4px;border:1px solid #D6DEEB;border-radius:6px;",
                    sec("border-radius:3px;overflow:hidden;", img(src)))
                + self.caption(n, cap, f"color:{self.accent};font-weight:700;margin-right:6px;", "margin:0 0 22px;"))

    def prompt(self, label, lines):
        return sec("margin:4px 0 22px;border-radius:6px;overflow:hidden;background:#0F172A;",
                   sec("padding:8px 14px;background:#1E293B;", sp("font-size:12px;color:#93A4BD;letter-spacing:1px;", label)),
                   sec("padding:12px 14px;", self.code_rows(lines, "#E2E8F0")))

    def tip(self, label, paras):
        return sec("margin:8px 0 24px;padding:12px 14px;background:#FFFBEB;border-left:3px solid #F59E0B;",
                   p("margin:0 0 4px;font-size:13px;font-weight:800;color:#B45309;", leaf(label)),
                   *[p("margin:0;font-size:14px;line-height:1.8;color:#4B5563;", self.rich(t)) for t in paras])

    def olist(self, items):
        return sec("margin:0 0 22px;", *[
            sec("display:flex;align-items:flex-start;margin:0 0 8px;",
                sp(f"flex-shrink:0;width:22px;color:{self.accent};font-weight:800;font-size:15px;line-height:1.8;"
                   f"font-family:{MONO};", f"{i + 1}."),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.8;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec(f"margin:28px 0;padding:4px 0 4px 16px;border-left:4px solid {self.accent};",
                   p(f"margin:0;font-size:17px;font-weight:800;line-height:1.7;color:{self.head};", leaf(plain(text))))

    def footer(self, sig, cta, cta2):
        rows = []
        if sig:
            rows.append(p(f"margin:0 0 12px;font-size:14px;line-height:1.8;color:{self.muted};", leaf(sig)))
        if cta:
            rows.append(p(f"margin:0;font-size:15px;line-height:1.8;font-weight:700;color:{self.head};",
                          leaf(cta), sp(f"color:{self.accent};", cta2) if cta2 else ""))
        return sec(f"margin:36px 0 0;padding:20px 0 0;border-top:1px solid {self.line};", *rows)


# ============ 2. 黑金 ============
class BlackGold(Theme):
    no, id, name = 2, "black-gold", "黑金"
    fit = "观点加方法、对外分享，想要有分量感"
    look = "黑底封面、金色细线、章节居中，分量感最重"
    recommend = "问答、观点文"
    swatch = ("#16130E", "#C19A4B", "#FAF6EC")
    K, GOLD, GD = "#16130E", "#C19A4B", "#8C6A24"
    accent, soft, ink, head, muted, line, radius = "#C19A4B", "#FAF6EC", "#2A2622", "#16130E", "#8A8377", "#E6DCC6", "4px"
    bold_bg, bold_fg = "#16130E", "#C19A4B"
    ul = "border-bottom:2px solid #D9C28F;font-weight:600;"
    strong = "color:#8C6A24;font-weight:700;"
    hi = "background:#F3E7C9;color:#16130E;padding:0 3px;"
    prompt_label = "原话照发"
    tip_label = "踩过的坑"

    def cover(self, d):
        rows = []
        kick = " · ".join(x for x in (d["kicker"], d["issue"]) if x)
        if kick:
            rows.append(p(f"margin:0 0 16px;font-size:11px;color:{self.GOLD};letter-spacing:3px;line-height:1.4;", leaf(kick)))
        rows.append(p("margin:0 0 16px;font-size:24px;font-weight:800;line-height:1.45;color:#FFFFFF;letter-spacing:1px;",
                      self.title_html(d["title"], f"color:{self.GOLD};")))
        rows.append(bar(f"width:36px;height:2px;background:{self.GOLD};margin:0 0 16px;"))
        if d["sub"]:
            rows.append(p("margin:0;font-size:14px;line-height:1.8;color:#CFC6B4;", leaf(d["sub"])))
        out = sec(f"margin:0 0 16px;padding:30px 22px 28px;background:{self.K};border-radius:4px;", *rows)
        if d["info"]:
            cells = []
            for k, v in d["info"]:
                inner = [p(f"margin:0;font-size:11px;color:{self.GD};letter-spacing:2px;line-height:1.6;", leaf(k))] if k else []
                inner.append(p(f"margin:0;font-size:13px;font-weight:600;color:{self.ink};line-height:1.6;", leaf(v)))
                cells.append(sec("flex:1;min-width:0;padding:0 6px 0 0;", *inner))
            out += sec(f"display:flex;margin:0 0 26px;padding:12px 2px;border-bottom:1px solid {self.line};", *cells)
        else:
            out = out.replace("margin:0 0 16px;padding:30px", "margin:0 0 26px;padding:30px", 1)
        return out

    def toc(self, items):
        rows = [p(f"margin:0;font-size:14px;line-height:2.1;color:{self.ink};", sp(f"color:{self.GOLD};margin-right:10px;", "—"),
                  leaf(t)) for t in items]
        return sec(f"margin:8px 0 30px;padding:14px 4px;border-top:1px solid {self.GOLD};border-bottom:1px solid {self.GOLD};",
                   p(f"margin:0 0 4px;font-size:11px;color:{self.GD};letter-spacing:4px;", leaf("本篇看点")), *rows)

    def chapter(self, n, title, last):
        return sec("margin:46px 0 24px;text-align:center;",
                   p(f"margin:0 0 6px;font-size:12px;color:{self.GD};letter-spacing:4px;line-height:1.4;",
                     leaf("最后" if last else f"第{cn_num(n)}部分")),
                   p(f"margin:0 0 12px;font-size:20px;font-weight:800;color:{self.K};line-height:1.5;letter-spacing:1px;",
                     leaf(title)),
                   bar(f"width:28px;height:2px;background:{self.GOLD};margin:0 auto;"))

    def step(self, n, title):
        return sec("display:flex;align-items:center;margin:26px 0 10px;",
                   sp(f"display:inline-block;flex-shrink:0;background:{self.K};color:{self.GOLD};font-size:12px;font-weight:700;"
                      "padding:3px 10px;border-radius:2px;letter-spacing:2px;margin-right:10px;line-height:1.6;", f"第 {n} 步"),
                   sp(f"flex:1;min-width:0;font-size:16px;font-weight:700;color:{self.K};line-height:1.5;", title))

    def shot(self, n, cap, src):
        return (sec(f"margin:4px 0 8px;border:1px solid {self.K};", img(src))
                + self.caption(n, cap, f"color:{self.GD};font-weight:700;margin-right:8px;letter-spacing:1px;",
                               "margin:0 0 22px;", "left"))

    def prompt(self, label, lines):
        return sec(f"margin:4px 0 22px;padding:14px 16px;background:{self.K};border-top:2px solid {self.GOLD};",
                   p(f"margin:0 0 6px;font-size:11px;color:{self.GOLD};letter-spacing:3px;", leaf(label)),
                   self.code_rows(lines, "#EDE6D6"))

    def tip(self, label, paras):
        return sec(f"margin:8px 0 24px;padding:14px 16px;background:{self.soft};border-left:3px solid {self.GOLD};",
                   p(f"margin:0 0 4px;font-size:12px;font-weight:700;color:{self.GD};letter-spacing:3px;", leaf(label)),
                   *[p(f"margin:0;font-size:14px;line-height:1.85;color:{self.ink};", self.rich(t)) for t in paras])

    def olist(self, items):
        return sec("margin:0 0 22px;", *[
            sec(f"display:flex;align-items:baseline;padding:10px 0;border-bottom:1px solid {self.line};",
                sp(f"flex-shrink:0;width:36px;color:{self.GOLD};font-weight:700;font-size:16px;line-height:1.6;letter-spacing:1px;",
                   f"{i + 1:02d}"),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.7;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec(f"margin:30px 0;padding:26px 22px;background:{self.K};text-align:center;border-radius:4px;",
                   p("margin:0;font-size:17px;font-weight:700;line-height:1.8;color:#F3E9D2;letter-spacing:1px;",
                     leaf(plain(text))))

    def footer(self, sig, cta, cta2):
        rows = []
        if sig:
            rows.append(p("margin:0 0 14px;font-size:14px;line-height:1.85;color:#6B655B;", leaf(sig)))
        if cta:
            rows.append(p(f"margin:0 0 6px;font-size:15px;line-height:1.8;font-weight:700;color:{self.K};", leaf(cta)))
            if cta2:
                rows.append(p(f"margin:0;font-size:13px;color:{self.GD};letter-spacing:3px;", leaf(cta2)))
        return sec(f"margin:36px 0 0;padding:22px 0 0;border-top:1px solid {self.GOLD};", *rows)


# ============ 3. 老板笔记 ============
class BossNotes(Theme):
    no, id, name = 3, "boss-notes", "老板笔记"
    fit = "踩坑实录、个人口吻强的内容，要像本人"
    look = "黄色荧光笔、黑粗字、硬边截图框，像自己记的本子"
    recommend = "踩坑实录、个人经历"
    swatch = ("#FFE45C", "#1A1A1A", "#D4380D")
    K, Y, RED = "#1A1A1A", "#FFE45C", "#D4380D"
    accent, soft, ink, head, muted, line, radius = "#1A1A1A", "#FFF9DB", "#262626", "#1A1A1A", "#737373", "#E5E5E5", "10px"
    mark, bold_bg, bold_fg = "#FFE45C", "#1A1A1A", "#FFE45C"
    ul = "border-bottom:3px solid #FFE45C;font-weight:600;"
    strong = "background:#FFE45C;color:#1A1A1A;font-weight:700;padding:1px 4px;border-radius:3px;"
    hi = "background:#FFF3A3;color:#1A1A1A;padding:0 3px;"
    prompt_label = "照着发就行"
    tip_label = "踩过的坑"

    def cover(self, d):
        top = []
        if d["kicker"]:
            top.append(sp(f"display:inline-block;background:{self.K};color:{self.Y};font-size:12px;font-weight:800;"
                          "padding:5px 10px;border-radius:4px;letter-spacing:2px;margin-right:10px;", d["kicker"]))
        if d["issue"]:
            top.append(sp(f"font-size:12px;color:{self.muted};", d["issue"]))
        rows = [p("margin:0 0 14px;line-height:1;", *top)] if top else []
        rows.append(p(f"margin:0 0 12px;font-size:25px;font-weight:900;line-height:1.5;color:{self.K};",
                      self.title_html(d["title"], f"background:{self.Y};padding:0 6px;border-radius:4px;")))
        if d["sub"]:
            rows.append(p(f"margin:0 0 14px;font-size:14px;line-height:1.8;color:{self.muted};", leaf(d["sub"])))
        if d["info"]:
            pills = [sp(f"display:inline-block;border:1.5px solid {self.K};border-radius:20px;padding:2px 12px;font-size:12px;"
                        f"color:{self.K};margin:0 8px 8px 0;line-height:1.7;", f"{k}：{v}" if k else v) for k, v in d["info"]]
            rows.append(p("margin:0;line-height:1;", *pills))
        return sec("margin:0 0 22px;", *rows)

    def toc(self, items):
        marks = "①②③④⑤⑥"
        rows = [p(f"margin:0;font-size:14px;line-height:2;color:{self.ink};", sp("font-weight:800;margin-right:8px;", marks[i]),
                  leaf(t)) for i, t in enumerate(items[:6])]
        return sec(f"margin:8px 0 30px;padding:14px 16px;border:1.5px solid {self.K};border-radius:10px;",
                   p("margin:0 0 6px;line-height:1.4;",
                     sp(f"display:inline-block;background:{self.Y};color:{self.K};font-size:12px;font-weight:800;"
                        "padding:2px 8px;border-radius:4px;",
                        f"这篇记{'两' if len(items) == 2 else cn_num(len(items))}件事")), *rows)

    def chapter(self, n, title, last):
        return sec(f"display:flex;align-items:center;margin:42px 0 20px;padding-bottom:10px;border-bottom:3px solid {self.K};",
                   sp(f"display:inline-block;flex-shrink:0;background:{self.Y};color:{self.K};font-size:16px;font-weight:900;"
                      "padding:2px 10px;border-radius:6px;margin-right:10px;line-height:1.6;", "完" if last else f"{n:02d}"),
                   sp(f"flex:1;min-width:0;font-size:19px;font-weight:900;color:{self.K};line-height:1.4;", title))

    def step(self, n, title):
        return sec("display:flex;align-items:center;margin:26px 0 10px;",
                   sp(f"display:inline-block;flex-shrink:0;background:{self.K};color:#FFFFFF;font-size:12px;font-weight:700;"
                      "padding:3px 9px;border-radius:4px;margin-right:10px;line-height:1.6;", f"第 {n} 步"),
                   sp(f"font-size:16px;font-weight:800;color:{self.K};line-height:1.5;border-bottom:6px solid #FFF3A3;", title))

    def shot(self, n, cap, src):
        return (sec(f"margin:6px 4px 12px 0;border:2px solid {self.K};border-radius:10px;overflow:hidden;"
                    f"box-shadow:4px 4px 0 {self.K};", img(src))
                + self.caption(n, cap, f"color:{self.K};font-weight:800;margin-right:6px;", "margin:0 0 22px;", "left")
                .replace(leaf(f"图 {n}"), leaf(f"▲ 图 {n}"), 1))

    def prompt(self, label, lines):
        return sec(f"margin:4px 0 22px;padding:12px 14px;background:{self.soft};border:1.5px solid {self.K};border-radius:10px;",
                   p(f"margin:0 0 6px;font-size:12px;font-weight:800;color:{self.K};", leaf(label)),
                   self.code_rows(lines, self.K))

    def tip(self, label, paras):
        return sec(f"margin:8px 0 24px;padding:2px 0 2px 14px;border-left:4px solid {self.RED};",
                   p(f"margin:0 0 2px;font-size:13px;font-weight:800;color:{self.RED};", leaf(label)),
                   *[p(f"margin:0;font-size:14px;line-height:1.85;color:{self.ink};", self.rich(t)) for t in paras])

    def olist(self, items):
        return sec("margin:0 0 22px;", *[
            sec("display:flex;align-items:flex-start;margin:0 0 10px;",
                sp(f"display:inline-block;flex-shrink:0;width:22px;height:22px;line-height:22px;text-align:center;"
                   f"background:{self.Y};color:{self.K};font-size:12px;font-weight:800;border-radius:50%;margin:3px 10px 0 0;",
                   str(i + 1)),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.8;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec(f"margin:28px 0;padding:20px 18px;background:{self.Y};border-radius:10px;",
                   p(f"margin:0;font-size:18px;font-weight:900;line-height:1.7;color:{self.K};", leaf(plain(text))))

    def footer(self, sig, cta, cta2):
        rows = []
        if sig:
            rows.append(p(f"margin:0 0 14px;font-size:14px;line-height:1.85;color:{self.muted};", leaf(sig)))
        if cta:
            rows.append(p(f"margin:0 0 12px;font-size:15px;line-height:1.8;font-weight:800;color:{self.K};", leaf(cta)))
            if cta2:
                rows.append(p("margin:0;line-height:1;",
                              sp(f"display:inline-block;border:1.5px solid {self.K};border-radius:20px;padding:5px 16px;"
                                 f"font-size:13px;font-weight:700;color:{self.K};line-height:1.5;", cta2)))
        return sec(f"margin:36px 0 0;padding:20px 0 0;border-top:1.5px solid {self.K};", *rows)


# ============ 4. 汇报青 ============
class ReportTeal(Theme):
    no, id, name = 4, "report-teal", "汇报青"
    fit = "部门实测、前后对比，用汇报的口吻讲"
    look = "先说结论、一二三提纲、表格式信息栏"
    recommend = "实测对比、复盘汇报"
    swatch = ("#0F766E", "#EEF7F5", "#B45309")
    AMB = "#B45309"
    accent, soft, ink, head, muted, line, radius = "#0F766E", "#EEF7F5", "#1C2B2A", "#1C2B2A", "#64748B", "#D5E5E2", "4px"
    ul = "border-bottom:2px solid #99D5CC;font-weight:600;"
    strong = "color:#0F766E;font-weight:700;"
    hi = "background:#D3EEE9;color:#1C2B2A;padding:0 3px;"
    prompt_label = "原话照发"
    tip_label = "踩坑"

    def cover(self, d):
        top = sec("display:flex;align-items:center;margin:0 0 12px;",
                  sp(f"flex:1;min-width:0;font-size:12px;font-weight:800;color:{self.accent};letter-spacing:4px;",
                     d["kicker"] or "工作汇报"),
                  sp(f"flex-shrink:0;font-size:12px;color:{self.muted};", d["issue"]) if d["issue"] else "")
        rows = [top, p(f"margin:0 0 16px;font-size:23px;font-weight:800;line-height:1.45;color:{self.head};",
                       self.title_html(d["title"], f"color:{self.accent};"))]
        if d["info"]:
            trs = [sec(f"display:flex;border-bottom:1px solid {self.line};",
                       sp(f"flex-shrink:0;width:52px;padding:7px 10px;background:{self.soft};font-size:12px;color:{self.accent};"
                          "font-weight:700;line-height:1.6;", k or "·"),
                       sp(f"flex:1;min-width:0;padding:7px 12px;font-size:13px;color:{self.ink};line-height:1.6;", v))
                   for k, v in d["info"]]
            rows.append(sec(f"border-top:2px solid {self.accent};margin:0 0 14px;", *trs))
        if d["sub"]:
            rows.append(sec(f"padding:14px 16px;background:{self.accent};border-radius:4px;",
                            p("margin:0 0 4px;font-size:11px;color:#A7E0D8;letter-spacing:3px;", leaf("先说结论")),
                            p("margin:0;font-size:15px;font-weight:700;line-height:1.7;color:#FFFFFF;", leaf(d["sub"]))))
        return sec("margin:0 0 24px;", *rows)

    def toc(self, items):
        rows = [p(f"margin:0;font-size:14px;line-height:2;color:{self.ink};",
                  sp(f"color:{self.accent};font-weight:800;margin-right:4px;", f"{cn_num(i + 1)}、"), leaf(t))
                for i, t in enumerate(items)]
        return sec(f"margin:8px 0 28px;padding:12px 16px;border:1px solid {self.line};border-radius:4px;",
                   p(f"margin:0 0 4px;font-size:12px;font-weight:700;color:{self.muted};letter-spacing:3px;", leaf("汇报提纲")),
                   *rows)

    def chapter(self, n, title, last):
        return sec(f"margin:40px 0 20px;padding:10px 14px;background:{self.soft};border-left:5px solid {self.accent};",
                   p(f"margin:0;font-size:19px;font-weight:800;color:{self.head};line-height:1.5;",
                     sp(f"color:{self.accent};", f"{cn_num(n)}、"), leaf(title)))

    def step(self, n, title):
        return sec("display:flex;align-items:center;margin:26px 0 10px;",
                   sp(f"display:inline-block;flex-shrink:0;width:24px;height:24px;line-height:24px;text-align:center;"
                      f"border:1.5px solid {self.accent};color:{self.accent};font-size:13px;font-weight:800;border-radius:4px;"
                      "margin-right:10px;", str(n)),
                   sp(f"flex:1;min-width:0;font-size:16px;font-weight:700;color:{self.head};line-height:1.5;", title))

    def shot(self, n, cap, src):
        return sec(f"margin:4px 0 22px;padding:8px 8px 10px;background:{self.soft};border-radius:4px;", img(src),
                   self.caption(n, cap, f"color:{self.accent};font-weight:700;margin-right:4px;", "margin:8px 0 0;")
                   .replace(leaf(f"图 {n}"), leaf(f"图 {n}｜"), 1))

    def prompt(self, label, lines):
        return sec(f"margin:4px 0 22px;border:1px solid {self.accent};border-radius:4px;overflow:hidden;",
                   sec(f"padding:6px 14px;background:{self.soft};",
                       sp(f"font-size:12px;font-weight:700;color:{self.accent};letter-spacing:2px;", label)),
                   sec("padding:12px 14px;", self.code_rows(lines, self.ink)))

    def tip(self, label, paras):
        return sec("margin:8px 0 24px;padding:12px 14px;background:#FFF8EB;border:1px solid #F3DDB3;border-radius:4px;",
                   p("margin:0 0 6px;line-height:1.4;",
                     sp(f"display:inline-block;background:{self.AMB};color:#FFFFFF;font-size:11px;font-weight:700;"
                        "padding:2px 8px;border-radius:2px;letter-spacing:2px;", label)),
                   *[p("margin:0;font-size:14px;line-height:1.85;color:#44403C;", self.rich(t)) for t in paras])

    def olist(self, items):
        return sec("margin:0 0 22px;", *[
            sec("display:flex;align-items:flex-start;margin:0 0 10px;",
                sp(f"display:inline-block;flex-shrink:0;width:20px;height:20px;line-height:20px;text-align:center;"
                   f"background:{self.accent};color:#FFFFFF;font-size:12px;font-weight:700;border-radius:50%;margin:4px 10px 0 0;",
                   str(i + 1)),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.8;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec(f"margin:30px 0;padding:18px 8px;border-top:2px solid {self.accent};border-bottom:2px solid {self.accent};"
                   "text-align:center;",
                   p(f"margin:0;font-size:17px;font-weight:800;line-height:1.8;color:{self.accent};", leaf(plain(text))))

    def footer(self, sig, cta, cta2):
        inner = []
        if sig:
            inner.append(p(f"margin:0 0 10px;font-size:14px;line-height:1.85;color:{self.muted};", leaf(sig)))
        if cta:
            inner.append(p(f"margin:0;font-size:15px;line-height:1.8;font-weight:700;color:{self.head};",
                           leaf(cta), sp(f"color:{self.accent};", cta2) if cta2 else ""))
        return sec("margin:36px 0 0;",
                   p(f"margin:0 0 16px;font-size:12px;color:{self.accent};text-align:center;letter-spacing:6px;font-weight:700;",
                     leaf("— 汇报完毕 —")),
                   sec(f"padding:16px;background:{self.soft};border-radius:4px;", *inner))


# ============ 5. 黑白极简 ============
class Mono(Theme):
    no, id, name = 5, "mono", "黑白极简"
    fit = "观点、随笔，字少、想让读者慢下来"
    look = "大号数字、细线、大留白，颜色只有一点红"
    recommend = "短观点、随笔"
    swatch = ("#111111", "#E5E5E5", "#E11D48")
    RED = "#E11D48"
    accent, soft, ink, head, muted, line, radius = "#111111", "#F5F5F5", "#2B2B2B", "#111111", "#8A8A8A", "#E5E5E5", "0px"
    ul = "border-bottom:1.5px solid #111111;font-weight:600;"
    strong = "color:#111111;font-weight:800;"
    hi = "background:#EDEDED;color:#111111;padding:0 3px;"
    prompt_label = "发给 AI"
    tip_label = "注"

    def cover(self, d):
        rows = []
        kick = " / ".join(x for x in (d["kicker"], d["issue"]) if x)
        if kick:
            rows.append(p(f"margin:0 0 18px;font-size:12px;color:{self.muted};letter-spacing:3px;line-height:1.4;", leaf(kick)))
        rows.append(p(f"margin:0 0 20px;font-size:28px;font-weight:900;line-height:1.35;color:{self.head};letter-spacing:1px;",
                      self.title_html(d["title"])))
        rows.append(bar(f"width:40px;height:3px;background:{self.head};margin:0 0 20px;"))
        if d["sub"]:
            rows.append(p(f"margin:0 0 10px;font-size:14px;line-height:1.9;color:{self.muted};", leaf(d["sub"])))
        if d["info"]:
            rows.append(p(f"margin:0;font-size:12px;color:{self.muted};line-height:1.6;",
                          leaf(" · ".join(v for _, v in d["info"][:2]))))
        return sec("margin:6px 0 30px;", *rows)

    def toc(self, items):
        rows = [sec(f"display:flex;align-items:baseline;padding:9px 0;border-bottom:1px solid {self.line};",
                    sp(f"flex-shrink:0;width:34px;font-size:12px;color:{self.muted};letter-spacing:1px;", f"{i + 1:02d}"),
                    sp(f"flex:1;min-width:0;font-size:14px;color:{self.ink};line-height:1.6;", t))
                for i, t in enumerate(items)]
        return sec(f"margin:10px 0 34px;border-top:1px solid {self.head};", *rows)

    def chapter(self, n, title, last):
        return sec("margin:52px 0 22px;",
                   p("margin:0;font-size:44px;font-weight:200;line-height:1.1;color:#D4D4D4;letter-spacing:2px;",
                     leaf("—" if last else f"{n:02d}")),
                   p(f"margin:6px 0 0;font-size:20px;font-weight:800;line-height:1.5;color:{self.head};", leaf(title)))

    def step(self, n, title):
        return sec(f"display:flex;align-items:baseline;margin:28px 0 10px;padding-top:14px;border-top:1px solid {self.line};",
                   sp(f"flex-shrink:0;font-size:16px;font-weight:900;color:{self.head};", str(n)),
                   sp("flex-shrink:0;font-size:14px;color:#C4C4C4;margin:0 8px;", "/"),
                   sp(f"flex:1;min-width:0;font-size:16px;font-weight:700;color:{self.head};line-height:1.5;", title))

    def shot(self, n, cap, src):
        return (sec("margin:6px 0 8px;", img(src))
                + self.caption(n, cap, f"color:{self.head};font-weight:700;margin-right:8px;", "margin:0 0 24px;", "left"))

    def prompt(self, label, lines):
        return sec("margin:4px 0 24px;padding:14px 16px;background:#F5F5F5;",
                   p(f"margin:0 0 6px;font-size:11px;color:{self.muted};letter-spacing:3px;", leaf(label)),
                   self.code_rows(lines, self.head))

    def tip(self, label, paras):
        return sec(f"display:flex;align-items:flex-start;margin:8px 0 26px;padding:14px 0;"
                   f"border-top:1px solid {self.line};border-bottom:1px solid {self.line};",
                   sp(f"flex-shrink:0;font-size:13px;font-weight:800;color:{self.RED};margin-right:14px;line-height:1.9;", label),
                   sec("flex:1;min-width:0;",
                       *[p(f"margin:0;font-size:14px;line-height:1.9;color:{self.ink};", self.rich(t)) for t in paras]))

    def olist(self, items):
        return sec("margin:0 0 24px;", *[
            sec("display:flex;align-items:baseline;margin:0 0 8px;",
                sp(f"flex-shrink:0;width:26px;font-size:13px;color:{self.muted};", f"{i + 1}."),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.85;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec("margin:36px 0;",
                   bar(f"width:24px;height:3px;background:{self.RED};margin:0 0 14px;"),
                   p(f"margin:0;font-size:20px;font-weight:800;line-height:1.7;color:{self.head};letter-spacing:1px;",
                     leaf(plain(text))))

    def saying(self, text, who):
        rows = [p(f"margin:0;font-size:16px;line-height:1.9;color:{self.head};font-weight:600;", leaf(f"“{plain(text)}”"))]
        if who:
            rows.append(p(f"margin:8px 0 0;font-size:12px;color:{self.muted};letter-spacing:1px;", leaf("—— " + who)))
        return sec(f"margin:6px 0 26px;padding:2px 0 2px 16px;border-left:1px solid {self.head};", *rows)

    def footer(self, sig, cta, cta2):
        rows = []
        if sig:
            rows.append(p(f"margin:0 0 14px;font-size:13px;line-height:1.9;color:{self.muted};", leaf(sig)))
        if cta:
            rows.append(p(f"margin:0 0 4px;font-size:15px;line-height:1.8;font-weight:800;color:{self.head};", leaf(cta)))
            if cta2:
                rows.append(p(f"margin:0;font-size:13px;color:{self.muted};", leaf(cta2)))
        return sec(f"margin:44px 0 0;padding:20px 0 0;border-top:1px solid {self.head};", *rows)


# ============ 6. 活力橙 ============
class CardOrange(Theme):
    no, id, name = 6, "card-orange", "活力橙"
    fit = "工具盘点、清单类，想让读者快速划着看"
    look = "橙色封面、圆角卡片、一步一块"
    recommend = "清单、工具盘点"
    swatch = ("#EA580C", "#FFF3EA", "#27272A")
    OD, CARD = "#C2410C", "#FAFAF9"
    accent, soft, ink, head, muted, line, radius = "#EA580C", "#FFF3EA", "#27272A", "#27272A", "#71717A", "#EDEBE8", "12px"
    bold_bg = "#C2410C"
    ul = "border-bottom:2px solid #FDBA8C;font-weight:600;"
    strong = "color:#C2410C;font-weight:700;"
    hi = "background:#FFE2CC;color:#27272A;padding:0 3px;border-radius:3px;"
    prompt_label = "复制这句发给 AI"
    tip_label = "踩坑提醒"

    def cover(self, d):
        rows = []
        kick = " · ".join(x for x in (d["kicker"], d["issue"]) if x)
        if kick:
            rows.append(p("margin:0 0 14px;line-height:1;",
                          sp("display:inline-block;background:rgba(255,255,255,0.22);color:#FFFFFF;font-size:12px;font-weight:700;"
                             "padding:4px 12px;border-radius:20px;line-height:1.6;", kick)))
        rows.append(p("margin:0 0 10px;font-size:24px;font-weight:800;line-height:1.45;color:#FFFFFF;",
                      self.title_html(d["title"])))
        if d["sub"]:
            rows.append(p("margin:0;font-size:14px;line-height:1.75;color:#FFE3D0;", leaf(d["sub"])))
        out = sec(f"margin:0 0 10px;padding:24px 20px 26px;background:{self.accent};border-radius:14px;", *rows)
        if d["info"]:
            n = len(d["info"])
            cards = []
            for i, (k, v) in enumerate(d["info"]):
                inner = [p(f"margin:0;font-size:11px;color:{self.muted};line-height:1.6;", leaf(k))] if k else []
                inner.append(p(f"margin:0;font-size:12px;font-weight:700;color:{self.ink};line-height:1.6;", leaf(v)))
                cards.append(sec(f"flex:1;min-width:0;margin:0 {0 if i == n - 1 else 8}px 0 0;padding:10px;"
                                 f"background:{self.CARD};border-radius:10px;", *inner))
            out += sec("display:flex;margin:0 0 24px;", *cards)
        else:
            out = out.replace("margin:0 0 10px;padding:24px", "margin:0 0 24px;padding:24px", 1)
        return out

    def toc(self, items):
        rows = [p(f"margin:0;font-size:14px;line-height:2;color:{self.ink};",
                  sp(f"color:{self.accent};font-weight:800;margin-right:8px;", "✓"), leaf(t)) for t in items]
        return sec(f"margin:8px 0 28px;padding:14px 16px;background:{self.soft};border-radius:12px;",
                   p(f"margin:0 0 4px;font-size:13px;font-weight:800;color:{self.OD};", leaf("看完你能带走")), *rows)

    def chapter(self, n, title, last):
        return sec("display:flex;align-items:center;margin:42px 0 18px;",
                   sp(f"display:inline-block;flex-shrink:0;background:{self.accent};color:#FFFFFF;font-size:14px;font-weight:800;"
                      "padding:2px 12px;border-radius:20px;margin-right:10px;line-height:1.7;", "完" if last else f"{n:02d}"),
                   sp(f"flex:1;min-width:0;font-size:19px;font-weight:800;color:{self.head};line-height:1.4;", title))

    def step(self, n, title):
        return sec(f"display:flex;align-items:center;margin:22px 0 12px;padding:10px 14px;background:{self.soft};border-radius:10px;",
                   sp(f"flex-shrink:0;font-size:12px;font-weight:800;color:{self.OD};letter-spacing:1px;margin-right:10px;",
                      f"第 {n} 步"),
                   sp(f"flex:1;min-width:0;font-size:16px;font-weight:700;color:{self.head};line-height:1.5;", title))

    def shot(self, n, cap, src):
        return sec(f"margin:4px 0 22px;padding:8px 8px 10px;background:{self.CARD};border:1px solid {self.line};border-radius:12px;",
                   sec("border-radius:8px;overflow:hidden;", img(src)),
                   self.caption(n, cap, f"color:{self.accent};font-weight:800;margin-right:6px;", "margin:8px 0 0;"))

    def prompt(self, label, lines):
        return sec(f"margin:4px 0 22px;padding:14px 16px;background:{self.ink};border-radius:12px;",
                   p("margin:0 0 8px;line-height:1.4;",
                     sp(f"display:inline-block;width:8px;height:8px;border-radius:50%;background:{self.accent};margin-right:8px;"
                        "font-size:0;line-height:0;overflow:hidden;", "."),
                     sp("font-size:12px;color:#A1A1AA;", label)),
                   self.code_rows(lines, "#F4F4F5"))

    def tip(self, label, paras):
        return sec(f"margin:8px 0 24px;padding:14px 16px;background:{self.soft};border-radius:12px;",
                   p("margin:0 0 6px;line-height:1.4;",
                     sp(f"display:inline-block;background:{self.OD};color:#FFFFFF;font-size:11px;font-weight:700;"
                        "padding:2px 10px;border-radius:20px;line-height:1.6;", label)),
                   *[p(f"margin:0;font-size:14px;line-height:1.85;color:{self.ink};", self.rich(t)) for t in paras])

    def olist(self, items):
        return sec("margin:0 0 22px;", *[
            sec(f"display:flex;align-items:center;margin:0 0 8px;padding:10px 14px;background:{self.CARD};"
                f"border:1px solid {self.line};border-radius:10px;",
                sp(f"flex-shrink:0;font-size:18px;font-weight:800;color:{self.accent};margin-right:12px;line-height:1.4;", str(i + 1)),
                tag("span", f"flex:1;min-width:0;font-size:15px;line-height:1.7;color:{self.ink};", self.rich(t)))
            for i, t in enumerate(items)])

    def quote(self, text):
        return sec(f"margin:28px 0;padding:20px 18px;border:2px solid {self.accent};border-radius:12px;text-align:center;",
                   p(f"margin:0;font-size:17px;font-weight:800;line-height:1.75;color:{self.OD};", leaf(plain(text))))

    def footer(self, sig, cta, cta2):
        rows = []
        if sig:
            rows.append(p(f"margin:0 0 10px;font-size:14px;line-height:1.85;color:{self.muted};", leaf(sig)))
        if cta:
            rows.append(p(f"margin:0 0 10px;font-size:15px;line-height:1.8;font-weight:700;color:{self.head};", leaf(cta)))
            if cta2:
                rows.append(p("margin:0;line-height:1;",
                              sp(f"display:inline-block;background:{self.OD};color:#FFFFFF;font-size:13px;font-weight:700;"
                                 "padding:5px 16px;border-radius:20px;line-height:1.6;", cta2)))
        return sec(f"margin:36px 0 0;padding:18px 16px;background:{self.CARD};border:1px solid {self.line};border-radius:12px;",
                   *rows)


THEMES = [ManualBlue(), BlackGold(), BossNotes(), ReportTeal(), Mono(), CardOrange()]


def find_theme(key):
    """按编号、中文名或英文标识找主题。"""
    key = str(key).strip()
    for t in THEMES:
        if key in (str(t.no), t.name, t.id):
            return t
    return None
