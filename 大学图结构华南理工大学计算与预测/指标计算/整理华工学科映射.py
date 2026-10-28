"""构建可追溯的华工楼栋学科资料及独立支持数据，不修改 MIT 文件。"""
import csv, hashlib, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = HERE.parent/'学科原始数据'
SUPPORT = ROOT/'大学图结构全学科构建及映射关系'/'华南理工大学'/'支持数据'
INPUT = Path('D:/用户/Downloads/华工五山拓扑-2026-10-13 (1).json')

# 研究者整理的事实摘要（非逐字引文）；事实与楼栋学科外推分别记录。
SOURCES = [
 ('S01','物理与光电学院简介','https://www2.scut.edu.cn/physics/_t1132/13944/list.psp','学院在18号楼；设置物理学和物理电子学相关学位点以及应用物理、光电信息专业。'),
 ('S02','2021博士招生材料接收地址','https://yz.scut.edu.cn/_upload/article/files/c3/9b/d6e5cfa64825afc2aedaa58610cd/2bb67b9e-f585-44c1-992a-a10ec8c3287f.pdf','历史地址表列出材料学院麟鸿楼、化工学院逸夫工程馆、食品学院13号楼、轻工学院造纸A楼、物理学院18号楼。'),
 ('S03','工商管理全英班白皮书（2022）','https://cnsba.scut.edu.cn/2022/0907/c24722a479233/page.htm','历史资料称汕头校友楼为学院办公楼，12号与22号楼为教学楼；不证明2026年整栋使用不变。'),
 ('S04','工商管理学院学科建设调研','https://news.scut.edu.cn/2023/1218/c42a48125/page.htm','学院建设管理科学与工程、工商管理两个一级学科。'),
 ('S05','历史院系主页','https://www.scut.edu.cn/faculty/faculty.html','旧版机构表列有高分子研究所、材料科学与工程研究中心、生物科学与工程研究中心；有助于解释底图旧机构名，不作现时整栋名册。'),
 ('S06','高分子化学报告（2026）','https://www.scut.edu.cn/new/2026/0417/c235a59762/page.htm','材料学院在25号楼唯美楼举办高分子精准合成主题报告；支持楼号和研究活动，不能推出全部入驻单位。'),
 ('S07','化学与化工学院本科介绍','https://www2.scut.edu.cn/_upload/article/files/4f/a9/be4e5c3c420fac1b7dd1f816e63f/7bc5fd5d-58fb-4342-8d36-68ca72192616.pdf','该学院有化学、化学工程与技术学科，介绍化学、应用化学和化学工程相关培养。'),
 ('S08','材料学院研究生专业目录','https://yz.scut.edu.cn/_upload/article/files/82/da/2a3dde3e486da150a8d303ad0141/91951345-e152-4d7d-82aa-02e3adf6f0e1.pdf','目录列化学（高分子化学与物理）、材料科学与工程，以及光电、无机非金属、金属、电子材料与器件等研究方向。'),
 ('S09','造纸楼学术活动（2025）','https://www.scut.edu.cn/new/2025/1118/c235a58614/page.htm','轻工学院与先进造纸与纸基材料实验室在造纸楼开展生物质材料研究活动。'),
 ('S10','轻工学院植物资源化学团队','https://news.scut.edu.cn/2018/1221/c73a39165/page.htm','轻工学院植物资源化学团队开展生物质结构、分离转化及生物基材料研究。'),
 ('S11','14号楼材料学院报告（2026）','https://www.scut.edu.cn/new/2026/0915/c235a60537/page.htm','材料学院在14号楼205会议室举办水泥混凝土材料报告。'),
 ('S12','14号楼电子材料导师资料','https://www2.scut.edu.cn/_upload/article/files/a2/37/538a38064747bb761251d8be4948/d14005c2-7c70-47e1-a444-76e4f4aa148a.pdf','导师资料给出14号楼312及电子材料、微电子和固体电子学研究方向。'),
 ('S13','16号楼化工学院报告（2026）','https://www.scut.edu.cn/new/2026/0604/c235a60103/page.htm','学校通知将16号楼214表述为化学与化工学院会议室。'),
 ('S14','光电楼实验室简报','https://www2.scut.edu.cn/_upload/article/files/f3/2e/8685329448caad4208f0c5111486/0dbf11b8-3636-4708-b69c-5e2d1814c8d9.pdf','发光材料与器件实验室简报记录光电楼211活动及铁电器件等主题，支持光电楼存在相关研究活动。'),
 ('S15','华工OLED研究','https://news.scut.edu.cn/2017/0623/c73a35212/page.htm','学校报道发光器件项目贯通合成化学、材料、器件与物理；该信息是团队研究范围，不是逐楼人员分布。'),
 ('S16','食品校友楼历史','https://news.scut.edu.cn/2023/0120/c161a46289/page.htm','校方报道食品校友楼筹建历史；未给出当前全部房间或单位分布。'),
 ('S17','UNESCO ISCED-F详细领域说明','https://www.uis.unesco.org/sites/default/files/medias/fichiers/2025/04/international-standard-classification-of-education-fields-of-education-and-training-2013-detailed-field-descriptions-2015-en.pdf','领域分类参照；光学属于0533物理学。工程电子方向可归0714；跨国学科名称对应仍需研究编码约定。'),
]

