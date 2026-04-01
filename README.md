*This project has been created as part of the 42 curriculum by acaire-d.*

# FLY_IN
flow optimization and resource scheduling

---

## Description

FLY_IN is a drone routing simulation. Given a map of zones connected by links, the goal is to move all drones from a start hub to an end hub in as few turns as possible.

Each zone has a type that affects movement:
- **Normal** — costs 1 turn to cross
- **Priority** — costs 1 turn, preferred by the pathfinder
- **Restricted** — costs 2 turns to cross (transit via a Connection object)
- **Blocked** — inaccessible

Each zone and connection also has a capacity limit — only a fixed number of drones can occupy them at once. The challenge is to route all drones efficiently without violating these constraints.

The project is built entirely in Python with no graph libraries. 
It includes a terminal renderer and an interactive pygame visualiser.

---

## Instructions


### Create virtual enviroment with dependencies

```bash
make install
```

### Run the simulation


```bash
make run MAP=maps/example.map
```

### Run the visualiser

```bash
make visualiser MAP=maps/example.map
```

### Run all test maps

```bash
make run-all
```

### Lint

```bash
make lint          # flake8
make lint-strict   # mypy --strict
```

---

## Algorithm choices and implementation strategy

### Step 1 — Parsing and models

The parser and models were built together so that zone objects have everything the pathfinder needs from the start: zone type, max capacity, and adjacency list with connection capacities.

### Step 2 — Pathfinder

**Why not BFS?**
BFS (Breadth-First Search) assumes every step costs the same. 
But here restricted zones cost 2 turns, so BFS would give wrong results.

**Dijkstra** finds the shortest path by cumulative turn cost using a priority queue (min-heap).
The heap always pops the zone with the lowest total cost first, so if a 5-step normal path costs 5 turns and a 3-step restricted path costs 6 turns, Dijkstra correctly picks the 5-step path.

Zone costs:
- Normal / Priority: weight = 1
- Restricted: weight = 2
- Start / End: weight = 0

**Yen's k-shortest paths** extends Dijkstra to find the top k paths instead of just the best one. It works by finding the best path, then systematically deviating from it at each node and re-running Dijkstra. This gives us a list of alternative routes to distribute the drones.

### Step 3 — Simulation engine

The engine runs turn by turn. Each turn has two phases:

**`_prepare_turn`** — 
decides where each drone will move, checking zone and link capacity using the `_net_occupancy` helper. 
Drones fall into three categories:
1. Already delivered — skip
2. In transit over a restricted zone — must land this turn
3. Free — try to advance either in a zone or a connaection if the next zone is a restricted one
    or, reroute if blocked

**`_apply_turn`** — commits all planned moves and updates drone positions.

### Optimizations

**1. Latency-based path distribution**
Instead of sending every drone down the same shortest path, each drone picks a path based on estimated latency, 
path cost plus how many drones are already assigned to it.
This naturally spreads drones across parallel routes.

```
Latency = Path Base Cost + Drones already assigned to that path
```

**2. Connection-leaving fix (biggest win)**
When a drone enters a restricted zone it spends 2 turns crossing it. 
The original `_net_occupancy` still counted that drone as occupying the zone it just left, blocking the next drone for an extra turn for no reason.
Fixing this one line dropped the challenger map from 67 turns to 48.

**3. Dynamic rerouting**
When a drone is blocked because its next zone is full, instead of waiting it reruns Dijkstra from its current position while ignoring all currently congested zones. If the alternative costs no more than 2 extra turns, it takes it immediately that same turn. The +2 tolerance prevents drones from taking massive detours just to avoid a one-turn wait.

### Complexity

|           Operation           |        Complexity       |
|-------------------------------|-------------------------|
| Dijkstra (single path)        | O((V + E) log V)        |
| Yen's k-shortest paths        | O(k · V · (V + E) log V)|
| `_give_paths` (once at start) | O(k · d)                |
| `_prepare_turn` (per turn)    | O(d²)                   |
| Full simulation               | O(T · d²)               |

Where V = zones, E = connections, k = paths computed, d = drones, T = turns.

The O(d²) per-turn cost comes from `_net_occupancy` scanning the `planned` dict for each drone. 
With 25 drones that's ~312 operations per turn — fine. 
With 1000 drones it becomes ~500,000 per turn, which would be the bottleneck.

### Memory usage

|       Component           |Complexity |              Reality                 |
|---------------------------|-----------|--------------------------------------|
| k-shortest path cache     | O(k · V)  | k=100, V=30 → ~3000 refs, negligible |
| Per-drone path assignment | O(d · V)  | Most paths shorter than V            |
| `planned` dict (per turn) | O(d)      | Discarded after each turn            |
| Visualiser snapshots      | O(T · d)  | 48 × 25 = 1200 strings on challenger |

---

## Visual representation

The pygame visualiser (`make visualiser MAP=...`) renders the full zone graph with:

- **Zone colors by type** — restricted zones in red, priority in green, start in light green, end in light red, normal in blue, blocked in grey
- **Drone positions** — circles displayed above each zone showing which drones are currently there
- **Overflow labels** — when multiple drones share a zone, a `+N` label shows the count instead of drawing overlapping circles
- **Turn counter HUD** — current turn displayed in the top-left corner
- **Arrow key navigation** — step forward and backward through turns
- **Auto-scaling** — the graph fits any map size automatically

This makes three things immediately visible that are invisible in the raw text output: where congestion is forming, which parallel paths drones are taking, and whether the pipeline is flowing smoothly or stalling at a bottleneck.

---

## Bonus

The challenger map (`tests/maps/challenger/01_the_impossible_dream.txt`) completed in **48 turns** (target was ≤41). The mandatory performance targets for easy, medium, and hard maps are all met.

My algo won't hit 41 turns on the challenger because `gate_hell1` is the only entry point (capacity 1), so there is no uncongested alternative for waiting drones — dynamic rerouting can't help drones that are physically stuck behind a single-file bottleneck with no bypass.

---

**Algorithm references:**

## Resources

- Aguilar, A. (n.d.). *Dijkstra's algorithm*. Algorithm Examples.
    https://python.algorithmexamples.com/web/graphs/dijkstra_algorithm.html
- Aguilar, A. (n.d.). *Dinic's algorithm*. Algorithm Examples.
    https://python.algorithmexamples.com/web/graphs/dinic.html
- Python Software Foundation. (n.d.). *heapq — Heap queue algorithm*. Python 3 Documentation.
        https://docs.python.org/3/library/heapq.html
- Patel, A. (n.d.). *Introduction to the A* algorithm*. Red Blob Games.
https://www.redblobgames.com/pathfinding/a-star/introduction.html
- Reducible. (2022, February 14). *This is how airlines schedule flights* [Video]. YouTube.
    https://www.youtube.com/watch?v=XeZTyUS8ZF0
- Spanning Tree. (2021, March 7). *Ford-Fulkerson in 5 minutes* [Video]. YouTube.
    https://www.youtube.com/watch?v=8QO487YsLPc&t=607s

**AI usage:**
Claude (Anthropic) was used throughout this project for:
- Debugging the `_net_occupancy` connection-leaving bug that caused the 67→48 turn improvement
- Designing and explaining the dynamic rerouting logic with cost guard
- Answering complexity and algorithm questions during development
- Code review and mypy/flake8 compliance fixes