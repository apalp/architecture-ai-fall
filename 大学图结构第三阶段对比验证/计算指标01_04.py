#!/usr/bin/env python3
"""计算 MIT 第 IV 阶段拓扑的四个单项指标并输出 CSV。

01 加权接近中心性：采用 Wasserman–Faust 可达比例修正。
02 全局效率：原网络效率及每个节点的固定分母效率贡献。
03 中介中心性：无向图标准化中介中心性。
04 结构洞：有效规模、结构洞效率、约束系数。

源 JSON 未提供真实距离或边权，故每条边的阻抗取 1。图面 x/y 坐标不参与计算。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import deque
from pathlib import Path

DEFAULT_JSON = Path(r"D:\用户\Downloads\MIT_四阶段底图修改.json")
DEFAULT_OUT = Path(r"D:\用户\Desktop\指标")


def sid(value: object) -> str:
    return str(value).strip()


def stage_label(index: int, stage: dict) -> str:
    raw = stage.get("name") or stage.get("title")
    return sid(raw) if raw else f"第{('I', 'II', 'III', 'IV')[index]}阶段"


def graph(stage: dict) -> tuple[list[str], dict[str, str], dict[str, str], dict[str, set[str]]]:
    nodes = stage["nodes"]
    ids = [sid(n["id"]) for n in nodes]
    names = {sid(n["id"]): sid(n.get("name") or n["id"]) for n in nodes}
    kinds = {sid(n["id"]): sid(n.get("kind") or "") for n in nodes}
    adj = {v: set() for v in ids}
    for edge in stage["edges"]:
        a, b = sid(edge["a"]), sid(edge["b"])
        if a in adj and b in adj and a != b:
            adj[a].add(b)
            adj[b].add(a)
    return ids, names, kinds, adj


def bfs(adj: dict[str, set[str]], start: str) -> dict[str, int]:
    dist = {start: 0}
    queue = deque([start])
    while queue:
        v = queue.popleft()
        for w in adj[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                queue.append(w)
    return dist


def global_efficiency(adj: dict[str, set[str]]) -> float:
    nodes = list(adj)
    n = len(nodes)
    if n < 2:
        return 0.0
    reciprocal_sum = 0.0
    for i, v in enumerate(nodes):
        dist = bfs(adj, v)
        reciprocal_sum += sum(1.0 / dist[w] for w in nodes[i + 1:] if w in dist and dist[w] > 0)
    return 2.0 * reciprocal_sum / (n * (n - 1))


def efficiency_without_node_fixed_denominator(adj: dict[str, set[str]], removed: str) -> float:
    """删除节点后仍使用原网络 N(N-1) 分母，保证节点贡献可比较。"""
    original_n = len(adj)
    remaining = [v for v in adj if v != removed]
    if original_n < 2:
        return 0.0
    reciprocal_sum = 0.0
    for i, start in enumerate(remaining):
        dist = {start: 0}
        queue = deque([start])
        while queue:
            v = queue.popleft()
            for w in adj[v]:
                if w == removed or w in dist:
                    continue
                dist[w] = dist[v] + 1
                queue.append(w)
        reciprocal_sum += sum(
            1.0 / dist[target]
            for target in remaining[i + 1:]
            if target in dist and dist[target] > 0
        )
    return 2.0 * reciprocal_sum / (original_n * (original_n - 1))


def components(adj: dict[str, set[str]]) -> int:
    unseen = set(adj)
    count = 0
    while unseen:
        count += 1
        reached = set(bfs(adj, next(iter(unseen))))
        unseen -= reached
    return count


def betweenness(adj: dict[str, set[str]]) -> dict[str, float]:
    score = {v: 0.0 for v in adj}
    for source in adj:
        stack: list[str] = []
        pred = {v: [] for v in adj}
        sigma = {v: 0.0 for v in adj}
        sigma[source] = 1.0
        distance = {v: -1 for v in adj}
        distance[source] = 0
        queue = deque([source])
        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj[v]:
                if distance[w] < 0:
                    distance[w] = distance[v] + 1
                    queue.append(w)
                if distance[w] == distance[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        dependency = {v: 0.0 for v in adj}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w] > 0:
                    dependency[v] += sigma[v] / sigma[w] * (1.0 + dependency[w])
            if w != source:
                score[w] += dependency[w]
    n = len(adj)
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 0.0
    return {v: score[v] * scale for v in score}


def structural_holes(adj: dict[str, set[str]], node: str) -> tuple[float, float, float]:
    neighbors = adj[node]
    degree = len(neighbors)
    if degree == 0:
        return 0.0, 0.0, 1.0
    neighbor_edges = sum(1 for a in neighbors for b in neighbors if a < b and b in adj[a])
    effective_size = degree - 2.0 * neighbor_edges / degree
    efficiency = effective_size / degree
    constraint = 0.0
    for j in neighbors:
        indirect = sum(
            (1.0 / degree) * (1.0 / len(adj[q]))
            for q in neighbors if len(adj[q]) > 0 and j in adj[q]
        )
        constraint += (1.0 / degree + indirect) ** 2
    return effective_size, efficiency, constraint


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    data = json.loads(args.json.read_text(encoding="utf-8-sig"))

    closeness_rows: list[dict[str, object]] = []
    efficiency_rows: list[dict[str, object]] = []
    betweenness_rows: list[dict[str, object]] = []
    holes_rows: list[dict[str, object]] = []

    # 本研究当前只评价最终形成的第 IV 阶段拓扑。
    for index, stage in [(3, data["stages"][3])]:
        label = stage_label(index, stage)
        ids, names, kinds, adj = graph(stage)
        node_count = len(ids)
        edge_count = sum(len(x) for x in adj.values()) // 2
        bc = betweenness(adj)

        base_efficiency = global_efficiency(adj)

        for node in ids:
            dist = bfs(adj, node)
            reachable = len(dist) - 1
            distance_sum = sum(dist.values())
            raw = reachable / distance_sum if distance_sum else 0.0
            wf = raw * reachable / (node_count - 1) if node_count > 1 else 0.0
            closeness_rows.append({
                "阶段": label,
                "楼栋": names[node],
                "节点ID": node,
                "节点类型": kinds[node],
                "度数": len(adj[node]),
                "可达节点数": reachable,
                "接近中心性_原始": round(raw, 10),
                "加权接近中心性_WF": round(wf, 10),
            })
            removed_efficiency = efficiency_without_node_fixed_denominator(adj, node)
            efficiency_contribution = base_efficiency - removed_efficiency
            efficiency_rows.append({
                "阶段": label,
                "楼栋": names[node],
                "节点ID": node,
                "节点类型": kinds[node],
                "节点数": node_count,
                "边数": edge_count,
                "连通分量数": components(adj),
                "原网络全局效率": round(base_efficiency, 10),
                "删除该节点后效率_固定分母": round(removed_efficiency, 10),
                "节点效率贡献": round(efficiency_contribution, 10),
                "相对效率贡献": round(efficiency_contribution / base_efficiency, 10) if base_efficiency else 0.0,
            })
            betweenness_rows.append({
                "阶段": label,
                "楼栋": names[node],
                "节点ID": node,
                "节点类型": kinds[node],
                "度数": len(adj[node]),
                "中介中心性_标准化": round(bc[node], 10),
            })
            effective_size, hole_efficiency, constraint = structural_holes(adj, node)
            holes_rows.append({
                "阶段": label,
                "楼栋": names[node],
                "节点ID": node,
                "节点类型": kinds[node],
                "度数": len(adj[node]),
                "结构洞有效规模": round(effective_size, 10),
                "结构洞效率": round(hole_efficiency, 10),
                "结构洞约束系数": round(constraint, 10),
            })

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "01_加权接近中心性.csv", closeness_rows)
    write_csv(args.out / "02_全局效率.csv", efficiency_rows)
    write_csv(args.out / "03_中介中心性.csv", betweenness_rows)
    write_csv(args.out / "04_结构洞.csv", holes_rows)
    print("完成：第 IV 阶段")
    for name in ("01_加权接近中心性.csv", "02_全局效率.csv", "03_中介中心性.csv", "04_结构洞.csv"):
        print(args.out / name)


if __name__ == "__main__":
    main()
