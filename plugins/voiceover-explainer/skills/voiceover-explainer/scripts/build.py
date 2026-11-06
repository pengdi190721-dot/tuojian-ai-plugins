"""生成动画页面和字幕文件。
用法：python3 build.py 项目目录 [--风格 heijin] [--竖|--横] [--输出 work/xxx.html]
没有录音时间表（work/timeline.json）时，会按语速估算一个，用来先做样片。"""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

KW_DEFAULT = ['训练企业AI', '大模型', '上下文', '连接器', 'Skill', 'MCP', '技能', '专家', '本地', '云端', '判断', '规矩', '钥匙']
ROUGH = ('<svg width="0" height="0" style="position:absolute"><defs><filter id="rough" x="-5%" y="-5%" width="110%" height="110%">'
         '<feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="2" seed="7"/>'
         '<feDisplacementMap in="SourceGraphic" scale="5"/></filter></defs></svg>')
MSG = '<svg width="40" height="36" viewBox="0 0 40 36"><path d="M4 4 H36 V26 H16 L8 33 V26 H4 Z" class="f-acc"/></svg>'
DOC = '<svg width="34" height="40" viewBox="0 0 34 40"><path d="M3 2 H22 L31 11 V38 H3 Z" class="f-mute"/><path d="M22 2 V11 H31" class="f-card" opacity=".6"/></svg>'


def estimate_timeline(flat):
    """还没录音时，按每秒4.3个字估一个时间表"""
    t, lines = 0.8, []
    for i, L in enumerate(flat):
        if i:
            t += 1.05 if L['first'] else (0.6 if L['punch'] else 0.35)
        n = max(ncount(L['text']), 1)
        nct = [round(t + k / 4.3, 3) for k in range(n)]
        lines.append({'text': L['text'], 'nct': nct, 'ns': nct[0], 'ne': round(nct[-1] + 0.25, 3)})
        t = nct[-1] + 0.25
    return {'total': round(t + 2.2, 3), 'lines': lines, '估算': True}


def make_subs(tl, maxc, kws):
    subs = []
    lines = tl['lines']
    for li, L in enumerate(lines):
        parts = [p for p in re.findall(r'[^，。；：？！]+[，。；：？！]?', L['text']) if p.strip()]
        chunks, cur = [], ''
        for p in parts:
            if cur and ncount(cur) + ncount(p) > maxc:
                chunks.append(cur); cur = p
            else:
                cur += p
        if cur:
            chunks.append(cur)
        fixed = []
        for c in chunks:
            while ncount(c) > maxc + 4:
                k = c.find('、', 6)
                k = k + 1 if 0 < k < len(c) - 4 else len(c) // 2
                fixed.append(c[:k]); c = c[k:]
            fixed.append(c)
        pos = 0
        for c in fixed:
            st = L['nct'][min(pos, len(L['nct']) - 1)]
            pos += ncount(c)
            disp = re.sub(r'[，；：。]', ' ', c.strip('，。；：')).strip()
            subs.append({'li': li, 'a': round(st - 0.08, 3), 'text': disp})
    for i, s in enumerate(subs):
        L = lines[s['li']]
        nxt = subs[i + 1]['a'] if i + 1 < len(subs) else tl['total']
        if i + 1 < len(subs) and subs[i + 1]['li'] == s['li']:
            s['b'] = round(nxt - 0.02, 3)
        else:
            s['b'] = round(min(nxt - 0.04, L['ne'] + 0.35), 3)
            if s['b'] <= s['a'] + 0.4:
                s['b'] = round(nxt - 0.04, 3)
    pat = re.compile('|'.join(map(re.escape, sorted(kws, key=len, reverse=True))))
    for s in subs:
        s['h'] = pat.sub(lambda m: f'<k>{m.group(0)}</k>', s['text'])
    return subs


