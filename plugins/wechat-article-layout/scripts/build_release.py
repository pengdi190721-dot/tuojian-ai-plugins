#!/usr/bin/env python3
"""公众号图文排版：生成主题清单和预览图、检查、构建插件包与独立技能包。
用法：python3 scripts/build_release.py
  - 改了 skills/wechat-article-layout/scripts/themes.py（加主题、改长相）以后必须跑一次，
    才会更新 references/themes.md 和安装页上的预览图 assets/主题预览.png（预览图需要装 playwright）
技能市场只收 .md / .yaml / .py 文件，所以技能文件夹里不放图片、网页；缩略图由 render.py --pick 现场生成。"""
from __future__ import annotations
import json, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

NAME = 'wechat-article-layout'
DISPLAY = '公众号图文排版'
ALLOWED = {'.md', '.yaml', '.py'}
PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / 'skills' / NAME
DIRS = ('scripts', 'references', 'assets', 'agents')
TOKEN = re.compile(r'(?<![\w./-])((?:' + '|'.join(DIRS) + r')/[^\s`\'"，。、；：）)\]】<>|]*)')


def require(ok, msg):
    if not ok:
        sys.exit('【不通过】' + msg)


def gen_themes_md():
    sys.path.insert(0, str(SKILL / 'scripts'))
    from themes import THEMES
    rows = '\n'.join(f'| {t.no} | {t.name} | {t.fit} | {t.look} | {t.recommend} |' for t in THEMES)
    (SKILL / 'references' / 'themes.md').write_text(
        '# 主题清单\n\n'
        '> 这个文件由插件的打包脚本根据 scripts/themes.py 自动生成，别手改。\n\n'
        '| 编号 | 主题 | 适合 | 长相 | 推荐栏目 |\n|---|---|---|---|---|\n'
        f'{rows}\n\n'
        '- 挑主题：在工作文件夹跑 `python3 scripts/render.py --pick`，把「选主题.png」发给用户；'
        '没装 playwright 就只有「选主题.html」，让用户打开看。\n'
        '- 用户没点名、栏目也对不上时，用设置里的默认主题。\n'
        '- 想拿用户自己的稿子比一比：`python3 scripts/render.py 文字稿.md --theme all`。\n',
        encoding='utf-8')
    print(f'主题清单已生成：{len(THEMES)} 套')
    return THEMES


def validate():
    codex = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    buddy = json.loads((PLUGIN / '.codebuddy-plugin/plugin.json').read_text(encoding='utf-8'))
    require(codex['name'] == buddy['name'] == NAME == PLUGIN.name, '插件名称不一致')
    require(codex['version'] == buddy['version'], '双平台版本不一致')
    require(codex['description'] == buddy['description'], '双平台介绍不一致')
    ver = codex['version']
    require(re.fullmatch(r'\d+\.\d+\.\d+', ver), '版本须为三段数字')
    require(codex['interface']['displayName'] == DISPLAY, '中文展示名称错误')
    front = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    m = re.match(r'\A---\n(.*?)\n---\n', front, re.S)
    require(m, '缺少技能元数据')
    require(re.search(r'(?m)^name: ' + NAME + '$', m.group(1)), '技能名称不一致')
    require(re.search(r'(?m)^  version: "' + re.escape(ver) + '"$', m.group(1)), '技能版本不一致')
    require(f'v{ver}' in front, 'SKILL.md 标题里的版本号没跟着改')
    readme = (PLUGIN / 'README.md').read_text(encoding='utf-8')
    require('版本：' + ver + ' ·' in readme, '安装页的版本号没跟着改')
    require('- **' + ver + '**' in readme, '更新记录里没有写本版')
    n = 0
    for p in sorted(SKILL.rglob('*')):
        if '__pycache__' in p.parts or not p.is_file():
            continue
        rel = p.relative_to(SKILL)
        require(not p.is_symlink(), '技能包含符号链接：' + str(rel))
        require(p.suffix in ALLOWED, '技能里有技能市场不收的文件：' + str(rel))
        text = p.read_text(encoding='utf-8')
        if p.suffix == '.md':
            for href in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
                if href.startswith(('http://', 'https://', '#')) or href in ('待补',) or href.startswith('示意图') \
                        or href.startswith('截图/'):
                    continue
                dest = (p.parent / href.split('#')[0]).resolve()
                require(str(dest).startswith(str(SKILL.resolve())), '技能引用越出自身目录：' + href)
                require(dest.is_file(), f'{rel} 引用的文件不存在：{href}')
        for t in TOKEN.findall(text):
            t = t.rstrip('.')
            if t.rstrip('/') in DIRS:
                continue
            require((SKILL / t).exists() or (p.parent / t).exists(), f'{rel} 提到的路径在技能里找不到：{t}')
        if p.suffix == '.py':
            compile(text, str(p), 'exec')
        n += 1
    repo = PLUGIN.parent.parent
    mk1, mk2 = repo / '.codebuddy-plugin/marketplace.json', repo / '.agents/plugins/marketplace.json'
    if mk1.exists() and mk2.exists():
        e1 = [p for p in json.loads(mk1.read_text(encoding='utf-8'))['plugins'] if p['name'] == NAME]
        e2 = [p for p in json.loads(mk2.read_text(encoding='utf-8'))['plugins'] if p['name'] == NAME]
        require(e1 and e2, '两个市场清单里都要登记本插件')
        require(e1[0]['version'] == ver, 'WorkBuddy 市场清单里的版本号没跟着改')
        require(e1[0]['description'] == buddy['description'], 'WorkBuddy 市场清单里的介绍和插件不一致')
        require(e1[0]['source'] == e2[0]['source']['path'] == f'./plugins/{NAME}', '市场清单里的路径不对')
        require(NAME in (repo / 'README.md').read_text(encoding='utf-8'), '仓库首页没有介绍本插件')
    print(f'检查通过：版本 {ver}，技能文件 {n} 个，只有 {"/".join(sorted(ALLOWED))}')
    return ver


