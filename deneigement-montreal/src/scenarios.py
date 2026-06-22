"""Les trois scénarios de priorisation du déneigement.

Tous les scénarios traitent **l'intégralité** des rues du secteur (contrainte
de l'énoncé) ; ils diffèrent par l'**ordre** de traitement, c'est-à-dire par
ce que l'on déneige en premier :

  S1 — « Axes d'abord »      : on traite les axes structurants, puis les voies
                               collectrices, puis la desserte locale. Objectif :
                               rétablir vite la fluidité du trafic de transit.
  S2 — « Services essentiels » : on traite d'abord les rues bordant hôpitaux,
                               écoles, casernes et arrêts de transport, puis le
                               reste. Objectif : sécurité et accès aux services.
  S3 — « Coût minimal »      : aucune priorité, on minimise directement la
                               distance parcourue (postier chinois pur). Sert de
                               référence économique.

Chaque scénario produit une tournée (pour un véhicule de référence), obtenue en
enchaînant des « passes » successives, chacune résolue par le postier rural
dirigé (S1/S2) ou le postier chinois (S3). On simule ensuite l'avancement du
déneigement pour mesurer le temps de remise en service de chaque classe de rue.
"""
from __future__ import annotations

import networkx as nx

from .cost import SPEED_KMH, vehicle_cost
from .cpp import directed_cpp, rural_postman, _cheapest_parallel_arc

SCENARIOS = {
    "S1": {"key": "S1", "nom": "Axes d'abord",
           "desc": "Axes structurants, puis collectrices, puis desserte locale."},
    "S2": {"key": "S2", "nom": "Services essentiels",
           "desc": "Rues des hôpitaux/écoles/transport d'abord, puis le reste."},
    "S3": {"key": "S3", "nom": "Coût minimal",
           "desc": "Postier chinois pur : distance minimale, sans priorité."},
}


def _edges_by_priority(G, levels):
    """Arcs (u,v,k) dont la classe de priorité est dans ``levels``."""
    return [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True)
            if d.get("priority", 3) in levels]


def _edges_essential(G, essential=True):
    return [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True)
            if bool(d.get("essential", False)) == essential]


def scenario_passes(G, key):
    """Liste ordonnée des ensembles d'arcs requis (une entrée par passe)."""
    if key == "S1":
        return [_edges_by_priority(G, {1}),
                _edges_by_priority(G, {2}),
                _edges_by_priority(G, {3})]
    if key == "S2":
        return [_edges_essential(G, True),
                _edges_essential(G, False)]
    if key == "S3":
        return [list(G.edges(keys=True))]
    raise KeyError(key)


def _connector(G, a, b, counter):
    """Arcs d'un plus court chemin a->b, en déplacements à vide."""
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


def build_route(G, key, source=None):
    """Construit la tournée complète d'un véhicule pour le scénario ``key``.

    Renvoie ``(route, info)`` où ``route`` est une liste d'arcs
    ``(u, v, data)`` et ``info`` contient les statistiques par passe.
    """
    passes = [p for p in scenario_passes(G, key) if p]
    if source is None:
        source = next(iter(G.nodes))

    if key == "S3":
        # Postier chinois pur : optimum de distance, une seule passe.
        circuit, stats = directed_cpp(G, source=source)
        return circuit, {"passes": [{"nom": "Tournée unique", **stats}], "stats": stats}

    route = []
    pos = source
    counter = [0]
    pass_infos = []
    for i, R in enumerate(passes):
        circ, st = rural_postman(G, R, source=pos)
        if not circ:
            continue
        start = circ[0][0]
        # Rejoindre le départ de la passe à vide.
        route.extend(_connector(G, pos, start, counter))
        route.extend(circ)
        pos = circ[-1][1]
        pass_infos.append({"nom": f"Passe {i + 1}", **st})
    # Retour au dépôt.
    route.extend(_connector(G, pos, source, counter))

    required_m = sum(d["length"] for _u, _v, d in route if not d.get("duplicate"))
    deadhead_m = sum(d["length"] for _u, _v, d in route if d.get("duplicate"))
    stats = {
        "required_m": required_m, "deadhead_m": deadhead_m,
        "total_m": required_m + deadhead_m,
        "required_km": required_m / 1000.0, "deadhead_km": deadhead_m / 1000.0,
        "total_km": (required_m + deadhead_m) / 1000.0,
        "deadhead_ratio": deadhead_m / required_m if required_m else 0.0,
        "n_edges_circuit": len(route),
    }
    return route, {"passes": pass_infos, "stats": stats}


def simulate_clearing(G, route, speed_kmh=SPEED_KMH):
    """Simule l'avancement : distance/temps de première couverture des rues.

    Un tronçon est considéré « déneigé » dès le premier passage du véhicule
    (la déneigeuse dégage la voie en roulant). Renvoie le temps de remise en
    service (h) par classe de priorité et pour les services essentiels.
    """
    first_km = {}
    cum_km = 0.0
    for u, v, d in route:
        cum_km += float(d.get("length", 0.0)) / 1000.0
        sid = (u, v, d.get("original_key"))
        if sid not in first_km:
            first_km[sid] = cum_km

    # Référence : classe de priorité et drapeau essentiel de chaque rue.
    by_class = {1: [], 2: [], 3: []}
    essential = []
    for u, v, k, data in G.edges(keys=True, data=True):
        sid = (u, v, k)
        t = first_km.get(sid)
        if t is None:
            continue
        by_class[data.get("priority", 3)].append(t)
        if data.get("essential"):
            essential.append(t)

    def restore(times):
        if not times:
            return {"km": None, "h": None, "n": 0}  # aucune rue de ce type
        m = max(times)
        return {"km": round(m, 2), "h": round(m / speed_kmh, 2), "n": len(times)}

    return {
        "axes_structurants": restore(by_class[1]),
        "voies_collectrices": restore(by_class[2]),
        "desserte_locale": restore(by_class[3]),
        "services_essentiels": restore(essential),
        "fin_totale": restore([t for ts in by_class.values() for t in ts]),
    }


def evaluate_scenario(G, key, speed_kmh=SPEED_KMH, source=None):
    """Évalue un scénario : tournée, coût (1 véhicule), indicateurs de service."""
    route, info = build_route(G, key, source=source)
    stats = info["stats"]
    clearing = simulate_clearing(G, route, speed_kmh)
    cost = vehicle_cost(stats["total_km"], speed_kmh)
    return {
        "scenario": key,
        "nom": SCENARIOS[key]["nom"],
        "route": route,
        "passes": info["passes"],
        "stats": stats,
        "clearing": clearing,
        "cost_1vehicule": cost.as_dict(),
    }
