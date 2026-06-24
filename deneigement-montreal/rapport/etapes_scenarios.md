| Étape Algorithmique | Scénario 3 (Coût Minimal) | Scénarios 1 & 2 (Axes ou Services Prioritaires) |
| :--- | :--- | :--- |
| **1. Entrée des données** | On prend l'intégralité des arcs du graphe en un seul bloc. | On divise les arcs en deux listes : Prioritaires (P) et Reste du réseau (R). |
| **2. Type de Problème** | Postier Chinois Dirigé (visiter tous les arcs). | Postier Rural Dirigé répété deux fois (visiter un sous-ensemble d'arcs). |
| **3. Connexion (Passe 1)** | — | Connexion des arcs Prioritaires (P) isolés entre eux en utilisant les chemins les plus courts. |
| **4. Équilibrage (Passe 1)** | Calcul des déséquilibres $b_i$ sur tout le graphe. Détermination des passages à vide $x_a$. | Calcul des déséquilibres sur le mini-réseau prioritaire (arcs P + liaisons). Détermination des $x_a$. |
| **5. Extraction Circuit 1** | Création de la Méga-Tournée complète. | Création de la Méga-Tournée prioritaire (Passe 1). |
| **6. Deuxième Passe** | — | Répétition des étapes 3, 4 et 5 sur la liste Reste du réseau (R) pour le déneiger. |
| **7. Assemblage (Méga-tournée)** | — | Concaténation : Tournée Prioritaire + Tournée du Reste du réseau. |
| **8. Division de la flotte** | On découpe la Méga-Tournée complète en $k$ tronçons égaux. | On découpe la Méga-Tournée assemblée en $k$ tronçons égaux. |
| **9. Connexion au Dépôt** | On relie le Dépôt au début et à la fin de chaque tronçon de déneigeuse. | On relie le Dépôt au début et à la fin de chaque tronçon de déneigeuse. |