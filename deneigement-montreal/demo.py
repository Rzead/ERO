#!/usr/bin/env python3
"""Démonstration de la solution — déneigement de Montréal (projet ERO1).

Pour chaque secteur étudié (Outremont, Verdun, Anjou, Rivière-des-Prairies–
Pointe-aux-Trembles), le script :
  1. charge le réseau routier (OpenStreetMap, via cache) ;
  2. résout les trois scénarios de priorisation (postier chinois / rural) ;
  3. dimensionne la flotte (coût = f(nombre de véhicules)) ;
  4. écrit les résultats et les cartes interactives dans ``secteurs/<nom>/`` ;
  5. génère les figures du rapport dans ``rapport/figures/``.

Usage :
    python demo.py                 # tous les secteurs
    python demo.py --secteur verdun
    python demo.py --quick         # uniquement Outremont (rapide)
    python demo.py --no-cartes     # n'écrit pas les cartes HTML (plus rapide)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Console Windows : forcer l'UTF-8 pour les accents et symboles (≤, –, …).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from src.io_osm import SECTORS, load_sector, load_pois, graph_summary
from src.priorities import annotate_priorities, annotate_essential, priority_breakdown
from src.scenarios import SCENARIOS, evaluate_scenario, build_route
from src.fleet import split_route, fleet_plan, cost_vs_vehicles, recommend_fleet_size
from src.cost import SPEED_KMH

ROOT = os.path.dirname(os.path.abspath(__file__))
SECTEURS_DIR = os.path.join(ROOT, "secteurs")
FIG_DIR = os.path.join(ROOT, "rapport", "figures")
RES_DIR = os.path.join(ROOT, "resultats")


def _round(o, n=2):
    if isinstance(o, float):
        return round(o, n)
    if isinstance(o, dict):
        return {k: _round(v, n) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v, n) for v in o]
    return o


def analyse_secteur(key, write_maps=True):
    """Analyse complète d'un secteur ; renvoie un dict de synthèse."""
    label = SECTORS[key]["label"]
    print(f"\n=== {label} ===")
    G = load_sector(key)
    annotate_priorities(G)
    pois = load_pois(key)
    annotate_essential(G, pois)
    summ = graph_summary(G)
    breakdown = priority_breakdown(G)
    print(f"  Réseau : {summ['n_noeuds']} nœuds, {summ['n_arcs']} tronçons, "
          f"{summ['longueur_totale_km']} km.")

    out_dir = os.path.join(SECTEURS_DIR, key)
    os.makedirs(out_dir, exist_ok=True)

    scen_results = {}
    for sk in SCENARIOS:
        r = evaluate_scenario(G, sk)
        scen_results[sk] = r
        cl = r["clearing"]
        ess = "—" if cl["services_essentiels"]["h"] is None else f"{cl['services_essentiels']['h']}h"
        print(f"  {sk} {SCENARIOS[sk]['nom']:<20} "
              f"{r['stats']['total_km']:>6.0f} km · "
              f"{r['cost_1vehicule']['total']:>5.0f}$/véh · "
              f"essentiels déneigés à {ess}")

    # Dimensionnement de la flotte sur le scénario de référence S3.
    route_s3 = scen_results["S3"]["route"]
    passes_s3 = scen_results["S3"]["passes"]
    depot = route_s3[0][0] if route_s3 else next(iter(G.nodes))
    curve = cost_vs_vehicles(G, route_s3, k_max=15, depot=depot, passes=passes_s3)
    reco = recommend_fleet_size(curve, max_hours=8.0)
    print(f"  Flotte recommandée (≤ 8 h, S3) : {reco['n_vehicules']} véhicules · "
          f"{reco['temps_remise_service_h']} h · {reco['cout_total']:.0f} $.")

    # --- Écriture des résultats (JSON) -------------------------------------
    payload = {
        "secteur": label, "cle": key,
        "reseau": summ, "voirie": breakdown,
        "scenarios": {sk: {
            "nom": SCENARIOS[sk]["nom"],
            "stats": _round(scen_results[sk]["stats"]),
            "clearing": _round(scen_results[sk]["clearing"]),
            "cost_1vehicule": _round(scen_results[sk]["cost_1vehicule"]),
            "passes": _round(scen_results[sk]["passes"]),
        } for sk in SCENARIOS},
        "flotte_S3": {"courbe": curve, "recommandation": reco},
    }
    with open(os.path.join(out_dir, "resultats.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # --- Cartes interactives ------------------------------------------------
    if write_maps:
        from src.viz import edge_geometries, sector_map
        geoms = edge_geometries(G)
        # Carte du réseau (priorités + services essentiels + POI).
        m0 = sector_map(G, routes=None, geoms=geoms, pois=pois)
        m0.save(os.path.join(out_dir, "carte_reseau.html"))
        # Carte des tournées (S3, flotte recommandée, animée, flocons).
        vehicles = split_route(G, route_s3, reco["n_vehicules"], depot=depot, passes=passes_s3)
        m1 = sector_map(G, routes=vehicles, geoms=geoms, animate=True,
                        speed_kmh=SPEED_KMH, pois=pois)
        m1.save(os.path.join(out_dir, "carte_tournees_S3.html"))
        print(f"  Cartes : {os.path.relpath(out_dir, ROOT)}/carte_*.html")

    return {"key": key, "label": label, "summ": summ, "breakdown": breakdown,
            "scen": scen_results, "curve": curve, "reco": reco,
            "route_s3": route_s3, "depot": depot, "G": G}


def generer_figures(analyses):
    """Figures du rapport à partir des analyses de secteurs."""
    from src import figures as F
    os.makedirs(FIG_DIR, exist_ok=True)

    # Vue d'ensemble de la voirie par secteur.
    rows = [{"label": a["label"].split("–")[0][:12], "axes": a["breakdown"]["axes_structurants_km"],
             "collectrices": a["breakdown"]["voies_collectrices_km"],
             "locale": a["breakdown"]["desserte_locale_km"]} for a in analyses]
    F.fig_voirie_overview(rows, os.path.join(FIG_DIR, "voirie_par_secteur.png"))

    for a in analyses:
        key = a["key"]
        # Courbe coût = f(nb véhicules).
        F.fig_cost_curve(a["curve"], os.path.join(FIG_DIR, f"cout_vehicules_{key}.png"),
                         title=f"Coût et temps — {a['label']} (scénario S3)")
        # Compromis entre scénarios.
        comp = []
        for sk in SCENARIOS:
            r = a["scen"][sk]; cl = r["clearing"]
            comp.append({"scenario": sk, "nom": SCENARIOS[sk]["nom"],
                         "cout": r["cost_1vehicule"]["total"],
                         "t_essentiels": cl["services_essentiels"]["h"] or 0.0,
                         "t_fin": cl["fin_totale"]["h"] or 0.0})
        F.fig_scenario_tradeoff(comp, os.path.join(FIG_DIR, f"compromis_{key}.png"),
                                title=f"Compromis entre scénarios — {a['label']}")
        # Carte statique d'illustration (tournée S3).
        F.fig_sector_map(a["G"], a["route_s3"], os.path.join(FIG_DIR, f"carte_{key}.png"),
                         title=f"{a['label']} — tournée (scénario S3)")
    print(f"\nFigures écrites dans {os.path.relpath(FIG_DIR, ROOT)}/")


def generer_synthese(analyses):
    """Synthèse comparative inter-secteurs (JSON + tableau console)."""
    os.makedirs(RES_DIR, exist_ok=True)
    synth = []
    for a in analyses:
        row = {"secteur": a["label"], "voirie_km": a["summ"]["longueur_totale_km"]}
        for sk in SCENARIOS:
            r = a["scen"][sk]
            row[f"{sk}_km"] = round(r["stats"]["total_km"], 1)
            row[f"{sk}_cout1"] = round(r["cost_1vehicule"]["total"])
        row["flotte_reco"] = a["reco"]["n_vehicules"]
        row["cout_flotte"] = a["reco"]["cout_total"]
        synth.append(row)
    with open(os.path.join(RES_DIR, "synthese.json"), "w", encoding="utf-8") as f:
        json.dump(synth, f, ensure_ascii=False, indent=2)

    print("\n================= SYNTHÈSE INTER-SECTEURS =================")
    print(f"{'Secteur':<28}{'Voirie':>8}{'S3 km':>8}{'S3 $':>8}{'Flotte':>8}{'Coût flotte':>13}")
    for r in synth:
        print(f"{r['secteur'][:27]:<28}{r['voirie_km']:>8.0f}{r['S3_km']:>8.0f}"
              f"{r['S3_cout1']:>8.0f}{r['flotte_reco']:>8}{r['cout_flotte']:>13.0f}")
    print(f"\nSynthèse écrite dans {os.path.relpath(RES_DIR, ROOT)}/synthese.json")


def main():
    ap = argparse.ArgumentParser(description="Démonstration déneigement Montréal (ERO1)")
    ap.add_argument("--secteur", choices=list(SECTORS), help="un seul secteur")
    ap.add_argument("--quick", action="store_true", help="uniquement Outremont")
    ap.add_argument("--no-cartes", action="store_true", help="ne pas écrire les cartes HTML")
    ap.add_argument("--no-figures", action="store_true", help="ne pas générer les figures")
    args = ap.parse_args()

    if args.quick:
        keys = ["outremont"]
    elif args.secteur:
        keys = [args.secteur]
    else:
        keys = list(SECTORS)

    print("Démonstration — optimisation des tournées de déneigement de Montréal")
    print(f"Secteurs : {', '.join(SECTORS[k]['label'] for k in keys)}")

    analyses = [analyse_secteur(k, write_maps=not args.no_cartes) for k in keys]
    if not args.no_figures:
        generer_figures(analyses)
    generer_synthese(analyses)
    print("\nTerminé. Voir secteurs/<nom>/ (résultats + cartes) et rapport/figures/.")


if __name__ == "__main__":
    main()
