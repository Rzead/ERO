"""Problème du postier chinois dirigé (Directed Chinese Postman Problem).

On veut faire passer une déneigeuse sur **chaque rue** (arc) du secteur au
moins une fois, en minimisant la distance totale parcourue (déneigement utile
+ déplacements à vide, dits *deadheading*). C'est le problème du postier
chinois sur un graphe orienté (les sens uniques imposent l'orientation).

Méthode (alignée sur le cours « Algos RO ») :
  1. On exige que le graphe soit fortement connexe.
  2. Un circuit eulérien existe ssi, en chaque nœud, degré entrant = degré
     sortant. Au départ ce n'est pas le cas : on calcule le *déséquilibre*
     imbalance(v) = degré_sortant(v) - degré_entrant(v).
  3. Pour rééquilibrer, il faut ajouter un minimum de passages supplémentaires
     (arcs dupliqués) le long des rues existantes. Trouver ces duplications à
     coût minimal est exactement un **problème de flot à coût minimum** : on
     « expédie » du flot des nœuds en excès de sortie vers les nœuds en excès
     d'entrée, au coût = longueur des rues empruntées (cf. cours, transport /
     flot à coût minimum).
  4. Le multigraphe « rues + duplications » est alors eulérien : on en extrait
     un circuit eulérien (algorithme de Hierholzer, via networkx).

Le graphe d'entrée est un ``networkx.MultiDiGraph`` à la osmnx : chaque arc
porte un attribut ``length`` (en mètres).
"""
from __future__ import annotations

import networkx as nx


def largest_strongly_connected(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Sous-graphe induit par la plus grande composante fortement connexe.

    Indispensable : sans forte connexité, certains nœuds en déséquilibre ne
    peuvent pas être reliés et aucun circuit eulérien n'existe.
    """
    if G.number_of_nodes() == 0:
        return G.copy()
    scc = max(nx.strongly_connected_components(G), key=len)
    return G.subgraph(scc).copy()


def node_imbalance(G: nx.MultiDiGraph) -> dict:
    """imbalance(v) = degré sortant - degré entrant (sur les arcs requis)."""
    imb = {n: 0 for n in G.nodes}
    for u, v in G.edges():
        imb[u] += 1
        imb[v] -= 1
    return imb


def _cheapest_parallel_arc(G: nx.MultiDiGraph):
    """Pour chaque couple (u, v), retient la clé de l'arc le plus court.

    Renvoie un dict (u, v) -> (clé, longueur). Sert au calcul de flot, où l'on
    n'a besoin que de « la » liaison u->v la moins chère (on peut l'emprunter
    autant de fois que nécessaire).
    """
    best: dict[tuple, tuple] = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 1.0))
        if (u, v) not in best or length < best[(u, v)][1]:
            best[(u, v)] = (k, length)
    return best


def _balance_by_min_cost_flow(G: nx.MultiDiGraph, imbalance: dict) -> dict:
    """Flot à coût minimum équilibrant les déséquilibres ``imbalance``.

    Renvoie un dict (u, v) -> nombre de passages supplémentaires à ajouter sur
    la liaison u->v (empruntée le long du réseau ``G``).
    """
    if all(v == 0 for v in imbalance.values()):
        return {}

    cheapest = _cheapest_parallel_arc(G)

    # Réseau de flot : demande(v) = imbalance(v). Convention networkx :
    # demande > 0 => le nœud absorbe du flot (excès de sortie à compenser par
    # des passages entrants supplémentaires) ; demande < 0 => source.
    F = nx.DiGraph()
    for n in G.nodes:
        F.add_node(n, demand=int(imbalance.get(n, 0)))
    for (u, v), (_k, length) in cheapest.items():
        F.add_edge(u, v, weight=int(round(length)), capacity=10 ** 9)

    flow = nx.min_cost_flow(F)  # déséquilibres entiers => flot entier

    add: dict[tuple, int] = {}
    for u, flows in flow.items():
        for v, f in flows.items():
            if f > 0:
                add[(u, v)] = f
    return add


def min_cost_augmentation(G: nx.MultiDiGraph) -> dict:
    """Duplications d'arcs à ajouter pour rendre le graphe eulérien.

    Résout un flot à coût minimum : renvoie un dict (u, v) -> nombre de
    passages supplémentaires sur la liaison u->v.
    """
    return _balance_by_min_cost_flow(G, node_imbalance(G))


def build_eulerian_multigraph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Multigraphe eulérien = rues (1 passage) + duplications (flot min)."""
    H = nx.MultiDiGraph()
    H.add_nodes_from(G.nodes(data=True))
    # Chaque rue, une fois.
    for u, v, k, data in G.edges(keys=True, data=True):
        H.add_edge(u, v, key=("req", k), length=float(data.get("length", 1.0)),
                   original_key=k, duplicate=False)
    # Duplications issues du flot à coût minimum.
    cheapest = _cheapest_parallel_arc(G)
    add = min_cost_augmentation(G)
    dup_id = 0
    for (u, v), count in add.items():
        k, length = cheapest[(u, v)]
        for _ in range(count):
            H.add_edge(u, v, key=("dup", dup_id), length=length,
                       original_key=k, duplicate=True)
            dup_id += 1
    return H


