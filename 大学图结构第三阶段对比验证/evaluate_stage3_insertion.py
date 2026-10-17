"""Stage III evaluation and exhaustive degree-two insertion, reproducible paired IC sampling."""
import csv, json, itertools, sys
from pathlib import Path
import numpy as np
from 计算指标01_04 import graph, bfs, betweenness, global_efficiency, components

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'结果'; OUT.mkdir(exist_ok=True)
stage=json.loads((ROOT/'输入数据/拓扑.json').read_text(encoding='utf-8-sig'))['stages'][2]
ids,names,kinds,adj=graph(stage); n=len(ids); ix={v:i for i,v in enumerate(ids)}
source=json.loads((ROOT/'输入数据/学科映射.json').read_text(encoding='utf-8'))
discip={r['node']:r for r in source['nodes']}
discip['12']=discip['12-old']
missing_ids=[v for v in ids if v not in discip]
for v in missing_ids: discip[v]=dict(node=v,fields=[],rao_stirling=None)
with (ROOT/'输入数据/学科距离矩阵.csv').open(encoding='utf-8-sig',newline='') as f: matrix=list(csv.DictReader(f))
dm={r['field_code']:r for r in matrix}
def prob(a,b):
    return .5*sum(x['share']*y['share']*np.exp(-2*float(dm[x['code']][y['code']])) for x in discip[a]['fields'] for y in discip[b]['fields'])
edges=sorted({tuple(sorted((ix[e['a']],ix[e['b']]))) for e in stage['edges']})
R=100000; rng=np.random.default_rng(20261015)
# Symmetric IC has the same source reach distribution as undirected live-edge connectivity.
parent=np.tile(np.arange(n,dtype=np.int16),(R,1)); rr=np.arange(R)
def roots(v):
    r=parent[:,v].copy()
    while True:
        nxt=parent[rr,r]
        if np.array_equal(nxt,r): return r
        r=nxt
edge_live={(a,b):rng.random(R)<prob(ids[a],ids[b]) for a,b in edges}
def connectivity(excluded=None):
    global parent
    parent=np.tile(np.arange(n,dtype=np.int16),(R,1))
    for a,b in edges:
        if (a,b)==excluded: continue
        ra,rb=roots(a),roots(b); live=edge_live[a,b]
        parent[rr[live],ra[live]]=rb[live]
    lab=np.column_stack([roots(i) for i in range(n)])
    sz=np.zeros((R,n),dtype=np.int16)
    for i in range(n): np.add.at(sz,(rr,lab[:,i]),1)
    return lab,sz
labels,sizes=connectivity()
base_reach=sizes[rr[:,None],labels]; base_ac=base_reach.mean(axis=0)-1
new_live=np.column_stack([rng.random(R)<prob('12',v) for v in ids])
refs=list(csv.DictReader((ROOT/'输入数据/标准化参照.csv').open(encoding='utf-8-sig')))
bounds=[(float(r['最小值']),float(r['最大值'])) for r in refs]
def score(vals): return sum((v-lo)/(hi-lo) for v,(lo,hi) in zip(vals,bounds))/4
def metrics(g,ac):
    bc=betweenness(g); rows=[]
    for i,v in enumerate(g):
        d=bfs(g,v); reach=len(d)-1
        c=reach**2/((len(g)-1)*sum(d.values())) if sum(d.values()) else 0
        profile=discip['12' if v=='NEW12' else v]
        raw_rs=profile['rao_stirling']
        count=len({q['code'] for q in profile['fields'] if q['share']>0})
        rs=raw_rs*count if raw_rs is not None else None
        vals=[c,bc[v],rs,float(ac[i])]
        valid=rs is not None and bool(discip['12' if v=='NEW12' else v]['fields'])
        rows.append(dict(node=v,name=names.get(v,'新增节点（12号楼学科）'),closeness=c,betweenness=bc[v],rao_stirling=raw_rs,discipline_count=count,weighted_rs=rs,additional_reach=float(ac[i]),score=score(vals) if valid else None))
    return rows
