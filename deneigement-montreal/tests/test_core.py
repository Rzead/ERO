"""Tests unitaires du cœur du projet (sans accès réseau).

Lancement :  python -m pytest tests/ -q
"""
import os
import sys

import networkx as nx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cost import vehicle_cost, summarize_fleet, NORMAL_HOURS, SPEED_KMH
from src.cpp import (directed_cpp, rural_postman, node_imbalance,
                     largest_strongly_connected)
from src.priorities import annotate_priorities, edge_priority
from src.scenarios import build_route, simulate_clearing


def triangle_graph():
    """Petit graphe dirigé fortement connexe, non eulérien."""
    G = nx.MultiDiGraph()
    for u, v, l in [("A", "B", 100), ("B", "C", 100), ("C", "A", 100),
                    ("B", "D", 50), ("D", "B", 50), ("C", "D", 80), ("D", "A", 120)]:
        G.add_edge(u, v, length=l, highway="residential")
    return G


def grid_graph(n=5):
    """Grille n×n bidirectionnelle (toutes rues à double sens)."""
    G = nx.MultiDiGraph()
    for i in range(n):
        for j in range(n):
            for di, dj in [(0, 1), (1, 0)]:
                a, b = (i, j), (i + di, j + dj)
                if 0 <= b[0] < n and 0 <= b[1] < n:
                    G.add_edge(a, b, length=100.0, highway="residential")
                    G.add_edge(b, a, length=100.0, highway="residential")
    return G


# --- Modèle de coût ---------------------------------------------------------

def test_cost_no_overtime():
    vc = vehicle_cost(40.0)  # 40 km à 10 km/h = 4 h < 8 h
    assert vc.duration_h == pytest.approx(4.0)
    assert vc.fixed == 500.0
    assert vc.km == pytest.approx(44.0)
    assert vc.hourly == pytest.approx(4.0 * 1.1)
    assert vc.total == pytest.approx(500 + 44 + 4.4)


def test_cost_overtime():
    vc = vehicle_cost(100.0)  # 10 h => 2 h supplémentaires
    assert vc.duration_h == pytest.approx(10.0)
    assert vc.hourly == pytest.approx(NORMAL_HOURS * 1.1 + 2.0 * 1.3)


def test_fleet_cost_additive():
    s = summarize_fleet([40.0, 40.0])
    assert s["n_vehicules"] == 2
    assert s["cout_fixe"] == pytest.approx(1000.0)
    assert s["distance_totale_km"] == pytest.approx(80.0)


# --- Postier chinois dirigé -------------------------------------------------

def _is_closed_walk(circuit):
    return all(circuit[i][1] == circuit[i + 1][0] for i in range(len(circuit) - 1)) \
        and circuit[-1][1] == circuit[0][0]


def test_cpp_covers_all_edges():
    G = triangle_graph()
    circuit, stats = directed_cpp(G, source="A")
    covered = {}
    for u, v, d in circuit:
        if not d["duplicate"]:
            covered[(u, v, d["original_key"])] = covered.get((u, v, d["original_key"]), 0) + 1
    required = {(u, v, k) for u, v, k in G.edges(keys=True)}
    assert set(covered) == required
    assert all(c == 1 for c in covered.values())


def test_cpp_is_closed_walk():
    circuit, _ = directed_cpp(triangle_graph(), source="A")
    assert _is_closed_walk(circuit)


def test_cpp_total_ge_required():
    _, stats = directed_cpp(triangle_graph())
    assert stats["total_m"] >= stats["required_m"]
    assert stats["deadhead_m"] >= 0


def test_cpp_eulerian_grid_zero_deadhead():
    # Une grille entièrement bidirectionnelle est déjà eulérienne : 0 deadhead.
    _, stats = directed_cpp(grid_graph(5))
    assert stats["deadhead_m"] == pytest.approx(0.0)


def test_imbalance_sums_to_zero():
    G = triangle_graph()
    assert sum(node_imbalance(G).values()) == 0


def test_largest_scc_keeps_strong_component():
    G = triangle_graph()
    G.add_edge("Z", "A", length=10.0)  # nœud non fortement connexe
    H = largest_strongly_connected(G)
    assert "Z" not in H
    assert nx.is_strongly_connected(H)


# --- Postier rural ----------------------------------------------------------

def test_rural_postman_covers_required_subset():
    G = grid_graph(5)
    annotate_priorities(G)
    required = list(G.edges(keys=True))[:10]
    circuit, stats = rural_postman(G, required)
    covered = {(u, v, d["original_key"]) for u, v, d in circuit if not d["duplicate"]}
    assert set(required).issubset(covered)


# --- Scénarios --------------------------------------------------------------

@pytest.mark.parametrize("key", ["S1", "S2", "S3"])
def test_scenario_route_covers_everything(key):
    G = grid_graph(5)
    annotate_priorities(G)
    for _u, _v, _k, d in G.edges(keys=True, data=True):
        d["essential"] = (d.get("priority", 3) <= 2)
    route, info = build_route(G, key)
    covered = {(u, v, d.get("original_key")) for u, v, d in route if not d.get("duplicate")}
    required = {(u, v, k) for u, v, k in G.edges(keys=True)}
    assert required.issubset(covered)


def test_clearing_priority_order_S1_before_S3():
    # En S1, les voies collectrices sont déneigées plus tôt qu'en S3.
    G = grid_graph(6)
    annotate_priorities(G)
    # Marquer une "artère" : une ligne de la grille en secondaire.
    for u, v, k, d in G.edges(keys=True, data=True):
        d["priority"] = 2 if u[0] == 0 else 3
        d["essential"] = False
    r1, _ = build_route(G, "S1")
    r3, _ = build_route(G, "S3")
    c1 = simulate_clearing(G, r1)["voies_collectrices"]["h"]
    c3 = simulate_clearing(G, r3)["voies_collectrices"]["h"]
    assert c1 is not None and c3 is not None
    assert c1 <= c3  # priorisation : collectrices traitées au plus tôt


def test_edge_priority_mapping():
    assert edge_priority({"highway": "primary"}) == 1
    assert edge_priority({"highway": "secondary"}) == 2
    assert edge_priority({"highway": "residential"}) == 3
    assert edge_priority({"highway": ["tertiary", "residential"]}) == 2
    assert edge_priority({}) == 3
