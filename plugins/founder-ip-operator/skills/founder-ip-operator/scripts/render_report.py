#!/usr/bin/env python3
"""Render a founder report with only the Python standard library. No network or publishing."""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]

def esc(value):
    return html.escape(str(value),quote=True)

def string(value,label):
    if not isinstance(value,str):raise ValueError(label+' 必须是文字')
    return value

def strings(value,label):
    if not isinstance(value,list) or not all(isinstance(x,str) for x in value):raise ValueError(label+' 必须是文字列表')
    return value

def obj(value,label):
    if not isinstance(value,dict):raise ValueError(label+' 必须是对象')
    return value

def url(value):
    value=string(value,'链接')
    u=urlparse(value)
    if u.scheme not in ('http','https') or not u.netloc:raise ValueError('来源链接仅支持完整的 http 或 https 地址')
    return esc(value)

def paragraphs(text,cls=''):
    return ''.join('<p'+(' class="'+cls+'"' if cls else '')+'>'+esc(p).replace('\n','<br>')+'</p>' for p in string(text,'正文').split('\n\n') if p.strip())

def render_block(b,prefix,reading):
    obj(b,'内容块');kind=b.get('type')
    if kind=='priorities':
        return '<div class="key-points">'+''.join('<article><small>'+esc(x.get('label',''))+'</small><h3>'+esc(x['title'])+'</h3>'+paragraphs(x['text'])+'</article>' for x in b['items'])+'</div>'
    if kind=='actions':
        return '<ol class="next-actions">'+''.join('<li><div><b>'+esc(x['title'])+'</b>'+paragraphs(x['text'])+'</div><aside>'+esc(x.get('owner',''))+'<br>'+esc(x.get('when',''))+'</aside></li>' for x in b['items'])+'</ol>'
    if kind=='links':
        return '<div class="resource-links">'+''.join('<a data-open-section href="#'+esc(x['target'])+'">'+esc(x['label'])+' ↗</a>' for x in b['items'])+'</div>'
    if kind=='text':return paragraphs(b['text'])
    if kind=='heading':return '<h3>'+esc(string(b['text'],'标题'))+'</h3>'
    if kind=='notice':return '<div class="notice"><b>'+esc(b.get('title','说明'))+'</b>'+paragraphs(b['text'])+'</div>'
    if kind=='quote':return '<div class="sample-opening"><span class="small-label">'+esc(b.get('label','语料摘句'))+'</span><blockquote>'+esc(string(b['text'],'引文'))+'</blockquote></div>'
    if kind=='list':return '<ul>'+''.join('<li>'+esc(x)+'</li>' for x in strings(b['items'],'条目'))+'</ul>'
    if kind=='table':
        heads=strings(b['headers'],'表头');rows=b['rows']
        if not heads or not isinstance(rows,list):raise ValueError('表格必须包含表头与行列表')
        for row in rows:
            strings(row,'表格行')
            if len(row)!=len(heads):raise ValueError('表格列数不一致')
        if reading:
            return '<div class="reading-records">'+''.join('<article><h4>'+esc(row[0])+'</h4>'+''.join('<p><span class="small-label">'+esc(heads[i])+'</span>'+esc(cell)+'</p>' for i,cell in enumerate(row) if i)+'</article>' for row in rows)+'</div>'
        return '<div class="table-wrap" tabindex="0" role="region" aria-label="'+esc(b.get('caption','报告表格'))+'"><table><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    if kind=='script':
        title=esc(string(b['title'],'文案标题'));meta=esc(b.get('meta',''));label=esc(b.get('status','待本人试读'))
        content='<div class="script-tools"><span>'+label+'</span>'+(('' if reading else '<button type="button" data-copy="'+prefix+'-text">复制文案</button>'))+'</div><div class="script-text" id="'+prefix+'-text">'+paragraphs(b['text'],'spoken')+'</div><div class="script-note">'+esc(b.get('notes',''))+'</div>'
        return '<details class="script"'+(' open' if reading else '')+'><summary><span><b>'+title+'</b><small>'+meta+'</small></span><span class="expand">展开文案</span></summary><div class="script-inner">'+content+'</div></details>'
    if kind=='platforms':
        items=b['items']
        if not isinstance(items,list) or not items:raise ValueError('平台内容不可为空')
        tabs='';panels=''
        for i,item in enumerate(items):
            obj(item,'平台');name=esc(string(item['name'],'平台名称'));key=prefix+'-platform-'+str(i)
            tabs+='<button type="button" role="tab" id="'+key+'-tab" aria-controls="'+key+'" aria-selected="'+str(i==0).lower()+'" tabindex="'+('0' if i==0 else '-1')+'">'+name+'</button>'
            body=''
            for field,label in [('mechanism','公开机制与证据范围'),('audience','观众使用场景'),('strategy','本项目内容建议'),('rules','规则与制作要求'),('metrics','主要观察指标')]:
                if field in item:body+='<h4>'+label+'</h4>'+paragraphs(item[field])
            if 'sources' in item:body+=render_block({'type':'sources','items':item['sources']},key+'-sources',reading)
            panels+='<article class="platform-panel" id="'+key+'"'+('' if reading else ' role="tabpanel" aria-labelledby="'+key+'-tab"')+(' hidden' if i and not reading else '')+'><h3>'+name+'</h3>'+body+'</article>'
        return '<div class="platform-group">'+('' if reading else '<div class="tabs" role="tablist" aria-label="平台策略">'+tabs+'</div>')+panels+'</div>'
    if kind=='services':
        plans=b['plans']
        if not isinstance(plans,list):raise ValueError('服务方案必须是列表')
        for plan in plans:obj(plan,'服务方案')
        if [p.get('name') for p in plans]!=['策划','成片交付','全案代运营']:raise ValueError('服务方案须依次列出策划、成片交付、全案代运营')
        selected=b.get('selected','待选择')
        if selected not in ['待选择','策划','成片交付','全案代运营']:raise ValueError('服务选择不合法')
        cards=''
        for i,plan in enumerate(plans):
            fields=plan['fields']
            if not isinstance(fields,dict):raise ValueError('服务范围必须是字段对象')
            cards+='<article class="service-plan'+(' selected' if plan['name']==selected else '')+'" data-plan="'+esc(plan['name'])+'"><h3>'+esc(plan['name'])+'</h3>'+''.join('<h4>'+esc(k)+'</h4>'+paragraphs(string(v,'服务说明')) for k,v in fields.items())+'</article>'
        controls='' if reading else '<div class="choice-buttons" role="group" aria-label="服务意向">'+''.join('<button type="button" data-service-choice="'+esc(name)+'" aria-pressed="'+str(selected==name).lower()+'">'+esc(name)+'</button>' for name in ['策划','成片交付','全案代运营','待选择'])+'</div>'
        return '<div class="service-group"><p class="pill">服务意向：<b data-selection>'+esc(selected)+'</b></p>'+controls+cards+'<p class="note">'+esc(b.get('note','具体周期、数量、人员与费用依双方确认清单执行。'))+'</p></div>'
    if kind=='sources':
        items=b['items']
        if not isinstance(items,list):raise ValueError('来源必须是列表')
        output=''
        for item in items:
            obj(item,'来源');output+='<li><div><a target="_blank" rel="noopener" href="'+url(item['url'])+'">'+esc(string(item['title'],'来源标题'))+'</a><p>'+esc(item.get('note',''))+'</p></div></li>'
        return '<ol class="source-list">'+output+'</ol>'
    raise ValueError('不支持的内容块：'+str(kind))

