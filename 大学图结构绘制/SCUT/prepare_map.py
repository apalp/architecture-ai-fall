"""Extract numbered buildings and their drawn footprints from the source map."""
import json, base64
from pathlib import Path
import pdfplumber
ROOT = Path(__file__).parent
def inside(x, y, poly):
    result = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result
with pdfplumber.open(ROOT/'wushan-source.pdf') as pdf:
    p = pdf.pages[0]
    footprints = [c for c in p.curves if c.get('fill') and tuple(c.get('non_stroking_color') or ()) == (0.0, 0.2, 0.6, 0.2)]
    words = p.extract_words()
    nodes = []
    for number in list(range(1,35)) + [38,39]:
        candidates = [w for w in words if w['text'] == str(number) or (number == 20 and w['text'].startswith('20'))]
        # Numbered teaching/research buildings: exclude north/east/west dormitory numbers.
        if not candidates:
            continue
        matches = []
        for w in candidates:
            x, y = (w['x0']+w['x1'])/2, (w['top']+w['bottom'])/2
            matches = [c for c in footprints if inside(x,y,c['pts'])]
            if matches:
                break
        if not matches:
            print('No footprint:',number)
            continue
        shape = min(matches,key=lambda c:c['width']*c['height'])
        points = [[round(px*2,2),round(py*2,2)] for px,py in shape['pts']]
        nodes.append(dict(id=str(number),label=f'{number}号楼',x=round(x*2,2),y=round(y*2,2),size=15,color='#932b36',category='编号楼栋',notes='楼号及轮廓提取自参考平面图，需现场核验。',footprint=points))
    result = dict(version=2,title='五山校区 · 楼栋接触图',campus='五山校区',edgeRule='footprint-contact',tolerance=0.5,map=dict(width=1665,height=2363,source='https://www.gdinsa.org/uploadfile/2023/0425/20230425015253632.pdf',credit='©ChienchouSu · 参考平面图（非测绘数据）'),nodes=nodes,edges=[])
    (ROOT/'map-data.js').write_text('window.WUSHAN_DATA = '+json.dumps(result,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    with (ROOT/'map-data.js').open('a',encoding='utf-8') as out:
        out.write('window.WUSHAN_MAP = "data:image/png;base64,'+base64.b64encode((ROOT/'wushan-map.png').read_bytes()).decode()+'";\n')
    print('Extracted',len(nodes),'numbered buildings')
