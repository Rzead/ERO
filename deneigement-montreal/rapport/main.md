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

# Les scénarios de priorisation et leur justification

## Pourquoi ces trois scénarios ?

Déneiger une ville n'est pas qu'un problème technique : c'est une **décision
publique** qui répartit une ressource rare (les heures de déneigeuse) entre des
usagers aux intérêts divergents. Or cette décision est tiraillée par trois
objectifs légitimes mais *inconciliables* simultanément :

- la **fluidité** du trafic et de l'économie (remettre les grands axes
et les circuits de bus en circulation au plus vite) ;

- la **sécurité et l'équité d'accès** (garantir d'abord l'accès aux
hôpitaux, écoles, casernes et aux populations vulnérables) ;

- la **maîtrise budgétaire** (déneiger au moindre coût pour le
contribuable).

Chacun de ces objectifs est défendu par des parties prenantes réelles et
correspond à des arbitrages effectivement débattus à Montréal : la Ville
priorise déjà le réseau artériel et les circuits d'autobus [vdm,new18],
tandis que le coût du déneigement est un enjeu politique récurrent [lef19,vezina20].

Nous avons donc retenu **trois scénarios qui incarnent chacun l'un de ces
objectifs à l'état pur** : S1 (fluidité), S2 (sécurité/équité), S3 (coût). Ils ne
sont pas des recettes à appliquer telles quelles, mais les **sommets du
triangle de décision** : ils bornent l'espace des compromis possibles. Toute
politique réaliste étant une pondération de ces trois extrêmes, comparer les
extrêmes rend visibles, et chiffrables, les tensions qu'un décideur doit
arbitrer (cf. la recommandation hybride, §[sec:reco]). C'est précisément ce
que notre outil permet de mesurer.

## Définition des trois scénarios

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

## Analyse d'impact : une matrice éthique par scénario

Pour évaluer chaque scénario, nous appliquons la *matrice
éthique* [mepham2006], qui croise les **parties prenantes** et trois
familles de valeurs : *bien-être* (utilitarisme : qui gagne/perd en
confort et sécurité ?), *autonomie* (déontologie : respecte-t-on les
choix et droits des personnes ?) et *justice* (équité : la charge et les
bénéfices sont-ils répartis équitablement ?). Une matrice par scénario
(Tab. [tab:ethique_s1]–[tab:ethique_s3]) en révèle les tensions
propres ($+$ effet favorable, $-$ défavorable, $\pm$ ambivalent).

