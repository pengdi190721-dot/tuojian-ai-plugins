"""新建项目 / 按口播稿生成画面骨架。
用法：
  python3 new_project.py 项目目录                 # 新建项目文件夹（project.json、script.txt、assets/）
  python3 new_project.py 项目目录 --画面骨架        # 口播稿写好后，生成 scenes.html 骨架：每段一个 section，写好主讲词、标签、画框和金句卡的位置
  加 --覆盖 可以覆盖已有的 scenes.html"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import parse_script

SCRIPT_TPL = """// 口播稿格式：
// # 段名            新的一段；段名后面加【章】，会显示在顶部进度条
// 每行一句          一行就是视频里的一句字幕，念的时候每句之间停半秒
// ★开头            金句，画面会弹出黑底金句卡，前面多停一下
// //开头           备注，不念

# 片头
想把AI用明白，这几个词老板们一定要搞懂。

# 第一个词【章】
第一个词，……
★所以……
"""


def create(d):
    d.mkdir(parents=True, exist_ok=True)
    (d / 'assets').mkdir(exist_ok=True)
    if not (d / 'project.json').exists():
        (d / 'project.json').write_text(json.dumps({'栏目标签': '老板问答', '系列名': '', '风格': 'qingshuang', '画幅': '横', '录音文件': ''},
                                                   ensure_ascii=False, indent=1), encoding='utf-8')
    if not (d / 'script.txt').exists():
        (d / 'script.txt').write_text(SCRIPT_TPL, encoding='utf-8')
    print(f'项目建好了：{d}\n  - 截图放进 assets/\n  - 口播稿写进 script.txt\n  - 风格、画幅在 project.json 里改')


def scaffold(d, overwrite=False):
    p = d / 'scenes.html'
    if p.exists() and not overwrite:
        sys.exit('scenes.html 已经有了。要重新生成请加 --覆盖（会丢掉已写的画面）')
    secs, flat = parse_script(d)
    out = ['<!-- 画面骨架：按口播稿自动生成。把所有占位内容换成真正的画面；组件和时间写法见技能里的 references/组件库.md -->']
    for k, s in enumerate(secs, 1):
        n = len(s['lines'])
        punch = [j for j, L in enumerate(s['lines'], 1) if L['punch']]
        out.append(f'\n<!-- ============ 第{k}段 {s["name"]} ============ -->')
        for j, L in enumerate(s['lines'], 1):
            out.append(f'<!-- {k}.{j} {"★" if L["punch"] else ""}{L["text"]} -->')
        out.append(f'<section class="sec" data-sec="{k}">')
        if k == 1:
            out.append(f''' <div class="R-center"><div class="center-col">
  <div class="h-huge el" data-in="ls('1.1')">TODO 片头大字</div>
 </div></div>''')
        else:
            out.append(f''' <div class="R-term el" data-a="left" data-in="S({k})+0.2">
  <div class="lbl">TODO 小标题</div><div class="term">{s["name"]}</div>
  <div class="eq el" data-a="left" data-in="ls('{k}.2')">＝TODO 一句话比喻</div>
 </div>
 <div class="R-notes">
  <div class="note el" data-a="left" data-sfx="pop" data-in="ls('{k}.2')">位置：<b>TODO 在界面哪里</b></div>
 </div>
 <div class="R-frame cam" id="cam{k}a" data-img="TODO.png"></div>''')
        for j in punch:
            dout = (' data-out="ls(' + "'" + f'{k}.{j + 1}' + "'" + ')"') if j < n else ''
            out.append(f''' <div class="a dim el" data-a="fade" data-in="ls('{k}.{j}')"{dout}></div>
 <div class="quote el" data-a="pop" data-sfx="thud" data-in="ls('{k}.{j}')"{dout}><small>划重点</small>TODO <em>金句重点</em></div>''')
        out.append('</section>')
        if k > 1:
            out.append(f'''<script>
cam('cam{k}a',{{show:[[S({k})+0.3, ls('{k}.{min(3, n)}')]], views:[[0,[0,0,1920,1080]]],
  marks:[{{in: ls('{k}.2'), out: ls('{k}.{min(3, n)}'), r:[0,0,100,100]}}]}});  // TODO 用 grid.py 读坐标
</script>''')
    p.write_text('\n'.join(out), encoding='utf-8')
    print(f'画面骨架：{p}（{len(secs)} 段）。接下来把每段的 TODO 写成真正的画面')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    d = Path(args[0] if args else '.').resolve()
    if '--画面骨架' in sys.argv:
        scaffold(d, '--覆盖' in sys.argv)
    else:
        create(d)
