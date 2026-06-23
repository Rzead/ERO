# Optimisation hivernale : tournées de déneigement à Montréal

**Auteurs :** Projet ERO1 — Groupe 10 (APPING1)

> **Résumé**
> 
>  Nous optimisons les tournées des déneigeuses sur quatre arrondissements de
> Montréal (Outremont, Verdun, Anjou, Rivière-des-Prairies–Pointe-aux-Trembles).
> Le réseau routier est modélisé comme un graphe orienté ; déneiger toutes les
> rues à coût minimal est le *problème du postier chinois dirigé*, que nous
> résolvons par un *flot à coût minimum* suivi de l'extraction d'un circuit
> eulérien. Nous comparons trois scénarios de priorisation (axes structurants,
> services essentiels, coût minimal) au moyen d'indicateurs génériques et
> spécifiques, et nous en analysons l'impact à l'aide d'une matrice éthique.

# Formalisation et méthode de résolution

## Données, périmètre et contraintes

**Données.** Le réseau routier carrossable de chaque arrondissement provient
d'OpenStreetMap (extraction via `osmnx`, type `drive`). Chaque
tronçon de rue porte sa longueur (en mètres) et son type fonctionnel
(`highway`). Les points d'intérêt sensibles (hôpitaux, écoles, casernes,
arrêts de transport) sont également extraits d'OpenStreetMap. Les paramètres
économiques sont ceux fournis par la municipalité (Tab. [tab:donnees]).

| Coût fixe | 500 $/jour | Coût horaire ($\leq 8$ h) | 1,1 $/h |
| --- | --- | --- | --- |
| Coût kilométrique | 1,1 $/km | Coût horaire ($>8$ h) | 1,3 $/h |
| Vitesse moyenne | 10 km/h | Seuil heures sup. | 8 h |

*Table : Données municipales utilisées (par déneigeuse).*

**Périmètre et contraintes retenues.** (i) *Couverture totale* : toute
rue du secteur doit être déneigée au moins une fois. (ii) *Sens de
circulation* : les rues à sens unique sont des arcs orientés ; le code de la
route est respecté (pas de marche arrière). (iii) *Priorisation* : certains
tronçons sont traités avant d'autres selon le scénario. (iv) *Coût et
durée* : on intègre le seuil d'heures supplémentaires (8 h) et la vitesse
moyenne. **Hors périmètre** (hypothèses simplificatrices) : on ne modélise
ni l'épandage de sel, ni le chargement/évacuation de la neige, ni la congestion
variable, ni la largeur des voies ; une déneigeuse traite une voie par passage.

## Hypothèses de modélisation

- Une rue est *déneigée* dès le premier passage de la déneigeuse (elle
dégage la voie en roulant) ; les passages suivants sont des déplacements
« à vide » (*deadhead*).

- Vitesse constante (10 km/h) : la durée est proportionnelle à la distance.

- Les déneigeuses partent et reviennent à un même dépôt ; elles sont
identiques.

- Le réseau de chaque secteur est ramené à sa plus grande composante
fortement connexe (garantit l'existence d'un circuit), ce qui couvre la quasi
totalité de la voirie.

## Formalisation : du postier chinois au flot à coût minimum

On modélise le secteur par un graphe orienté $G=(V,A)$ où $V$ est l'ensemble des
intersections et $A$ l'ensemble des tronçons de rue ; chaque arc $a=(i,j)$ a une
longueur $w_a>0$. Déneiger toute la ville à distance minimale revient à trouver
un **parcours fermé empruntant chaque arc au moins une fois**, de longueur
totale minimale : c'est le *postier chinois dirigé* [edmonds1973].

Un graphe orienté connexe admet un **circuit eulérien** (passant une et une
seule fois par chaque arc) si et seulement si, en chaque nœud, le degré entrant
égale le degré sortant. Notre graphe ne vérifie pas cette propriété : il faut
*ajouter* le minimum de passages supplémentaires pour rééquilibrer les
degrés. Soit $x_a\in\mathbb{N}$ le nombre de passages *supplémentaires* sur
l'arc $a$ (l'arc est parcouru $1+x_a$ fois). En notant $\delta^+(i)$ et
$\delta^-(i)$ les arcs sortant/entrant de $i$, le problème s'écrit :

$$
\min_{x\ge 0}\ \sum_{a\in A} w_a  x_a
\quad\text{s.c.}\quad
\sum_{a\in\delta^-(i)} x_a-\!\!\sum_{a\in\delta^+(i)} x_a = b_i\ \ \forall i\in V,
\qquad b_i=\deg^+(i)-\deg^-(i).

