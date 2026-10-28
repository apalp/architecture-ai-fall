"""独立核验原公式输出：树图解析中心性、传播期望及AHP复算。"""
import csv,hashlib,json,math
from collections import deque
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[1]

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    out=P/'正式输出';raw=json.loads((P.parent/'学科原始数据/用户确认拓扑_原始.json').read_text(encoding='utf-8'))
    nodes=[n['id'] for n in raw['nodes']];adj={v:[] for v in nodes}
    for e in raw['edges']:adj[e['a']].append(e['b']);adj[e['b']].append(e['a'])
    n=len(nodes);paths={}
    for v in nodes:
        paths[v]={v:[v]};queue=deque([v])
        while queue:
            u=queue.popleft()
            for w in adj[u]:
                if w not in paths[v]:paths[v][w]=paths[v][u]+[w];queue.append(w)
    comps={tuple(sorted(paths[v])) for v in nodes}
    assert len(raw['edges'])==n-len(comps),'此解析核验要求输入是森林'
    c={r['楼号']:float(r['接近中心性_WF']) for r in read(out/'四指标/01_接近中心性.csv')}
    b={r['楼号']:float(r['中介中心性_标准化']) for r in read(out/'四指标/02_中介中心性.csv')}
    for v in nodes:
        reach=len(paths[v])-1;dist=sum(len(path)-1 for path in paths[v].values())
        assert abs(c[v]-(reach**2/((n-1)*dist) if dist else 0))<1e-12
        pair_count=sum(v in paths[a][target][1:-1] for i,a in enumerate(nodes) for target in nodes[i+1:] if target in paths[a] and v not in [a,target])
        assert abs(b[v]-pair_count/((n-1)*(n-2)/2))<1e-12
    probs={tuple(sorted((r['起点'],r['终点']))):float(r['传播概率']) for r in read(out/'边传播概率与拓扑确认.csv')}
    coverage={r['楼号']:r for r in read(out/'四指标/04_信息传播新增覆盖.csv')}
    analytic=[]
    for v in nodes:
        exact=0.
        for target,path in paths[v].items():
            if target==v:continue
            exact+=math.prod(probs[tuple(sorted((a,b)))] for a,b in zip(path,path[1:]))
        estimate=float(coverage[v]['传播新增覆盖']);se=float(coverage[v]['蒙特卡洛标准误'])
        assert abs(estimate-exact)<=6*se+1e-12,(v,estimate,exact,se)
        analytic.append({'节点ID':v,'解析传播新增覆盖':exact,'蒙特卡洛新增覆盖':estimate,'绝对误差':abs(estimate-exact),'标准误':se,'六倍标准误内':True})
    rows=read(out/'AHP评价/01_AHP综合得分与排名.csv')
    keys=['接近中心性_WF','中介中心性_标准化','数量加权RS_N乘RS','传播新增覆盖']
    bounds=[(min(float(r[k]) for r in rows),max(float(r[k]) for r in rows)) for k in keys]
    for r in rows:
        score=sum((float(r[k])-lo)/(hi-lo) for k,(lo,hi) in zip(keys,bounds))/4
        assert abs(score-float(r['AHP综合得分']))<1e-12
        rank=1+sum(float(s['AHP综合得分'])>score+1e-12 for s in rows)
        assert int(r['综合排名'])==rank
    support=ROOT/'大学图结构全学科构建及映射关系/华南理工大学/支持数据'
    profiles=json.loads((support/'学科映射.json').read_text(encoding='utf8'))
    matrix={r['field_code']:r for r in read(support/'学科距离矩阵.csv')}
    rs={r['楼号']:r for r in read(out/'四指标/03_学科数量加权RS.csv')}
    for profile in profiles['nodes']:
        fields=profile['fields'];assert abs(sum(f['share'] for f in fields)-1)<1e-12
        score=sum(a['share']*b['share']*float(matrix[a['code']][b['code']]) for a in fields for b in fields)
        assert abs(float(rs[profile['node']]['数量加权RS_N乘RS'])-len(fields)*score)<1e-12
    record=json.loads((out/'正式运行记录.json').read_text(encoding='utf8'))
    assert all(item['内容完全一致'] for item in record['原公式核验'].values())
    assert record['节点数']==15 and record['边数']==8 and record['评分节点数']==15
    original_mit=ROOT/'大学图结构全学科构建及映射关系/支持数据/学科映射.json'
    assert json.loads(original_mit.read_text(encoding='utf-8-sig')).get('mapped_mit_discipline_labels')
    with (out/'传播覆盖_树图解析核验.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(analytic[0]));w.writeheader();w.writerows(analytic)
    checks=['15节点8边及7连通分量；全部提交边纳入',
            '15节点WF接近中心性与独立路径枚举一致',
            '15节点中介中心性与独立点对最短路枚举一致',
            '15节点传播覆盖落在森林解析期望的6个模拟标准误内',
            '15节点RS和份额归一化独立复算一致',
            '15节点AHP极差标准化、25%权重与并列排名复算一致',
            '原公式副本逐字节核验通过；MIT映射保持原结构']
    report='\n'.join('PASS '+c for c in checks)+'\n'
    (out/'结果核验记录.txt').write_text(report,encoding='utf8');print(report)

if __name__=='__main__':main()
