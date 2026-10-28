"""按楼号生成案例卡、可离线查看的索引与PDF预览，原始来源文件保持不变。"""
import csv,hashlib,html,json,subprocess
from pathlib import Path
from pypdf import PdfReader
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
POP=Path('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def md(p,s):p.write_text(s,encoding='utf-8')
with (ROOT/'大学图结构AHP评价'/'评价输出'/'01_AHP综合得分与排名.csv').open(encoding='utf-8-sig',newline='') as f:
    ranking={r['楼号']:r for r in csv.DictReader(f)}
mapping=json.loads((ROOT/'大学图结构全学科构建及映射关系'/'支持数据'/'学科映射.json').read_text(encoding='utf-8-sig'))
profiles={r['node']:r for r in mapping['nodes']}
names={'16':'多兰斯楼 Dorrance Building','12':'MIT.nano / Lisa T. Su Building','13':'范内瓦·布什楼 Vannevar Bush Building','26':'康普顿实验楼 Compton Laboratories','10':'麦克劳林楼 Maclaurin Building'}
notes={
 '12':('核心案例；资料最充分','共享科研设施、实验可视性、公共走廊与展陈、庭院路径。',
   '12.pdf为2024年官方手册，元数据生成及修改日期2024-11-21；第4—5页含功能分层轴测示意，第12—13页涉及汇聚交流与STUDIO.nano。另有2022年室外导览、2021年三层局部图。均属于2018年启用的新MIT.nano，未收入旧12号楼资料。',
   '完整房间级逐层平面、可校准尺度、各房间实际用途及净面积；公开手册不能替代完整图纸。',
   '实验室核心与公共可视界面之间如何组织；共享平台如何连接多个学科；信息展陈是否与日常路径相遇。'),
 '16':('核心候选；等待完整平面','校园网络中的连接角色、跨学科学习活动与公共空间。',
   '已保存官方校园地图入口和Terrascope官方页面。后者说明跨学科课程、聚会与休息学习空间，页面地址16-177；不能据此推断整栋建筑各房间功能。公共资料中有2023年楼层连接示意。',
   '完整逐层平面、跨楼入口及楼梯位置的房间级核对、实验/办公/教学分布；当前不能计算整楼内部空间句法。',
   '外部高中心性是否转化为内部穿行；共享学习空间与交通交汇的关系。'),
 '13':('核心候选；现状完整平面未取得','入口与公共大厅、科研空间和校园通行的关系。',
   '已保存MIT官方建筑介绍；其描述首层柱廊与大厅、原拟入口角色。2023年公共连接图可辅助跨楼分析。只有2004年公开课程文件含首层建筑平面，单独放在“历史补充”，不标为现状图。',
   '新版整层及全部楼层平面、房间功能、改造记录与可校准尺度；旧图只能提出假设，不能直接支撑现状面积统计。',
   '入口大厅是否可成为可停留的交流节点；穿行交通与安静科研空间怎样分层。'),
 '26':('补充候选；等待完整平面','科研与教学活动的联系及楼群连接。',
   '已保存MIT校园地图建筑入口；公共资料中的2023年地图包含多楼层连接示意。尚未取得可公开下载的完整房间级平面。',
   '完整逐层平面、功能分配与空间尺度；不能用其它学校同为26号楼的平面代替。',
   '教学与科研交通是否重叠；跨楼连接与建筑内公共节点怎样衔接。'),
 '10':('补充候选；局部空间参照','公共活动房间与大厅/交通的联系。',
   '已保存10-105 Bush Room的2025版家具布置平面（元数据修改日期2025-02-11）。它是10号楼的一间活动房间，既不是13号楼，也不是10号楼完整首层平面。历史13/10首层图在13/历史补充中。',
   '建筑整体的新平面和房间用途；单个房间图不足以支撑整楼分析。',
   '不同活动布置对共处与交流的影响；需与建筑交通及实际使用资料结合。')}
records=json.loads((HERE/'来源与下载核验.json').read_text(encoding='utf-8'))
pdfchecks=[]
for p in HERE.rglob('*.pdf'):
    reader=PdfReader(p);texts=[page.extract_text() or '' for page in reader.pages]
    text='\n\n'.join(f'--- PDF第{i+1}页 ---\n{v}' for i,v in enumerate(texts))
    p.with_suffix('.txt').write_text(text,encoding='utf-8')
    pdfchecks.append({'文件':p.relative_to(HERE).as_posix(),'页数':len(reader.pages),'元数据':dict(reader.metadata or {}),'可提取文本页数':sum(bool(v.strip()) for v in texts)})
def render(rel,first,last,prefix):
    out=HERE/prefix;out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(POP),'-f',str(first),'-l',str(last),'-scale-to','1800','-png',str(HERE/rel),str(out)],check=True,capture_output=True)
