"""A 线：字幕稿 + 包装单 → 时间线 work/tl.json（所有时间都从字的时间算出来，不写死秒数）。
用法：python3 video_build.py 项目目录
需要：work/asr_cut.json（video_cut.py 生成）、字幕稿.txt、包装.json（写法见 references/口播剪辑.md）"""
import json, re, sys, difflib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *

CANON = {'地': '的', '得': '的', '它': '他', '她': '他', '做': '作'}


def bad(msg):
    sys.exit('【出错】' + msg)


def read_lines(d):
    p = d / '字幕稿.txt'
    if not p.exists():
        bad('还没有 字幕稿.txt。先看 work/字幕稿_草稿.txt，改好后存成项目目录里的 字幕稿.txt')
    lines = [l.strip() for l in p.read_text(encoding='utf-8').splitlines()]
    lines = [l for l in lines if l and not l.startswith('//')]
    for i, l in enumerate(lines, 1):
        if l.count('【') != l.count('】'):
            bad(f'字幕稿第 {i} 行【】没配对：{l}')
        n = len(re.sub(r'[【】，。、？！：；“”‘’,.?!:; ]', '', l))
        if n > 16:
            print(f'【提醒】字幕稿第 {i} 行有 {n} 个字，超过 16 个字一行放不下，建议拆成两行：{l}')
    return lines


def chars_of(line):
    """返回 [(显示的字, 是否重点词, 用来对齐的字)]；AI 当成 a、i 两个字对齐"""
    out, kw = [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '【': kw = True; i += 1; continue
        if ch == '】': kw = False; i += 1; continue
        if line[i:i + 2].upper() == 'AI':
            out.append(('A', kw, 'a')); out.append(('I', kw, 'i')); i += 2; continue
        key = '' if ch in '，。、？！：；“”‘’,.?!:; ' else ch.lower()
        out.append((ch, kw, key))
        i += 1
    return out


def align(lines, asr):
    A = []
    for s in asr['segs']:
        for t, ts in s['toks']:
            for c in t.lower():
                if c.strip():
                    A.append((c, ts))
    S = []
    for li, line in enumerate(lines):
        for ci, (ch, kw, key) in enumerate(chars_of(line)):
            if key:
                S.append((key, li, ci))
    cz = lambda c: CANON.get(c, c)
    sm = difflib.SequenceMatcher(None, [cz(c) for c, _, _ in S], [cz(c) for c, _ in A], autojunk=False)
    times = [None] * len(S)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace'):
            for k in range(min(i2 - i1, j2 - j1)):
                times[i1 + k] = A[j1 + k][1]
    for i in range(len(times)):
        if times[i] is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j] is not None), 0.0)
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j] is not None), prev + 0.25)
            times[i] = (prev + nxt) / 2
    out = []
    for li, line in enumerate(lines):
        cs = chars_of(line)
        tmap = {S[k][2]: times[k] for k in range(len(S)) if S[k][1] == li}
        if not tmap:
            bad(f'字幕稿第 {li + 1} 行对不上录音：{line}')
        chars, last = [], min(tmap.values())
        for ci, (ch, kw, key) in enumerate(cs):
            t = tmap.get(ci, last); last = t
            chars.append([ch, round(t, 3), kw])
        # 这一行和录音的吻合度
        own = [k for k in range(len(S)) if S[k][1] == li]
        out.append({'n': li + 1, 'text': re.sub('[【】]', '', line), 'chars': chars,
                    'start': round(min(tmap.values()), 3), 'end': round(max(tmap.values()) + 0.24, 3)})
    ratio = sm.ratio()
    return out, ratio


class Ref:
    def __init__(self, lines):
        self.L = lines

    def line(self, n, what='行号'):
        if not isinstance(n, int) or n < 1 or n > len(self.L):
            bad(f'包装.json 里的{what}「{n}」不对：字幕稿一共 {len(self.L)} 行')
        return self.L[n - 1]

    def t(self, ref):
        """'10' → 第10行开始；'10:客户' → 第10行里“客户”开始的时间"""
        s = str(ref)
        m = re.fullmatch(r'\s*(\d+)\s*(?:[:：]\s*(.+?))?\s*', s)
        if not m:
            bad(f'时间点「{ref}」写错了，要写成 "行号" 或 "行号:关键词"，例如 "10:客户"')
        L = self.line(int(m.group(1)))
        if not m.group(2):
            return L['start']
        txt = ''.join(c[0] for c in L['chars'])
        w = m.group(2)
        k = txt.find(w)
        if k < 0:
            bad(f'第 {L["n"]} 行「{L["text"]}」里找不到「{w}」，关键词要用这一行里原样有的字')
        return L['chars'][k][1]

    def end(self, n):
        return self.line(n)['end']


