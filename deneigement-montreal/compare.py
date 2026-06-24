import sys
import os
import json

# Force UTF-8 pour éviter les soucis d'affichage
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.io_osm import load_sector, load_pois
from src.priorities import annotate_priorities, annotate_essential
from src.scenarios import SCENARIOS, evaluate_scenario
from src.fleet import split_route, summarize_fleet

def _route_length_km(route):
    return sum(float(d.get("length", 0.0)) for _u, _v, d in route) / 1000.0

def _deadhead_km(route):
    return sum(float(d.get("length", 0.0)) for _u, _v, d in route if d.get("duplicate")) / 1000.0

print("Chargement Anjou...")
G = load_sector("anjou")
annotate_priorities(G)
pois = load_pois("anjou")
annotate_essential(G, pois)

print("Evaluation S1...")
res = evaluate_scenario(G, "S1")
route = res["route"]
passes = res["passes"]
depot = route[0][0]

k = 4 # 4 véhicules pour Anjou

print("\n--- ETAPE 1 (Découpage naïf, ne respecte pas les priorités) ---")
veh_before = split_route(G, route, k, depot=depot, passes=None)
dist_before = [_route_length_km(v) for v in veh_before]
dh_before = sum(_deadhead_km(v) for v in veh_before)
s_before = summarize_fleet(dist_before, 10.0)
print(f"Deadhead total flotte : {dh_before:.2f} km")

print("\n--- ETAPE 2 (Découpage par passe, transition naïve i -> i) ---")
# On force le couplage i -> i
from src.fleet import _connector
veh_inter = [[] for _ in range(k)]
current_positions = [depot] * k

for p_info in passes:
    pass_circuit = p_info.get("route", [])
    if not pass_circuit: continue
    total = _route_length_km(pass_circuit)
    target = total / k
    chunks, cur, cur_km = [], [], 0.0
    for edge in pass_circuit:
        cur.append(edge)
        cur_km += float(edge[2].get("length", 0.0)) / 1000.0
        if cur_km >= target and len(chunks) < k - 1:
            chunks.append(cur)
            cur, cur_km = [], 0.0
    if cur: chunks.append(cur)
    while len(chunks) < k: chunks.append([])
    
    starts = [c[0][0] if c else None for c in chunks]
    
    # Transition naïve i -> i
    for i in range(k):
        v = starts[i]
        chunk = chunks[i]
        if v is not None:
            veh_inter[i].extend(_connector(G, current_positions[i], v))
        veh_inter[i].extend(chunk)
        if chunk:
            current_positions[i] = chunk[-1][1]
            
for i, u in enumerate(current_positions):
    veh_inter[i].extend(_connector(G, u, depot))
    
dist_inter = [_route_length_km(v) for v in veh_inter]
dh_inter = sum(_deadhead_km(v) for v in veh_inter)
print(f"Deadhead total flotte : {dh_inter:.2f} km")


print("\n--- ETAPE 3 (Découpage par passe, transition Hongroise) ---")
veh_after = split_route(G, route, k, depot=depot, passes=passes)
dist_after = [_route_length_km(v) for v in veh_after]
dh_after = sum(_deadhead_km(v) for v in veh_after)
s_after = summarize_fleet(dist_after, 10.0)
print(f"Deadhead total flotte : {dh_after:.2f} km")

