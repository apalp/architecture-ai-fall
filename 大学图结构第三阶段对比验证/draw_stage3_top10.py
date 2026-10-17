"""Draw fixed-position Stage III insertion candidates as PNG/SVG and a contact sheet."""
import json, math, html
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
PACKAGED=(HERE/'输入数据').exists()
DATA=HERE/'输入数据'
RESULT=HERE/'结果' if PACKAGED else HERE/'分析输出/第III阶段新增节点优化'
OUT=RESULT/'前10名图结构'; OUT.mkdir(parents=True,exist_ok=True)
stage=json.loads((DATA/'拓扑.json').read_text(encoding='utf-8-sig'))['stages'][2]
result=json.loads((RESULT/'计算结果.json').read_text(encoding='utf-8'))
nodes={r['id']:r for r in stage['nodes']}
W,H=1500,1180; SCALE=6; LEFT=150; TOP=190
fontpath='C:/Windows/Fonts/msyh.ttc'
fonts={s:ImageFont.truetype(fontpath,s) for s in [18,20,23,26,30,38]}
def xy(node):return (LEFT+(node['x']-65)*SCALE,TOP+(node['y']-40)*SCALE)
def draw_one(row=None):
    im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>']
    def line(p,q,color,width):
        d.line((*p,*q),fill=color,width=width)
        svg.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{color}" stroke-width="{width}"/>')
    def circle(p,r,fill,outline,width=2):
        x,y=p;d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=outline,width=width)
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{outline}" stroke-width="{width}"/>')
    def text(p,s,size=23,fill='#334155',anchor='la'):
        d.text(p,s,font=fonts[size],fill=fill,anchor=anchor)
        align='middle' if anchor.startswith('m') else 'start'
        svg.append(f'<text x="{p[0]}" y="{p[1]+size}" text-anchor="{align}" font-family="Microsoft YaHei,Arial" font-size="{size}" fill="{fill}">{html.escape(s)}</text>')
    name='原始V3图结构' if row is None else f"第{row['rank']:02d}名 · {row['a']}号楼—新增节点—{row['b']}号楼"
    text((60,32),name,38,'#0f172a')
    subtitle=f"{len(stage['nodes'])}个节点 / {len(stage['edges'])}条边 / 原始节点坐标固定" if row is None else f"综合分 {row['score']:.6f}    全局效率 {row['global_efficiency']:.6f}    33个节点 / {row['total_edges']}条边"
    text((60,94),subtitle,26)
    selected={row['a'],row['b']} if row else set()
    for e in stage['edges']:
        if row and row['original_edge'] and {e['a'],e['b']}==selected:continue
        line(xy(nodes[e['a']]),xy(nodes[e['b']]),'#94a3b8',3)
    newpos=None
    if row:
        p,q=xy(nodes[row['a']]),xy(nodes[row['b']]);newpos=((p[0]+q[0])/2,(p[1]+q[1])/2)
        # Start at the geometric midpoint. Offset only the new node if it obscures an old node.
        if min(math.dist(newpos,xy(n)) for n in nodes.values())<40:
            dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy) or 1
            candidates=[(newpos[0]-dy/length*s,newpos[1]+dx/length*s) for s in [45,-45,70,-70,95,-95]]
            newpos=max(candidates,key=lambda z:min(math.dist(z,xy(n)) for n in nodes.values()))
        line(p,newpos,'#e11d48',7);line(newpos,q,'#e11d48',7)
    for ident,node in nodes.items():
        p=xy(node); endpoint=ident in selected
        circle(p,15 if endpoint else 11,'#dbeafe' if endpoint else '#f1f5f9','#2563eb' if endpoint else '#64748b',3 if endpoint else 2)
        # Preserve the editor's original label offsets and add a small baseline displacement.
        lx=p[0]+node.get('labelDx',0)*SCALE;ly=p[1]+node.get('labelDy',6)*SCALE+2
        text((lx,ly),ident,23,'#1d4ed8' if endpoint else '#334155','ma')
    if row:
        circle(newpos,30,'#ffe4e6','#e11d48',4);circle(newpos,21,'#e11d48','#ffffff',2)
        text((newpos[0],newpos[1]-16),'新',26,'white','ma')
        # A fixed legend avoids attaching a long label to a crowded building cluster.
        text((60,1010),'红色节点 / 红线：新增节点（12号楼学科）及两条连接；蓝色：两个连接端点。',23)
        rule='原端点有边：删除原边并插入，净增1条边。' if row['original_edge'] else '原端点无边：新增两条连接，净增2条边。'
        text((60,1052),rule,23)
        row['drawing_new_node_position']={'x':(newpos[0]-LEFT)/SCALE+65,'y':(newpos[1]-TOP)/SCALE+40}
    else:text((60,1010),'原始V3坐标按统一比例绘制；后续10个方案中原节点位置完全一致。',23)
    text((60,1100),'图面坐标仅用于展示；按拓扑步数评分，不代表实际建筑选址或米制距离。',20,'#64748b')
    svg.append('</svg>')
    stem='00_原始V3图结构' if row is None else f"{row['rank']:02d}_{row['a']}_{row['b']}_新增后图结构"
    im.save(OUT/(stem+'.png'));(OUT/(stem+'.svg')).write_text('\n'.join(svg),encoding='utf-8')
    if row:
        modified=json.loads(json.dumps(stage));modified['nodes'].append(dict(id='NEW12',name='新增节点（12号楼学科）',kind='building',**row['drawing_new_node_position']))
        if row['original_edge']:modified['edges']=[e for e in modified['edges'] if {e['a'],e['b']}!=selected]
        modified['edges'] += [dict(a=row['a'],b='NEW12'),dict(a='NEW12',b=row['b'])]
        assert all(modified['nodes'][i]==stage['nodes'][i] for i in range(len(stage['nodes'])))
        assert len(modified['edges'])==row['total_edges']
        (OUT/(stem+'.json')).write_text(json.dumps(modified,ensure_ascii=False,indent=2),encoding='utf-8')
    return im

draw_one()
ims=[draw_one(dict(r)) for r in result['top10']]
tw,th=750,590
sheet=Image.new('RGB',(tw*2,th*5),'#e2e8f0')
for i,im in enumerate(ims):sheet.paste(im.resize((tw,th),Image.Resampling.LANCZOS),((i%2)*tw,(i//2)*th))
sheet.save(OUT/'前10名总览.png')
links=''.join(f'<figure><img src="{r["rank"]:02d}_{r["a"]}_{r["b"]}_新增后图结构.svg"><figcaption>第{r["rank"]}名：{r["a"]}—{r["b"]}，得分{r["score"]:.6f}</figcaption></figure>' for r in result['top10'])
(OUT/'查看全部方案.html').write_text('<!doctype html><meta charset="utf-8"><title>V3新增节点前10名</title><style>body{font-family:system-ui;background:#eef2f6;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(600px,1fr));gap:20px}figure{background:white;margin:0;padding:12px}img{width:100%}figcaption{text-align:center;padding:10px}</style><h1>V3新增节点前10名</h1><p>原V3节点位置固定。红色为新增节点及连接线，蓝色为连接端点。</p><main>'+links+'</main>',encoding='utf-8')
print(str(OUT))
