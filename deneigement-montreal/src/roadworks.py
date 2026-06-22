"""Tronçons en travaux : rues fermées à toute circulation.

On retire du réseau un certain nombre de rues (les deux sens), puis on reprend
la plus grande composante fortement connexe : déneigeuses et véhicules doivent
contourner les fermetures, et certaines zones peuvent devenir inaccessibles —
ce que les indicateurs (coût, accessibilité) reflètent ensuite.
"""
from __future__ import annotations

import random

from .cpp import largest_strongly_connected


def apply_roadworks(G, n_blocked: int = 0, seed: int = 0):
    """Ferme ``n_blocked`` rues (tirées aléatoirement, graine ``seed``).

    Renvoie ``(H, blocked_info)`` où ``H`` est le réseau restant (plus grande
    composante fortement connexe) et ``blocked_info`` la liste des arcs fermés
    ``(u, v, k, data)`` (avec leur géométrie d'origine, pour l'affichage).
    """
    if n_blocked <= 0:
        return G.copy(), []

    rng = random.Random(seed)
    candidates = list({(u, v) for u, v in G.edges()})
    rng.shuffle(candidates)

    H = G.copy()
    blocked_info = []
    blocked_pairs = set()
    for (u, v) in candidates:
        if len(blocked_pairs) >= n_blocked:
            break
        if (u, v) in blocked_pairs or (v, u) in blocked_pairs:
            continue
        # Fermer la rue dans les deux sens si elle existe.
        for a, b in [(u, v), (v, u)]:
            if H.has_edge(a, b):
                for k in list(H[a][b]):
                    blocked_info.append((a, b, k, dict(G.get_edge_data(a, b, k))))
                    H.remove_edge(a, b, k)
        blocked_pairs.add((u, v))

    H = largest_strongly_connected(H)
    return H, blocked_info
