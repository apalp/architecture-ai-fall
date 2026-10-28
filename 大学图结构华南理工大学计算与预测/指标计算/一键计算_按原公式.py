"""直接调用项目原四指标/AHP脚本副本，计算已由用户确认的华工拓扑。"""
import argparse,csv,hashlib,json,subprocess,sys
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RAW=HERE.parent/'学科原始数据'
SUPPORT=ROOT/'大学图结构全学科构建及映射关系'/'华南理工大学'/'支持数据'

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--json',type=Path,default=RAW/'用户确认拓扑_原始.json')
    p.add_argument('--support',type=Path,default=SUPPORT)
    p.add_argument('--out',type=Path,default=HERE/'正式输出')
    p.add_argument('--runs',type=int,default=20000)
    p.add_argument('--seed',type=int,default=20261017)
    p.add_argument('--beta',type=float,default=.5)
    p.add_argument('--kappa',type=float,default=2.)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    raw=json.loads(a.json.read_text(encoding='utf-8-sig'))
    ids=[str(n['id']) for n in raw['nodes']]
    if len(ids)!=len(set(ids)) or not ids:raise ValueError('节点为空或重复')
    seen=set()
    for e in raw['edges']:
        pair=tuple(sorted((str(e['a']),str(e['b']))))
        if pair[0]==pair[1] or not set(pair)<=set(ids) or pair in seen:raise ValueError(f'无效或重复边 {pair}')
        seen.add(pair)
    # 原脚本接口只接收 stages[3]。前三个槽位为空；不是编造历史阶段。
    adapted={'schema':'scut-confirmed-adapter','stages':[None,None,None,{
        'name':'华工用户确认拓扑','nodes':raw['nodes'],'edges':[{'a':e['a'],'b':e['b']} for e in raw['edges']]}],
        '说明':'用户2026-10-19确认提交的全部边，忽略遗留confirmed布尔值；4为脚本槽位，不是历史阶段'}
    adapted_path=a.out/'原脚本适配输入.json'
    adapted_path.write_text(json.dumps(adapted,ensure_ascii=False,indent=2),encoding='utf-8')
    source_dir=HERE/'原公式代码';logs=[]
    commands=[
        [sys.executable,str(source_dir/'计算四指标.py'),str(adapted_path),'--support',str(a.support),'--stage','4','--runs',str(a.runs),'--seed',str(a.seed),'--beta',str(a.beta),'--kappa',str(a.kappa),'--out',str(a.out/'四指标')],
        [sys.executable,str(source_dir/'计算AHP评价.py'),'--input',str(a.out/'四指标'),'--out',str(a.out/'AHP评价')]]
    for cmd in commands:
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'})
        logs.append({'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
        print(run.stdout)
        (a.out/'原脚本调用日志.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
        if run.returncode:raise SystemExit(f'原脚本运行失败：{run.stderr}')
    profiles=json.loads((a.support/'学科映射.json').read_text(encoding='utf-8-sig'))
    profiles_by_id={str(n['node']):n for n in profiles['nodes']}
    mapping_audit={r['节点ID']:r for r in read(a.support/'华工楼栋学科映射审计.csv')}
    ranked=read(a.out/'AHP评价'/'01_AHP综合得分与排名.csv')
    merged=[]
    for r in ranked:
        v=r['楼号'];m=mapping_audit[v]
        merged.append({'节点ID':v,'楼名':r['楼名'],'计算对象':'用户已确认的五山拓扑',
                       **{k:x for k,x in r.items() if k not in ['阶段','楼号','楼名']},
                       '映射证据等级':m['证据等级'],'整理学科':m['整理学科'],'领域份额':m['领域份额'],
                       '映射来源':m['来源编号'],'映射局限':m['局限']})
    write(a.out/'华工四指标与AHP总表.csv',merged)
    (a.out/'华工四指标与AHP总表.json').write_text(json.dumps(merged,ensure_ascii=False,indent=2),encoding='utf-8')
    prob=[];matrix_rows=read(a.support/'学科距离矩阵.csv');matrix={r['field_code']:r for r in matrix_rows}
    import math
    for edge in raw['edges']:
        v,w=str(edge['a']),str(edge['b']);fa=profiles_by_id.get(v,{}).get('fields',[]);fb=profiles_by_id.get(w,{}).get('fields',[])
        value=a.beta*sum(float(x['share'])*float(y['share'])*math.exp(-a.kappa*float(matrix[x['code']][y['code']])) for x in fa for y in fb)
        prob.append({'起点':v,'终点':w,'传播概率':value,'拓扑状态':'用户已确认','原遗留confirmed':edge.get('confirmed',''),'用于计算':True})
    if prob:write(a.out/'边传播概率与拓扑确认.csv',prob)
    original_paths={
        '计算四指标.py':ROOT/'大学图结构四指标体系'/'计算四指标.py',
        '计算AHP评价.py':ROOT/'大学图结构AHP评价'/'计算AHP评价.py',
        '拓扑算法.py':ROOT/'大学图结构全学科构建及映射关系'/'支持数据'/'拓扑算法.py'}
    matches={name:{'副本SHA256':sha(source_dir/name),'指定原脚本SHA256':sha(path),
                   '内容完全一致':(source_dir/name).read_bytes()==path.read_bytes()} for name,path in original_paths.items()}
    if not all(x['内容完全一致'] for x in matches.values()):raise ValueError('公式副本与指定原脚本不一致')
    counts={g:sum(n['evidence_grade']==g for n in profiles['nodes']) for g in ['A','B','C']}
    manifest={'时间':datetime.now().astimezone().isoformat(),'输入路径':str(a.json.resolve()),'输入SHA256':sha(a.json),
        '学科映射路径':str((a.support/'学科映射.json').resolve()),'学科映射SHA256':sha(a.support/'学科映射.json'),
        '学科距离矩阵SHA256':sha(a.support/'学科距离矩阵.csv'),'原公式核验':matches,
        '节点数':len(ids),'边数':len(seen),'评分节点数':sum(r['状态']=='有效' for r in ranked),
        '映射证据等级计数':counts,'参数':{'runs':a.runs,'seed':a.seed,'beta':a.beta,'kappa':a.kappa},
        '拓扑确认':'用户明确确认全部15节点8边，confirmed=false不用于过滤',
        '阶段说明':'原表阶段4为软件槽位，不是华工历史阶段','常量指标处理':'严格沿用指定AHP脚本：有常量时报错，不自行改规则',
        '权重':'两个准则层各0.5，层内各0.5，最终四项各0.25','前五':[{k:r[k] for k in ['楼号','楼名','AHP综合得分','综合排名']} for r in ranked[:5]]}
    (a.out/'正式运行记录.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    report=['# 华工五山拓扑四指标与 AHP 正式结果','',
        f'按用户确认的 {len(ids)} 个节点、{len(seen)} 条无向边计算。全部拓扑边有效，原 JSON 中遗留 confirmed=false 不作过滤。',
        f'本次 {manifest["评分节点数"]} 个节点有四指标及综合得分；学科份额为等份模型，不是楼内人数或面积实测。',
        '','直接调用用户指定脚本的逐字节一致副本。四指标为 WF 修正接近中心性、标准化中介中心性、K×RS 和信息传播新增覆盖；AHP 四项各25%，在共同完整样本内极差标准化。',
        '','## 综合排名','', '|排名|节点|楼名|AHP得分|','|---:|---|---|---:|']
    for r in ranked:report.append(f'|{r["综合排名"]}|{r["楼号"]}|{r["楼名"]}|{float(r["AHP综合得分"]):.6f}|' if r['AHP综合得分'] else f'|—|{r["楼号"]}|{r["楼名"]}|缺失|')
    report+=['','## 解释边界','',
        '拓扑已确认；学科到建筑的映射仍是不同证据强度的研究情景，不能把拓扑确认等同于全部入驻学科、分布与份额也已核验。',
        f'证据等级 A/B/C 的节点数分别为 {counts["A"]}/{counts["B"]}/{counts["C"]}。A级也没有实测学科份额；B级包含学院/团队到楼栋外推；C级主要依赖输入标签和有限背景材料。',
        '所有学科名称、来源、领域编码及逐节点局限见“学科原始数据”以及总表后几列。研究学科数 K 是统一四位领域去重数量，不是中文学科标签数。',
        '学科距离矩阵与 MIT 计算共用项目149领域矩阵，未重新拟合。分数按本次图结构自身标准化，不能直接据此与 MIT 的独立标准化分数作绝对高低比较。',
        '传播模型参数与原脚本一致；其蒙特卡洛标准误仅反映模拟抽样，不涵盖映射和模型不确定性。',
        '原表中“阶段=4”仅为原脚本读取接口；没有重建华工四个历史阶段。',
        '此前只有3节点的探索性评分以及0边情景已移入“初次探索_已停用”，不作为正式结论。']
    (a.out/'结果摘要.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    # 更正原AHP脚本写出的通用说明中不适用的“缺失”及历史措辞，保留其原内容供追溯。
    copied_note=a.out/'AHP评价'/'计算说明.md'
    copied_note.write_text(copied_note.read_text(encoding='utf-8')+'\n本次调用对象为华南理工大学用户确认拓扑；学科来自新整理的华工映射，非MIT映射。所有同等权重为沿用项目设定，非声称本次重新进行了专家打分。阶段4仅为接口槽位。\n',encoding='utf-8')
    print('正式输出：',a.out)

if __name__=='__main__':main()
