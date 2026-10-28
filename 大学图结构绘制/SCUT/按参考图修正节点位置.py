"""按用户2026-10-22提供的编辑器截图同步15个节点的位置。"""
import json,re,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
# 参考截图上的圆心；底图可见区域左上角(3,7)，宽1071像素。
centers={'B01':(431,105),'B02':(931,72),'B03':(571,178),
 'B04':(836,169),'B05':(908,238),'B06':(391,357),'B07':(343,454),
 'B09':(588,541),'B11':(809,435),'B16':(178,717),'B28':(265,560),
 'N1':(530,250),'N2':(583,409),'N3':(926,325),'N4':(702,330)}
path=HERE/'华工五山_已确认拓扑.json'
graph=json.loads(path.read_text(encoding='utf-8-sig'))
for name in ['华工五山_已确认拓扑.json','data.js','app.js']:
    backup=HERE/(name+'.位置修正前.bak')
    if not backup.exists():shutil.copyfile(HERE/name,backup)
assert set(centers)=={n['id'] for n in graph['nodes']}
for n in graph['nodes']:
    x,y=centers[n['id']];n['x']=round((x-3)*820/1071,4);n['y']=round((y-7)*820/1071,4)
graph['coordinateRevision']='20261022-reference-2'
path.write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
path=HERE/'data.js';s=path.read_text(encoding='utf-8')
s=re.sub(r'const INITIAL = .*?;\s*(?=const REFERENCE_IMAGE)',lambda m:'const INITIAL = '+json.dumps(graph,ensure_ascii=False,indent=2)+';\n',s,count=1,flags=re.S)
path.write_text(s,encoding='utf-8')
path=HERE/'app.js';s=path.read_text(encoding='utf-8')
marker='function state()'
if '用户参考截图坐标修正' not in s:
    migration="""// 用户参考截图坐标修正：仅迁移同ID节点位置，不覆盖连线和其他属性。
if(data.coordinateRevision!==INITIAL.coordinateRevision){const referenceNodes=new Map(INITIAL.nodes.map(n=>[n.id,n]));for(const n of data.nodes){const ref=referenceNodes.get(n.id);if(ref){n.x=ref.x;n.y=ref.y}}data.coordinateRevision=INITIAL.coordinateRevision;notice='已按用户参考图修正节点位置。'}
"""
    s=s.replace(marker,migration+marker,1)
path.write_text(s,encoding='utf-8')
print('已同步15个节点位置；边和排名未改变。')
