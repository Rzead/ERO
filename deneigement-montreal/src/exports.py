"""Export des tournées : traces GPS (GPX), GeoJSON, statistiques (CSV/JSON).

Produit une archive ZIP téléchargeable contenant, pour chaque déneigeuse :
  - sa trace GPS horodatée (.gpx) enrichie de points de passage (waypoints)
    indiquant *quoi* déneiger (ou parcourir à vide) et *quand* ;
  - une feuille de route lisible (.csv) : étape par étape, l'heure de début/fin,
    l'action (déneigement ou trajet à vide), la rue et sa priorité ;
ainsi qu'un récapitulatif des statistiques (distance, durée, coût) et un GeoJSON
de l'ensemble des tournées.
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
import json
import xml.sax.saxutils as _sx
import zipfile

from .cost import SPEED_KMH, vehicle_cost
from .viz import _coords_for

# Heure de départ conventionnelle des opérations (06:00, 15 janvier).
START = _dt.datetime(2026, 1, 15, 6, 0, 0)

# Libellé des classes de priorité (cf. src/priorities.py).
PRIORITY_LABELS = {1: "Axe structurant", 2: "Voie collectrice", 3: "Desserte locale"}


def _street_name(G, u, v, k) -> str:
    """Nom de la rue d'un arc (gère listes et absence de nom)."""
    try:
        data = G[u][v][k]
    except (KeyError, TypeError):
        return "(rue sans nom)"
    name = data.get("name")
    if isinstance(name, (list, tuple)):
        name = ", ".join(str(n) for n in name if n)
    if not name:
        return "(rue sans nom)"
    return str(name)


def _edge_info(G, u, v, d):
    """(nom de rue, action, priorité) d'un arc de tournée.

    ``d['duplicate']`` distingue le déneigement utile (premier passage,
    ``False``) du déplacement « à vide » / *deadhead* (``True``).
    """
    k = d.get("original_key")
    name = _street_name(G, u, v, k)
    action = "Trajet à vide" if d.get("duplicate") else "Déneigement"
    prio = 3
    try:
        prio = int(G[u][v][k].get("priority", 3))
    except (KeyError, TypeError):
        pass
    return name, action, prio


def _hms(t: _dt.datetime) -> str:
    return t.strftime("%H:%M:%S")


def route_legs(G, route, geoms, speed_kmh: float = SPEED_KMH):
    """Découpe une tournée en *étapes* (rue + action contiguës).

    Renvoie une liste de dicts ordonnés : ``ordre``, ``rue``, ``action``,
    ``priorite``, ``debut`` / ``fin`` (datetime), ``distance_m``, ``cumul_km`` et
    ``point`` (lat, lon de départ de l'étape) — ce qui décrit, pas à pas, *quoi*
    passer et *quand*.
    """
    legs = []
    cum_h = 0.0
    cum_m = 0.0
    cur = None
    for u, v, d in route:
        name, action, prio = _edge_info(G, u, v, d)
        seg = _coords_for(G, u, v, d.get("original_key"), geoms)
        length_m = float(d.get("length", 0.0))
        seg_h = (length_m / 1000.0) / speed_kmh
        start_t = START + _dt.timedelta(hours=cum_h)
        if cur is not None and cur["rue"] == name and cur["action"] == action:
            cur["distance_m"] += length_m
            cur["fin"] = start_t + _dt.timedelta(hours=seg_h)
        else:
            if cur is not None:
                legs.append(cur)
            pt = seg[0] if seg else None
            cur = {"rue": name, "action": action, "priorite": prio,
                   "debut": start_t, "fin": start_t + _dt.timedelta(hours=seg_h),
                   "distance_m": length_m, "point": pt}
        cum_h += seg_h
        cum_m += length_m
        cur["cumul_km"] = cum_m / 1000.0
    if cur is not None:
        legs.append(cur)
    for i, leg in enumerate(legs, 1):
        leg["ordre"] = i
    return legs


def vehicle_trace(G, route, geoms, speed_kmh: float = SPEED_KMH):
    """Liste de points (lat, lon, datetime) le long d'une tournée."""
    pts = []
    cum_h = 0.0
    for u, v, d in route:
        seg = _coords_for(G, u, v, d.get("original_key"), geoms)
        seg_h = (float(d.get("length", 0.0)) / 1000.0) / speed_kmh
        n = max(len(seg) - 1, 1)
        for j, (lat, lon) in enumerate(seg):
            if pts and abs(pts[-1][0] - lat) < 1e-9 and abs(pts[-1][1] - lon) < 1e-9:
                continue
            t = START + _dt.timedelta(hours=cum_h + seg_h * (j / n))
            pts.append((lat, lon, t))
        cum_h += seg_h
    return pts


