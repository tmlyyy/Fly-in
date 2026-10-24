"""Terminal visualization kept separate from machine-readable stdout."""

from collections import defaultdict
from typing import TextIO

from models import Move, Network, Transit, ZoneType
from simulation import Simulation


class TerminalView:
    """Print colored zone occupancy and in-flight drones to stderr."""

    _colors = {
        "black": 90, "red": 91, "green": 92, "yellow": 93,
        "blue": 94, "magenta": 95, "purple": 95, "cyan": 96,
        "white": 97, "gray": 90, "grey": 90, "orange": 33,
        "gold": 93, "lime": 92, "brown": 33, "violet": 95,
        "maroon": 31, "crimson": 91, "darkred": 31,
    }

    def __init__(self, network: Network, stream: TextIO,
                 enabled: bool, color: bool) -> None:
        """Configure the independent visual stream and ANSI support."""
        self.network = network
        self.stream = stream
        self.enabled = enabled
        self.color = color

    def _paint(self, text: str, name: str) -> str:
        """Use named colors or a stable palette for arbitrary color words."""
        if not self.color:
            return text
        code = self._colors.get(name, 91 + sum(map(ord, name)) % 7)
        return f"\033[{code}m{text}\033[0m"

    def render(self, simulation: Simulation, moves: list[Move]) -> None:
        """Show zone state, capacities, transit, and completed deliveries."""
        if not self.enabled:
            return
        occupants: dict[str, list[str]] = defaultdict(list)
        flying: list[str] = []
        for drone, position in sorted(simulation.positions.items()):
            if isinstance(position, Transit):
                flying.append(f"D{drone}@{position.connection}")
            else:
                occupants[position].append(f"D{drone}")
        zones: list[str] = []
        for hub in self.network.hubs.values():
            ids = ",".join(occupants[hub.name]) or "-"
            limit = ("unlimited" if hub.name in (
                self.network.start, self.network.end)
                     else str(hub.capacity))
            if hub.zone == ZoneType.BLOCKED:
                ids = "BLOCKED"
            label = f"{hub.name}[{ids}; cap={limit}; {hub.zone.value}]"
            zones.append(self._paint(label, hub.color or "white"))
        print(f"Turn {simulation.turn}: " + " ".join(map(str, moves)),
              file=self.stream)
        print("  " + " | ".join(zones), file=self.stream)
        if flying:
            print("  In flight: " + ", ".join(flying), file=self.stream)
        print(f"  Delivered: {simulation.delivered}/"
              f"{self.network.drone_count}", file=self.stream)
