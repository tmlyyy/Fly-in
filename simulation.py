"""Independent turn validator: no dependency on routing reservations."""

from collections import Counter
from pathlib import Path
import re

from errors import SimulationError
from models import Move, Network, Transit, ZoneType


class Simulation:
    """Apply complete turns atomically and check all movement rules."""

    def __init__(self, network: Network) -> None:
        """Place the entire fleet at start before turn one."""
        self.network = network
        self.turn = 0
        self.delivered = 0
        self.positions: dict[int, str | Transit] = {
            drone: network.start
            for drone in range(1, network.drone_count + 1)
        }

    def step(self, moves: list[Move]) -> None:
        """Validate a simultaneous turn before committing any state."""
        try:
            self._step(moves)
        except SimulationError as error:
            raise SimulationError(f"turn {self.turn + 1}: {error}") from error

    def _step(self, moves: list[Move]) -> None:
        """Compute departures, compulsory arrivals, and final occupancy."""
        if not self.positions:
            raise SimulationError("simulation already finished")
        next_positions = self.positions.copy()
        moved: set[int] = set()
        links: Counter[tuple[str, str]] = Counter()
        arrivals = 0
        for move in moves:
            if move.drone in moved:
                raise SimulationError(f"D{move.drone} moves twice")
            if move.drone not in self.positions:
                raise SimulationError(f"unknown or delivered D{move.drone}")
            moved.add(move.drone)
            origin = self.positions[move.drone]
            destination: str | Transit
            if isinstance(origin, Transit):
                if move.target != origin.destination:
                    raise SimulationError("restricted transit must arrive now")
                destination = origin.destination
            else:
                destination = self._departure(origin, move.target, links)
            if destination == self.network.end:
                del next_positions[move.drone]
                arrivals += 1
            else:
                next_positions[move.drone] = destination
        for drone, position in self.positions.items():
            if isinstance(position, Transit) and drone not in moved:
                raise SimulationError(f"D{drone} cannot wait on a connection")
        occupancy = Counter(position for position in next_positions.values()
                            if isinstance(position, str))
        for name, count in occupancy.items():
            if count > self.network.capacity(name):
                raise SimulationError(f"zone {name!r} capacity exceeded")
        for key, count in links.items():
            if count > self.network.connections[key].capacity:
                raise SimulationError(f"connection {key} capacity exceeded")
        self.positions = next_positions
        self.delivered += arrivals
        self.turn += 1

    def _departure(self, origin: str, target: str,
                   links: Counter[tuple[str, str]]) -> str | Transit:
        """Check adjacency and distinguish entry from restricted transit."""
        if target in self.network.hubs:
            key = (min(origin, target), max(origin, target))
            if key not in self.network.connections:
                raise SimulationError(
                    f"no connection from {origin} to {target}",
                )
            hub = self.network.hubs[target]
            if hub.zone == ZoneType.BLOCKED:
                raise SimulationError(f"cannot enter blocked zone {target}")
            if hub.zone == ZoneType.RESTRICTED:
                raise SimulationError(
                    "restricted entry requires a transit turn",
                )
            links[key] += 1
            return target
        parts = target.split("-")
        if len(parts) != 2:
            raise SimulationError(f"unknown destination {target!r}")
        key = (min(parts[0], parts[1]), max(parts[0], parts[1]))
        edge = self.network.connections.get(key)
        if edge is None or origin not in (edge.first, edge.second):
            raise SimulationError(
                f"invalid connection {target!r} from {origin}",
            )
        destination = edge.second if origin == edge.first else edge.first
        if self.network.hubs[destination].zone != ZoneType.RESTRICTED:
            raise SimulationError("only restricted entries use transit tokens")
        links[key] += 1
        return Transit(destination, edge.name)

    def finish(self) -> None:
        """Require delivery of the entire fleet at the end of output."""
        if self.positions:
            raise SimulationError(
                f"incomplete simulation: {len(self.positions)} drones remain",
            )


class ScheduleReader:
    """Load plain movement output for independent replay and checking."""

    def read(self, path: Path) -> list[list[Move]]:
        """Preserve empty turns and report malformed output by line."""
        turns: list[list[Move]] = []
        with path.open(encoding="utf-8") as source:
            for line, text in enumerate(source, 1):
                moves: list[Move] = []
                for token in text.split():
                    match = re.fullmatch(r"D([1-9][0-9]*)-(\S+)", token)
                    if match is None:
                        raise SimulationError(
                            f"output line {line}: invalid token {token!r}",
                        )
                    try:
                        drone = int(match.group(1))
                    except ValueError as error:
                        raise SimulationError(
                            f"output line {line}: drone ID too large",
                        ) from error
                    moves.append(Move(drone, match.group(2)))
                turns.append(moves)
        return turns