# 学科到项目统一领域的编码，材料和生物工程沿用现有 MIT 同名标签对应。
DISCIPLINES = {
 '物理学':['0533'],'物理电子学':['0714'], '食品科学与工程':['0721'],
 '工商管理':['0413'],'管理科学与工程':['0413'],
 '生物工程':['0512','0711'],'材料科学与工程':['0539','0722'],
 '高分子化学与物理':['0531','0533'],'高分子材料与工程':['0722'],
 '化学':['0531'],'化学工程与技术':['0711'],
 '制浆造纸工程':['0722'],'造纸装备':['0715'],
 '电子材料与器件':['0714'],'轻工技术与工程':['0711','0722']}

# 字段：节点、研究学科、来源、依据等级、局限。
PROFILES = [
 ('B01',['物理学','物理电子学'],['S01','S02'],'A','18号楼归属有官方支持；将学院两个已列领域用于楼栋，未获得面积/人数份额。原JSON光学工程标签由官方学院领域细化，不等于认定光学本身是0714。'),
 ('B02',['食品科学与工程'],['S02'],'A','13号楼食品学院地址有历史官方支持；食品专业统一映射0721，未增添所有交叉基础学科。'),
 ('B03',['工商管理','管理科学与工程'],['S04'],'B','楼栋机构由用户底图提供；官网证实学院学科，但未识别该楼组每个翼部的实际使用单位。'),
 ('B04',['生物工程'],['S05','S16'],'C','按用户填写生物工程研究中心建模；历史中心名与食品校友楼当前入驻尚缺直接对应证据，不因食品楼名改写成食品学科。'),
 ('B05',['材料科学与工程','高分子化学与物理'],['S02','S08'],'B','麟鸿楼作为材料学院地址有历史依据，学科集合从学院层面外推到楼栋，不证明所有方向都在该楼。'),
 ('B06',['高分子化学与物理','高分子材料与工程'],['S05','S06','S08'],'B','唯美楼25号有官方活动依据；按输入高分子研究所及研究方向建模，未核验每间实验室。'),
 ('B07',['化学','化学工程与技术'],['S02','S07'],'B','逸夫工程馆有化工学院地址支持，采用学院两领域情景；逐楼完整学科份额未公开。'),
 ('B28',['材料科学与工程'],['S05'],'C','用户填写材料研究中心，历史官网支持该机构名；具体楼号和全部研究方向尚未直接核实。B28不是据此认定为28号楼。'),
 ('B09',['制浆造纸工程','造纸装备'],['S09'],'C','据输入造纸技术与装备公共实验室标签推定两个领域；来源支持造纸研究背景，不是该标签楼组的直接房间名册。'),
 ('B11',['材料科学与工程','物理学','化学','电子材料与器件'],['S14','S15'],'C','光电楼与发光器件研究有活动记录；使用团队交叉领域外推，楼内各领域份额未核实；节点不与其他楼擅自合并。'),
 ('B16',['化学','化学工程与技术'],['S13','S07'],'B','16号楼作为化工学院使用空间有官方依据；应用学院领域外推，不将临近光华中心直接认定为整楼归属。'),
 ('N1',['工商管理','管理科学与工程'],['S03','S04'],'B','汕头校友楼历史上为学院办公楼；当前是否仍全部使用待核，按历史办公归属与学院领域情景计算。'),
 ('N2',['制浆造纸工程','化学工程与技术'],['S09','S10'],'B','造纸楼轻工研究活动有官方支持；用造纸和化工工艺构成研究情景，不按讲座嘉宾所有学科扩展。'),
 ('N3',['材料科学与工程','电子材料与器件'],['S11','S12'],'B','14号楼材料学院活动与电子材料办公地址有官方依据；具体入驻领域完整性与份额仍按建模假设。'),
 ('N4',['轻工技术与工程'],['S09','S10'],'C','用户将学院名称作为节点，未明确对应楼号；不改变已确认拓扑，只按学院代表领域构建机构情景。'),
]