def directed_cpp(G: nx.MultiDiGraph, source=None):
    """Résout le postier chinois dirigé sur ``G`` (déjà fortement connexe).

    Renvoie ``(circuit, stats)`` où :
      - ``circuit`` est la liste ordonnée d'arcs ``(u, v, data)`` parcourus ;
      - ``stats`` agrège les longueurs (requis, deadhead, total) en mètres.
    """
    H = build_eulerian_multigraph(G)

    required_m = sum(d["length"] for _u, _v, _k, d in H.edges(keys=True, data=True)
                     if not d["duplicate"])
    deadhead_m = sum(d["length"] for _u, _v, _k, d in H.edges(keys=True, data=True)
                     if d["duplicate"])

    if source is None:
        source = next(iter(H.nodes))

    circuit = []
    for u, v, k in nx.eulerian_circuit(H, source=source, keys=True):
        circuit.append((u, v, H[u][v][k]))

    stats = {
        "required_m": required_m,
        "deadhead_m": deadhead_m,
        "total_m": required_m + deadhead_m,
        "required_km": required_m / 1000.0,
        "deadhead_km": deadhead_m / 1000.0,
        "total_km": (required_m + deadhead_m) / 1000.0,
        "deadhead_ratio": (deadhead_m / required_m) if required_m else 0.0,
        "n_edges_required": G.number_of_edges(),
        "n_edges_circuit": len(circuit),
    }
    return circuit, stats


def _add_path_as_deadhead(H: nx.MultiDiGraph, G: nx.MultiDiGraph, path, counter):
    """Ajoute les arcs d'un chemin (liste de nœuds) à H comme déplacements à vide."""
    cheapest = _cheapest_parallel_arc(G)
    for a, b in zip(path[:-1], path[1:]):
        k, length = cheapest[(a, b)]
        H.add_edge(a, b, key=("con", counter[0]), length=length,
                   original_key=k, duplicate=True)
        counter[0] += 1


def rural_postman(G: nx.MultiDiGraph, required, source=None):
    """Postier rural dirigé : couvre exactement les rues ``required``.

    ``required`` est un itérable d'arcs ``(u, v, k)`` que la déneigeuse doit
    traiter ; toutes les autres rues de ``G`` ne servent qu'aux déplacements à
    vide. Heuristique en trois temps (toutes vues en cours) :
      1. on connecte les composantes du sous-graphe requis par des plus courts
         chemins ;
      2. on rééquilibre les degrés par un flot à coût minimum ;
      3. on extrait un circuit eulérien.

    Renvoie ``(circuit, stats)`` au même format que :func:`directed_cpp`.
    """
    req = [e for e in required]
    if not req:
        return [], {"required_m": 0.0, "deadhead_m": 0.0, "total_m": 0.0,
                    "required_km": 0.0, "deadhead_km": 0.0, "total_km": 0.0,
                    "deadhead_ratio": 0.0, "n_edges_required": 0, "n_edges_circuit": 0}

    H = nx.MultiDiGraph()
    H.add_nodes_from(G.nodes(data=True))
    for (u, v, k) in req:
        H.add_edge(u, v, key=("req", (u, v, k)), length=float(G[u][v][k]["length"]),
                   original_key=k, duplicate=False)

    counter = [0]
    # 1. Connecter les composantes faiblement connexes du graphe requis.
    used_nodes = set()
    for (u, v, _k) in req:
        used_nodes.add(u)
        used_nodes.add(v)
    sub = H.subgraph(used_nodes)
    comps = list(nx.weakly_connected_components(sub))
    if len(comps) > 1:
        reps = [next(iter(c)) for c in comps]
        for i in range(len(reps)):
            a, b = reps[i], reps[(i + 1) % len(reps)]
            try:
                path = nx.shortest_path(G, a, b, weight="length")
                _add_path_as_deadhead(H, G, path, counter)
            except nx.NetworkXNoPath:
                pass

    # 2. Rééquilibrer par flot à coût minimum (déplacements à vide).
    imb = {n: 0 for n in G.nodes}
    for u, v in H.edges():
        imb[u] += 1
        imb[v] -= 1
    add = _balance_by_min_cost_flow(G, imb)
    cheapest = _cheapest_parallel_arc(G)
    for (u, v), cnt in add.items():
        k, length = cheapest[(u, v)]
        for _ in range(cnt):
            H.add_edge(u, v, key=("dup", counter[0]), length=length,
                       original_key=k, duplicate=True)
            counter[0] += 1

    required_m = sum(d["length"] for _u, _v, _k, d in H.edges(keys=True, data=True)
                     if not d["duplicate"])
    deadhead_m = sum(d["length"] for _u, _v, _k, d in H.edges(keys=True, data=True)
                     if d["duplicate"])

    if source is None:
        source = req[0][0]
    # Le circuit eulérien doit démarrer sur la composante connexe utile.
    if source not in H or H.degree(source) == 0:
        source = req[0][0]

    circuit = []
    try:
        for u, v, k in nx.eulerian_circuit(H, source=source, keys=True):
            circuit.append((u, v, H[u][v][k]))
    except (nx.NetworkXError, KeyError):
        # Repli : circuit eulérien sur la composante du source uniquement.
        comp = nx.node_connected_component(H.to_undirected(), source)
        Hc = H.subgraph(comp).copy()
        for u, v, k in nx.eulerian_circuit(Hc, source=source, keys=True):
            circuit.append((u, v, Hc[u][v][k]))

    stats = {
        "required_m": required_m,
        "deadhead_m": deadhead_m,
        "total_m": required_m + deadhead_m,
        "required_km": required_m / 1000.0,
        "deadhead_km": deadhead_m / 1000.0,
        "total_km": (required_m + deadhead_m) / 1000.0,
        "deadhead_ratio": (deadhead_m / required_m) if required_m else 0.0,
        "n_edges_required": len(req),
        "n_edges_circuit": len(circuit),
    }
    return circuit, stats
