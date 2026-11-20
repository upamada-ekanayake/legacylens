from collections import defaultdict, deque
from typing import Iterable

from .models import CodeEdge, CodeNode, CycleInfo, ImpactReport


def _reverse_adjacency(edges: Iterable[CodeEdge]) -> dict[str, set[str]]:
    """Map each node to the set of nodes that depend on it (edge source -> target means source depends on target)."""
    reverse: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        reverse[edge.target].add(edge.source)
    return reverse


def find_cycles(nodes: Iterable[CodeNode], edges: Iterable[CodeEdge]) -> list[CycleInfo]:
    """Find circular dependencies using an iterative Tarjan SCC (no recursion, so deep graphs are safe)."""
    node_ids = sorted({n.id for n in nodes})
    known = set(node_ids)
    adjacency: dict[str, list[str]] = defaultdict(list)
    self_loops: set[str] = set()
    for edge in edges:
        if edge.source not in known or edge.target not in known:
            continue
        if edge.source == edge.target:
            self_loops.add(edge.source)
        adjacency[edge.source].append(edge.target)
    for targets in adjacency.values():
        targets.sort()

    index_of: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    counter = 0
    components: list[list[str]] = []

    for root in node_ids:
        if root in index_of:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, child_pos = work.pop()
            if child_pos == 0:
                index_of[node] = lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            children = adjacency.get(node, [])
            descended = False
            for pos in range(child_pos, len(children)):
                child = children[pos]
                if child not in index_of:
                    work.append((node, pos + 1))
                    work.append((child, 0))
                    descended = True
                    break
                if child in on_stack:
                    lowlink[node] = min(lowlink[node], index_of[child])
            if descended:
                continue
            if lowlink[node] == index_of[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(component)
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

    cycles: list[CycleInfo] = []
    for component in components:
        members = sorted(component)
        if len(members) > 1:
            cycles.append(
                CycleInfo(
                    nodes=members,
                    description=f"Circular dependency between {len(members)} files: {' <-> '.join(members)}",
                )
            )
        elif members[0] in self_loops:
            cycles.append(CycleInfo(nodes=members, description=f"{members[0]} depends on itself"))
    cycles.sort(key=lambda c: c.nodes)
    return cycles


def compute_blast_radius(
    target_id: str,
    nodes: Iterable[CodeNode],
    edges: Iterable[CodeEdge],
) -> ImpactReport:
    """Direct dependents are 1 hop away; transitive dependents are 2+ hops. Cycle-safe via a visited set."""
    node_list = list(nodes)
    edge_list = list(edges)
    known = {n.id for n in node_list}
    if target_id not in known:
        raise KeyError(target_id)

    reverse = _reverse_adjacency(edge_list)
    distance: dict[str, int] = {target_id: 0}
    queue: deque[str] = deque([target_id])
    while queue:
        current = queue.popleft()
        for dependent in sorted(reverse.get(current, ())):
            if dependent in distance or dependent not in known:
                continue
            distance[dependent] = distance[current] + 1
            queue.append(dependent)

    direct = sorted(n for n, d in distance.items() if d == 1)
    transitive = sorted(n for n, d in distance.items() if d >= 2)
    risk_score = min(100, len(direct) * 20 + len(transitive) * 10)

    notes = f"{len(direct)} direct and {len(transitive)} transitive dependents found in parsed imports."
    in_cycle = [c for c in find_cycles(node_list, edge_list) if target_id in c.nodes]
    if in_cycle:
        notes += " Target is part of a circular dependency."

    return ImpactReport(
        target_id=target_id,
        direct_impacts=direct,
        transitive_impacts=transitive,
        risk_score=risk_score,
        notes=notes,
    )


def assign_risk_levels(nodes: list[CodeNode], edges: Iterable[CodeEdge]) -> None:
    """Set risk_level from fan-in (how many files depend on the node). Mutates nodes in place."""
    fan_in = {nid: len(deps) for nid, deps in _reverse_adjacency(edges).items()}
    for node in nodes:
        count = fan_in.get(node.id, 0)
        node.risk_level = "high" if count >= 3 else "medium" if count >= 1 else "low"
