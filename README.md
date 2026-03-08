# FLY_IN
flow optimixation and resource scheduling

## important steps
1. Create models + parcing 
    doing both at the same time ensures the classes have all they need
2. the pathfinder
    this will analyse the managers graph and give a list of all the possible routes
    without moving the drone. == just map directions
    inputs needed:
        - adjency list
        - zone objects for zone_type and max_drones
        - max_link_capacity

    Attention, we will not use the Breadth-First Search (BFS) because it assumes every step is equal.
    we need an algo that will use a "Priority Queue" meaning, 
        - It always picks the hub that currently has the lowest total cost from the start.
        - If it finds a path to a hub that is "longer" in distance but "cheaper" in turns, it will prioritize that path.
        # concrete exameple:

        The Heap always gives us the zone_name with the lowest total_cost first. This ensures that if there is a 5-step "normal" path (cost 5) and a 3-step "restricted" path (cost 6), Dijkstra will pick the 5-step path because it takes fewer turns.
2.a Dijkstra algorithm 
    for finding paths with the lowest cumulative weight (weight = turns)
    application: 
    - Normal/Priority Hubs: Weight = 1.
    - Restricted Hubs: Weight = 2.
    - Start Hub: Weight = 0 (you're already there).
    Problem:
    Djikstra finds the fastest path BUT it does not take into account the zone capacity...
    bottleneck term = when drones are blocked in a zone
2.b # Yen's algorith:
        need to fin the top paths (3-4 paths) so we can send more drones simultaneously
        1. take the best path 
        2. find a hub on that path where we deviate
        2. do a new dijksra search from that hub ignoring the original connections

3. the simulation engine
    code needs:
    - to know where the drone is **right now** to check for capacity limit, collisions
    capacity limit is illustarted with the path occupancy and total latency concept:
    $$\text{Latency} = \text{Path Base Cost} + \text{Drones already in that "line"}$$
    2. A Practical Example (The "Simple Fork")Imagine you have 3 Drones and 2 Paths:Path A: 3 Turns (Base Cost)Path B: 3 Turns (Base Cost)StepDronePath A Latency (3+Occ)Path B Latency (3+Occ)Decision1D13 + 0 = 33 + 0 = 3D1 takes Path A (Occ A becomes 1)2D23 + 1 = 43 + 0 = 3D2 takes Path B (Occ B becomes 1)3D33 + 1 = 43 + 1 = 4D3 takes Path A (Occ A becomes 2)Result: D1 and D3 use Path A, D2 uses Path B. The path_occupancy list ended up as [2, 1].

    the engine has 3 main functions:
    1. _prepare_drones : 
    2. _apply_turn :
    3. run : 

## BONUS ?
    ok now i need to restructure my code to assign paths
    The challenger....
    1. my 25 drones need to go to the "gate_hell1" with a cap of 1.... So i start with a minimum of 25 turns just to pass the first level.... 
        so the problem is there are huge gaps where no drone passes to the bottle neck when they should be pipelining

## testing
# Priority:
this text file shows super clearly if priority is well implemented in your code:
# Priority tiebreaker test
"   # Two paths from start to goal, both cost exactly 3 turns:
    #   Path A (priority): start -> priority_mid -> goal  (1 + 1 = 2 hops, cost 2)
    #   Path B (normal):   start -> normal_mid -> goal    (1 + 1 = 2 hops, cost 2)
    # If priority is working, Dijkstra must always return Path A.

nb_drones: 1

start_hub: start 0 0 [max_drones=2]
hub: priority_mid 1 1 [zone=priority]
hub: normal_mid 1 -1 [zone=normal]
end_hub: goal 2 0 [max_drones=2]

connection: start-priority_mid
connection: start-normal_mid
connection: priority_mid-goal
connection: normal_mid-goal"

## Ressources:

from https://www.algorithmexamples.com/ a ressource to explain and implement algorithms
- dijkstra Algorithm (find shortest path) here: https://python.algorithmexamples.com/web/graphs/dijkstra_algorithm.html
- Dini's Algo here: https://python.algorithmexamples.com/web/graphs/dinic.html

for a visual and iteractive algo explanation:
- https://www.redblobgames.com/pathfinding/a-star/introduction.html

for understanding real world implications:
- https://www.youtube.com/watch?v=XeZTyUS8ZF0

Explains the Ford-Fulkerson algo:
https://www.youtube.com/watch?v=8QO487YsLPc&t=607s

for the heapq module:
- https://docs.python.org/3/library/heapq.html