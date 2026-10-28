"""使用用户提供的地图截图作为SCUT默认底图并绘制现状AHP排名。"""
import base64,csv,json,re,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
SOURCE=Path('C:/Users/ASUS/AppData/Local/Temp/codex-clipboard-96125e9f-6073-407c-b4b9-281d3717ff4d.png')
TARGET=HERE/'五山校区_用户指定底图.png'
if SOURCE.exists(): shutil.copyfile(SOURCE,TARGET)
bg=Image.open(TARGET).convert('RGB')
w,h=bg.size
js=HERE/'data.js'
s=js.read_text(encoding='utf-8')
if not (HERE/'data_更换底图前.js.bak').exists(): shutil.copyfile(js,HERE/'data_更换底图前.js.bak')
s=re.sub(r'const REFERENCE_IMAGE = "data:image/png;base64,[^"]+";',lambda m:'const REFERENCE_IMAGE = "data:image/png;base64,'+base64.b64encode(TARGET.read_bytes()).decode()+'";',s)
js.write_text(s,encoding='utf-8')
app=HERE/'app.js'
s=app.read_text(encoding='utf-8')
if not (HERE/'app_更换底图前.js.bak').exists(): shutil.copyfile(app,HERE/'app_更换底图前.js.bak')
s=re.sub(r"const defaultBackground=\(\)=>\(\{.*?\}\);",f"const defaultBackground=()=>({{src:REFERENCE_IMAGE,name:'五山校区 · 用户指定地图截图',x:0,y:0,width:820,height:820*{h}/{w},isDefault:true}});",s,count=1)
s=s.replace("notice='已读取本机修改。'", "if(background?.isDefault)background=defaultBackground();notice='已读取本机修改。'")
app.write_text(s,encoding='utf-8')
graph=json.loads((HERE/'华工五山_已确认拓扑.json').read_text(encoding='utf-8-sig'))
out=ROOT/'大学图结构华南理工大学计算与预测/指标计算/正式输出/AHP评价'
rows=list(csv.DictReader((out/'01_AHP综合得分与排名.csv').open(encoding='utf-8-sig',newline='')))
data={r['楼号']:r for r in rows}
assert set(data)=={n['id'] for n in graph['nodes']}
valid=[r for r in rows if r['综合排名']]
hi=max(int(r['综合排名']) for r in valid)
im=Image.new('RGB',(w+180,h+95),'white')
im.paste(bg,(0,80))
d=ImageDraw.Draw(im)
def f(sz):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',sz)
def txt(x,y,t,sz=21,fill='#17202a',halo=True):d.text((x,y),t,font=f(sz),fill=fill,anchor='mm',stroke_width=3 if halo else 0,stroke_fill='white')
def xy(n):return n['x']*w/820,80+n['y']*w/820
nodes={n['id']:n for n in graph['nodes']}
for e in graph['edges']: d.line([xy(nodes[e['a']]),xy(nodes[e['b']])],fill='#64748b',width=4)
stops=[(255,255,204),(254,178,76),(252,78,42),(189,0,38),(128,0,38)]
def color(rank):
    t=(hi-rank)/max(1,hi-1)*4;i=min(int(t),3);q=t-i
    return tuple(round(a+(b-a)*q) for a,b in zip(stops[i],stops[i+1]))
for n in graph['nodes']:
    x,y=xy(n);r=data[n['id']];rank=int(r['综合排名']) if r['综合排名'] else None
    d.ellipse((x-25,y-25,x+25,y+25),fill=color(rank) if rank else '#cbd5e1',outline='#475569',width=2)
    txt(x,y,n['id'],18,'white' if rank and rank<=5 else '#17202a',False)
    txt(x,y+40,f'第{rank}名' if rank else '缺失',20)
txt((w+180)/2,37,'华南理工大学五山校区｜AHP综合排名热力图',32,halo=False)
bx,by,bh=w+42,180,h-220
for j in range(bh):d.line((bx,by+j,bx+32,by+j),fill=color(1+j/(bh-1)*(hi-1)))
d.rectangle((bx,by,bx+32,by+bh),outline='#475569',width=2)
txt(bx+16,by-35,'综合排名',20,halo=False)
for r in range(1,hi+1):
    if r==1 or r==hi or r%2==0:txt(bx+64,by+(r-1)/(hi-1)*bh,str(r),19,halo=False)
im.save(out/'05_华工AHP综合排名热力图_截图底图.png',dpi=(300,300))
print('截图尺寸',w,h,'节点数',len(rows),'有效排名',len(valid),'输出',out)
