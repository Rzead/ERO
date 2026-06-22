"""Application Streamlit — simulation des tournées de déneigement de Montréal.

Lancement :  streamlit run app/streamlit_app.py

On configure la simulation (secteur, scénario, nombre de déneigeuses, tronçons
en travaux) puis on lance le calcul. L'application affiche une carte interactive
(réseau, services essentiels, travaux, déneigeuses animées en flocons),
les indicateurs (coût, remise en service, accessibilité de la population aux
services essentiels) et permet d'exporter les traces GPS des véhicules.
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.io_osm import SECTORS, load_sector, load_pois, graph_summary  # noqa: E402
from src.priorities import annotate_priorities, annotate_essential  # noqa: E402
from src.scenarios import SCENARIOS, evaluate_scenario  # noqa: E402
from src.simulate import run_simulation  # noqa: E402
from src.exports import build_export_zip  # noqa: E402
from src.viz import edge_geometries, sector_map  # noqa: E402
from src.cost import SPEED_KMH  # noqa: E402

st.set_page_config(page_title="Déneigement Montréal — ERO1", layout="wide",
                   page_icon="❄️")


# --- Calculs mis en cache ---------------------------------------------------

@st.cache_resource(show_spinner="Chargement du secteur (OpenStreetMap)…")
def get_sector(key):
    G = load_sector(key)
    annotate_priorities(G)
    pois = load_pois(key)
    annotate_essential(G, pois)
    geoms = edge_geometries(G)
    return G, geoms, pois


@st.cache_resource(show_spinner="Calcul de la simulation…")
def compute(sector, scenario, n_veh, n_blocked, seed):
    G, geoms, pois = get_sector(sector)
    sim = run_simulation(G, pois, scenario, n_veh, n_blocked, seed)
    return sim, geoms, pois


@st.cache_resource(show_spinner="Construction de la carte…")
def build_map(sector, scenario, n_veh, n_blocked, seed, animate, base_style):
    sim, geoms, pois = compute(sector, scenario, n_veh, n_blocked, seed)
    return sector_map(sim["graph"], routes=sim["vehicles"], geoms=geoms,
                      animate=animate, speed_kmh=SPEED_KMH, pois=pois,
                      blocked=sim["blocked"], base_style=base_style)


@st.cache_data(show_spinner=False)
def export_zip(sector, scenario, n_veh, n_blocked, seed):
    sim, geoms, _ = compute(sector, scenario, n_veh, n_blocked, seed)
    meta = {"secteur": SECTORS[sector]["label"], "scenario": scenario,
            "nom_scenario": SCENARIOS[scenario]["nom"], "n_vehicules": n_veh,
            "troncons_fermes": sim["n_blocked_streets"],
            "cout_total": sim["fleet"]["cout_total"],
            "temps_remise_service_h": sim["fleet"]["temps_remise_service_h"],
            "accessibilite_finale_pct": sim["accessibility"]["final_pct"]}
    return build_export_zip(sim["graph"], sim["vehicles"], geoms,
                            sim["distances_km"], meta)


@st.cache_data(show_spinner=False)
def compare_scenarios(sector, n_blocked, seed):
    rows = []
    for sk in SCENARIOS:
        sim, _, _ = compute(sector, sk, 1, n_blocked, seed)
        r = sim["result"]
        cl = r["clearing"]
        a = sim["accessibility"]
        rows.append({
            "Scénario": f"{sk} — {SCENARIOS[sk]['nom']}",
            "Distance (km)": round(r["stats"]["total_km"], 1),
            "À vide (%)": round(100 * r["stats"]["deadhead_ratio"]),
            "Coût 1 véh. ($)": round(r["cost_1vehicule"]["total"]),
            "Essentiels déneigés": fmt_h(cl["services_essentiels"]),
            "90 % accessible": ("—" if a["t_90"] is None else f"{a['t_90']:.1f} h"),
            "Fin secteur": fmt_h(cl["fin_totale"]),
        })
    return rows


def fmt_h(d):
    return "—" if d.get("h") is None else f"{d['h']:.1f} h"


# Explication courte du scénario sélectionné (toujours affichée).
SCENARIO_HELP = {
    "S1": "**S1 — Axes d'abord** : on déneige d'abord les grands axes et les voies "
          "collectrices, puis la desserte locale. ✅ Trafic et bus rétablis vite. "
          "⚠️ Rues résidentielles déneigées tard, coût un peu plus élevé.",
    "S2": "**S2 — Services essentiels** : on déneige d'abord les rues des hôpitaux, "
          "écoles, casernes et arrêts de transport. ✅ Accès aux soins et sécurité "
          "prioritaires. ⚠️ Services dispersés → beaucoup de trajets à vide, scénario "
          "le plus coûteux, reste du réseau déneigé tard.",
    "S3": "**S3 — Coût minimal** : aucune priorité, on minimise la distance totale "
          "(postier chinois pur). ✅ Le moins cher et le plus sobre. ⚠️ Aucune "
          "garantie de service : un axe ou un hôpital peut être déneigé en dernier.",
}

# Explications détaillées (dépliable).
EXPLAIN_MD = """
### Les trois scénarios de priorisation
Tous **déneigent l'intégralité** des rues du secteur ; ils diffèrent par **l'ordre** :
- **S1 — Axes d'abord** : priorité aux axes structurants puis collectrices (fluidité du trafic, circuits de bus, véhicules d'urgence).
- **S2 — Services essentiels** : priorité aux rues bordant hôpitaux, écoles, casernes, transport (sécurité et accès des plus vulnérables).
- **S3 — Coût minimal** : aucune priorité, distance minimale (référence économique).