| \multicolumn{4}{l}{**S1 — Axes d'abord** (fluidité du trafic)} |  |  |  |
| --- | --- | --- | --- |
| Partie prenante | Bien-être | Autonomie | Justice |
| Automobilistes / éco. | **$+$** axes dégagés en 3,6 h, trafic et bus rétablis vite | mobilité motorisée préservée | favorisés au détriment des usagers locaux |
| Riverains résidentiels | **$-$** desserte locale déneigée en dernier | subissent l'ordre choisi sans consultation | **$-$** le transit prime sur le quartier |
| Pop. vulnérables / secours | **$\pm$** secours fluides sur les axes, mais services de quartier (écoles) tardifs | accès facilité aux soins via le réseau structurant | **$-$** services de proximité négligés |
| Municipalité / contribuables | **$+$** activité économique préservée | choix politique assumé et lisible | surcoût modéré ($+15 %$) à justifier |

*Table : Matrice éthique du scénario S1.*

| \multicolumn{4}{l}{**S2 — Services essentiels** (sécurité et accès)} |  |  |  |
| --- | --- | --- | --- |
| Partie prenante | Bien-être | Autonomie | Justice |
| Automobilistes / éco. | **$-$** axes dégagés tard (39,8 h), trafic ralenti | mobilité motorisée non prioritaire | transit sacrifié au profit du soin |
| Riverains résidentiels | **$-$** rues locales déneigées très tard | subissent l'ordre choisi | **$\pm$** équité d'accès aux services, mais attente longue chez soi |
| Pop. vulnérables / secours | **$+$** accès soins/écoles prioritaire (16,4 h) | meilleure autonomie d'accès aux soins | **$+$** corrige une inégalité d'accès |
| Municipalité / contribuables | **$-$** scénario le plus coûteux (990 $, 81 % à vide) | engagement de sécurité publique assumé | charge budgétaire au nom de l'équité |

*Table : Matrice éthique du scénario S2.*

| \multicolumn{4}{l}{**S3 — Coût minimal** (référence budgétaire)} |  |  |  |
| --- | --- | --- | --- |
| Partie prenante | Bien-être | Autonomie | Justice |
| Automobilistes / éco. | **$-$** aucun axe priorisé, tout dégagé à 26,4 h | aucune garantie de service | ni privilège ni pénalité |
| Riverains résidentiels | **$\pm$** traités « comme tout le monde », mais tard | aucune priorité subie | **$+$** traitement uniforme de toutes les rues |
| Pop. vulnérables / secours | **$-$** accès aux soins non garanti, possiblement en dernier | risque sanitaire non maîtrisé | **$-$** ignore les besoins différenciés |
| Municipalité / contribuables | **$+$** coût minimal (824 $, 20 % à vide), plus sobre | marge budgétaire préservée | équité non prise en compte, risque reporté |

*Table : Matrice éthique du scénario S3.*

Aucun scénario ne domine les autres sur les trois valeurs : S1 sert le bien-être
des mobilités mais lèse la justice spatiale, S2 sert la justice et la sécurité
mais au prix du bien-être collectif et du budget, S3 préserve le budget mais
abandonne toute garantie de service. Ce constat motive l'analyse chiffrée
(§[sec:resultats]) et la recommandation hybride (§[sec:reco]).

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

Pour les scénarios priorisés (S1, S2), nécessitant plusieurs passes successives, on couvre d'abord un sous-ensemble de rues : c'est le *postier rural dirigé*, résolu par la même mécanique. 

Le déploiement d'une **flotte** de $k$ véhicules sur ces scénarios a fait l'objet d'une optimisation algorithmique spécifique (cf. Tableau [tab:avant_apres]) pour pallier les limites majeures d'une approche de découpage naïve.

|  | **Étape 1 : Découpage naïf global** | **Étape 2 : Découpage par passe (sans opti)** | **Étape 3 : Découpage avec Algorithme Hongrois** |
| --- | --- | --- | --- |
| **Méthode** | Tournée globale découpée aveuglément en $k$. | Découpe de *chaque* passe. Raccordement direct (véhicule $i \to$ tronçon $i$). | Découpe de *chaque* passe. Couplage optimal inter-passes. |
| **Priorités** | \textcolor{red}{**Violées**} (Certains commencent par la fin) | \textcolor{green!60!black}{**Respectées**} | \textcolor{green!60!black}{**Respectées**} |
| **Déplacements** | Géographiquement continu. | Sous-optimal : croisements fréquents entre les véhicules. | **Optimisés** : Le couplage minimise la distance totale. |
| **Impact** (Anjou, 4 véh, S1) | Deadhead : **161,8 km** | Deadhead : **180,4 km** \textcolor{red}{(+11,5 %)} | Deadhead : **170,2 km** \textcolor{green!60!black}{(-10,2 km)} |

*Table : Processus d'optimisation de l'heuristique de flotte pour les scénarios multi-passes (S1, S2).*

Ce tableau illustre parfaitement le processus d'optimisation : on constate d'abord que le modèle naïf ne respecte pas les priorités (Étape 1). En le forçant à les respecter (Étape 2), on détruit la continuité géographique, ce qui fait exploser les kilomètres à vide (+11,5 %). L'introduction de l'algorithme hongrois (Étape 3) vient alors minimiser le surcoût de cette transition obligatoire, sauvant ainsi environ 10 km de deadhead par jour tout en garantissant le respect de la contrainte métier.

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
notre outil permet d'en chiffrer le compromis. Bien que l'introduction du couplage par Algorithme Hongrois limite drastiquement les redondances inter-passes, la forte part de déplacements à vide due au postier rural constitue encore une borne supérieure : un solveur de tournées plus complexe la réduirait encore, sans pour autant changer l'ordre de nos conclusions.

# Logiciel livré et rendu

Le rendu ne se limite pas à ce rapport : nous livrons un **logiciel
complet**, à la fois bibliothèque Python réutilisable et application interactive.

## Architecture et chaîne de traitement

Le code est organisé en un paquet `src/` (modules testés
indépendamment, `tests/`) piloté par une application web
`app/streamlit\_app.py`. La chaîne de traitement est entièrement
automatisée, du téléchargement des données au rendu :

- **Extraction** du réseau routier et des services essentiels depuis
OpenStreetMap (`osmnx`, module `io\_osm`) ;

- **Annotation** des rues par classe de priorité et proximité d'un
service essentiel (`priorities`) ;

- **Résolution** du postier chinois / rural dirigé par flot à coût
minimum et circuit eulérien (`cpp`, `scenarios`) ;

- **Dimensionnement de la flotte** par découpage des passes et couplage
optimal (algorithme hongrois, `fleet`) ;

- **Indicateurs** : coût, temps de remise en service, accessibilité de
la population aux services essentiels (`cost`, `accessibility`) ;

- **Restitution** : carte interactive animée (`viz`, Folium) et
export ZIP (`exports`).

On peut, en outre, simuler des **tronçons en travaux** (rues fermées) : le
réseau et les tournées sont alors recalculés.

## L'application interactive

L'utilisateur choisit dans la barre latérale un *secteur*, un
*scénario*, un *nombre de déneigeuses* et un nombre de
*tronçons en travaux*, puis lance la simulation. L'application affiche les
indicateurs clés, une carte où les déneigeuses sont animées dans le temps
(curseur de lecture), des graphiques (accessibilité, coût en fonction de la
flotte) et des tableaux comparatifs.

*Figure : Configuration de la simulation dans l'application.*

*Figure : Carte interactive des tournées (avec, si possible, des tronçons en
travaux pour illustrer le recalcul).*

*Figure : Graphiques et tableaux de résultats.*

## L'export des tournées

Le bouton d'export produit une archive ZIP contenant, **pour chaque
déneigeuse** :

- une **trace GPS horodatée** (`gpx/vehicule\_$i$.gpx`) :
au-delà du tracé, elle contient des *points de passage* (waypoints)
ordonnés indiquant, à chaque étape, *quelle rue* déneiger ou parcourir à
vide, *quand* (heure de début et de fin) et sur quelle distance — lisibles
dans n'importe quel visualiseur GPX ;

- une **feuille de route** (`feuilles\_de\_route/vehicule\_$i$.csv`)
: une ligne par étape (ordre, heure début/fin, action déneigement ou trajet à
vide, rue, priorité, distance, kilométrage cumulé).

L'archive contient aussi un CSV de statistiques par véhicule, un GeoJSON de
toutes les tournées et un résumé JSON de la configuration.

*Figure : Export d'une tournée : trace GPS horodatée et feuille de route.*

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