def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def csvwrite(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    RAW.mkdir(parents=True,exist_ok=True); SUPPORT.mkdir(parents=True,exist_ok=True)
    input_path = INPUT if INPUT.is_file() else RAW/'用户确认拓扑_原始.json'
    contents=input_path.read_bytes(); raw=json.loads(contents.decode('utf-8-sig'))
    (RAW/'用户确认拓扑_原始.json').write_bytes(contents)
    source_rows=[dict(来源编号=i,标题=t,URL=u,核查日期='2026-10-19',事实摘要=s) for i,t,u,s in SOURCES]
    dump(RAW/'官方资料来源与事实摘要.json',source_rows)
    csvwrite(RAW/'官方资料来源索引.csv',source_rows)
    nodes={str(n['id']):n for n in raw['nodes']}
    if set(nodes)!={r[0] for r in PROFILES}:raise ValueError('当前整理资料与输入节点不匹配，请补充 PROFILES')
    with (ROOT/'大学图结构全学科构建及映射关系'/'支持数据'/'学科距离矩阵.csv').open(encoding='utf-8-sig',newline='') as f:
        code_names={r['field_code']:r['field_name_zh'] for r in csv.DictReader(f)}
    profiles=[]; audit=[]; long_rows=[]
    for v,labels,sources,grade,limitations in PROFILES:
        counts={}
        for label in labels:
            codes=DISCIPLINES[label]
            for code in codes:
                if code not in code_names: raise ValueError(code)
                counts[code]=counts.get(code,0)+1/len(labels)/len(codes)
                long_rows.append({'节点ID':v,'楼名':nodes[v]['name'],'整理学科':label,'ISCED代码':code,
                                  '标签份额':1/len(labels),'该标签内代码份额':1/len(codes),
                                  '来源编号':';'.join(sources),'证据等级':grade,'局限':limitations})
        fields=[{'code':c,'name':code_names[c],'share':s} for c,s in sorted(counts.items())]
        profiles.append({'node':v,'name':nodes[v]['name'],'disciplines':labels,'fields':fields,
                         'evidence_grade':grade,'source_ids':sources,'limitations':limitations})
        audit.append({'节点ID':v,'楼名':nodes[v]['name'],'原始机构':nodes[v].get('colleges',''),
                      '原始学科':nodes[v].get('disciplines',''),'整理学科':';'.join(labels),
                      '领域份额':';'.join(f'{x["code"]}:{x["share"]:.8f}' for x in fields),
                      '证据等级':grade,'来源编号':';'.join(sources),'局限':limitations})
    info={'university':'华南理工大学','campus':'五山校区','stage':4,
          'stage_note':'4仅为原公式脚本的接口槽位，不是华工历史第四阶段',
          'measure':'Rao–Stirling','weight_assumption':'原始标签等份，标签内代码等份，合并重复代码后归一化；不是实测份额',
          'evidence_grades':{'A':'官方楼址与学院领域均有支持，份额仍假设','B':'官方支持部分归属，学院/团队领域到楼栋为外推','C':'输入机构/楼名及有限研究活动支持的推定情景，需核验'},
          'topology_confirmation':'用户于2026-10-19明确确认全部提交拓扑，原confirmed=false是遗留标记，不作为过滤条件',
          'input_sha256':hashlib.sha256(contents).hexdigest(),'mapped_scut_discipline_labels':DISCIPLINES,
          'nodes':profiles,'edges':raw['edges'],'sources':source_rows}
    dump(RAW/'华工楼栋学科整理记录.json',info)
    dump(SUPPORT/'学科映射.json',info)
    csvwrite(RAW/'楼栋学科原始与整理对照.csv',audit)
    csvwrite(RAW/'楼栋学科展开表.csv',long_rows)
    csvwrite(SUPPORT/'华工楼栋学科映射审计.csv',audit)
    csvwrite(SUPPORT/'华工学科标签到ISCED映射.csv',[
        {'学科标签':label,'代码':c,'代码领域':code_names[c],'标签内份额':1/len(codes)}
        for label,codes in DISCIPLINES.items() for c in codes])
    shutil.copyfile(ROOT/'大学图结构全学科构建及映射关系'/'支持数据'/'学科距离矩阵.csv',SUPPORT/'学科距离矩阵.csv')
    shutil.copyfile(HERE/'原公式代码'/'拓扑算法.py',SUPPORT/'拓扑算法.py')
    print('华工映射已保存：',SUPPORT)
    print('原始资料和审计已保存：',RAW)

if __name__=='__main__': main()
