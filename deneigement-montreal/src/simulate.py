"""Orchestration d'une simulation : configuration -> calcul complet.

Point d'entrée unique appelé par l'application : à partir du réseau d'un
secteur et d'une configuration (scénario, nombre de déneigeuses, tronçons en
travaux), renvoie la tournée, la flotte, le coût, l'accessibilité aux services
et tout ce qu'il faut pour l'affichage et l'export.
"""
from __future__ import annotations

from .accessibility import accessibility_curve
from .cost import SPEED_KMH
from .fleet import split_route, fleet_plan, cost_vs_vehicles, recommend_fleet_size
from .roadworks import apply_roadworks
from .scenarios import evaluate_scenario


def run_simulation(G_full, pois, scenario, n_vehicles, n_blocked=0, seed=0,
                   speed_kmh: float = SPEED_KMH, k_max: int = 15):
    """Exécute une simulation complète et renvoie un dictionnaire de résultats.

    ``G_full`` doit déjà porter les attributs ``priority`` et ``essential``.
    """
    H, blocked = apply_roadworks(G_full, n_blocked, seed)

    result = evaluate_scenario(H, scenario, speed_kmh=speed_kmh)
    route = result["route"]
    passes = result.get("passes")
    depot = route[0][0] if route else next(iter(H.nodes))

    vehicles = split_route(H, route, n_vehicles, depot, passes=passes)
    plan = fleet_plan(H, route, n_vehicles, depot=depot, speed_kmh=speed_kmh, passes=passes)
    access = accessibility_curve(H, route, speed_kmh=speed_kmh)
    curve = cost_vs_vehicles(H, route, k_max=max(k_max, n_vehicles), depot=depot,
                             speed_kmh=speed_kmh, passes=passes)
    reco = recommend_fleet_size(curve, max_hours=8.0)

    return {
        "graph": H,
        "blocked": blocked,
        "n_blocked_streets": len(blocked),
        "scenario": scenario,
        "result": result,
        "route": route,
        "depot": depot,
        "vehicles": vehicles,
        "distances_km": plan["distances_km"],
        "fleet": plan["summary"],
        "accessibility": access,
        "curve": curve,
        "reco": reco,
    }
