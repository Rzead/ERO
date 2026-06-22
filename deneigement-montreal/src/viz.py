"""Visualisation cartographique (folium) : réseau, services, travaux, tournées.

Carte interactive Leaflet montrant :
  - le réseau coloré par classe de priorité ;
  - les services essentiels (marqueurs typés, regroupés en clusters) ;
  - les tronçons en travaux (rouge hachuré) ;
  - les tournées des déneigeuses, animées dans le temps, chaque engin marqué
    par une icône flocon ❄ de couleur propre (greffon TimestampedGeoJson).

Confort d'usage : plein écran, mini-carte, mesure de distance, légende, choix
du fond de carte.
"""
from __future__ import annotations

import base64
from statistics import mean

import folium
from folium.plugins import (Fullscreen, MeasureControl, MiniMap,
                            MarkerCluster, TimestampedGeoJson)

# Couleurs par classe de priorité (axes / collectrices / desserte).
PRIORITY_COLORS = {1: "#d7191c", 2: "#f39c12", 3: "#4a86c5"}
PRIORITY_WEIGHTS = {1: 5, 2: 3, 3: 2}
VEHICLE_COLORS = ["#0b3d91", "#188a42", "#8e44ad", "#c0392b",
                  "#0e7c7b", "#d35400", "#7f8c8d", "#2c3e50",
                  "#16a085", "#922b21", "#1f618d", "#6c3483", "#b9770e"]

TILES = {
    "clair": ("cartodbpositron", "© CARTO © OpenStreetMap"),
    "sombre": ("cartodbdark_matter", "© CARTO © OpenStreetMap"),
    "plan": ("OpenStreetMap", "© OpenStreetMap"),
}


# --- Géométries -------------------------------------------------------------

def edge_geometries(G):
    """dict (u, v, k) -> liste de (lat, lon) le long de la rue."""
    import osmnx as ox
    try:
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
    except Exception:
        return {}
    geoms = {}
    for idx, row in edges.iterrows():
        u, v, k = idx
        geom = row.get("geometry")
        if geom is not None and hasattr(geom, "coords"):
            geoms[(u, v, k)] = [(lat, lon) for lon, lat in geom.coords]
    return geoms


def _coords_for(G, u, v, k, geoms):
    """Coordonnées (lat, lon) d'un arc : géométrie OSM, sinon segment droit."""
    c = geoms.get((u, v, k))
    if c:
        return c
    if u in G.nodes and v in G.nodes:
        return [(G.nodes[u]["y"], G.nodes[u]["x"]), (G.nodes[v]["y"], G.nodes[v]["x"])]
    return []


# --- Icône flocon (data URI, autonome : pas d'image externe à charger) ------

