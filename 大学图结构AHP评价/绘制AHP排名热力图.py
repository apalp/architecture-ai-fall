"""使用完整AHP结果与MIT第四阶段原始底图绘制排名热力图。"""
import base64, csv, io, json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / '评价输出'
DIST = HERE.parent / '大学图结构绘制/MIT/dist'
rows = list(csv.DictReader((OUT / '01_AHP综合得分与排名.csv').open(encoding='utf-8-sig', newline='')))
data = {r['楼号']: r for r in rows}
stage = json.loads((DIST / 'MIT_四阶段底图修改 .json').read_text(encoding='utf-8-sig'))['stages'][3]
assert set(data) == {n['id'] for n in stage['nodes']}, 'CSV与第四阶段节点不一致'
encoded = re.search(r'const BASE_IMAGE="data:image/png;base64,([^"]+)', (DIST / 'data.js').read_text(encoding='utf-8'))[1]
base = Image.open(io.BytesIO(base64.b64decode(encoded))).convert('RGB')
print('底图尺寸', base.size, '节点', len(rows), '首节点', stage['nodes'][0])
S = 5
LEFT, TOP = 35, 100
W, H = 1370, 940
im = Image.new('RGB', (W, H), 'white')
base = base.crop((360,237,595,399)).resize((235*S,162*S), Image.Resampling.LANCZOS)
base = Image.blend(Image.new('RGB',base.size,'white'),base,0.68)
im.paste(base,(LEFT,TOP))
d = ImageDraw.Draw(im)
fontpath = 'C:/Windows/Fonts/msyh.ttc'
def font(size): return ImageFont.truetype(fontpath,size)
def text(pos,value,size=22,fill='#17202a',anchor='mm',halo=False):
    d.text(pos,str(value),font=font(size),fill=fill,anchor=anchor,stroke_width=3 if halo else 0,stroke_fill='white')
def xy(n): return LEFT+(n['x']-50)*S, TOP+(n['y']-30)*S
nodes={n['id']: n for n in stage['nodes']}
for e in stage['edges']:
    d.line([xy(nodes[e['a']]),xy(nodes[e['b']])],fill='#94a3b8',width=3)
valid=[r for r in rows if r['综合排名'].strip()]
maxrank=max(int(r['综合排名']) for r in valid)
stops=[(255,255,204),(255,237,160),(254,178,76),(253,141,60),(252,78,42),(227,26,28),(189,0,38),(128,0,38)]
def color(rank):
    t=(maxrank-rank)/(maxrank-1)*(len(stops)-1)
    i=min(int(t),len(stops)-2); f=t-i
    return tuple(round(a+(b-a)*f) for a,b in zip(stops[i],stops[i+1]))
for n in stage['nodes']:
    r=data[n['id']]; x,y=xy(n); rank=int(r['综合排名']) if r['综合排名'].strip() else None
    fill=color(rank) if rank else '#cbd5e1'
    d.ellipse((x-23,y-23,x+23,y+23),fill=fill,outline='#535d68',width=2)
    text((x,y-1),n['id'],23,'white' if rank and rank<=10 else '#111827')
    # Keep the ranking outside the marker; move upper-row labels above it.
    dy=-38 if n['id'] in {'35','37','38','36'} else 39
    offsets={'33':(-47,37),'17':(14,40),'6C':(-42,34),'8':(43,0)}
    dx,dy=offsets.get(n['id'],(0,dy))
    text((x+dx,y+dy),f'第{rank}名' if rank else '缺失',18,'#334155',halo=True)
text((W/2,43),'MIT 第IV阶段｜AHP综合排名热力图',36)
bx,by,bw,bh=1240,180,36,650
for j in range(bh):
    rank=1+j/(bh-1)*(maxrank-1)
    d.line((bx,by+j,bx+bw,by+j),fill=color(rank))
d.rectangle((bx,by,bx+bw,by+bh),outline='#4b5563',width=2)
for rank in [1,5,10,15,20,25,30,maxrank]:
    y=by+(rank-1)/(maxrank-1)*bh
    d.line((bx+bw,y,bx+bw+7,y),fill='#4b5563',width=2)
    text((bx+bw+12,y),str(rank),20,anchor='lm')
text((bx+20,by-37),'综合排名',22)
im.save(OUT/'05_AHP综合排名热力图.png',dpi=(300,300))
im.save(OUT/'05_AHP综合排名热力图.pdf',resolution=300)
print(f'全部{len(rows)}个节点：{len(valid)}个有排名，{len(rows)-len(valid)}个缺失。输出完成。')
