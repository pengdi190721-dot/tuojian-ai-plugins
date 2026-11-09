#!/usr/bin/env python3
"""模拟 WorkBuddy 开放平台的“内置文件缺失”检查：扫专家包里每个文档提到的文件路径，包里找不到就报出来。
用法：python3 scripts/check_refs.py 专家包.zip（或解压后的目录）
规则（宁严勿松）：
  - md 链接 [文字](路径)
  - 反引号里、或正文里以 scripts/ references/ agents/ avatars/ skills/ assets/ 开头的路径
  - 正文里带常见扩展名的文件名（.py .md .yaml .json .png .jpg）
  以上都要能在包里找到（相对文档所在目录、技能根目录、包根目录，任一处有即可）；
  带 * 或 xxx、脚本名 这种占位写法一律算问题。"""
import re, sys, zipfile, tempfile
warns = set()
from pathlib import Path

DIRS = ('scripts', 'references', 'agents', 'avatars', 'skills', 'assets')
EXT = ('py', 'md', 'yaml', 'yml', 'json', 'png', 'jpg', 'jpeg')
TOKEN = re.compile(r'(?<![\w./-])((?:\.{1,2}/)?(?:' + '|'.join(DIRS) + r')/[^\s`\'"，。、；：）)\]】<>|]*)')
FILE = re.compile(r'(?<![\w/.-])([\w一-鿿.-]+\.(?:' + '|'.join(EXT) + r'))(?![\w])')
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')


def check(root):
    root = Path(root)
    skills = [p.parent for p in root.rglob('SKILL.md')]
    files = [p for p in root.rglob('*') if p.is_file() and p.suffix in ('.md', '.yaml', '.yml', '.py', '.json')]
    allnames = {p.name for p in root.rglob('*')}
    problems = []
    global warns

    def exists(ref, doc):
        ref = ref.split('#')[0].rstrip('/')
        if not ref:
            return True
        if any(x in ref for x in ('*', 'xxx', '脚本名', '文件名', '...')):
            return False
        # 技能里的文档：相对文档本身或技能根目录；技能外的（agents、README）：相对文档本身或包根目录
        sk = next((s for s in skills if s in doc.parents), None)
        bases = [doc.parent, sk] if sk else [doc.parent, root]
        return any((b / ref).exists() for b in bases)

    for f in files:
        text = f.read_text(encoding='utf-8', errors='replace')
        rel = f.relative_to(root)
        for m in LINK.finditer(text):
            t = m.group(1)
            if t.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            if not exists(t, f):
                problems.append((str(rel), t, '链接指向的文件不存在'))
        for m in TOKEN.finditer(text):
            t = m.group(1).rstrip('.')
            if '/' not in t.strip('./') and t.rstrip('/') in DIRS:
                continue
            if not exists(t, f):
                problems.append((str(rel), t, '提到的路径在包里找不到'))
        if f.suffix == '.md':
            for m in FILE.finditer(text):
                t = m.group(1)
                if t in allnames or exists(t, f):
                    continue
                warns.add((str(rel), t))
    return problems


if __name__ == '__main__':
    src = Path(sys.argv[1])
    if src.suffix == '.zip':
        tmp = tempfile.mkdtemp()
        zipfile.ZipFile(src).extractall(tmp)
        src = Path(tmp)
    ps = check(src)
    seen = set()
    for doc, ref, why in ps:
        if (doc, ref) in seen:
            continue
        seen.add((doc, ref))
        print(f'【问题】{doc}：{why} → {ref}')
    if warns:
        names = sorted({t for _, t in warns})
        print(f'【提醒，不算问题】{len(names)} 个单独的文件名是用户项目里运行时才有的（截图、项目配置等），平台目前不查：{"、".join(names)}')
    print('引用检查：' + ('全部找得到' if not ps else f'{len(seen)} 处有问题'))
    sys.exit(1 if ps else 0)
