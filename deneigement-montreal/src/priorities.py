"""Priorisation des rues.

Chaque rue (arc) reçoit :
  - une **classe de priorité** déduite de son type OSM ``highway`` :
      1 = axes structurants (autoroutes, artères, voies primaires) ;
      2 = voies collectrices (secondaires / tertiaires) ;
      3 = voies de desserte locale (résidentielles, etc.) ;
  - un **drapeau « service essentiel »** si elle borde un point d'intérêt
    sensible (hôpital, école, caserne, arrêt de transport).

Ces attributs alimentent les trois scénarios de priorisation (cf.
``scenarios.py``) et les indicateurs de remise en service.
"""
from __future__ import annotations

import networkx as nx

# Type de voie OSM -> classe de priorité.
HIGHWAY_PRIORITY = {
    "motorway": 1, "motorway_link": 1,
    "trunk": 1, "trunk_link": 1,
    "primary": 1, "primary_link": 1,
    "secondary": 2, "secondary_link": 2,
    "tertiary": 2, "tertiary_link": 2,
    "residential": 3, "living_street": 3, "unclassified": 3,
    "road": 3, "service": 3, "busway": 2,
}

PRIORITY_LABELS = {
    1: "Axe structurant",
    2: "Voie collectrice",
    3: "Desserte locale",
}


def edge_priority(data: dict) -> int:
    """Classe de priorité (1, 2 ou 3) d'un arc d'après son attribut highway."""
    hw = data.get("highway", "residential")
    if isinstance(hw, list):  # osmnx peut renvoyer une liste
        hw = hw[0]
    return HIGHWAY_PRIORITY.get(hw, 3)


def annotate_priorities(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Ajoute l'attribut ``priority`` (1/2/3) à chaque arc, en place."""
    for _u, _v, _k, data in G.edges(keys=True, data=True):
        data["priority"] = edge_priority(data)
    return G


def annotate_essential(G: nx.MultiDiGraph, pois, radius_m: float = 120.0) -> nx.MultiDiGraph:
    """Marque ``essential=True`` les arcs proches d'un service essentiel.

    ``pois`` est un GeoDataFrame de points (cf. ``io_osm.load_pois``). Pour
    chaque POI on repère le nœud du réseau le plus proche ; tout arc incident
    à ce nœud (ou à un voisin à moins de ``radius_m``) est jugé essentiel.

    Repli robuste : si ``pois`` est absent (échec réseau), on considère comme
    essentielles les voies de classe 1 et 2 — les services se situent en
    pratique sur ou près du réseau collecteur/structurant.
    """
    for _u, _v, _k, data in G.edges(keys=True, data=True):
        data["essential"] = False

    if pois is None or len(pois) == 0:
        for _u, _v, _k, data in G.edges(keys=True, data=True):
            data["essential"] = data.get("priority", 3) <= 2
        return G

    essential_nodes = _nearest_nodes(G, pois)
    for u, v, _k, data in G.edges(keys=True, data=True):
        if u in essential_nodes or v in essential_nodes:
            data["essential"] = True
    return G


def _nearest_nodes(G: nx.MultiDiGraph, pois) -> set:
    """Nœud du réseau le plus proche de chaque POI (recherche numpy, sans sklearn).

    Distance euclidienne approchée en degrés, corrigée du cosinus de la
    latitude — largement suffisant à l'échelle d'un arrondissement.
    """
    import numpy as np

    node_ids = list(G.nodes)
    nx_ = np.array([G.nodes[n]["x"] for n in node_ids], dtype=float)
    ny_ = np.array([G.nodes[n]["y"] for n in node_ids], dtype=float)
    cos_lat = np.cos(np.radians(np.mean(ny_)))

    result = set()
    for x, y in zip(pois.geometry.x.to_numpy(), pois.geometry.y.to_numpy()):
        dx = (nx_ - x) * cos_lat
        dy = ny_ - y
        result.add(node_ids[int(np.argmin(dx * dx + dy * dy))])
    return result


def priority_breakdown(G: nx.MultiDiGraph) -> dict:
    """Répartition des longueurs de voirie par classe de priorité (km)."""
    km = {1: 0.0, 2: 0.0, 3: 0.0}
    ess = 0.0
    for _u, _v, _k, data in G.edges(keys=True, data=True):
        length_km = float(data.get("length", 0.0)) / 1000.0
        km[data.get("priority", 3)] += length_km
        if data.get("essential"):
            ess += length_km
    return {
        "axes_structurants_km": round(km[1], 2),
        "voies_collectrices_km": round(km[2], 2),
        "desserte_locale_km": round(km[3], 2),
        "services_essentiels_km": round(ess, 2),
    }