def build(d):
    cfg = load_cfg(d)
    meta = info(d)
    cut = json.loads((d / 'work' / 'cut.json').read_text(encoding='utf-8'))
    asr = json.loads((d / 'work' / 'asr_cut.json').read_text(encoding='utf-8'))
    lines, ratio = align(read_lines(d), asr)
    print(f'字幕稿 {len(lines)} 行，和录音吻合度 {ratio:.0%}' + ('' if ratio > 0.9 else '（偏低：检查字幕稿是不是漏了句子或多写了）'))
    pk = d / '包装.json'
    P = json.loads(pk.read_text(encoding='utf-8')) if pk.exists() else {}
    R = Ref(lines)
    fps = meta['fps']
    speech_end = lines[-1]['end']
    video_end = cut['frames'] / fps
    has_cta = bool(P.get('片尾', cfg.get('片尾')))
    END = round(max(video_end, speech_end + (2.4 if has_cta else 0.6)), 3)
    nxt = lambda n: lines[n]['start'] if n < len(lines) else END
    tl = {'fps': fps, 'end': END, 'video_frames': cut['frames'], 'orient': meta['orient'], 'theme': cfg['风格'],
          'column': P.get('栏目', cfg.get('栏目', '')), 'lines': lines, 'title': None, 'pops': [], 'pip': [], 'cards': [],
          'quotes': [], 'stamps': [], 'cta': None, 'cuts': cut['cuts_at'], 'hide_sub': [], 'sfx': []}
    if P.get('片头'):
        h = P['片头']
        if not (isinstance(h, list) and len(h) == 2):
            bad('包装.json 的“片头”要写两行，例如 ["老员工一句", "“这个要看情况”"]')
        later = [L['start'] for L in lines if L['start'] >= 2.8]
        tl['title'] = {'t0': 0.15, 't1': round(max(2.5, (later[0] if later else 3.2) - 0.15), 3), 'l1': h[0], 'l2': h[1]}
    windows = []
    for it in P.get('画面', []):
        k = it.get('类型')
        if k == '大字':
            n = it['行']; L = R.line(n)
            tl['pops'].append({'t0': L['start'] - 0.05, 't1': min(nxt(n), L['end'] + 0.4) - 0.1, 'text': it.get('文字', L['text'])})
            tl['hide_sub'].append(n)
        elif k == '金句':
            ns = it['行'] if isinstance(it['行'], list) else [it['行']]
            em = it.get('重点', ns[-1])
            parts = [[R.line(n)['text'], R.line(n)['start'], n == em] for n in ns]
            tl['quotes'].append({'t0': parts[0][1] - 0.15, 't1': min(R.end(ns[-1]) + 0.3, nxt(ns[-1]) - 0.05) if ns[-1] < len(lines) else speech_end + 0.15,
                                 'parts': parts, 'lines': ns})
            tl['hide_sub'] += ns
        elif k == '对比字':
            n = it['行']
            t0 = R.t(f"{n}:{it['词']}") if it.get('词') else R.line(n)['start']
            tl['stamps'].append({'t0': t0 - 0.05, 't1': nxt(n) - 0.1, 'a': it['左'], 'b': it['右']})
        elif k in ('要点卡', '三步卡', '截图'):
            a, b = it['从'], it['到']
            R.line(a, '“从”'); R.line(b, '“到”')
            if b < a:
                bad(f'{k}的“到”比“从”还早：{a} → {b}')
            c = {'t0': R.line(a)['start'] - 0.12, 'end': R.end(b) + 0.2, 'title': it.get('标题', '')}
            if k == '要点卡':
                c['kind'] = 'rows'
                c['rows'] = [[r[0], R.t(r[1])] for r in it['要点']]
                if len(c['rows']) > 4:
                    bad('要点卡最多 4 条，多了放不下，拆成两张')
            elif k == '三步卡':
                c['kind'] = 'steps'
                if it.get('不要'): c['no'] = [it['不要'][0], R.t(it['不要'][1])]
                c['steps'] = [[s[0], R.t(s[1])] for s in it['步骤']]
                if it.get('结论'): c['yes'] = [it['结论'][0], R.t(it['结论'][1])]
                c['label'] = it.get('标签', '要拆成：')
                if not 2 <= len(c['steps']) <= 4:
                    bad('三步卡的“步骤”要 2 到 4 个')
            else:
                img = d / it['图']
                if not img.exists():
                    img = d / 'assets' / it['图']
                if not img.exists():
                    bad(f'截图找不到：{it["图"]}（截图放进项目的 assets 文件夹，“图”里写截图的文件名）')
                from PIL import Image
                c['kind'] = 'shot'; c['src'] = img.resolve().as_uri(); c['size'] = list(Image.open(img).size)
                c['marks'] = [[m[0], m[1], m[2], m[3], R.t(m[4])] for m in it.get('圈', [])]
            windows.append(c)
        elif k:
            bad(f'不认识的画面类型「{k}」：只能是 大字、金句、对比字、要点卡、三步卡、截图')
    # 小窗段：相邻卡片间隔不到 1 秒就连成一段，不来回切
    windows.sort(key=lambda c: c['t0'])
    for i, c in enumerate(windows):
        c['t1'] = windows[i + 1]['t0'] if i + 1 < len(windows) and windows[i + 1]['t0'] - c['end'] < 1.0 else c['end']
    for c in windows:
        a, b = c['t0'] - 0.18, c['t1'] + 0.05
        if tl['pip'] and a - tl['pip'][-1][1] < 1.0:
            tl['pip'][-1][1] = b
        else:
            tl['pip'].append([a, b])
    # 小窗收尾时如果刚好碰上剪辑点，把收尾挪到剪辑点之后，跳剪藏在小窗里
    for seg in tl['pip']:
        for cpt in tl['cuts']:
            if seg[1] - 0.5 < cpt < seg[1] + 0.35:
                seg[1] = cpt + 0.06
        if seg[1] - seg[0] < 4:
            print(f'【提醒】{seg[0]:.1f} 秒开始的小窗只有 {seg[1] - seg[0]:.1f} 秒，少于 4 秒会显得切得太勤')
    tl['cards'] = [{k: v for k, v in c.items() if k != 'end'} for c in windows]
    for q in tl['quotes']:
        for a, b in tl['pip']:
            if q['t0'] < b and q['t1'] > a:
                # 只是首尾挨着（换版式那半秒里淡出/淡入）没关系，挪一下；真压在小窗段里才报错
                if q['t0'] < a and q['t1'] - a <= 0.7:
                    q['t1'] = min(q['t1'], a + 0.2)
                elif q['t1'] > b and b - q['t0'] <= 0.7:
                    q['t0'] = max(q['t0'], b - 0.2)
                else:
                    bad(f'第 {q["lines"][0]} 行的金句落在小窗段里了：金句只能在人像全屏时出现，改一下“从/到”')
    if has_cta:
        tl['cta'] = {'t0': round(speech_end + 0.15, 3), 't1': END, 'text': P.get('片尾', cfg.get('片尾'))}
    # 音效：换版式嗖、卡片和要点啵、金句和结论嘀、对比字咚
    sfx = []
    for a, b in tl['pip']:
        sfx += [['whoosh', a], ['whoosh', b - 0.5]]
    for c in tl['cards']:
        for r in c.get('rows', []): sfx.append(['pop', r[1]])
        if c['kind'] == 'steps':
            if c.get('no'): sfx.append(['thud', c['no'][1]])
            for s in c['steps']: sfx.append(['pop', s[1]])
            if c.get('yes'): sfx.append(['ding', c['yes'][1]])
        if c['kind'] == 'shot':
            for m in c['marks']: sfx.append(['ding', m[4] + 0.45])
    for q in tl['quotes']:
        sfx += [['whoosh', q['t0']], ['ding', [p for p in q['parts'] if p[2]][0][1] if any(p[2] for p in q['parts']) else q['parts'][-1][1]]]
    for p in tl['pops']: sfx.append(['ding', p['t0']])
    for s in tl['stamps']: sfx.append(['thud', s['t0']])
    if tl['title']: sfx.append(['pop', tl['title']['t0'] + 0.2])
    if tl['cta']: sfx.append(['pop', tl['cta']['t0'] + 0.1])
    tl['sfx'] = sorted(sfx, key=lambda x: x[1])
    (d / 'work' / 'tl.json').write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding='utf-8')
    with open(d / 'work' / '行号表.txt', 'w', encoding='utf-8') as f:
        for L in lines:
            f.write(f"{L['n']:3d}  {L['start']:6.2f}–{L['end']:6.2f}  {L['text']}\n")
    print(f'时间线好了：{END:.1f} 秒，小窗 {len(tl["pip"])} 段，卡片 {len(tl["cards"])} 张，金句 {len(tl["quotes"])} 张，音效 {len(sfx)} 个')
    return tl


if __name__ == '__main__':
    build(proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True))