def snowflake_icon(color: str, size: int = 30) -> str:
    """Renvoie une icône flocon SVG (data URI) de la couleur donnée."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 30 30">'
        f'<circle cx="15" cy="15" r="12" fill="{color}" stroke="white" stroke-width="2"/>'
        f'<g stroke="white" stroke-width="1.8" stroke-linecap="round">'
        f'<line x1="15" y1="5" x2="15" y2="25"/>'
        f'<line x1="6.7" y1="10" x2="23.3" y2="20"/>'
        f'<line x1="6.7" y1="20" x2="23.3" y2="10"/>'
        f'<line x1="15" y1="7.5" x2="12.5" y2="10"/><line x1="15" y1="7.5" x2="17.5" y2="10"/>'
        f'<line x1="15" y1="22.5" x2="12.5" y2="20"/><line x1="15" y1="22.5" x2="17.5" y2="20"/>'
        f'</g></svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


# --- Carte de base ----------------------------------------------------------

def base_map(G, zoom_start: int = 14, base_style: str = "clair"):
    ys = [d["y"] for _, d in G.nodes(data=True)]
    xs = [d["x"] for _, d in G.nodes(data=True)]
    tiles, attr = TILES.get(base_style, TILES["clair"])
    m = folium.Map(location=[mean(ys), mean(xs)], zoom_start=zoom_start,
                   tiles=tiles, attr=attr, control_scale=True)
    Fullscreen(title="Plein écran", title_cancel="Quitter").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    m.add_child(MeasureControl(primary_length_unit="kilometers"))
    return m


# --- Couches ----------------------------------------------------------------

def add_priority_layer(m, G, geoms):
    """Réseau coloré par priorité (+ couche services essentiels)."""
    layer = folium.FeatureGroup(name="Réseau (par priorité)", show=True)
    for u, v, k, data in G.edges(keys=True, data=True):
        coords = _coords_for(G, u, v, k, geoms)
        if not coords:
            continue
        prio = data.get("priority", 3)
        folium.PolyLine(coords, color=PRIORITY_COLORS[prio],
                        weight=PRIORITY_WEIGHTS[prio], opacity=0.7).add_to(layer)
    layer.add_to(m)


def add_essential_streets_layer(m, G, geoms):
    layer = folium.FeatureGroup(name="Rues des services essentiels", show=False)
    for u, v, k, data in G.edges(keys=True, data=True):
        if data.get("essential"):
            coords = _coords_for(G, u, v, k, geoms)
            if coords:
                folium.PolyLine(coords, color="#1a9641", weight=4,
                                opacity=0.9).add_to(layer)
    layer.add_to(m)


def _poi_kind(row):
    """(catégorie, couleur folium, icône FontAwesome) d'un point d'intérêt."""
    a = row.get("amenity") if "amenity" in row else None
    h = row.get("highway") if "highway" in row else None
    r = row.get("railway") if "railway" in row else None
    if a in ("hospital", "clinic"):
        return ("Santé", "red", "plus-square")
    if a in ("school", "kindergarten", "university", "college"):
        return ("Éducation", "blue", "graduation-cap")
    if a == "fire_station":
        return ("Caserne", "orange", "fire")
    if a == "police":
        return ("Police", "darkblue", "shield")
    if h == "bus_stop" or r in ("station", "tram_stop", "subway_entrance"):
        return ("Transport", "gray", "bus")
    return ("Autre service", "lightgray", "info")


def add_poi_markers(m, pois):
    """Marqueurs typés des services essentiels (regroupés en clusters)."""
    if pois is None or len(pois) == 0:
        return
    cluster = MarkerCluster(name="Services essentiels (points)", show=True)
    for _, row in pois.iterrows():
        try:
            lon, lat = float(row.geometry.x), float(row.geometry.y)
        except Exception:
            continue
        cat, color, icon = _poi_kind(row)
        nom = row.get("name") if "name" in row else None
        label = f"{cat}" + (f" — {nom}" if isinstance(nom, str) else "")
        folium.Marker([lat, lon], tooltip=label,
                      icon=folium.Icon(color=color, icon=icon, prefix="fa")
                      ).add_to(cluster)
    cluster.add_to(m)


def add_roadworks_layer(m, G, blocked, geoms):
    """Tronçons en travaux : rouge hachuré + marqueur d'avertissement."""
    if not blocked:
        return
    layer = folium.FeatureGroup(name="Tronçons en travaux", show=True)
    seen = set()
    for u, v, k, data in blocked:
        coords = geoms.get((u, v, k))
        if not coords:
            geom = data.get("geometry")
            if geom is not None and hasattr(geom, "coords"):
                coords = [(lat, lon) for lon, lat in geom.coords]
        if not coords:
            continue
        folium.PolyLine(coords, color="#b30000", weight=6, opacity=0.95,
                        dash_array="6,8", tooltip="Tronçon fermé (travaux)").add_to(layer)
        mid = coords[len(coords) // 2]
        if mid not in seen:
            seen.add(mid)
            folium.Marker(mid, tooltip="Travaux",
                          icon=folium.Icon(color="red", icon="ban", prefix="fa")
                          ).add_to(layer)
    layer.add_to(m)


def _route_coords(G, route, geoms):
    pts = []
    for u, v, d in route:
        seg = _coords_for(G, u, v, d.get("original_key"), geoms)
        if pts and seg and pts[-1] == seg[0]:
            pts.extend(seg[1:])
        else:
            pts.extend(seg)
    return pts


def add_route_static(m, G, routes, geoms):
    layer = folium.FeatureGroup(name="Tournées", show=True)
    for i, route in enumerate(routes):
        color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
        folium.PolyLine(_route_coords(G, route, geoms), color=color, weight=3,
                        opacity=0.85, tooltip=f"Déneigeuse {i + 1}").add_to(layer)
    layer.add_to(m)


def add_route_animation(m, G, routes, geoms, speed_kmh: float = 10.0):
    """Anime les déneigeuses : tracé progressif + icône flocon mobile."""
    base_ms = 1_768_456_800_000  # 2026-01-15T06:00:00Z (millisecondes)
    features = []
    for i, route in enumerate(routes):
        color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
        coords, times = [], []
        cum_h = 0.0
        for u, v, d in route:
            seg = _coords_for(G, u, v, d.get("original_key"), geoms)
            seg_h = (float(d.get("length", 0.0)) / 1000.0) / speed_kmh
            n = max(len(seg) - 1, 1)
            for j, (lat, lon) in enumerate(seg):
                if coords and coords[-1] == [lon, lat]:
                    continue
                coords.append([lon, lat])
                times.append(int(base_ms + (cum_h + seg_h * (j / n)) * 3600 * 1000))
            cum_h += seg_h
        if len(coords) < 2:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "times": times,
                "icon": "marker",
                "iconstyle": {"iconUrl": snowflake_icon(color), "iconSize": [28, 28],
                              "iconAnchor": [14, 14]},
                "style": {"color": color, "weight": 4, "opacity": 0.9},
                "tooltip": f"Déneigeuse {i + 1}",
            },
        })
    if not features:
        return
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT3M", add_last_point=True, auto_play=False, loop=False,
        max_speed=30, transition_time=120, time_slider_drag_update=True,
    ).add_to(m)


