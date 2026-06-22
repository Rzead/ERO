"""Accessibilité aux services essentiels au fil du déneigement.

Indicateur d'impact social : quelle part de la population peut, à un instant
donné, rejoindre un service essentiel (hôpital, école, transport…) en
n'empruntant que des rues **déjà déneigées** ?

Faute de données de recensement à la maille de l'intersection, on utilise un
proxy de densité résidentielle : chaque intersection est pondérée par la
longueur de voies de desserte locale qui lui sont incidentes (là où les gens
habitent). On calcule alors, à plusieurs instants de la tournée, la fraction de
cette population proxy capable d'atteindre un service essentiel par le
sous-réseau déneigé (accessibilité « porte-à-service »).
"""
from __future__ import annotations

import networkx as nx

from .cost import SPEED_KMH


def essential_target_nodes(G) -> set:
    """Nœuds incidents à au moins une rue « service essentiel »."""
    E = set()
    for u, v, _k, d in G.edges(keys=True, data=True):
        if d.get("essential"):
            E.add(u)
            E.add(v)
    return E


def node_population_weight(G) -> dict:
    """Poids « population » par nœud (proxy de densité résidentielle)."""
    w = {n: 0.0 for n in G.nodes}
    for u, v, _k, d in G.edges(keys=True, data=True):
        if d.get("priority", 3) == 3:  # desserte locale = habitat
            half = float(d.get("length", 0.0)) / 2.0
            w[u] += half
            w[v] += half
    if sum(w.values()) == 0:  # repli : population uniforme
        w = {n: 1.0 for n in G.nodes}
    return w


def _reverse_reachable(cleared_adj_rev, sources) -> set:
    """Nœuds depuis lesquels on atteint ``sources`` (BFS sur graphe inversé)."""
    seen = set(sources)
    stack = list(sources)
    while stack:
        x = stack.pop()
        for y in cleared_adj_rev.get(x, ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def _first_km_by_street(route) -> dict:
    """Distance cumulée (km) au premier passage sur chaque rue."""
    first = {}
    cum = 0.0
    for u, v, d in route:
        cum += float(d.get("length", 0.0)) / 1000.0
        sid = (u, v, d.get("original_key"))
        if sid not in first:
            first[sid] = cum
    return first, cum


def accessibility_curve(G, route, speed_kmh: float = SPEED_KMH, n_points: int = 12):
    """Courbe d'accessibilité aux services essentiels au fil du temps.

    Renvoie un dict : ``curve`` (liste de points {t_h, km, pct}),
    ``final_pct``, et les temps pour atteindre 50 % et 90 % d'accessibilité.
    """
    first_km, total = _first_km_by_street(route)
    E = essential_target_nodes(G)
    W = node_population_weight(G)
    totW = sum(W.values())
    if not E or totW == 0 or total == 0:
        return {"curve": [], "final_pct": 0.0, "t_50": None, "t_90": None}

    curve = []
    for i in range(1, n_points + 1):
        tkm = total * i / n_points
        # Adjacence inversée des rues déneigées à cet instant.
        adj_rev = {}
        for u, v, k in G.edges(keys=True):
            if first_km.get((u, v, k), float("inf")) <= tkm + 1e-9:
                adj_rev.setdefault(v, []).append(u)
        reach = _reverse_reachable(adj_rev, E)
        acc = sum(W[n] for n in reach) / totW
        curve.append({"t_h": round(tkm / speed_kmh, 2), "km": round(tkm, 1),
                      "pct": round(100 * acc, 1)})

    def time_to(threshold):
        for p in curve:
            if p["pct"] >= threshold:
                return p["t_h"]
        return None

    return {"curve": curve, "final_pct": curve[-1]["pct"],
            "t_50": time_to(50), "t_90": time_to(90)}
