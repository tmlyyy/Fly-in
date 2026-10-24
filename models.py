"""Typed domain objects for the map and discrete drone movements."""

from dataclasses import dataclass, field
from enum import Enum


class ZoneType(str, Enum):
    """Describe destination accessibility and entry duration."""

    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Hub:
    """Store a zone's geometry, visual metadata, and occupancy limit."""

    name: str
    x: int
    y: int
    zone: ZoneType = ZoneType.NORMAL
    color: str | None = None
    capacity: int = 1

    @property
    def duration(self) -> int:
        """Return the number of turns needed to enter this zone."""
        return 2 if self.zone == ZoneType.RESTRICTED else 1


@dataclass(frozen=True)
class Connection:
    """Store one undirected connection with its shared capacity."""

    first: str
    second: str
    capacity: int = 1

    @property
    def name(self) -> str:
        """Return the connection name in its input declaration order."""
        return f"{self.first}-{self.second}"

    @property
    def key(self) -> tuple[str, str]:
        """Return a direction-independent reservation key."""
        return min(self.first, self.second), max(self.first, self.second)


@dataclass
class Network:
    """Represent an adjacency-list graph without graph libraries."""

    drone_count: int
    hubs: dict[str, Hub]
    connections: dict[tuple[str, str], Connection]
    start: str
    end: str
    adjacency: dict[str, list[tuple[str, Connection]]] = field(
        init=False, default_factory=dict,
    )

    def __post_init__(self) -> None:
        """Build both directions of every declared edge."""
        self.adjacency = {name: [] for name in self.hubs}
        for edge in self.connections.values():
            self.adjacency[edge.first].append((edge.second, edge))
            self.adjacency[edge.second].append((edge.first, edge))

    def capacity(self, name: str) -> int:
        """Model unlimited terminals using the total fleet size."""
        if name in (self.start, self.end):
            return self.drone_count
        return self.hubs[name].capacity


@dataclass(frozen=True)
class Move:
    """Describe one output token, including in-flight positions."""

    drone: int
    target: str

    def __str__(self) -> str:
        """Serialize a movement using the subject's exact format."""
        return f"D{self.drone}-{self.target}"


@dataclass(frozen=True)
class Leg:
    """Describe a planned transition; identical endpoints mean waiting."""

    origin: str
    destination: str
    departure: int
    arrival: int
    edge: Connection | None = None


@dataclass(frozen=True)
class Transit:
    """Track a drone that must arrive at the very next turn."""

    destination: str
    connection: str
