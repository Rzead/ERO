# ERO1 — Optimisation Hivernale (Déneigement de Montréal)

Projet EPITA APPING1 — Groupe 10

Optimisation des tournées de véhicules de déneigement sur quatre arrondissements de Montréal via le **Problème du Postier Chinois Dirigé** (CPP).

## Arrondissements étudiés

- Outremont
- Verdun
- Anjou
- Rivière-des-Prairies–Pointe-aux-Trembles

## Approche

1. Modélisation du réseau routier en graphe orienté (OpenStreetMap via `osmnx`)
2. Résolution du déséquilibre de degrés par flot de coût minimum
3. Extraction d'un circuit eulérien sur le multigraphe équilibré
4. Comparaison de trois scénarios de priorisation des rues
5. Modèle de coût municipal (tarifs fixes, kilométriques et horaires)
6. Dimensionnement optimal de la flotte de véhicules

## Scénarios

| Scénario | Description |
|----------|-------------|
| S1 | Priorisation des axes principaux |
| S2 | Services essentiels en premier (hôpitaux, urgences) |
| S3 | Optimisation du coût minimal |

## Stack technique

- Python 3.10+
- `networkx`, `osmnx`, `scipy` — algorithmes de graphes et optimisation
- `streamlit`, `folium` — application interactive et cartes
- `geopandas`, `shapely` — données géospatiales

## Structure

```
deneigement-montreal/   # Implémentation principale
sujet/                  # Documents du projet (PDFs)
```

## Lancement

```bash
cd deneigement-montreal
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