def srt_time(t):
    ms = int(round(max(t, 0) * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{sec:02d},{ms:03d}'


def build(d, theme=None, orient=None, out=None, quiet=False):
    cfg = load_project(d)
    theme = theme or cfg['风格']
    orient = orient or cfg['画幅']
    secs, flat = parse_script(d)
    tlp = d / 'work' / 'timeline.json'
    if tlp.exists():
        tl = json.loads(tlp.read_text(encoding='utf-8'))
        if len(tl['lines']) != len(flat) or any(norm(a['text']) != norm(b['text']) for a, b in zip(tl['lines'], flat)):
            if tl.get('估算'):
                tl = estimate_timeline(flat); tlp.write_text(json.dumps(tl, ensure_ascii=False), encoding='utf-8')
            else:
                sys.exit('【出错】口播稿和录音时间表对不上（改过 script.txt？）。请重新运行 align_edit.py')
    else:
        tl = estimate_timeline(flat)
        tlp.write_text(json.dumps(tl, ensure_ascii=False), encoding='utf-8')
        if not quiet:
            print('【提示】还没有录音时间表，先按语速估算（每秒4.3个字），只用来做样片')
    first, n = [], 1
    for s in secs:
        first.append({'name': s['name'], 'first': n}); n += len(s['lines'])
    chapters = [{'name': s['name'], 'sec': i + 1} for i, s in enumerate(secs) if s['chapter']]
    kws = cfg.get('字幕重点词') or KW_DEFAULT
    subs = make_subs(tl, 15 if orient == '竖' else 20, kws)

    scenes_p = d / 'scenes.html'
    scenes = scenes_p.read_text(encoding='utf-8') if scenes_p.exists() else '<!-- 还没有画面 -->'
    scripts = re.findall(r'<script>(.*?)</script>', scenes, flags=re.S)
    markup = re.sub(r'<script>.*?</script>', '', scenes, flags=re.S).replace('%MSG%', MSG).replace('%DOC%', DOC)
    proj = {'sections': first, 'chapters': chapters, 'orient': orient}
    tl_js = {'total': tl['total'], 'lines': [{'text': L['text'], 'nct': L['nct'], 'ne': L['ne']} for L in tl['lines']]}
    from engine_assets import BASE_CSS, ENGINE_JS, THEMES_CSS
    base, eng = BASE_CSS, ENGINE_JS
    tcss = THEMES_CSS[theme]
    # 项目里可以放自己的样式文件（project.json 里写 "自定义样式": "my.css"），在风格之后加载，用来微调颜色或加新风格
    if cfg.get('自定义样式') and (d / cfg['自定义样式']).exists():
        tcss += '\n' + (d / cfg['自定义样式']).read_text(encoding='utf-8')
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><base href="{d.as_uri()}/">
<title>{cfg.get('系列名') or '口播科普动画'}</title><style>{base}</style><style>{tcss}</style></head>
<body class="{'V' if orient == '竖' else 'H'} theme-{theme}">{ROUGH}<div id="stage">
<div id="topbar"><div class="badge">{cfg['栏目标签']}</div><div class="series">{cfg['系列名']}</div></div>
<div id="chapters"></div>
{markup}
<div id="sub"></div><div id="fade"></div></div>
<script>const TL={json.dumps(tl_js, ensure_ascii=False)};const SUBS={json.dumps([{k: s[k] for k in ('a', 'b', 'h')} for s in subs], ensure_ascii=False)};const PROJ={json.dumps(proj, ensure_ascii=False)};</script>
<script>{eng}</script>
<script>{''.join(scripts)}</script>
<script>engineStart();</script>
</body></html>'''
    outp = Path(out) if out else d / 'work' / 'index.html'
    outp.write_text(html, encoding='utf-8')
    # 行号表：写画面时对照用
    with open(d / 'work' / '行号表.txt', 'w', encoding='utf-8') as f:
        f.write('写画面时用“段.行”指定时间，比如 at(\'3.2\',\'右下角\')。\n\n')
        for L, T in zip(flat, tl['lines']):
            if L['first']:
                f.write(f"\n# 第{L['sec']}段 {L['secname']}（S({L['sec']})）\n")
            f.write(f"{L['sec']}.{L['li']}  {T['nct'][0]:7.2f}秒  {'★' if L['punch'] else ' '}{L['text']}\n")
    if not tl.get('估算'):
        with open(d / 'out' / '字幕.srt', 'w', encoding='utf-8') as f:
            for i, s in enumerate(subs, 1):
                f.write(f"{i}\n{srt_time(s['a'])} --> {srt_time(s['b'])}\n{s['text']}\n\n")
    if not quiet:
        print(f'页面已生成：{outp}（{THEMES[theme]}·{orient}版，{len(flat)}句，{len(subs)}条字幕，总长{tl["total"]:.1f}秒）')
    return outp, tl


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('项目', nargs='?', default='.')
    ap.add_argument('--风格'); ap.add_argument('--竖', action='store_true'); ap.add_argument('--横', action='store_true')
    ap.add_argument('--输出')
    a = ap.parse_args()
    build(proj_dir(a.项目), a.风格, '竖' if a.竖 else ('横' if a.横 else None), a.输出)
