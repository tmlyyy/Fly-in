"""Replay and report the ten optimization targets in the supplied subject."""

from pathlib import Path
import sys
from time import perf_counter

from errors import FlyInError
from parser import MapParser
from routing import Router
from simulation import Simulation


class Benchmark:
    """Measure turns independently from movement correctness."""

    targets = {
        "easy/01_linear_path.txt": 4,
        "easy/02_simple_fork.txt": 4,
        "easy/03_basic_capacity.txt": 4,
        "medium/01_dead_end_trap.txt": 8,
        "medium/02_circular_loop.txt": 10,
        "medium/03_priority_puzzle.txt": 6,
        "hard/01_maze_nightmare.txt": 13,
        "hard/02_capacity_hell.txt": 16,
        "hard/03_ultimate_challenge.txt": 26,
        "challenger/01_the_impossible_dream.txt": 43,
    }

    def run(self) -> int:
        """Validate every schedule and print actual versus reference turns."""
        root = Path(__file__).resolve().parent
        if root.name == "tools":
            root = root.parent / "maps"
        failures = 0
        print(f"{'Map':49} {'Turns':>5} {'Target':>6} "
              f"{'Valid':>5} {'Time':>8}")
        for name, target in self.targets.items():
            started = perf_counter()
            try:
                path = root / name if root.name == "maps" else root / Path(
                    name,
                ).name
                network = MapParser().parse_file(path)
                turns = Router(network).plan()
                simulation = Simulation(network)
                for moves in turns:
                    simulation.step(moves)
                simulation.finish()
                print(f"{name:49} {len(turns):5} {target:6} {'yes':>5} "
                      f"{perf_counter() - started:7.3f}s")
            except (FlyInError, OSError, UnicodeError) as error:
                failures += 1
                print(f"{name}: {error}", file=sys.stderr)
        return int(failures > 0)


if __name__ == "__main__":
    sys.exit(Benchmark().run())