render('12/12.pdf',4,5,'12/预览/12_官方手册')
render('12/12.pdf',12,13,'12/预览/12_共享交流')
render('公共资料/12_13_16_26_楼层连接示意.pdf',2,2,'公共资料/12_13_16_26_连接示意')
wrong=HERE/'13/历史补充/13_10_首层平面_2004-4.png'
correct=HERE/'13/历史补充/13_10_研究说明_2004-4.png'
if wrong.exists() and not correct.exists():wrong.rename(correct)
render('13/历史补充/13_10_首层平面来源_2004.pdf',5,5,'13/历史补充/13_10_首层平面_2004')
render('10/10_105房间平面_2025.pdf',1,1,'10/10_105房间平面_2025')
selected=[]
for no in ['16','12','13','26','10']:
    row=dict(ranking[no]);original=row['楼名'];row['楼名']=names[no]
    row['原始结果名称']=original;row['命名说明']='用户已明确确认12号节点采用新MIT.nano学科标签；本案例库统一新楼名称，得分保持原值。' if no=='12' else ''
    selected.append(row);folder=HERE/no;folder.mkdir(exist_ok=True)
    p=dict(profiles['12-old' if no=='12' else no]);p['source_node_key']=p['node'];p['node']=no;p['building_name']=names[no]
    p['identity_note']=row['命名说明'];dump(folder/(no+'.json'),{'AHP':row,'学科映射快照':p})
    status,focus,have,missing,questions=notes[no]
    links=[]
    for r in records:
        if r['文件'].startswith(no+'/'):
            local=f"[{r['文件'].split('/')[-1]}]({r['文件'][len(no)+1:]})" if r['状态']=='已下载' else r['文件'].split('/')[-1]+'（未保存文件）'
            links.append(f"- {local}：{r['说明']}；年份：{r['资料年份']}；{r['状态']}。来源：[原页面]({r['来源']})")
    if no=='12':links.append('- [三层局部图来源说明](https://mitnano.mit.edu/facility-updates/reduced-hours-nanomat-solar-frontiers-space)：发布于2021-03-25；图中施工限制仅为当时信息。')
    md(folder/(no+'.md'),f'# {no}号楼｜{names[no]}\n\nAHP排名：{row["综合排名"]}；得分：{float(row["AHP综合得分"]):.9f}。状态：{status}。\n\n## 已有资料\n\n{have}\n\n'+ '\n'.join(links)+f'\n\n## 案例研究重点\n\n{focus}\n\n待检验的问题：{questions}\n\n## 尚缺资料\n\n{missing}\n\n## 使用边界\n\nAHP为既有校园节点模型结果，不能直接证明内部平面更优。图纸上传时间、建筑竣工时间和图纸修订时间分别记录；未说明日期的网页不标为2026版图纸。公开文件须保留来源署名。\n\n[返回总览](../案例总览.html)\n')
dump(HERE/'12_13_16_26_10_AHP案例快照.json',selected)
main='# MIT AHP优选案例资料库\n\n整理日期：2026-10-22。按楼号建立目录；12号楼明确为新MIT.nano。\n\n'
main+='|楼号|AHP排名|得分|资料状态|\n|---|---:|---:|---|\n'
for r in selected:
    no=r['楼号'];main+=f"|[{no}]({no}/{no}.md)|{r['综合排名']}|{float(r['AHP综合得分']):.6f}|{notes[no][0]}|\n"
