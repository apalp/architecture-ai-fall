"""输入人工拓扑JSON，调用配套学科资料计算四指标；Python标准库即可运行。"""
import argparse,csv,json,math,random,hashlib,importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
DEFAULT_SUPPORT=HERE.parent/'大学图结构全学科构建及映射关系'/'支持数据'

def select_json():
    """无命令行路径时允许窗口选取；无图形环境时允许键盘输入。"""
    selected=''
    try:
        import tkinter as tk
        from tkinter import filedialog
        window=tk.Tk()
        try:
            window.withdraw()
            window.attributes('-topmost',True)
            selected=filedialog.askopenfilename(parent=window,title='选择四阶段拓扑JSON文件',
                filetypes=[('JSON文件','*.json'),('所有文件','*.*')])
        finally:
            window.destroy()
    except Exception:
        pass
    if not selected:
        selected=input('请输入JSON文件完整路径（直接回车退出）：').strip().strip('"').strip("'")
    if not selected:
        raise SystemExit('未选择输入文件，已退出。')
    return Path(selected)
def write(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('json',type=Path,nargs='?',default=None,help='省略时弹出选择窗口或输入路径')
    p.add_argument('--support',type=Path,default=DEFAULT_SUPPORT,help='学科映射和距离矩阵所在目录')
    p.add_argument('--stage',type=int,choices=[1,2,3,4],default=4)
    p.add_argument('--runs',type=int,default=20000)
    p.add_argument('--seed',type=int,default=20261017)
    p.add_argument('--beta',type=float,default=.5)
    p.add_argument('--kappa',type=float,default=2.)
    p.add_argument('--out',type=Path,default=None)
    a=p.parse_args()
    if a.json is None:a.json=select_json()
    if not a.json.is_file():p.error(f'输入文件不存在：{a.json}')
    if a.runs<2 or not 0<=a.beta<=1 or a.kappa<0:raise ValueError('runs≥2，0≤beta≤1，kappa≥0')
    spec=importlib.util.spec_from_file_location('graph_tools',a.support/'拓扑算法.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    raw=a.json.read_bytes();stage=json.loads(raw.decode('utf-8-sig'))['stages'][a.stage-1]
    ids,names,kinds,adj=m.graph(stage)
    if len(ids)!=len(set(ids)):raise ValueError('节点编号重复')
    for e in stage['edges']:
        if str(e['a']) not in adj or str(e['b']) not in adj:raise ValueError('边端点不存在')
    profiles=json.loads((a.support/'学科映射.json').read_text(encoding='utf-8-sig'))
    prof={str(r['node']):r for r in profiles['nodes']}
    if '12-old' in prof:prof.setdefault('12',prof['12-old'])
    with (a.support/'学科距离矩阵.csv').open(encoding='utf-8-sig',newline='') as f:matrix={r['field_code']:r for r in csv.DictReader(f)}
    def fields(v):
        fs=prof.get(v,{}).get('fields',[])
        counts={}
        for q in fs:
            if float(q['share'])>0:counts[q['code']]=counts.get(q['code'],0)+float(q['share'])
        total=sum(counts.values())
        return {k:v/total for k,v in counts.items()} if total else {}
    flds={v:fields(v) for v in ids}
    bc=m.betweenness(adj);n=len(ids)
    one=[];two=[];three=[]
    for v in ids:
        common={'阶段':a.stage,'楼号':v,'楼名':names[v]}
        d=m.bfs(adj,v);reachable=len(d)-1
        c=reachable**2/((n-1)*sum(d.values())) if n>1 and sum(d.values()) else 0
        one.append({**common,'接近中心性_WF':c,'可达其他节点数':reachable})
        two.append({**common,'中介中心性_标准化':bc[v]})
        fs=flds[v];rs=sum(pi*pj*float(matrix[i][j]) for i,pi in fs.items() for j,pj in fs.items()) if fs else None
        three.append({**common,'学科数量N':len(fs) if fs else '', '原始RS':rs if rs is not None else '',
                      '数量加权RS_N乘RS':len(fs)*rs if rs is not None else '', '数据状态':'有效' if fs else '缺少学科映射'})
    ix={v:i for i,v in enumerate(ids)}
    es=[]
    for u in ids:
        for v in sorted(adj[u]):
            if ix[u]<ix[v]:
                prob=a.beta*sum(pi*pj*math.exp(-a.kappa*float(matrix[i][j])) for i,pi in flds[u].items() for j,pj in flds[v].items())
                es.append((ix[u],ix[v],prob))
    # 对称独立级联的单起点可达分布等价于无向live-edge连通分量；每次样本同时统计所有起点。
    rng=random.Random(a.seed);tot=[0.]*n;sq=[0.]*n
    for _ in range(a.runs):
        parent=list(range(n));size=[1]*n
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        for u,v,prob in es:
            if rng.random()<prob:
                u,v=root(u),root(v)
                if u!=v:parent[u]=v;size[v]+=size[u]
        for i in range(n):
            reach=size[root(i)]-1;tot[i]+=reach;sq[i]+=reach*reach
    four=[]
    missing=[v for v in ids if not flds[v]]
    for i,v in enumerate(ids):
        mean=tot[i]/a.runs;se=math.sqrt(max(0,(sq[i]-tot[i]**2/a.runs)/(a.runs-1))/a.runs)
        four.append({'阶段':a.stage,'楼号':v,'楼名':names[v],
            '传播新增覆盖':mean if flds[v] else '', '蒙特卡洛标准误':se if flds[v] else '',
            '数据状态':'有效（缺失映射的边按0传播）' if flds[v] else '缺少学科映射，不评分'})
    out=a.out or HERE/f'第{a.stage}阶段输出';out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('01_接近中心性.csv',one),('02_中介中心性.csv',two),('03_学科数量加权RS.csv',three),('04_信息传播新增覆盖.csv',four)]:write(out/name,rows)
    (out/'运行记录.json').write_text(json.dumps({'拓扑输入':str(a.json),'SHA256':hashlib.sha256(raw).hexdigest(),
        '阶段':a.stage,'节点数':n,'边数':len(es),'缺失映射楼号':missing,'模拟次数':a.runs,'seed':a.seed,'beta':a.beta,'kappa':a.kappa,
        '说明':'边成本为1；绘图坐标不当作距离；学科映射沿用现有审核资料，未进行历史学科重建。'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'完成：阶段{a.stage}，{n}节点，{len(es)}边；缺失映射：{missing}')

if __name__=='__main__':main()
