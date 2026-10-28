"""读取新版01—04指标表，按等权分层AHP评价；仅依赖Python标准库。"""
import argparse,csv,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,rs):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=HERE.parent/'大学图结构四指标体系'/'第4阶段输出')
    p.add_argument('--out',type=Path,default=HERE/'评价输出')
    a=p.parse_args()
    specs=[('01_接近中心性.csv','接近中心性_WF'),('02_中介中心性.csv','中介中心性_标准化'),
           ('03_学科数量加权RS.csv','数量加权RS_N乘RS'),('04_信息传播新增覆盖.csv','传播新增覆盖')]
    tables=[read(a.input/name) for name,k in specs]
    maps=[]
    for table in tables:
        m={r['楼号']:r for r in table}
        if len(m)!=len(table):raise ValueError('楼号重复')
        maps.append(m)
    ids=list(maps[0])
    if any(set(m)!=set(ids) for m in maps):raise ValueError('四表楼号集合不一致')
    if any(m[v]['阶段']!=maps[0][v]['阶段'] for m in maps for v in ids):raise ValueError('四表阶段不一致')
    vals={v:[float(m[v][k]) if m[v][k].strip() else None for m,(_,k) in zip(maps,specs)] for v in ids}
    valid=[v for v in ids if all(x is not None for x in vals[v])]
    if len(valid)<2:raise ValueError('完整数据不足2个节点')
    bounds=[(min(vals[v][i] for v in valid),max(vals[v][i] for v in valid)) for i in range(4)]
    if any(hi==lo for lo,hi in bounds):raise ValueError('存在常量指标，不能极差标准化')
    rows=[]
    for v in ids:
        z=[(x-lo)/(hi-lo) for x,(lo,hi) in zip(vals[v],bounds)] if v in valid else None
        row={'阶段':maps[0][v]['阶段'],'楼号':v,'楼名':maps[0][v]['楼名']}
        for i,(_,k) in enumerate(specs):row[k]=vals[v][i] if vals[v][i] is not None else '';row[k+'_标准化']=z[i] if z else ''
        row.update({'拓扑结构潜力':(z[0]+z[1])/2 if z else '', '理论创新潜力':(z[2]+z[3])/2 if z else '',
            'AHP综合得分':sum(z)/4 if z else '', '只保留接近中心性得分':z[0]/2+(z[2]+z[3])/4 if z else '',
            '只保留中介中心性得分':z[1]/2+(z[2]+z[3])/4 if z else '', '状态':'有效' if z else '指标缺失，暂不评分'})
        rows.append(row)
    for score,rank in [('AHP综合得分','综合排名'),('只保留接近中心性得分','仅接近中心性排名'),('只保留中介中心性得分','仅中介中心性排名')]:
        for r in rows:r[rank]=1+sum(t[score]>r[score]+1e-12 for t in rows if t['状态']=='有效') if r['状态']=='有效' else ''
    rows.sort(key=lambda r:r['综合排名'] if r['综合排名']!='' else 999999)
    a.out.mkdir(parents=True,exist_ok=True)
    save(a.out/'01_AHP综合得分与排名.csv',rows)
    save(a.out/'02_AHP权重.csv',[{'指标':k,'准则层':'拓扑结构潜力' if i<2 else '理论创新潜力','准则层权重':.5,'层内权重':.5,'最终权重':.25} for i,(_,k) in enumerate(specs)])
    save(a.out/'03_标准化参照.csv',[{'指标':k,'最小值':lo,'最大值':hi,'有效样本数':len(valid)} for (_,k),(lo,hi) in zip(specs,bounds)])
    save(a.out/'04_中心性敏感性排名.csv',[{k:r[k] for k in ['楼号','楼名','综合排名','仅接近中心性排名','仅中介中心性排名']} for r in rows])
    (a.out/'计算说明.md').write_text('# 新版四指标AHP\n\n第三指标为学科数量×RS，不能与旧版RS评分直接比较。用户指定三个2×2判断矩阵全为1：准则层各50%，层内各50%，最终各25%。2×2矩阵天然一致，CI=0，CR不适用。\n\n四项指标在共同完整样本中做极差标准化；缺失留空，不填0；分数用于本次图结构内排序，不代表实证验证的创新能力。敏感性分析保持两个准则层各50%，分别仅保留接近或中介中心性代表拓扑。\n',encoding='utf-8')
    print(f'完成：{len(ids)}节点，{len(valid)}节点有效评分；输出：{a.out}')
    for r in rows[:5]:print(r['楼号'],r['AHP综合得分'])
if __name__=='__main__':main()