$$

Le terme $b_i$ est le *déséquilibre* du nœud $i$. Le programme
\eqref{eq:mcf} est exactement un **problème de flot à coût minimum** (vu en
cours) : on « expédie » des passages supplémentaires des nœuds en excès de
sortie vers les nœuds en excès d'entrée, au coût de la longueur des rues
empruntées. Comme $\sum_i b_i=0$ et que les $b_i$ sont entiers, la solution est
entière. Le multigraphe formé des rues (une fois) et des $x_a$ duplications est
alors eulérien : on en extrait un circuit par l'algorithme de Hierholzer.

## Méthode retenue et alternatives

Le tableau [tab:methodes] résume les méthodes envisagées. Nous retenons la
réduction **flot à coût minimum + circuit eulérien** : elle est
*exacte* pour le postier chinois dirigé, s'appuie directement sur les
outils du cours, et passe à l'échelle (résolution $<1$ s sur
Rivière-des-Prairies, 5 191 arcs).

| Méthode | Adéquation | Décision |
| --- | --- | --- |
| Plus court chemin (Dijkstra) | relie deux points | insuffisant : ne couvre pas *toutes* les rues |
| Voyageur de commerce (TSP) | visite des *sommets* | inadapté : on couvre des *arcs*, pas des nœuds ; NP-difficile |
| **Postier chinois dirigé via flot à coût min.** | couvre tous les arcs, sens uniques | **retenue** : exacte, alignée au cours, rapide |
| Postier rural dirigé | couvre un *sous-ensemble* d'arcs | retenue pour les passes prioritaires (S1, S2) |

*Table : Recherche et choix de la méthode de résolution au vu du contexte.*

Pour les scénarios priorisés, on couvre d'abord un sous-ensemble de rues : c'est
le *postier rural dirigé*, résolu par la même mécanique (connexion des
composantes par plus courts chemins, rééquilibrage par flot à coût minimum,
circuit eulérien). Pour la **flotte** de $k$ véhicules, on applique une
heuristique « route d'abord, découpe ensuite » : la tournée d'un véhicule est
découpée en $k$ tronçons de longueur égale, chacun relié au dépôt par un plus
court chemin.

## Indicateurs génériques

Pour toute solution : distance totale parcourue (km), part de déplacements à vide
(%), durée et coût total ($), et *temps de remise en service* d'une classe
de rue = instant où le dernier tronçon de cette classe est déneigé.

## Limites du modèle