Aucun n'est globalement meilleur : c'est un **compromis** entre coût, fluidité et équité d'accès.

### Les indicateurs
- **Voirie active** : longueur de rues à déneiger (diminue si des tronçons sont en travaux).
- **Coût total / jour** : coût de la flotte = coût fixe (500 \\$/véhicule) + kilométrage (1,1 \\$/km) + heures (1,1 \\$/h, puis 1,3 \\$/h au-delà de 8 h).
- **Remise en service** : temps pour que la dernière rue soit déneigée (les véhicules travaillent en parallèle).
- **Accès services essentiels** : part de la population (proxy de densité résidentielle) pouvant rejoindre un service essentiel **par des rues déjà déneigées**. La courbe montre sa progression dans le temps (temps pour 50 % et 90 %).

### Lire la carte
- **Couleurs des rues** : rouge = axe structurant · orange = voie collectrice · bleu = desserte locale.
- **Marqueurs** (cliquables, regroupés en pastilles) = services essentiels : 🏥 santé, 🎓 éducation, 🚒 caserne, 🛡 police, 🚌 transport.
- **Flocons ❄** = position des déneigeuses ; faites glisser le **curseur de temps** (en bas) ou appuyez sur ▶ pour rejouer la tournée.
- **Rouge hachuré ⚠** = tronçons en travaux (fermés).
- Outils : plein écran, mesure de distance, choix du fond de carte, activation des couches (icône en haut à droite).

### Tronçons en travaux
Le curseur **« Tronçons en travaux »** ferme des rues (dans les deux sens) : le réseau et les tournées sont **recalculés** en conséquence (contournements, coût, accessibilité).

