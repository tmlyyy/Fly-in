"""Cooperative space-time routing using future capacity reservations."""

from collections import defaultdict
from heapq import heappop, heappush

from errors import FlyInError
from models import Connection, Leg, Move, Network, ZoneType


class Reservations:
    """Count zone occupancy and shared link usage at discrete times."""

    def __init__(self, network: Network) -> None:
        """Create sparse reservations; unmentioned resources are free."""
        self.network = network
        self.zones: dict[tuple[str, int], int] = defaultdict(int)
        self.links: dict[tuple[tuple[str, str], int], int] = defaultdict(int)
        self.last_arrival = 0

    def zone_free(self, name: str, time: int) -> bool:
        """Check occupancy after all simultaneous moves at this time."""
        return self.zones.get((name, time), 0) < self.network.capacity(name)

    def link_free(self, edge: Connection, time: int) -> bool:
        """Check new crossings, with arriving transits already released."""
        return self.links.get((edge.key, time), 0) < edge.capacity

    def reserve(self, path: list[Leg]) -> None:
        """Commit an entire route, including waits and future arrivals."""
        for leg in path:
            self.zones[leg.destination, leg.arrival] += 1
            if leg.edge is not None:
                self.links[leg.edge.key, leg.departure + 1] += 1
        self.last_arrival = max(self.last_arrival, path[-1].arrival)


class Router:
    """Plan earliest feasible delivery for each drone in identifier order."""

    def __init__(self, network: Network) -> None:
        """Cache weighted distances once and share a reservation table."""
        self.network = network
        self.reservations = Reservations(network)
        self.distances = self._distances()

    def _distances(self) -> dict[str, int]:
        """Run reverse Dijkstra with destination-based movement costs."""
        end = self.network.end
        if self.network.hubs[end].zone == ZoneType.BLOCKED:
            return {}
        distances = {end: 0}
        queue = [(0, end)]
        while queue:
            distance, current = heappop(queue)
            if distance != distances[current]:
                continue
            cost = self.network.hubs[current].duration
            for neighbor, _ in self.network.adjacency[current]:
                if self.network.hubs[neighbor].zone == ZoneType.BLOCKED:
                    continue
                candidate = distance + cost
                if candidate < distances.get(neighbor, candidate + 1):
                    distances[neighbor] = candidate
                    heappush(queue, (candidate, neighbor))
        return distances

    def plan(self) -> list[list[Move]]:
        """Return turn-indexed moves, omitting all stationary drones."""
        if self.network.start not in self.distances:
            raise FlyInError("unsolvable map: no accessible start-to-end path")
        turns: list[list[Move]] = []
        for drone in range(1, self.network.drone_count + 1):
            path = self._path()
            self.reservations.reserve(path)
            while len(turns) < path[-1].arrival:
                turns.append([])
            for leg in path:
                if leg.edge is None:
                    continue
                if leg.arrival - leg.departure == 2:
                    turns[leg.departure].append(Move(drone, leg.edge.name))
                turns[leg.arrival - 1].append(Move(drone, leg.destination))
        return turns

    def _path(self) -> list[Leg]:
        """Search (zone, time) with A*, allowing strategic waiting.

        Previously planned drones are fixed. The horizon is safe because a
        new drone can wait at start until they finish, then use a shortest
        route. Among equally early deliveries, prefer fewer non-priority
        entries. Positive durations and a finite horizon ensure termination.
        """
        start = (self.network.start, 0)
        horizon = (self.reservations.last_arrival
                   + self.distances[self.network.start])
        queue = [(self.distances[start[0]], 0, 0, start[0])]
        penalties = {start: 0}
        previous: dict[tuple[str, int], Leg] = {}
        while queue:
            _, penalty, time, name = heappop(queue)
            if penalty != penalties.get((name, time)):
                continue
            if name == self.network.end:
                return self._reconstruct(previous, (name, time))
            for leg in self._successors(name, time, horizon):
                state = (leg.destination, leg.arrival)
                extra = 0
                destination = self.network.hubs[leg.destination]
                if leg.edge is not None:
                    if destination.zone != ZoneType.PRIORITY:
                        extra = 1
                candidate = penalty + extra
                if candidate >= penalties.get(state, candidate + 1):
                    continue
                penalties[state] = candidate
                previous[state] = leg
                estimate = leg.arrival + self.distances[leg.destination]
                heappush(queue, (estimate, candidate, leg.arrival,
                                 leg.destination))
        raise FlyInError("routing failed: no feasible schedule within horizon")

    def _successors(self, name: str, time: int,
                    horizon: int) -> list[Leg]:
        """Generate waits and legal departures with guaranteed arrivals."""
        candidates = [Leg(name, name, time, time + 1)]
        for neighbor, edge in self.network.adjacency[name]:
            if (neighbor == self.network.start
                    or neighbor not in self.distances):
                continue
            arrival = time + self.network.hubs[neighbor].duration
            if self.reservations.link_free(edge, time + 1):
                candidates.append(Leg(name, neighbor, time, arrival, edge))
        available: list[Leg] = []
        for leg in candidates:
            earliest_finish = leg.arrival + self.distances[leg.destination]
            if earliest_finish > horizon:
                continue
            if self.reservations.zone_free(leg.destination, leg.arrival):
                available.append(leg)
        return available

    def _reconstruct(self, previous: dict[tuple[str, int], Leg],
                     state: tuple[str, int]) -> list[Leg]:
        """Follow predecessor transitions back to the initial state."""
        path: list[Leg] = []
        while state in previous:
            leg = previous[state]
            path.append(leg)
            state = (leg.origin, leg.departure)
        path.reverse()
        return path