def smoke(themes):
    render = SKILL / 'scripts' / 'render.py'
    with tempfile.TemporaryDirectory() as t:
        shutil.copy(SKILL / 'assets' / 'sample.md', Path(t) / '样稿.md')
        for th in themes:
            r = subprocess.run([sys.executable, str(render), str(Path(t) / '样稿.md'), '--theme', str(th.no)],
                               capture_output=True, text=True)
            require(r.returncode == 0 and '检查：通过' in r.stdout, f'{th.name} 排样稿没通过：\n{r.stdout[-600:]}{r.stderr[-600:]}')
        r = subprocess.run([sys.executable, str(render), '--pick', '--out', t], capture_output=True, text=True)
        require(r.returncode == 0 and (Path(t) / '选主题.html').is_file(), '选主题缩略图页没生成：' + r.stderr[-600:])
        png = Path(t) / '选主题.png'
        if png.is_file():
            shutil.copy(png, PLUGIN / 'assets' / '主题预览.png')
            print('预览图已更新：assets/主题预览.png')
        else:
            print('没装 playwright，预览图沿用旧的')
    require((PLUGIN / 'assets' / '主题预览.png').is_file(), '安装页用的预览图 assets/主题预览.png 不存在')
    print(f'样稿检查通过：{len(themes)} 套主题都能排、都过公众号格式检查，缩略图页能生成')


def package(ver):
    repo = PLUGIN.parent.parent
    out = (repo / 'output') if (repo / '.codebuddy-plugin/marketplace.json').exists() else (PLUGIN / 'output')
    out.mkdir(exist_ok=True)
    skip = lambda p: '__pycache__' in p.parts or p.suffix == '.pyc' or p.relative_to(PLUGIN).parts[0] == 'output'
    z1 = out / f'{NAME}-插件包-{ver}.zip'
    with zipfile.ZipFile(z1, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PLUGIN.rglob('*')):
            if p.is_file() and not skip(p):
                z.write(p, Path(NAME) / p.relative_to(PLUGIN))
    z2 = out / f'{NAME}-独立技能包-{ver}.zip'
    with zipfile.ZipFile(z2, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SKILL.rglob('*')):
            if p.is_file() and not skip(p):
                z.write(p, Path(NAME) / p.relative_to(SKILL))
    print('已构建：', z1.name, '、', z2.name, '（在', out, '）')


if __name__ == '__main__':
    themes = gen_themes_md()
    ver = validate()
    smoke(themes)
    package(ver)
