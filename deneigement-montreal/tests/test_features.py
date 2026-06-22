"""Tests des modules « travaux », « accessibilité » et « export »."""
import io
import os
import sys
import zipfile

import networkx as nx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.priorities import annotate_priorities
from src.scenarios import build_route
from src.roadworks import apply_roadworks
from src.accessibility import accessibility_curve, essential_target_nodes
from src.exports import build_export_zip, trace_to_gpx, vehicle_trace


def grid_geo(n=6):
    """Grille n×n bidirectionnelle, nœuds munis de coordonnées x/y."""
    G = nx.MultiDiGraph()
    for i in range(n):
        for j in range(n):
            G.add_node((i, j), x=float(j), y=float(i))
    for i in range(n):
        for j in range(n):
            for di, dj in [(0, 1), (1, 0)]:
                b = (i + di, j + dj)
                if 0 <= b[0] < n and 0 <= b[1] < n:
                    G.add_edge((i, j), b, length=100.0, highway="residential")
                    G.add_edge(b, (i, j), length=100.0, highway="residential")
    return G


# --- Travaux ----------------------------------------------------------------

def test_roadworks_zero_keeps_graph():
    G = grid_geo(5)
    H, blocked = apply_roadworks(G, 0)
    assert blocked == []
    assert H.number_of_edges() == G.number_of_edges()


def test_roadworks_blocks_and_stays_strongly_connected():
    G = grid_geo(6)
    H, blocked = apply_roadworks(G, 5, seed=1)
    assert len(blocked) > 0
    assert H.number_of_edges() < G.number_of_edges()
    assert nx.is_strongly_connected(H)


def test_roadworks_reproducible():
    G = grid_geo(6)
    b1 = apply_roadworks(G, 5, seed=42)[1]
    b2 = apply_roadworks(G, 5, seed=42)[1]
    assert {(u, v) for u, v, _k, _d in b1} == {(u, v) for u, v, _k, _d in b2}


# --- Accessibilité ----------------------------------------------------------

def _annotate_with_essential(G):
    annotate_priorities(G)
    # Marque comme essentiel les rues touchant le coin (0,0).
    for u, v, _k, d in G.edges(keys=True, data=True):
        d["essential"] = (u == (0, 0) or v == (0, 0))


def test_accessibility_reaches_full_when_connected():
    G = grid_geo(5)
    _annotate_with_essential(G)
    route, _ = build_route(G, "S3")
    acc = accessibility_curve(G, route, n_points=10)
    assert acc["curve"], "courbe non vide"
    assert acc["final_pct"] == pytest.approx(100.0, abs=1e-6)


def test_accessibility_is_monotonic():
    G = grid_geo(5)
    _annotate_with_essential(G)
    route, _ = build_route(G, "S2")
    acc = accessibility_curve(G, route, n_points=12)
    pcts = [p["pct"] for p in acc["curve"]]
    assert all(b >= a - 1e-6 for a, b in zip(pcts, pcts[1:]))  # croissante


def test_essential_target_nodes_detected():
    G = grid_geo(4)
    _annotate_with_essential(G)
    assert (0, 0) in essential_target_nodes(G)


# --- Export -----------------------------------------------------------------

def test_gpx_well_formed():
    G = grid_geo(4)
    annotate_priorities(G)
    route, _ = build_route(G, "S3")
    trace = vehicle_trace(G, route, geoms={})
    gpx = trace_to_gpx(trace, "test")
    assert gpx.startswith("<?xml")
    assert "<trkpt" in gpx and "</gpx>" in gpx
    # Le GPX doit être un XML valide.
    import xml.etree.ElementTree as ET
    ET.fromstring(gpx)


def test_export_zip_contents():
    G = grid_geo(5)
    annotate_priorities(G)
    route, _ = build_route(G, "S3")
    vehicles = [route]
    z = build_export_zip(G, vehicles, geoms={}, distances_km=[12.3],
                         meta={"secteur": "Test", "scenario": "S3"})
    names = zipfile.ZipFile(io.BytesIO(z)).namelist()
    assert "gpx/vehicule_1.gpx" in names
    assert "statistiques_vehicules.csv" in names
    assert "tournees.geojson" in names
    assert "resume.json" in names
