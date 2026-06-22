# Optimisation hivernale — déneigement de Montréal (projet ERO1)

Optimisation des tournées des déneigeuses sur quatre arrondissements de
Montréal (Outremont, Verdun, Anjou, Rivière-des-Prairies–Pointe-aux-Trembles).
On modélise le réseau routier comme un graphe orienté (les sens uniques
comptent) et on cherche à **parcourir toutes les rues à coût minimal** — c'est
le problème du **postier chinois dirigé**, résolu via un **flot à coût
minimum** puis l'extraction d'un **circuit eulérien**. Trois scénarios de
priorisation sont comparés, et un modèle de coût dimensionne la flotte.

## Installation

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate      |  Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10+ recommandé (testé avec 3.12). La première exécution télécharge les
données OpenStreetMap ; elles sont ensuite **mises en cache** dans `data/`
(les fichiers `*.graphml` fournis permettent de travailler **hors ligne**).

## Démonstration (script)

```bash
python demo.py              # les 4 secteurs : résultats + cartes + figures
python demo.py --quick      # uniquement Outremont (rapide)
python demo.py --secteur verdun
python demo.py --no-cartes  # sans les cartes HTML (plus rapide)
```

La démonstration écrit, pour chaque secteur, dans `secteurs/<nom>/` :
`resultats.json` (statistiques, coûts, indicateurs de remise en service,
dimensionnement de flotte), `carte_reseau.html` et `carte_tournees_S3.html`
(cartes interactives). Les figures du rapport vont dans `rapport/figures/`, et
la synthèse inter-secteurs dans `resultats/synthese.json`.

## Application interactive

```bash
streamlit run app/streamlit_app.py
```

Choix du secteur, du scénario et du nombre de déneigeuses ; carte interactive
avec **animation des trajets**, indicateurs, courbe coût = f(nombre de
véhicules) et comparaison des trois scénarios.

## Structure du rendu

```
deneigement-montreal/
├── AUTHORS                 Liste des auteurs
├── README.md               Ce fichier
├── requirements.txt        Dépendances Python
├── demo.py                 Script de démonstration
├── src/                    Code source
│   ├── io_osm.py           Chargement OSM (osmnx) + cache
│   ├── cpp.py              Postier chinois / rural dirigé (flot min + Euler)
│   ├── cost.py             Modèle de coût (données municipales)
│   ├── priorities.py       Classes de priorité + services essentiels
│   ├── scenarios.py        Les trois scénarios de priorisation
│   ├── fleet.py            Découpage en flotte + coût = f(nb véhicules)
│   ├── viz.py              Cartes Folium (priorités + animation)
│   └── figures.py          Figures matplotlib pour le rapport
├── app/streamlit_app.py    Application interactive
├── data/                   Graphes OSM en cache (*.graphml) + POI
├── secteurs/<nom>/         Étude du parcours par secteur (résultats + cartes)
├── resultats/              Synthèse inter-secteurs
├── tests/                  Tests unitaires
└── rapport/                Rapport LaTeX + figures
```

## Méthode (résumé)

1. **Modélisation** : réseau routier carrossable d'OpenStreetMap → graphe
   orienté `MultiDiGraph` (arc = tronçon de rue, attribut `length` en mètres),
   réduit à sa plus grande composante fortement connexe.
2. **Postier chinois dirigé** : un circuit eulérien existe ssi chaque nœud a
   degré entrant = degré sortant. On calcule le déséquilibre des degrés, puis
   on ajoute le minimum de passages supplémentaires par un **flot à coût
   minimum** (cf. cours « Algos RO »). Le multigraphe devient eulérien et on en
   extrait un circuit (Hierholzer).
3. **Scénarios** (S1 axes / S2 services essentiels / S3 coût minimal) : traités
   par passes successives via le **postier rural dirigé** (généralisation
   couvrant un sous-ensemble de rues requises).
4. **Coût et flotte** : modèle de coût municipal (fixe, kilométrique, horaire
   avec seuil 8 h) ; découpage « route d'abord, découpe ensuite » pour
   répartir la tournée entre `k` véhicules et tracer `coût = f(k)`.

## Tests

```bash
python -m pytest tests/ -q
```
