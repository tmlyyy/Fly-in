*This project has been created as part of the 42 curriculum by thamoliv.*

# Fly-in

## Description

Fly-in delivers a fleet of drones through a network of connected zones.
It plans simultaneous movements and waiting while respecting zone and
connection capacities. Entering a restricted zone takes two turns;
blocked zones cannot be entered. The objective is to minimize the turn
in which the final drone arrives.

The implementation uses Python 3.10 or later, an object-oriented design,
type hints, docstrings, and standard-library algorithms. No graph library
or third-party runtime dependency is used. All project files are at the
repository root, following chapter X of the subject.

## Instructions

Install the development tools and run the project:

```sh
make install
make run
make gui
```

`make install` creates `.venv` and installs flake8 and mypy. If those
exact versions already exist in your system installation, you can reuse
them with `make install VENV_FLAGS=--system-site-packages`.

Choose a different map or request statistics:

```sh
make run MAP=02_capacity_hell.txt ARGS="--stats"
make gui MAP=02_circular_loop.txt
```

The simulator also runs without installing development packages:

```sh
python3 fly_in.py 01_linear_path.txt
python3 fly_in.py 02_circular_loop.txt --gui
python3 fly_in.py --help
```

Other available commands:

```sh
make debug
make lint
make lint-strict
make benchmark
make clean
```

`make debug` starts the built-in `pdb` debugger. `make clean` removes
caches while preserving the source and virtual environment. `make lint`
uses the mandatory flake8 and mypy flags; `make lint-strict` also checks
strict typing. `make benchmark` independently validates all ten supplied
maps and reports turn counts. Local test programs are not submitted.

To save movements and validate them independently:

```sh
python3 fly_in.py 01_linear_path.txt --visual never > /tmp/fly-in-output.txt
python3 fly_in.py 01_linear_path.txt --check /tmp/fly-in-output.txt
```

stdout contains only movement tokens, one line per turn. Visual frames,
statistics, and errors use stderr. Exit codes are `0` for success, `1`
for input/routing/simulation errors, `2` for CLI usage errors, and `130`
for interruption. Parser errors identify the source line and cause.

## Algorithm and implementation strategy

1. `MapParser` validates declarations, metadata, names, coordinates,
   capacities, and duplicate connections. `Network` stores adjacency
   lists with both directions of every edge.
2. `Router` runs reverse Dijkstra once, caching the minimum remaining
   travel time to the end. Reverse relaxation uses the original forward
   destination's entry cost. Coordinates do not determine travel time.
3. For each drone, A* searches states `(zone, time)`. Its heuristic is
   the cached minimum remaining duration. Successors include waiting
   and adjacent entries allowed by earlier drones' reservations.
4. Among equally early deliveries, fewer entries into non-priority
   zones are preferred. Priority does not change the physical duration.
5. `Reservations` commits the entire route. It reserves zone occupancy
   at arrival/wait times and shared connection capacity on crossing
   launch turns. A restricted entry reserves its arrival two turns ahead.
6. `Simulation` independently validates the whole result before output:
   adjacency, occupancy, link capacities, blocked zones, identifiers,
   and mandatory restricted arrivals. Turns are applied atomically.

Departures free capacity for simultaneous arrivals. Restricted transits
release their connection on arrival, allowing a new launch in that same
turn. Both directions share each connection's capacity. The start and
end have unlimited occupancy; delivered drones are removed.

The search horizon is `last_reserved_arrival + shortest_distance`.
A drone can wait at the unlimited start until earlier drones finish,
then use a shortest accessible route. This gives a finite, feasible
fallback on connected accessible maps without a fixed fleet-size limit.

The strategy is prioritized cooperative routing. Earlier routes are
fixed while later drones are planned. It matches all supplied targets,
but it does not guarantee a globally optimal fleet schedule on every
unseen graph.

For `V` zones, `E` connections, `D` drones, and maximum horizon `H`,
Dijkstra takes `O((V + E) log V)` time. A conservative planning bound is
`O(D H (V + E) log(VH))` time and `O(H(V + E))` memory, plus stored output.
The horizon can grow with the fleet size.

## Visual representation

`make gui` generates `build/fly-in.html` and opens it in your browser.
The page works offline without a server or graphics package. It shows
zone colors, occupants, capacities, in-flight drones, and delivery counts.
Play/pause, previous/next turn, restart, interval, timeline, zoom, and
scroll controls help follow congestion and restricted entry timing.

Restricted zones have dashed borders, priority zones have stars, and
blocked zones show an X. Hover over a zone or connection for details.
Unknown single-word colors receive a deterministic palette color.
The layout preserves coordinate ordering on a readable grid.

`graphical.py` draws one SVG frame for each validated turn; the small
JavaScript block in `viewer.html` switches the visible frame. Movement
is represented as discrete states, following the simulation rules.
Large simulations produce larger HTML files because frames are stored.

To save the page without opening a browser:

```sh
python3 fly_in.py 01_linear_path.txt --html build/fly-in.html
```

A colored terminal view is also available. It enables automatically
when stderr is attached to a terminal. `--visual always` forces it;
`--visual never` disables it. `--color never` disables ANSI colors.
`--gui` disables terminal frames while retaining plain movement stdout.

## Example input and expected output

```text
nb_drones: 2
start_hub: start 0 0
hub: waypoint1 1 0
hub: waypoint2 2 0
end_hub: goal 3 0
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Expected stdout:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

For `connection: s-r` where `r` is restricted, a drone emits `D1-s-r`
in transit and `D1-r` on the next turn. The token preserves the declared
connection name even when traveling in the reverse declaration order.

## Benchmark results

| Map | Subject target | Measured turns |
| --- | ---: | ---: |
| Linear path | 4 | 4 |
| Simple fork | 4 | 4 |
| Basic capacity | 4 | 4 |
| Dead end trap | 8 | 8 |
| Circular loop | 10 | 10 |
| Priority puzzle | 6 | 6 |
| Maze nightmare | 13 | 13 |
| Capacity hell | 16 | 16 |
| Ultimate challenge | 26 | 26 |
| The Impossible Dream | 43 | 43 |

All schedules were independently replayed and validated. Subject version
2.0 takes precedence over the older 45-turn record in the original map
notes. Correctness and optimization are assessed separately.

## Resources

- Fly-in subject, version 2.0: authoritative specification, distributed
  separately through the curriculum.
- [Study guide in Portuguese](GUIA_DE_ESTUDO.md): requirements, design
  choices, concepts, walkthroughs, exercises, and peer-review preparation.
- Python's reference documentation, available locally through
  `python3 -m pydoc heapq`, `python3 -m pydoc dataclasses`,
  `python3 -m pydoc typing`, and `python3 -m pydoc pdb`.
  Relevant concepts include Dijkstra, A*, adjacency lists, and
  cooperative pathfinding with time reservations.

ChatGPT was used as a study guide to help understand the project and
its concepts.