def trace_to_gpx(trace, name: str, legs=None) -> str:
    """Trace GPS -> document GPX 1.1.

    La piste (``<trk>``) horodatée porte la géométrie du parcours. Les étapes
    (``legs``) sont ajoutées en points de passage (``<wpt>``) horodatés : ouvert
    dans n'importe quel visualiseur GPX, on lit ainsi *dans l'ordre* quelle rue
    déneiger (ou parcourir à vide) et à quelle heure.
    """
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="ERO1-deneigement" '
            'xmlns="http://www.topografix.com/GPX/1/1">\n')
    body = []
    # Points de passage : un par étape (quoi passer, et quand).
    for leg in (legs or []):
        if not leg.get("point"):
            continue
        lat, lon = leg["point"]
        ts = leg["debut"].strftime("%Y-%m-%dT%H:%M:%SZ")
        wname = (f"{leg['ordre']:03d} · {leg['action']} · {leg['rue']}")
        desc = (f"{leg['action']} de « {leg['rue']} » "
                f"({PRIORITY_LABELS.get(leg['priorite'], '—')}) — "
                f"de {_hms(leg['debut'])} à {_hms(leg['fin'])}, "
                f"{leg['distance_m']:.0f} m")
        sym = "Crossing" if leg["action"] == "Trajet à vide" else "Waypoint"
        body.append(f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}">'
                    f"<time>{ts}</time>"
                    f"<name>{_sx.escape(wname)}</name>"
                    f"<desc>{_sx.escape(desc)}</desc>"
                    f"<type>{_sx.escape(leg['action'])}</type>"
                    f"<sym>{sym}</sym></wpt>")
    # Piste horodatée.
    body.append(f"  <trk><name>{_sx.escape(name)}</name><trkseg>")
    for lat, lon, t in trace:
        ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        body.append(f'    <trkpt lat="{lat:.6f}" lon="{lon:.6f}">'
                    f"<time>{ts}</time></trkpt>")
    body.append("  </trkseg></trk>\n</gpx>\n")
    return head + "\n".join(body)


def roadbook_csv(legs) -> str:
    """Feuille de route lisible : une ligne par étape (quoi passer, et quand)."""
    sbuf = io.StringIO()
    writer = csv.writer(sbuf)
    writer.writerow(["ordre", "heure_debut", "heure_fin", "action", "rue",
                     "priorite", "distance_m", "cumul_km"])
    for leg in legs:
        writer.writerow([
            leg["ordre"], _hms(leg["debut"]), _hms(leg["fin"]), leg["action"],
            leg["rue"], PRIORITY_LABELS.get(leg["priorite"], "—"),
            round(leg["distance_m"]), round(leg.get("cumul_km", 0.0), 2),
        ])
    return sbuf.getvalue()


def routes_to_geojson(G, vehicles, geoms):
    """FeatureCollection GeoJSON : une LineString par véhicule."""
    feats = []
    for i, route in enumerate(vehicles):
        coords = []
        for u, v, d in route:
            for lat, lon in _coords_for(G, u, v, d.get("original_key"), geoms):
                if not coords or coords[-1] != [lon, lat]:
                    coords.append([lon, lat])
        feats.append({"type": "Feature",
                      "properties": {"vehicule": i + 1},
                      "geometry": {"type": "LineString", "coordinates": coords}})
    return {"type": "FeatureCollection", "features": feats}


def vehicle_stats_rows(distances_km, speed_kmh: float = SPEED_KMH):
    """Statistiques par véhicule (distance, durée, coût détaillé)."""
    rows = []
    for i, dist in enumerate(distances_km):
        c = vehicle_cost(dist, speed_kmh)
        rows.append({
            "vehicule": i + 1,
            "distance_km": round(c.distance_km, 2),
            "duree_h": round(c.duration_h, 2),
            "cout_fixe": round(c.fixed, 2),
            "cout_km": round(c.km, 2),
            "cout_horaire": round(c.hourly, 2),
            "cout_total": round(c.total, 2),
        })
    return rows


def build_export_zip(G, vehicles, geoms, distances_km, meta: dict,
                     speed_kmh: float = SPEED_KMH) -> bytes:
    """Construit l'archive ZIP d'export (GPX + feuilles de route + CSV + JSON + GeoJSON)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # Traces GPS + feuilles de route par véhicule.
        for i, route in enumerate(vehicles):
            legs = route_legs(G, route, geoms, speed_kmh)
            trace = vehicle_trace(G, route, geoms, speed_kmh)
            name = f"{meta.get('secteur', 'secteur')} — véhicule {i + 1}"
            z.writestr(f"gpx/vehicule_{i + 1}.gpx", trace_to_gpx(trace, name, legs))
            z.writestr(f"feuilles_de_route/vehicule_{i + 1}.csv", roadbook_csv(legs))

        # Statistiques par véhicule (CSV).
        rows = vehicle_stats_rows(distances_km, speed_kmh)
        sbuf = io.StringIO()
        writer = csv.DictWriter(sbuf, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
        z.writestr("statistiques_vehicules.csv", sbuf.getvalue())

        # GeoJSON de toutes les tournées.
        z.writestr("tournees.geojson",
                   json.dumps(routes_to_geojson(G, vehicles, geoms), ensure_ascii=False))

        # Récapitulatif JSON (configuration + indicateurs).
        z.writestr("resume.json", json.dumps({**meta, "vehicules": rows},
                                             ensure_ascii=False, indent=2))
    return buf.getvalue()
