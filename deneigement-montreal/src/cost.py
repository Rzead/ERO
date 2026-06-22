"""Modèle de coût des opérations de déblaiement.

Données fournies par la municipalité (voir énoncé, section 4) :
  - Coût fixe                       : 500 $/jour/véhicule
  - Coût kilométrique               : 1.1 $/km
  - Coût horaire (8 premières heures): 1.1 $/h
  - Coût horaire (au-delà de 8 h)    : 1.3 $/h
  - Vitesse moyenne                  : 10 km/h

Le coût d'un véhicule sur une journée se décompose donc en une part fixe,
une part kilométrique (distance parcourue, déneigement + déplacements à vide)
et une part horaire avec un seuil d'heures supplémentaires à 8 h.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

# --- Données municipales (constantes du problème) ---------------------------
FIXED_COST = 500.0          # $/jour/véhicule
KM_COST = 1.1               # $/km
HOURLY_COST_NORMAL = 1.1    # $/h, sur les 8 premières heures
HOURLY_COST_OVERTIME = 1.3  # $/h, au-delà de 8 heures
SPEED_KMH = 10.0            # km/h, vitesse moyenne d'une déneigeuse
NORMAL_HOURS = 8.0          # seuil d'heures supplémentaires


@dataclass
class VehicleCost:
    """Décomposition du coût d'un véhicule pour une tournée donnée."""
    distance_km: float
    duration_h: float
    fixed: float
    km: float
    hourly: float
    total: float

    def as_dict(self) -> dict:
        return asdict(self)


def vehicle_cost(distance_km: float, speed_kmh: float = SPEED_KMH) -> VehicleCost:
    """Coût d'un véhicule parcourant ``distance_km`` km à ``speed_kmh`` km/h."""
    duration_h = distance_km / speed_kmh if speed_kmh > 0 else 0.0
    normal_h = min(duration_h, NORMAL_HOURS)
    overtime_h = max(0.0, duration_h - NORMAL_HOURS)
    fixed = FIXED_COST
    km = distance_km * KM_COST
    hourly = normal_h * HOURLY_COST_NORMAL + overtime_h * HOURLY_COST_OVERTIME
    total = fixed + km + hourly
    return VehicleCost(distance_km, duration_h, fixed, km, hourly, total)


def fleet_cost(distances_km: list[float], speed_kmh: float = SPEED_KMH):
    """Coût d'une flotte : une distance par véhicule.

    Renvoie ``(liste_de_VehicleCost, cout_total)``.
    """
    vcs = [vehicle_cost(d, speed_kmh) for d in distances_km]
    return vcs, sum(v.total for v in vcs)


def summarize_fleet(distances_km: list[float], speed_kmh: float = SPEED_KMH) -> dict:
    """Indicateurs agrégés d'une flotte (pour les tableaux du rapport / l'app)."""
    vcs, total = fleet_cost(distances_km, speed_kmh)
    return {
        "n_vehicules": len(vcs),
        "distance_totale_km": round(sum(v.distance_km for v in vcs), 2),
        "duree_max_h": round(max((v.duration_h for v in vcs), default=0.0), 2),
        "heures_sup": any(v.duration_h > NORMAL_HOURS for v in vcs),
        "cout_fixe": round(sum(v.fixed for v in vcs), 2),
        "cout_km": round(sum(v.km for v in vcs), 2),
        "cout_horaire": round(sum(v.hourly for v in vcs), 2),
        "cout_total": round(total, 2),
    }