La vitesse constante ignore la congestion et la météo ; le découpage de flotte
est heuristique (borne supérieure, non optimale) ; les passes prioritaires
engendrent des déplacements à vide importants (cf. §3) ; un seul dépôt est
considéré ; le déneigement est supposé instantané au passage (pas de file
d'attente de chargement). Ces limites sont acceptables pour comparer des
*scénarios* à l'échelle d'une journée type.

# Trois scénarios de priorisation

Les trois scénarios traitent l'**intégralité** de la voirie ; ils diffèrent
par l'*ordre* de traitement. La priorisation repose sur la classification
fonctionnelle des rues (axes structurants, voies collectrices, desserte locale)
et sur la proximité des services essentiels.

**S1 — Axes d'abord (fluidité du trafic).**
 On déneige d'abord les axes
structurants, puis les collectrices, puis la desserte locale. *Argumentaire*
: la politique réelle de la Ville de Montréal traite en priorité le réseau
artériel et les circuits d'autobus pour éviter la paralysie économique [vdm,new18].
*Bénéfices / cibles* : automobilistes, transport collectif, activité
économique ; remise en circulation rapide des grands axes. *Risques* :
les rues résidentielles et certains services restent enneigés longtemps ;
déplacements à vide accrus. *Indicateur* : temps de remise en service des
axes structurants.

**S2 — Services essentiels (sécurité et accès).**
 On déneige d'abord les
rues bordant hôpitaux, écoles, casernes et arrêts de transport. *Argumentaire*
: l'accès des secours et des populations vulnérables est un objectif de sécurité
publique reconnu [vdm]. *Bénéfices / cibles* : patients, élèves,
personnes à mobilité réduite, services d'urgence. *Risques* : services
dispersés $\Rightarrow$ déplacements à vide très élevés et coût accru ; le reste
du réseau est déneigé tardivement. *Indicateur* : temps de remise en service
des rues « services essentiels ».

**S3 — Coût minimal (référence budgétaire).**
 Aucune priorité : on
minimise directement la distance (postier chinois pur). *Argumentaire* : la
pression budgétaire sur le déneigement est un enjeu récurrent à Montréal [lef19,vezina20].
*Bénéfices / cibles* : contribuables, équilibre du budget municipal.
*Risques* : aucune garantie de service pour les axes ni les services
sensibles ; équité non prise en compte. *Indicateur* : coût total et
distance à vide.

## Analyse d'impact : matrice éthique

La matrice éthique [mepham2006] croise les parties prenantes et trois
familles de valeurs : *bien-être* (utilitarisme), *autonomie*
(déontologie) et *justice* (équité). Le tableau [tab:ethique] fait
apparaître les tensions propres à chaque scénario.

| Partie prenante | Bien-être | Autonomie | Justice |
| --- | --- | --- | --- |
| Automobilistes / éco. | **S1+** axes dégagés vite ; **S2/S3$-$** trafic ralenti | S1 favorise la mobilité motorisée | S1 avantage le transit au détriment du local |
| Riverains résidentiels | **S1/S2$-$** rues locales déneigées en dernier | subissent l'ordre choisi sans consultation | **S3$+$** traite tout le monde « pareil », mais tard |
| Pop. vulnérables / secours | **S2+** accès hôpitaux/écoles prioritaire | meilleure capacité d'accès aux soins | **S2+** corrige une inégalité d'accès |
| Municipalité / contribuables | **S3+** coût minimal ; **S2$-$** coût élevé | marge budgétaire préservée (S3) | arbitrage coût/équité à assumer |

*Table : Matrice éthique des trois scénarios ($+$ effet favorable, $-$ défavorable).*

# Analyse des résultats

On illustre sur **Anjou** (220,6 km de voirie, seul secteur réunissant les
trois classes de rues), puis on généralise aux quatre secteurs.

|  | Dist. | À vide | Coût/véh | Axes | Essentiels | Fin |
| --- | --- | --- | --- | --- | --- | --- |
| Scénario (Anjou) | (km) | (%) | ($) | dégagés | dégagés | secteur |
| S1 — Axes d'abord | 362 | 64 | 944 | **3,6 h** | 35,6 h | 35,7 h |
| S2 — Services essentiels | 400 | 81 | 990 | 39,8 h | **16,4 h** | 39,8 h |
| S3 — Coût minimal | **265** | **20** | **824** | 26,4 h | 26,4 h | **26,4 h** |

*Table : Indicateurs génériques et spécifiques (Anjou, 1 véhicule de référence).*

**Lecture (Tab. [tab:anjou], Fig. [fig:compromis]).** S3 minimise le
coût (824 $, seulement 20 % à vide) mais ne dégage rien en avance : tout est
traité à 26,4 h. S1 dégage les axes en **3,6 h** (dix fois plus vite),
au prix de $+15 %$ de coût et de 64 % de déplacements à vide. S2 dégage les
services essentiels en **16,4 h** (contre 26,4 h en S3), mais c'est le
plus coûteux (990 $, 81 % à vide) car les services sont géographiquement
dispersés. Chaque scénario optimise donc une dimension différente : il n'existe
pas de solution dominant les autres.

![À gauche : compromis coût / temps de remise en service par scénario
(Anjou). À droite : coût total et temps de remise en service en fonction du
nombre de déneigeuses (scénario S3). Le temps passe sous 8 h à partir de 4
véhicules.](figures/compromis_anjou.png)
![À gauche : compromis coût / temps de remise en service par scénario
(Anjou). À droite : coût total et temps de remise en service en fonction du
nombre de déneigeuses (scénario S3). Le temps passe sous 8 h à partir de 4
véhicules.](figures/cout_vehicules_anjou.png)

*Figure : À gauche : compromis coût / temps de remise en service par scénario
(Anjou). À droite : coût total et temps de remise en service en fonction du
nombre de déneigeuses (scénario S3). Le temps passe sous 8 h à partir de 4
véhicules.*

**Modèle de coût et dimensionnement de la flotte.** Avec une seule
déneigeuse, le secteur d'Anjou demanderait $\approx 26$ h : irréaliste. La
courbe coût $=f(\text{nombre de véhicules})$ (Fig. [fig:compromis], droite)
montre un coût qui croît linéairement (le coût fixe de 500 $/véhicule domine)
et un temps qui décroît en $1/k$. Le plus petit effectif respectant la borne de
8 h est de **4 véhicules** (7,6 h, 2 353 $/jour). Le
tableau [tab:synthese] étend ce dimensionnement aux quatre secteurs.

| Secteur | Voirie (km) | Tournée S3 (km) | Flotte ($\leq$8 h) | Coût/jour ($) |
| --- | --- | --- | --- | --- |
| Outremont | 70 | 81 | 2 | 1 103 |
| Verdun | 102 | 110 | 2 | 1 145 |
| Anjou | 221 | 265 | 4 | 2 353 |
| Rivière-des-Prairies–P.-a.-T. | 707 | 786 | 13 | 7 634 |
| **Total (4 secteurs)** | **1 100** | **1 242** | **21** | **12 235** |

*Table : Dimensionnement de la flotte par secteur (scénario S3, remise en
service $\leq 8$ h). La part de déplacements à vide reste faible en S3
(8–20 %).*

![À gauche : longueur de voirie par secteur et par classe de priorité.
À droite : réseau d'Anjou coloré par priorité (rouge = axes, orange =
collectrices, bleu = desserte locale) avec la tournée du scénario S3.](figures/voirie_par_secteur.png)
![À gauche : longueur de voirie par secteur et par classe de priorité.
À droite : réseau d'Anjou coloré par priorité (rouge = axes, orange =
collectrices, bleu = desserte locale) avec la tournée du scénario S3.](figures/carte_anjou.png)

