"""Chargement des données routières OpenStreetMap (via osmnx) avec cache.

Pour chaque secteur (arrondissement de Montréal), on télécharge le réseau
routier carrossable (``network_type='drive'``, qui respecte les sens uniques)
et, optionnellement, les points d'intérêt « services essentiels » (hôpitaux,
écoles, casernes, arrêts de transport).

Tout est mis en cache sur disque (``data/<secteur>.graphml`` et
``data/<secteur>_pois.gpkg``) afin que la démonstration fonctionne **hors
ligne** une fois la première récupération effectuée.
"""
from __future__ import annotations

import os

import networkx as nx
import osmnx as ox

from .cpp import largest_strongly_connected

# Configuration osmnx : on garde les caches HTTP d'osmnx aussi.
ox.settings.use_cache = True
ox.settings.log_console = False

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Les 4 secteurs imposés par l'énoncé (arrondissements de Montréal).
SECTORS = {
    "outremont": {
        "label": "Outremont",
        "query": "Outremont, Montréal, Québec, Canada",
    },
    "verdun": {
        "label": "Verdun",
        "query": "Verdun, Montréal, Québec, Canada",
    },
    "anjou": {
        "label": "Anjou",
        "query": "Anjou, Montréal, Québec, Canada",
    },
    "rdp-pat": {
        "label": "Rivière-des-Prairies–Pointe-aux-Trembles",
        "query": "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada",
    },
}

# POI considérés comme « services essentiels » pour le scénario S2.
ESSENTIAL_TAGS = {
    "amenity": ["hospital", "clinic", "school", "kindergarten", "fire_station",
                "police", "university", "college"],
    "highway": ["bus_stop"],
    "railway": ["station", "subway_entrance", "tram_stop"],
}


def _graph_path(key: str) -> str:
    return os.path.join(DATA_DIR, f"{key}.graphml")


def _pois_path(key: str) -> str:
    return os.path.join(DATA_DIR, f"{key}_pois.gpkg")


def download_sector(key: str, simplify: bool = True) -> nx.MultiDiGraph:
    """Télécharge le réseau routier d'un secteur et le met en cache."""
    cfg = SECTORS[key]
    os.makedirs(DATA_DIR, exist_ok=True)
    G = ox.graph_from_place(cfg["query"], network_type="drive", simplify=simplify)
    # On travaille sur la plus grande composante fortement connexe : garantit
    # l'existence d'un circuit eulérien après rééquilibrage.
    G = largest_strongly_connected(G)
    ox.save_graphml(G, _graph_path(key))
    return G


def load_sector(key: str, force_download: bool = False) -> nx.MultiDiGraph:
    """Charge le graphe d'un secteur (cache si disponible, sinon télécharge)."""
    if key not in SECTORS:
        raise KeyError(f"Secteur inconnu : {key!r}. Choix : {list(SECTORS)}")
    path = _graph_path(key)
    if force_download or not os.path.exists(path):
        return download_sector(key)
    G = ox.load_graphml(path)
    # osmnx relit length/coords en str : on reconvertit les longueurs.
    for _u, _v, _k, data in G.edges(keys=True, data=True):
        if "length" in data:
            data["length"] = float(data["length"])
    return largest_strongly_connected(G)


def download_pois(key: str):
    """Télécharge les POI « services essentiels » d'un secteur, avec cache.

    Renvoie un GeoDataFrame (ou ``None`` si indisponible / erreur réseau).
    """
    cfg = SECTORS[key]
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        gdf = ox.features_from_place(cfg["query"], tags=ESSENTIAL_TAGS)
    except Exception:
        return None
    if gdf is None or len(gdf) == 0:
        return None
    # On réduit aux points (centroïdes pour polygones), colonnes utiles.
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.representative_point()
    try:
        gdf.to_file(_pois_path(key), driver="GPKG")
    except Exception:
        pass
    return gdf


def load_pois(key: str, force_download: bool = False):
    """Charge les POI d'un secteur (cache si disponible)."""
    import geopandas as gpd  # import local : dépendance optionnelle
    path = _pois_path(key)
    if not force_download and os.path.exists(path):
        try:
            return gpd.read_file(path)
        except Exception:
            pass
    return download_pois(key)


def graph_summary(G: nx.MultiDiGraph) -> dict:
    """Quelques statistiques descriptives d'un graphe de secteur."""
    total_m = sum(float(d.get("length", 0.0)) for _u, _v, _k, d in G.edges(keys=True, data=True))
    return {
        "n_noeuds": G.number_of_nodes(),
        "n_arcs": G.number_of_edges(),
        "longueur_totale_km": round(total_m / 1000.0, 2),
        "fortement_connexe": nx.is_strongly_connected(G),
    }
