"""Flotte de déneigeuses : découpage d'une tournée entre plusieurs véhicules.

On retient une heuristique « route d'abord, découpe ensuite » (route-first,
split-second), simple et toujours réalisable :

  1. On calcule la tournée d'un véhicule unique pour le scénario choisi.
  2. On la découpe en ``k`` tronçons contigus de longueur sensiblement égale.
  3. Chaque véhicule rejoint le début de son tronçon depuis le dépôt (à vide),
     le parcourt, puis revient au dépôt (à vide).

Les ``k`` véhicules travaillant en parallèle, le temps de remise en service du
secteur est le maximum des durées individuelles, alors que le coût total croît
avec le nombre de véhicules (coût fixe par véhicule + déplacements à vide vers
les tronçons). Ce compromis fonde le modèle de coût « coût = f(nb véhicules) ».
"""
from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment

from .cost import SPEED_KMH, summarize_fleet, vehicle_cost
from .cpp import _cheapest_parallel_arc


def _route_length_km(route) -> float:
    return sum(float(d.get("length", 0.0)) for _u, _v, d in route) / 1000.0


def _connector(G, a, b):
    """Arcs d'un plus court chemin a->b (déplacement à vide)."""
    out = []
    if a == b:
        return out
    cheapest = _cheapest_parallel_arc(G)
    try:
        path = nx.shortest_path(G, a, b, weight="length")
    except nx.NetworkXNoPath:
        return out
    for x, y in zip(path[:-1], path[1:]):
        k, length = cheapest[(x, y)]
        out.append((x, y, {"length": length, "original_key": k, "duplicate": True}))
    return out


def split_route(G, route, k: int, depot=None, passes=None):
    """Découpe ``route`` en ``k`` tournées de véhicules (route-first split-second).

    Si ``passes`` est fourni (multi-passes), affecte intelligemment les déneigeuses 
    entre les passes pour minimiser le déplacement à vide (Algorithme Hongrois).
    Renvoie la liste des tournées (chacune une liste d'arcs ``(u, v, data)``).
    """
    if k <= 1 or not passes or len(passes) <= 1:
        if k <= 1 or len(route) <= 1:
            return [route]
        if depot is None:
            depot = route[0][0]

        total = _route_length_km(route)
        target = total / k

    # Découpe en k tronçons contigus d'environ ``target`` km.
    chunks, cur, cur_km, idx = [], [], 0.0, 0
    for edge in route:
        cur.append(edge)
        cur_km += float(edge[2].get("length", 0.0)) / 1000.0
        if cur_km >= target and len(chunks) < k - 1:
            chunks.append(cur)
            cur, cur_km = [], 0.0
    if cur:
        chunks.append(cur)

    # Chaque véhicule : dépôt -> tronçon -> dépôt.
    vehicles = []
    for chunk in chunks:
        if not chunk:
            continue
        start = chunk[0][0]
        end = chunk[-1][1]
        v_route = _connector(G, depot, start) + chunk + _connector(G, end, depot)
        vehicles.append(v_route)
        return vehicles

    # --- Mode Multi-Passes optimisé ---
    if depot is None:
        for p in passes:
            if p.get("route"):
                depot = p["route"][0][0]
                break
        if depot is None:
            depot = next(iter(G.nodes))

    vehicles_routes = [[] for _ in range(k)]
    current_positions = [depot] * k

    for p_info in passes:
        pass_circuit = p_info.get("route", [])
        if not pass_circuit:
            continue

        total = _route_length_km(pass_circuit)
        target = total / k

        chunks, cur, cur_km = [], [], 0.0
        for edge in pass_circuit:
            cur.append(edge)
            cur_km += float(edge[2].get("length", 0.0)) / 1000.0
            if cur_km >= target and len(chunks) < k - 1:
                chunks.append(cur)
                cur, cur_km = [], 0.0
        if cur:
            chunks.append(cur)

        # Compléter avec des tronçons vides si k > len(chunks)
        while len(chunks) < k:
            chunks.append([])

        starts = [c[0][0] if c else None for c in chunks]

        # Matrice de coût
        cost_matrix = np.zeros((k, k))
        for i, u in enumerate(current_positions):
            try:
                # Distances depuis la position courante du véhicule i
                lengths = nx.single_source_dijkstra_path_length(G, u, weight="length")
            except Exception:
                lengths = {}
            for j, v in enumerate(starts):
                if v is None or u == v:
                    cost_matrix[i, j] = 0.0
                else:
                    if v in lengths:
                        cost_matrix[i, j] = lengths[v]
                    else:
                        cost_matrix[i, j] = 1e9

        # Affectation optimale (Algorithme Hongrois)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        new_positions = [None] * k
        for i, j in zip(row_ind, col_ind):
            v = starts[j]
            chunk = chunks[j]
            if v is not None:
                vehicles_routes[i].extend(_connector(G, current_positions[i], v))
            vehicles_routes[i].extend(chunk)
            if chunk:
                new_positions[i] = chunk[-1][1]
            else:
                new_positions[i] = current_positions[i]

        current_positions = new_positions

    # Retour au dépôt
    for i, u in enumerate(current_positions):
        vehicles_routes[i].extend(_connector(G, u, depot))

    return vehicles_routes


def fleet_distances_km(G, route, k: int, depot=None, passes=None):
    """Distances (km) par véhicule pour un découpage en ``k`` tournées."""
    vehicles = split_route(G, route, k, depot, passes=passes)
    return [_route_length_km(v) for v in vehicles]


def fleet_plan(G, route, k: int, depot=None, speed_kmh: float = SPEED_KMH, passes=None):
    """Plan complet d'une flotte de ``k`` véhicules pour une tournée donnée."""
    vehicles = split_route(G, route, k, depot, passes=passes)
    distances = [_route_length_km(v) for v in vehicles]
    summary = summarize_fleet(distances, speed_kmh)
    summary["temps_remise_service_h"] = round(
        max((d / speed_kmh for d in distances), default=0.0), 2)
    return {"vehicles": vehicles, "distances_km": distances, "summary": summary}


def cost_vs_vehicles(G, route, k_max: int = 8, depot=None, speed_kmh: float = SPEED_KMH, passes=None):
    """Courbe coût = f(nb véhicules) : un point par k de 1 à ``k_max``.

    Renvoie une liste de dicts {k, cout_total, temps_remise_service_h, ...}.
    """
    rows = []
    for k in range(1, k_max + 1):
        distances = fleet_distances_km(G, route, k, depot, passes=passes)
        s = summarize_fleet(distances, speed_kmh)
        rows.append({
            "n_vehicules": k,
            "cout_total": s["cout_total"],
            "distance_totale_km": s["distance_totale_km"],
            "temps_remise_service_h": round(max((d / speed_kmh for d in distances),
                                                default=0.0), 2),
            "heures_sup": s["heures_sup"],
        })
    return rows


def recommend_fleet_size(rows, max_hours: float = 8.0):
    """Plus petit nombre de véhicules permettant de finir en ``max_hours`` h.

    À défaut (aucun ne respecte la borne), renvoie celui de temps minimal.
    """
    feasible = [r for r in rows if r["temps_remise_service_h"] <= max_hours]
    if feasible:
        return min(feasible, key=lambda r: r["n_vehicules"])
    return min(rows, key=lambda r: r["temps_remise_service_h"])