def render(data,reading=False,brief=False):
    obj(data,'报告')
    for key in ['report_title','client_name','report_date','status']:string(data[key],key)
    if not isinstance(data.get('simulation'),bool):raise ValueError('simulation 必须明确为 true 或 false')
    if data.get('layout')=='focused':
        from report_focus import render_focused
        return render_focused(data,reading,brief,esc,paragraphs,render_block)
    if brief:raise ValueError('重点版需要分层报告资料')
    sections=data['sections']
    if not isinstance(sections,list) or not sections:raise ValueError('报告至少应有一章')
    headings=[];contents=[]
    for n,s in enumerate(sections,1):
        obj(s,'章节');title=string(s['title'],'章节标题');key='chapter-'+str(n);headings.append((key,title))
        if not isinstance(s.get('blocks'),list):raise ValueError('章节必须有内容块列表')
        body=''.join(render_block(b,key+'-block-'+str(j),reading) for j,b in enumerate(s['blocks']))
        contents.append('<section class="report-section" id="'+key+'" data-title="'+esc(title)+'"><header class="section-header"><div class="eyebrow">'+str(n).zfill(2)+' / '+esc(data['client_name'])+'</div><h2>'+esc(title)+'</h2>'+paragraphs(s.get('summary',''))+'</header>'+body+'<footer class="section-footer"><span>'+esc(data['client_name'])+' · '+esc(data['status'])+'</span><span>'+str(n)+' / '+str(len(sections))+'</span></footer></section>')
    nav=''.join('<a href="#'+key+'" data-index="'+str(i)+'"><span>'+str(i+1).zfill(2)+'</span>'+esc(title)+'</a>' for i,(key,title) in enumerate(headings))
    css=(ROOT/'assets/report.css').read_text(encoding='utf-8');js='' if reading else (ROOT/'assets/report.js').read_text(encoding='utf-8')
    status='模拟样稿｜人物与故事为演示设定，不作为真实客户案例。' if data['simulation'] else '报告状态：'+data['status']
    cover='<div class="generated-cover"><span class="eyebrow">创始人 IP 操盘手 · 1.3.0</span><h1>'+esc(data['report_title'])+'</h1><p>'+esc(data['client_name'])+' · '+esc(data['report_date'])+'</p>'+paragraphs(data.get('subtitle',''))+'<p class="simulation">'+esc(status)+'</p></div>'
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(data['report_title'])+'</title><link rel="icon" href="data:,"><style>'+css+'</style></head><body class="'+('reading' if reading else '')+'"><a class="skip" href="#main">跳至报告</a><aside class="sidebar"><div class="brand"><span class="brand-mark">策</span><div><b>创始人 IP</b><small>客户专属报告</small></div></div><div class="nav-label">报告目录</div><nav aria-label="报告章节">'+nav+'</nav></aside><header class="toolbar"><div class="breadcrumb"><b id="current-title">'+esc(data['client_name'])+'</b></div><div class="toolbar-actions"><button id="theme">深色</button><button id="print">打印</button><button id="present" class="primary" aria-pressed="false">演示模式</button></div></header><div class="mobile-nav"><label for="chapter">报告章节</label><select id="chapter">'+''.join('<option value="'+k+'">'+esc(t)+'</option>' for k,t in headings)+'</select></div><main id="main">'+cover+''.join(contents)+'</main><div class="presentation-controls"><button id="prev">上一章</button><span id="slide-status" aria-live="polite"></span><button id="next">下一章</button></div><div id="toast" role="status"></div><script>'+js+'</script></body></html>'

def main():
    parser=argparse.ArgumentParser(description='根据结构化报告资料生成独立 HTML')
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--reading',action='store_true',help='展开文案和平台，宽表格转成竖版内容');parser.add_argument('--overwrite',action='store_true',help='允许覆盖指定输出文件')
    parser.add_argument('--brief',action='store_true',help='只输出分层报告的重点章节')
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():parser.error('输入与输出不能是同一文件')
    if args.output.exists() and not args.overwrite:parser.error('输出已存在；确认要更新时使用 --overwrite')
    try:
        data=json.loads(args.input.read_text(encoding='utf-8'));result=render(data,args.reading,args.brief)
    except (OSError,ValueError,KeyError,TypeError) as e:parser.error('资料格式错误：'+str(e))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(result,encoding='utf-8')
    print('已生成：'+str(args.output))

if __name__=='__main__':main()