base=metrics(adj,base_ac); baseE=global_efficiency(adj); candidates=[]
for index,(a,b) in enumerate(itertools.combinations(range(n),2)):
    adjacent=(a,b) in edge_live
    lab,sz=connectivity((a,b)) if adjacent else (labels,sizes)
    candidate_base=sz[rr[:,None],lab] if adjacent else base_reach
    la,lb=lab[:,a],lab[:,b]; sa,sb=sz[rr,la],sz[rr,lb]
    va,vb=new_live[:,a],new_live[:,b]; different=la!=lb
    newsize=1+va*sa+vb*sb-(va&vb&~different)*sb
    hit=((lab==la[:,None])&va[:,None])|((lab==lb[:,None])&vb[:,None])
    reach=np.where(hit,newsize[:,None],candidate_base)
    ac=np.append(reach.mean(axis=0)-1,newsize.mean()-1)
    g={v:set(ns) for v,ns in adj.items()}; u,v=ids[a],ids[b]
    if adjacent: g[u].remove(v);g[v].remove(u)
    g['NEW12']={u,v};g[u].add('NEW12');g[v].add('NEW12')
    assert sum(map(len,g.values()))//2==len(edges)+(1 if adjacent else 2)
    row=metrics(g,ac)[-1]; E=global_efficiency(g)
    row.update(original_edge=adjacent,net_added_edges=1 if adjacent else 2,total_edges=len(edges)+(1 if adjacent else 2))
    old_delta=(reach-base_reach).mean(axis=1)
    row.update(a=u,b=v,global_efficiency=E,delta_efficiency=E-baseE,mean_additional_reach=float(ac.mean()),delta_mean_additional_reach=float(ac.mean()-base_ac.mean()),old_origins_coverage_gain=float(old_delta.mean()),old_origins_coverage_gain_se=float(old_delta.std(ddof=1)/np.sqrt(R)),new_reach_se=float(newsize.std(ddof=1)/np.sqrt(R)),midpoint_x=(stage['nodes'][a]['x']+stage['nodes'][b]['x'])/2,midpoint_y=(stage['nodes'][a]['y']+stage['nodes'][b]['y'])/2)
    candidates.append(row)
    if index%100==0: print(f'evaluated {index+1}/{n*(n-1)//2}',flush=True)
candidates.sort(key=lambda r:-r['score'])
for rank,r in enumerate(candidates,1):r['rank']=rank
base.sort(key=lambda r:-(r['score'] if r['score'] is not None else -1))
def save_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
save_csv('原图节点四指标评分.csv',base);save_csv('全部候选排名.csv',candidates)
save_csv('Top10排名.csv',candidates[:10])
best=candidates[0]; g={v:set(ns) for v,ns in adj.items()};g['NEW12']={best['a'],best['b']}
for v in g['NEW12']:g[v].add('NEW12')
payload=dict(stage=3,runs=R,seed=20261015,beta=.5,kappa=2,normalization='固定沿用新版第四阶段AHP参照，第三指标=N乘RS；允许超出0—1，不截断',discipline_assumption='各阶段沿用已有第IV阶段学科映射；不是历史学科重建；缺失学科传播概率为0',new_node_fields=discip['12'],base=dict(nodes=n,edges=len(edges),components=components(adj),global_efficiency=baseE,mean_additional_reach=float(base_ac.mean()),node_scores=base),best=best,top10=candidates[:10],best_efficiency=max(candidates,key=lambda r:r['delta_efficiency']),best_propagation=max(candidates,key=lambda r:r['delta_mean_additional_reach']))
payload['insertion_rule']='原来有边则删除原边，改为两条新边（净增1边）；原来无边则新增两条边（净增2边）'
(OUT/'计算结果.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
modified=json.loads(json.dumps(stage));modified['nodes'].append(dict(id='NEW12',name='新增节点（12号楼学科）',kind='building',x=best['midpoint_x'],y=best['midpoint_y']));modified['edges'] += [dict(a=best['a'],b='NEW12'),dict(a='NEW12',b=best['b'])]
if best['original_edge']:
    modified['edges']=[e for e in modified['edges'] if {e['a'],e['b']}!={best['a'],best['b']}]
(OUT/'最佳方案_第3阶段.json').write_text(json.dumps(modified,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in payload.items() if k not in ['new_node_fields','base']},ensure_ascii=False,indent=2))