main+='\n先打开[案例总览.html](案例总览.html)。12/12.pdf是2024版MIT.nano官方手册；各楼号.md说明已有资料与缺口，各楼号.json保留AHP和学科映射快照。\n\n'
main+='新版优先：已使用2024手册、2025房间局部图和2023官方楼层连接图。13号楼未找到新版公开完整平面，故将2004年13/10首层图单独存入历史补充，不能作为现状依据。无旧12号楼图纸。\n\n'
main+='完整性：尚未取得这五栋建筑的现状完整逐层房间级平面。16、13、26暂为候选资料卡，12有较充分功能与局部空间资料；10仅有2025单房间图。无障碍图是交通连接示意，不能用来统计房间面积。\n\n'
main+='完整图纸官方入口：https://floorplans.mit.edu/ ，MIT官方说明其面向校内社区。公开获取不到的资料保留缺口，不伪造或以旧楼替代。\n\n'
main+='原项目未改动：12-old仅在本案例库记录为历史键名，案例身份统一为新MIT.nano；原始AHP表、计算脚本和评分未修改。下载记录包含来源URL、文件年份、SHA256；下载失败的HGA项目页及RLE页面保留链接，不生成假文件。\n'
md(HERE/'使用说明.md',main)
cards=[]
for r in selected:
    no=r['楼号'];files=[]
    for p in sorted((HERE/no).rglob('*')):
        if p.is_file() and p.suffix in ['.pdf','.png','.html','.md','.json']:
            rel=p.relative_to(HERE).as_posix();files.append(f'<li><a href="{html.escape(rel)}">{html.escape(p.name)}</a></li>')
    preview=''
    if no=='12':preview='<img src="12/预览/12_官方手册-05.png" alt="12号楼官方手册功能分层示意">'
    if no=='10':preview='<img src="10/10_105房间平面_2025-1.png" alt="10-105房间局部平面">'
    status,focus,have,missing,_=notes[no]
    cards.append(f'<section><h2>{no}号楼 · {html.escape(names[no])}</h2><p class="rank">AHP第{r["综合排名"]}名 · {float(r["AHP综合得分"]):.6f}</p><p><b>{status}</b></p><p>{have}</p>{preview}<p><b>研究重点：</b>{focus}</p><p class="gap"><b>待补：</b>{missing}</p><details><summary>本地文件</summary><ul>{"".join(files)}</ul></details></section>')
sources=''.join(f'<tr><td>{html.escape(r["文件"])}</td><td>{html.escape(r["资料年份"])}</td><td>{html.escape(r["状态"])}</td><td><a href="{html.escape(r["来源"])}">来源</a></td></tr>' for r in records)
doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>MIT AHP优选案例</title><style>body{margin:0;background:#f1f5f9;color:#172033;font-family:"Microsoft YaHei",sans-serif;line-height:1.7}header,main,footer{max-width:1280px;margin:auto;padding:28px}h1{margin:0;font-size:32px}h2{font-size:23px}header p{max-width:1000px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:22px}section{background:white;padding:25px;border-radius:12px;border-top:5px solid #0f766e}section img{width:100%;max-height:520px;object-fit:contain;background:white}.rank{color:#0f766e;font-weight:bold}.gap{background:#fff7ed;padding:12px}a{color:#0369a1}table{border-collapse:collapse;background:white;width:100%;font-size:14px}td,th{padding:10px;border:1px solid #cbd5e1;text-align:left}summary{cursor:pointer}footer{font-size:14px}</style>'''
doc+='<header><h1>MIT AHP优选案例</h1><p>16 / 12 / 13 为核心候选，26 / 10 为补充。12号楼统一为新MIT.nano。资料按楼号命名，优先新版；完整逐层平面尚未取得。</p><p>2024官方手册、2025局部房间图、2023楼层连接示意已保存。历史13/10平面隔离留档。AHP用于案例筛选，内部空间质量仍需另行分析。</p></header><main><div class="grid">'+''.join(cards)+'</div><h2>共同参考：官方楼层连接示意</h2><p>2023年版本，第2页；仅显示连接与无障碍交通，不是房间级平面。</p><p><a href="公共资料/12_13_16_26_楼层连接示意.pdf">打开原PDF</a></p><img style="width:100%" src="公共资料/12_13_16_26_连接示意-2.png" alt="官方多楼层交通连接示意"><h2>来源与版本记录</h2><table><tr><th>文件</th><th>资料年份</th><th>状态</th><th>来源</th></tr>'+sources+'</table></main><footer>整理日期：2026-10-22。原始项目文件未修改。完整官方图纸入口 floorplans.mit.edu 需要MIT社区访问权限。所有来源文件保留原始内容。</footer></html>'
(HERE/'案例总览.html').write_text(doc,encoding='utf-8')
checks=[]
for r in records:
    if r['状态']=='已下载':
        p=HERE/r['文件'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['SHA256'];checks.append(r['文件'])
dump(HERE/'文件核验记录.json',{'原始下载文件完整性通过':len(checks),'PDF核验':pdfchecks,'12号身份':'新MIT.nano；用户明确确认','未取得完整逐层平面':['12','13','16','26','10']})
print('PDFs',len(pdfchecks),'sources',len(checks),'index ready')
