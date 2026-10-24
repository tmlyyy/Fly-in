"""Command-line entry point for the Fly-in drone routing project."""

import argparse
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Sequence
import webbrowser

from display import TerminalView
from errors import FlyInError
from graphical import GraphicalView
from parser import MapParser
from routing import Router
from simulation import ScheduleReader, Simulation


class Application:
    """Orchestrate input, planning, independent validation, and rendering."""

    def _arguments(self, argv: Sequence[str] | None) -> argparse.Namespace:
        """Define execution, replay, visual, and statistics options."""
        parser = argparse.ArgumentParser(
            description="Route drones using collision-free time reservations.",
        )
        parser.add_argument("map", type=Path, help="UTF-8 network map")
        parser.add_argument("--check", type=Path, metavar="OUTPUT",
                            help="validate an existing plain-text schedule")
        parser.add_argument("--visual", choices=("auto", "always", "never"),
                            default="auto", help="show zone states on stderr")
        parser.add_argument("--color", choices=("auto", "always", "never"),
                            default="auto", help="ANSI colors in visual view")
        parser.add_argument("--stats", action="store_true",
                            help="report turns and elapsed time on stderr")
        parser.add_argument("--gui", action="store_true",
                            help="open the graphical replay in your browser")
        parser.add_argument("--html", type=Path, metavar="FILE",
                            help="save an offline graphical replay as HTML")
        return parser.parse_args(argv)

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Execute the CLI and convert expected failures into clear errors."""
        args = self._arguments(argv)
        started = perf_counter()
        try:
            network = MapParser().parse_file(args.map)
            turns = (ScheduleReader().read(args.check) if args.check
                     else Router(network).plan())
            # Validate the whole plan before emitting any movement output.
            simulation = Simulation(network)
            for moves in turns:
                simulation.step(moves)
            simulation.finish()
            if args.gui or args.html:
                output = args.html or Path("build/fly-in.html")
                GraphicalView(network).save(output, turns)
                print(f"Graphical replay: {output.resolve()}",
                      file=sys.stderr)
                if args.gui:
                    self._open_browser(output)
            visual = (args.visual == "always" or
                      (args.visual == "auto" and sys.stderr.isatty()))
            if args.gui:
                visual = False
            color = (args.color == "always" or
                     (args.color == "auto" and sys.stderr.isatty()
                      and "NO_COLOR" not in os.environ))
            view = TerminalView(network, sys.stderr, visual, color)
            replay = Simulation(network) if visual else None
            if replay is not None:
                view.render(replay, [])
            for moves in turns:
                if not args.check:
                    print(" ".join(map(str, moves)))
                if replay is not None:
                    replay.step(moves)
                    view.render(replay, moves)
            if args.stats or args.check:
                print(f"OK: {network.drone_count} drones, {len(turns)} turns, "
                      f"{perf_counter() - started:.3f}s", file=sys.stderr)
            sys.stdout.flush()
            return 0
        except BrokenPipeError:
            # Avoid another failed stdout flush when used with e.g. head.
            with open(os.devnull, "w", encoding="utf-8") as sink:
                os.dup2(sink.fileno(), sys.stdout.fileno())
            return 0
        except (FlyInError, OSError, UnicodeError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("Interrupted.", file=sys.stderr)
            return 130

    def _open_browser(self, path: Path) -> None:
        """Try the desktop browser; the saved HTML also opens manually."""
        try:
            opened = webbrowser.open(path.resolve().as_uri())
        except (webbrowser.Error, OSError):
            opened = False
        if not opened:
            print("Open the HTML file in your browser.", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(Application().run())