def add_legend(m, has_blocked=False):
    """Légende HTML flottante."""
    rows = [
        ("Axe structurant", PRIORITY_COLORS[1], "line"),
        ("Voie collectrice", PRIORITY_COLORS[2], "line"),
        ("Desserte locale", PRIORITY_COLORS[3], "line"),
        ("Service essentiel", "#1a9641", "dot"),
        ("Déneigeuse (position)", VEHICLE_COLORS[0], "snow"),
    ]
    if has_blocked:
        rows.append(("Tronçon en travaux", "#b30000", "dash"))
    items = []
    for label, color, kind in rows:
        if kind == "line":
            mark = f'<span style="display:inline-block;width:22px;height:4px;background:{color};vertical-align:middle"></span>'
        elif kind == "dash":
            mark = f'<span style="display:inline-block;width:22px;height:0;border-top:4px dashed {color};vertical-align:middle"></span>'
        elif kind == "dot":
            mark = f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};vertical-align:middle"></span>'
        else:  # snow
            mark = '<span style="vertical-align:middle">❄️</span>'
        items.append(f'<div style="margin:2px 0">{mark}&nbsp; {label}</div>')
    # Placée en haut à gauche, sous les boutons de zoom : n'empiète pas sur le
    # curseur de temps (en bas) ni sur le contrôle des couches (en haut à droite).
    html = (
        '<div style="position:absolute; top:90px; left:10px; z-index:9999; '
        'background:rgba(255,255,255,0.92); padding:6px 10px; border-radius:8px; '
        'box-shadow:0 1px 4px rgba(0,0,0,0.3); font-size:11.5px; '
        'font-family:sans-serif; color:#222; line-height:1.3">'
        '<b>Légende</b>' + "".join(items) + '</div>'
    )
    m.get_root().html.add_child(folium.Element(html))


def sector_map(G, routes=None, geoms=None, animate=True, speed_kmh: float = 10.0,
               pois=None, blocked=None, base_style: str = "clair"):
    """Carte complète d'un secteur (réseau + services + travaux + tournées)."""
    if geoms is None:
        geoms = edge_geometries(G)
    m = base_map(G, base_style=base_style)
    add_priority_layer(m, G, geoms)
    add_essential_streets_layer(m, G, geoms)
    if blocked:
        add_roadworks_layer(m, G, blocked, geoms)
    if pois is not None:
        add_poi_markers(m, pois)
    if routes:
        if animate:
            add_route_animation(m, G, routes, geoms, speed_kmh)
        else:
            add_route_static(m, G, routes, geoms)
    folium.LayerControl(collapsed=True).add_to(m)
    add_legend(m, has_blocked=bool(blocked))
    return m
