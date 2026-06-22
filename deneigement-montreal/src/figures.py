"""Figures matplotlib pour le rapport (backend Agg, sans affichage).

Génère des PNG : carte statique d'un secteur coloré par priorité avec la
tournée, courbe coût = f(nb véhicules), compromis entre scénarios, et vue
d'ensemble de la voirie par secteur.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from .priorities import PRIORITY_LABELS  # noqa: E402

PRIORITY_COLORS = {1: "#d7191c", 2: "#fdae61", 3: "#5e8fb8"}


def fig_sector_map(G, route, path, title="", geoms=None):
    """Carte statique : réseau coloré par priorité + tournée (en gris foncé)."""
    from .viz import edge_geometries, _coords_for
    if geoms is None:
        geoms = edge_geometries(G)
    fig, ax = plt.subplots(figsize=(7, 7))
    for u, v, k, data in G.edges(keys=True, data=True):
        coords = _coords_for(G, u, v, k, geoms)
        xs = [lon for lat, lon in coords]
        ys = [lat for lat, lon in coords]
        ax.plot(xs, ys, color=PRIORITY_COLORS[data.get("priority", 3)],
                linewidth=0.8, alpha=0.6, zorder=1)
    if route:
        rx, ry = [], []
        for u, v, d in route:
            coords = _coords_for(G, u, v, d.get("original_key"), geoms)
            rx.extend([lon for lat, lon in coords] + [None])
            ry.extend([lat for lat, lon in coords] + [None])
        ax.plot(rx, ry, color="#222222", linewidth=0.5, alpha=0.5, zorder=2)
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.axis("off")
    legend = [Line2D([0], [0], color=PRIORITY_COLORS[p], lw=2, label=PRIORITY_LABELS[p])
              for p in (1, 2, 3)]
    ax.legend(handles=legend, loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig_cost_curve(rows, path, title="Coût et temps en fonction du nombre de véhicules"):
    """Courbe coût total et temps de remise en service vs nombre de véhicules."""
    ks = [r["n_vehicules"] for r in rows]
    cost = [r["cout_total"] for r in rows]
    time = [r["temps_remise_service_h"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6.5, 4))
    ax1.plot(ks, cost, "o-", color="#1b6ca8", label="Coût total ($)")
    ax1.set_xlabel("Nombre de déneigeuses")
    ax1.set_ylabel("Coût total ($/jour)", color="#1b6ca8")
    ax1.tick_params(axis="y", labelcolor="#1b6ca8")
    ax2 = ax1.twinx()
    ax2.plot(ks, time, "s--", color="#d7191c", label="Temps de remise en service (h)")
    ax2.axhline(8, color="grey", ls=":", lw=1)
    ax2.set_ylabel("Temps de remise en service (h)", color="#d7191c")
    ax2.tick_params(axis="y", labelcolor="#d7191c")
    ax1.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig_scenario_tradeoff(comparison, path, title="Compromis entre scénarios"):
    """Barres : coût (1 véhicule) et temps de remise en service par scénario.

    ``comparison`` : liste de dicts {scenario, nom, cout, t_essentiels, t_fin}.
    """
    labels = [f"{c['scenario']}\n{c['nom']}" for c in comparison]
    cost = [c["cout"] for c in comparison]
    t_ess = [c["t_essentiels"] for c in comparison]
    t_fin = [c["t_fin"] for c in comparison]
    x = range(len(labels))
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar([i - 0.2 for i in x], cost, width=0.4, color="#9ecae1",
            label="Coût (1 véh., $)")
    ax1.set_ylabel("Coût (1 véhicule, $)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, fontsize=8)
    ax2 = ax1.twinx()
    ax2.plot(list(x), t_ess, "o-", color="#1a9641", label="Essentiels déneigés (h)")
    ax2.plot(list(x), t_fin, "s--", color="#d7191c", label="Fin secteur (h)")
    ax2.set_ylabel("Temps (h)")
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lab1 + lab2, fontsize=8, loc="upper center")
    ax1.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig_voirie_overview(sector_rows, path, title="Voirie par secteur et par priorité"):
    """Barres empilées : km de voirie par classe de priorité et par secteur.

    ``sector_rows`` : liste de dicts {label, axes, collectrices, locale}.
    """
    labels = [r["label"] for r in sector_rows]
    axes_km = [r["axes"] for r in sector_rows]
    coll_km = [r["collectrices"] for r in sector_rows]
    loc_km = [r["locale"] for r in sector_rows]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x, axes_km, color=PRIORITY_COLORS[1], label="Axes structurants")
    ax.bar(x, coll_km, bottom=axes_km, color=PRIORITY_COLORS[2], label="Collectrices")
    bottom2 = [a + c for a, c in zip(axes_km, coll_km)]
    ax.bar(x, loc_km, bottom=bottom2, color=PRIORITY_COLORS[3], label="Desserte locale")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8, rotation=15, ha="right")
    ax.set_ylabel("Longueur de voirie (km)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
