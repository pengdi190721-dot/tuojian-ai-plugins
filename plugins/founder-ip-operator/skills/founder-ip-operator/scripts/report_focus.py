"""分层报告页面；由主生成器调用，仅使用标准库。"""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def render_focused(data,reading,brief,esc,paragraphs,render_block):
    source=data['sections']
    if not isinstance(source,list) or not source:raise ValueError('报告至少应有一章')
    ids=[]
    for section in source:
        if not isinstance(section,dict):raise ValueError('章节必须是对象')
        key=section.get('id','')
        if not isinstance(key,str) or not re.fullmatch(r'[a-z][a-z0-9-]*',key):raise ValueError('章节编号须为小写字母开头的英文短标识')
        if key in ids:raise ValueError('章节编号重复')
        if section.get('tier') not in ('main','detail'):raise ValueError('章节须标明重点或资料层')
        if not isinstance(section.get('blocks'),list):raise ValueError('章节内容须为列表')
        ids.append(key)
    main=[s for s in source if s['tier']=='main']
    if not main:raise ValueError('分层报告至少需要一个重点章节')
    for s in source:
        for b in s['blocks']:
            if b.get('type')=='links':
                for item in b['items']:
                    if item.get('target') not in ids:raise ValueError('资料链接指向不存在的章节')
    sections=main if brief else source
    details=[s for s in sections if s['tier']=='detail']
    first=main[0]['id']
    rendered=[]
    for i,s in enumerate(sections):
        key=s['id'];primary=s['tier']=='main'
        body=''.join(render_block(b,key+'-block-'+str(j),reading) for j,b in enumerate(s['blocks']) if not (brief and b.get('type')=='links'))
        heading='<header class="section-header"><div class="eyebrow">'+('重点决策' if primary else '配套资料')+' / '+esc(data['client_name'])+'</div><h2 tabindex="-1">'+esc(s['title'])+'</h2>'+paragraphs(s.get('summary',''))+'</header>'
        takeaway='<div class="takeaway"><span>'+esc(s.get('takeaway_label','注意事项'))+'</span>'+paragraphs(s['takeaway'])+'</div>' if s.get('takeaway') else ''
        status='<p class="scope-note">'+esc(data['status'])+' · '+esc(data['report_date'])+(' · 人物、故事与计划为模拟设定。' if data['simulation'] else '')+'</p>'
        back='' if primary or reading else '<a class="back-main" data-open-section href="#'+first+'">← 返回核心建议</a>'
        hidden=' hidden' if not reading and key!=first else ''
        rendered.append('<section class="report-section tier-'+s['tier']+'" data-tier="'+s['tier']+'" data-title="'+esc(s['title'])+'" id="'+key+'"'+hidden+'>'+back+heading+takeaway+body+'<footer class="section-footer">'+status+'</footer></section>')
    def nav(s,n=None):
        return '<a data-open-section href="#'+s['id']+'">'+('<span>'+str(n).zfill(2)+'</span>' if n else '')+esc(s.get('nav_title',s['title']))+'</a>'
    primary_nav=''.join(nav(s,i+1) for i,s in enumerate(main))
    detail_nav='<details class="detail-nav"><summary>配套资料 <span>'+str(len(details))+' 项</span></summary>'+''.join(nav(s) for s in details)+'</details>' if details else ''
    options='<optgroup label="先看重点">'+''.join('<option value="'+s['id']+'">'+esc(s.get('nav_title',s['title']))+'</option>' for s in main)+'</optgroup>'
    if details:options+='<optgroup label="按需查阅">'+''.join('<option value="'+s['id']+'">'+esc(s['title'])+'</option>' for s in details)+'</optgroup>'
    css=(ROOT/'assets/report.css').read_text()+'\n'+(ROOT/'assets/report-focus.css').read_text()
    js='' if reading else (ROOT/'assets/report-focus.js').read_text()
    intro='<div class="reading-title"><p class="eyebrow">创始人 IP 操盘手 · 1.3.0</p><h1>'+esc(data['report_title'])+'</h1><p>'+('老板重点版：核心建议、行动安排与合作选择。完整文案和研究材料另见完整版。' if brief else '完整阅读版：重点决策与配套资料均已展开。')+'</p></div>' if reading else ''
    html='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(data['report_title'])+'</title><link rel="icon" href="data:,"><style>'+css+'</style></head>'
    html+='<body class="focused'+(' reading' if reading else '')+(' brief' if brief else '')+'" data-print-scope="'+('all' if reading else 'main')+'"><a class="skip" href="#main">跳至报告</a>'
    html+='<aside class="sidebar"><div class="brand"><span class="brand-mark">策</span><div><b>创始人 IP</b><small>先看重点，再查资料</small></div></div><p class="nav-label">建议阅读顺序</p><nav aria-label="重点章节">'+primary_nav+'</nav>'+detail_nav+'<p class="sidebar-note">'+esc(data['client_name'])+'<br>'+esc(data['report_date'])+' · '+('模拟方案' if data['simulation'] else esc(data['status']))+'</p></aside>'
    html+='<header class="toolbar"><b id="current-title">'+esc(main[0]['title'])+'</b><div class="toolbar-actions"><details class="print-menu"><summary>导出 / 打印</summary><button data-print="main">仅打印重点</button><button data-print="all">打印完整报告</button></details><button id="present" class="primary" aria-pressed="false">演示重点</button></div></header>'
    html+='<div class="mobile-nav"><label for="chapter">阅读位置</label><select id="chapter">'+options+'</select></div><main id="main">'+intro+''.join(rendered)+'</main>'
    html+='<div class="presentation-controls"><button id="prev">上一页</button><span id="slide-status"></span><button id="next">下一页</button></div><div id="toast" role="status"></div>'
    html+='<noscript><style>.focused .report-section[hidden]{display:block!important}</style></noscript><script>'+js+'</script></body></html>'
    return html
