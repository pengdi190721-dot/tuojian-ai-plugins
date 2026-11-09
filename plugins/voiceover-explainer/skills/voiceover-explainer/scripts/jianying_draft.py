"""试验功能：出一份剪映草稿（用户说要才出）。草稿里是“剪好但没包装的视频 + 字幕轨”，用户可以在剪映里接着改。
用法：python3 jianying_draft.py 项目目录 [剪映草稿文件夹]
  - 不写草稿文件夹时，自动找电脑上剪映专业版的草稿位置；找不到就放在 out/剪映草稿/，再让用户手动拷过去
  - 只负责生成草稿文件，不会打开剪映、不连剪映服务器，不花剪映积分
  - 剪映版本差别大：第一次一定让用户在自己的剪映里打开试一次；苹果电脑能打开，但要自己点导出"""
import subprocess, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from video_common import *

MIRROR = 'https://pypi.tuna.tsinghua.edu.cn/simple'


def lib():
    try:
        import pyJianYingDraft
        return pyJianYingDraft
    except ImportError:
        print('第一次用，安装剪映草稿工具（pyJianYingDraft）…')
        cmd = [sys.executable, '-m', 'pip', 'install', '-i', MIRROR, 'pyJianYingDraft']
        if subprocess.run(cmd).returncode != 0:
            subprocess.run(cmd + ['--break-system-packages'])
        import pyJianYingDraft
        return pyJianYingDraft


def find_draft_dir():
    home = Path.home()
    cands = [home / 'AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft',
             home / 'Movies/JianyingPro/User Data/Projects/com.lveditor.draft',
             home / 'Movies/CapCut/User Data/Projects/com.lveditor.draft']
    return next((c for c in cands if c.exists()), None)


def main():
    d = proj(sys.argv[1] if len(sys.argv) > 1 else '.', need_src=True)
    meta = info(d)
    cut = d / 'work' / 'cut.mov'
    srt = d / 'out' / '字幕.srt'
    if not cut.exists() or not srt.exists():
        sys.exit('【出错】先把成片做完（要有 work/cut.mov 和 out/字幕.srt），再出剪映草稿')
    dr = lib()
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else find_draft_dir()
    manual = target is None
    if manual:
        target = d / 'out' / '剪映草稿'
        target.mkdir(parents=True, exist_ok=True)
    # 素材拷一份到 out/，草稿里引用这个位置，项目文件夹别挪
    mat = d / 'out' / '剪映素材_剪好的视频.mov'
    if not mat.exists() or mat.stat().st_mtime < cut.stat().st_mtime:
        import shutil; shutil.copy2(cut, mat)
    name = f'{d.name}_口播剪辑'
    import json
    dur = json.loads((d / 'work' / 'cut.json').read_text(encoding='utf-8'))['dur']
    f = dr.DraftFolder(str(target))
    s = f.create_draft(name, meta['W'], meta['H'], fps=meta['fps'], allow_replace=True)
    v = s.append_track(dr.TrackSpec(dr.TrackType.video, name='剪好的视频'))
    s.add_segment(dr.VideoSegment(str(mat.resolve()), dr.Timerange(0, int(dur * 1e6))), v)
    s.append_track(dr.TrackSpec(dr.TrackType.text, name='字幕'))
    s.import_srt(str(srt.resolve()), track_name='字幕')
    s.save()
    print(f'剪映草稿：{target / name}')
    if manual:
        print('没找到剪映的草稿文件夹：把这个文件夹拷进剪映的草稿位置（剪映 → 设置 → 草稿位置能看到），再打开剪映')
    print('提醒用户：这是试验功能，第一次先在自己的剪映里打开看看；里面没有包装动画，包装在成片里')


if __name__ == '__main__':
    main()