### Export
Le bouton **« Exporter les traces GPS »** produit un ZIP : une **trace `.gpx` horodatée par déneigeuse**, un **CSV** de statistiques, un **GeoJSON** des tournées et un **résumé JSON**.
"""


# --- Barre latérale : configuration -----------------------------------------

st.sidebar.title("❄️ Déneigement Montréal")
st.sidebar.caption("Projet ERO1 — optimisation hivernale")

with st.sidebar.form("config"):
    st.markdown("**Configuration**")
    sector_key = st.selectbox("Secteur", list(SECTORS),
                              format_func=lambda k: SECTORS[k]["label"])
    scenario_key = st.selectbox("Scénario de priorisation", list(SCENARIOS),
                                format_func=lambda k: f"{k} — {SCENARIOS[k]['nom']}")
    n_vehicles = st.slider("Nombre de déneigeuses", 1, 15, 3)
    n_blocked = st.slider("Tronçons en travaux (fermés)", 0, 40, 0,
                          help="Rues fermées à toute circulation ; le réseau est recalculé.")
    seed = st.number_input("Graine (travaux)", 0, 9999, 1, step=1)
    base_style = st.selectbox("Fond de carte", ["clair", "sombre", "plan"])
    animate = st.checkbox("Animer les déneigeuses", value=True)
    submitted = st.form_submit_button("▶ Lancer la simulation", use_container_width=True)

if submitted:
    st.session_state["cfg"] = dict(sector=sector_key, scenario=scenario_key,
                                   n_veh=n_vehicles, n_blocked=n_blocked, seed=int(seed),
                                   animate=animate, base_style=base_style)

cfg = st.session_state.get("cfg")
if not cfg:
    st.title("Simulation des tournées de déneigement de Montréal")
    st.info("⬅️ Configurez la simulation dans la barre latérale (secteur, scénario, "
            "nombre de déneigeuses, tronçons en travaux), puis cliquez sur "
            "**« ▶ Lancer la simulation »**.")
    st.markdown("""
    **Ce que fait l'outil :** il modélise le réseau routier en graphe orienté et
    calcule les tournées des déneigeuses (postier chinois dirigé) selon trois
    stratégies de priorisation, en tenant compte d'éventuels tronçons en travaux.
    Il restitue le coût, le temps de remise en service, l'**accessibilité de la
    population aux services essentiels**, et permet d'**exporter les traces GPS**.

    Lisez les explications ci-dessous avant de lancer une simulation.
    """)
    st.markdown(EXPLAIN_MD)
    st.stop()

# --- Exécution --------------------------------------------------------------
sim, geoms, pois = compute(cfg["sector"], cfg["scenario"], cfg["n_veh"],
                           cfg["n_blocked"], cfg["seed"])
H = sim["graph"]
summ = graph_summary(H)
fleet = sim["fleet"]
acc = sim["accessibility"]
cl = sim["result"]["clearing"]

st.title(f"Déneigement — {SECTORS[cfg['sector']]['label']}")
st.caption(f"Scénario **{cfg['scenario']} · {SCENARIOS[cfg['scenario']]['nom']}** · "
           f"{cfg['n_veh']} déneigeuse(s)"
           + (f" · {sim['n_blocked_streets']} tronçon(s) fermé(s)" if sim["n_blocked_streets"] else ""))
st.info(SCENARIO_HELP[cfg["scenario"]])

# --- Indicateurs ------------------------------------------------------------
r1 = st.columns(4)
r1[0].metric("Voirie active", f"{summ['longueur_totale_km']:.0f} km",
             f"{summ['n_arcs']} tronçons")
r1[1].metric("Coût total / jour", f"{fleet['cout_total']:.0f} $",
             f"{cfg['n_veh']} véhicule(s)")
r1[2].metric("Remise en service", f"{fleet['temps_remise_service_h']:.1f} h",
             "⚠️ heures sup." if fleet["heures_sup"] else "≤ 8 h")
r1[3].metric("Accès services essentiels", f"{acc['final_pct']:.0f} %",
             ("90 % à " + (f"{acc['t_90']:.1f} h" if acc["t_90"] else "—")))

# --- Export -----------------------------------------------------------------
zbytes = export_zip(cfg["sector"], cfg["scenario"], cfg["n_veh"],
                    cfg["n_blocked"], cfg["seed"])
st.download_button(
    "⬇️ Exporter les traces GPS des déneigeuses (ZIP : GPX + stats + GeoJSON)",
    data=zbytes,
    file_name=f"tournees_{cfg['sector']}_{cfg['scenario']}_{cfg['n_veh']}veh.zip",
    mime="application/zip", use_container_width=True)

with st.expander("ℹ️ Explications — scénarios, indicateurs et lecture de la carte"):
    st.markdown(EXPLAIN_MD)

# --- Carte (pleine largeur) -------------------------------------------------
st.subheader("Carte interactive")
m = build_map(cfg["sector"], cfg["scenario"], cfg["n_veh"], cfg["n_blocked"],
              cfg["seed"], cfg["animate"], cfg["base_style"])
st_folium(m, height=640, use_container_width=True, returned_objects=[])
st.caption("Flocons ❄ = déneigeuses (faites glisser le curseur de temps en bas, "
           "ou ▶ pour rejouer). Marqueurs = services essentiels (cliquables, "
           "regroupés). Rouge hachuré = travaux. Couches et fond de carte "
           "réglables via les icônes en haut à droite.")

# --- Graphiques (sous la carte) --------------------------------------------
g1, g2 = st.columns(2)
with g1:
    st.subheader("Accessibilité aux services essentiels")
    if acc["curve"]:
        dfa = pd.DataFrame(acc["curve"]).rename(
            columns={"t_h": "heures", "pct": "% population"}).set_index("heures")
        st.line_chart(dfa[["% population"]], height=240)
        st.caption(f"% de la population (proxy de densité résidentielle) pouvant "
                   f"atteindre un service essentiel par les rues déneigées, au fil "
                   f"du temps. 50 % atteint à {acc['t_50']} h · 90 % à {acc['t_90']} h.")
    else:
        st.info("Pas de service essentiel identifié sur ce périmètre.")
with g2:
    st.subheader("Coût et temps = f(nombre de véhicules)")
    dfc = pd.DataFrame(sim["curve"]).set_index("n_vehicules")
    st.line_chart(dfc[["cout_total"]], height=110)
    st.line_chart(dfc[["temps_remise_service_h"]], height=110)
    reco = sim["reco"]
    st.success(f"Pour finir en ≤ 8 h : **{reco['n_vehicules']} véhicules** "
               f"({reco['temps_remise_service_h']} h, {reco['cout_total']:.0f} $).")

# --- Tableaux (sous les graphiques) ----------------------------------------
t1, t2 = st.columns(2)
with t1:
    st.subheader("Remise en service par type de voie")
    st.dataframe(pd.DataFrame([
        {"Type de voie": "Axes structurants", "Déneigé à": fmt_h(cl["axes_structurants"])},
        {"Type de voie": "Voies collectrices", "Déneigé à": fmt_h(cl["voies_collectrices"])},
        {"Type de voie": "Desserte locale", "Déneigé à": fmt_h(cl["desserte_locale"])},
        {"Type de voie": "Services essentiels", "Déneigé à": fmt_h(cl["services_essentiels"])},
        {"Type de voie": "Secteur complet", "Déneigé à": fmt_h(cl["fin_totale"])},
    ]), hide_index=True, width="stretch")
with t2:
    st.subheader("Comparaison des trois scénarios")
    comp = compare_scenarios(cfg["sector"], cfg["n_blocked"], cfg["seed"])
    st.dataframe(pd.DataFrame(comp), hide_index=True, width="stretch")
    st.caption("Indicateurs pour 1 véhicule de référence. Chaque scénario "
               "optimise une dimension différente (coût, fluidité, équité).")