*Figure : À gauche : longueur de voirie par secteur et par classe de priorité.
À droite : réseau d'Anjou coloré par priorité (rouge = axes, orange =
collectrices, bleu = desserte locale) avec la tournée du scénario S3.*

## Projection des effets réels sur les habitants

**S1 (axes d'abord).** *Positif* : remise en circulation rapide des
grands axes et des lignes de bus — l'activité économique et les déplacements
pendulaires reprennent vite ; les véhicules d'urgence circulent mieux sur le
réseau structurant. *Négatif* : les rues résidentielles restent enneigées
très longtemps (desserte locale dégagée en dernier) et, paradoxalement, les
abords de certains services (écoles de quartier) attendent ; injustice spatiale
au détriment des quartiers purement résidentiels.

**S2 (services essentiels).** *Positif* : un patient, un élève ou une
personne à mobilité réduite accède aux services et aux secours nettement plus
tôt (16 h contre 26 h) ; gain d'équité et de sécurité. *Négatif* : le coût
le plus élevé (jusqu'à 81 % de déplacements à vide) pèse sur le budget, et le
reste du réseau est déneigé tardivement — la majorité des usagers « ordinaires »
attend plus longtemps. Le bénéfice se paie en argent public et en délai pour le
plus grand nombre.

**S3 (coût minimal).** *Positif* : déneigement le moins cher, le plus
sobre (moins de kilomètres parcourus, donc moins d'émissions et d'usure) ;
traitement « égalitaire » de toutes les rues. *Négatif* : aucune garantie
de service — un axe vital ou l'accès à un hôpital peut n'être dégagé qu'en toute
fin de tournée ; en cas d'épisode intense, le risque sanitaire et économique
n'est pas maîtrisé.

## Critique et recommandation

Aucun scénario n'est globalement supérieur : S3 est *efficient* mais
*aveugle au service*, S1 sert la mobilité mais néglige l'équité, S2 sert
l'équité mais coûte cher et retarde la majorité. En pratique, une politique
*hybride* — services essentiels et axes structurants en première vague,
puis desserte locale au coût minimal — combinerait l'essentiel des bénéfices ;
notre outil permet d'en chiffrer le compromis. La forte part de déplacements à
vide des scénarios priorisés (heuristique de postier rural) constitue une borne
supérieure : un solveur de tournées plus fin la réduirait, ce qui resserrerait
l'écart de coût avec S3 sans changer l'ordre des conclusions.

## Références

- **[edmonds1973]** J. Edmonds, E. L. Johnson. *Matching, Euler tours and
the Chinese postman*. Mathematical Programming, 1973.
- **[eiselt1995]** H. A. Eiselt, M. Gendreau, G. Laporte. *Arc routing
problems*. Operations Research, 1995.
- **[vdm]** Ville de Montréal. *Tout savoir sur le déneigement dans
l'arrondissement*. Opération déneigement.
- **[new18]** CBC News. *How Montreal takes 300 000 truckloads of snow
off the street every winter*, 2018.
- **[lef19]** S.-M. Lefebvre. *Les prix du déneigement explosent partout
au Québec*. Journal de Montréal, 2019.
- **[vezina20]** H. Ouellette Vézina. *Déneigement : « on craint toujours
de dépasser le budget »*. Métro, 2020.
- **[mepham2006]** B. Mepham, M. Kaiser, E. Bjørnerud, S. Tomkins.
*Ethical Matrix Manual*, 2006.
