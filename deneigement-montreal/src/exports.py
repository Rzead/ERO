"""Export des tournées : traces GPS (GPX), GeoJSON, statistiques (CSV/JSON).

Produit une archive ZIP téléchargeable contenant, pour chaque déneigeuse, sa
trace GPS horodatée (.gpx), ainsi qu'un récapitulatif des statistiques
importantes (distance, durée, coût) et un GeoJSON de l'ensemble des tournées.
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


def trace_to_gpx(trace, name: str) -> str:
    """Trace GPS -> document GPX 1.1 (une piste horodatée)."""
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="ERO1-deneigement" '
            'xmlns="http://www.topografix.com/GPX/1/1">\n')
    body = [f"  <trk><name>{_sx.escape(name)}</name><trkseg>"]
    for lat, lon, t in trace:
        ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        body.append(f'    <trkpt lat="{lat:.6f}" lon="{lon:.6f}">'
                    f"<time>{ts}</time></trkpt>")
    body.append("  </trkseg></trk>\n</gpx>\n")
    return head + "\n".join(body)


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
    """Construit l'archive ZIP d'export (GPX + CSV + JSON + GeoJSON)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # Traces GPS par véhicule.
        for i, route in enumerate(vehicles):
            trace = vehicle_trace(G, route, geoms, speed_kmh)
            name = f"{meta.get('secteur', 'secteur')} — véhicule {i + 1}"
            z.writestr(f"gpx/vehicule_{i + 1}.gpx", trace_to_gpx(trace, name))

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
