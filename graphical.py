"""Desenhe a simulação em HTML/SVG, sem servidor ou biblioteca externa."""

from collections import defaultdict
from html import escape
from pathlib import Path

from models import Move, Network, Transit, ZoneType
from simulation import Simulation


class GraphicalView:
    """Transforme os estados do simulador em quadros para o navegador."""

    _palette = {
        "green": "#15803d", "red": "#dc2626", "blue": "#2563eb",
        "yellow": "#ca8a04", "orange": "#ea580c", "purple": "#9333ea",
        "cyan": "#0891b2", "gray": "#64748b", "grey": "#64748b",
        "black": "#334155", "white": "#64748b", "gold": "#ca8a04",
        "lime": "#65a30d", "brown": "#92400e", "maroon": "#991b1b",
        "violet": "#7c3aed", "magenta": "#c026d3", "crimson": "#be123c",
        "darkred": "#991b1b",
    }

    def __init__(self, network: Network) -> None:
        """Prepare posições com espaço para os nomes e capacidades."""
        self.network = network
        # A ordem das coordenadas é preservada; intervalos viram uma grade.
        columns = sorted({hub.x for hub in network.hubs.values()})
        rows = sorted({hub.y for hub in network.hubs.values()}, reverse=True)
        self.points: dict[str, tuple[int, int]] = {}
        duplicates: dict[tuple[int, int], int] = defaultdict(int)
        for hub in network.hubs.values():
            offset = duplicates[hub.x, hub.y] * 55
            x = 130 + columns.index(hub.x) * 190 + offset
            y = 100 + rows.index(hub.y) * 150 + offset
            self.points[hub.name] = x, y
            duplicates[hub.x, hub.y] += 1
        self.width = max(850, max(x for x, _ in self.points.values()) + 150)
        self.height = max(420, max(y for _, y in self.points.values()) + 120)

    def save(self, path: Path, turns: list[list[Move]]) -> None:
        """Reproduza os turnos e salve uma página que funciona offline."""
        simulation = Simulation(self.network)
        frames = [self._frame(simulation, [])]
        for moves in turns:
            simulation.step(moves)
            frames.append(self._frame(simulation, moves))
        simulation.finish()
        template = Path(__file__).with_name("viewer.html").read_text(
            encoding="utf-8",
        )
        document = template.replace("<!-- FRAMES -->", "\n".join(frames))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8")

    def _frame(self, simulation: Simulation, moves: list[Move]) -> str:
        """Monte um quadro completo: resumo, rede, ocupação e movimentos."""
        occupants: dict[str, list[str]] = defaultdict(list)
        flying: dict[str, list[str]] = defaultdict(list)
        for drone, position in sorted(simulation.positions.items()):
            if isinstance(position, Transit):
                flying[position.connection].append(f"D{drone}")
            else:
                occupants[position].append(f"D{drone}")
        delivered = simulation.delivered
        total = self.network.drone_count
        hidden = " hidden" if simulation.turn else ""
        drawing = self._connections(flying)
        for hub in self.network.hubs.values():
            drawing += self._hub(hub.name, occupants[hub.name], delivered)
        movement = escape(" ".join(map(str, moves)))
        if not movement:
            movement = "Posição inicial" if not simulation.turn else "Espera"
        return (
            f'<section class="frame"{hidden}>'
            f'<p class="summary">Entregues: <strong>{delivered}/{total}'
            f'</strong> · Em voo: {sum(map(len, flying.values()))}</p>'
            f'<div class="network"><svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" '
            f'role="img" aria-label="Rede no turno {simulation.turn}">'
            f'{drawing}</svg></div>'
            f'<p class="moves"><b>Movimentos:</b> <code>{movement}</code></p>'
            '</section>'
        )

    def _connections(self, flying: dict[str, list[str]]) -> str:
        """Desenhe ligações e drones no meio de uma entrada restrita."""
        drawing: list[str] = []
        for edge in self.network.connections.values():
            x1, y1 = self.points[edge.first]
            x2, y2 = self.points[edge.second]
            middle_x, middle_y = (x1 + x2) // 2, (y1 + y2) // 2
            ids = flying.get(edge.name, [])
            color = "#d97706" if ids else "#cbd5e1"
            title = escape(f"{edge.name}: capacidade {edge.capacity}")
            drawing.append(
                f'<g><title>{title}</title>'
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{color}" stroke-width="3"/>'
                f'<text class="link-label" x="{middle_x}" '
                f'y="{middle_y - 10}">cap {edge.capacity}</text></g>',
            )
            if ids:
                drawing.append(
                    f'<g><title>Em voo: {escape(", ".join(ids))}</title>'
                    f'<circle cx="{middle_x}" cy="{middle_y}" r="16" '
                    'fill="#fef3c7" stroke="#d97706" stroke-width="2"/>'
                    f'<text x="{middle_x}" y="{middle_y + 5}">'
                    f'{len(ids)}</text><text class="drone-label" '
                    f'x="{middle_x}" y="{middle_y + 35}">'
                    f'{escape(self._short_ids(ids))}</text></g>',
                )
        return "".join(drawing)

    def _hub(self, name: str, ids: list[str], delivered: int) -> str:
        """Desenhe uma zona com cor, tipo, capacidade e IDs dos drones."""
        hub = self.network.hubs[name]
        x, y = self.points[name]
        capacity = str(self.network.capacity(name))
        count = len(ids)
        role = hub.zone.value
        if name == self.network.start:
            capacity, role = "∞", "início"
        elif name == self.network.end:
            capacity, role, count = "∞", "fim", delivered
        color = self._palette.get(hub.color or "blue")
        if color is None:
            colors = ("#2563eb", "#9333ea", "#0891b2", "#ca8a04")
            color = colors[sum(map(ord, hub.color or "")) % len(colors)]
        fill = "#dbeafe" if ids else "#ffffff"
        dash = ""
        if hub.zone == ZoneType.RESTRICTED:
            dash = ' stroke-dasharray="5 4"'
        if hub.zone == ZoneType.BLOCKED:
            fill = "#e2e8f0"
        label = "X" if hub.zone == ZoneType.BLOCKED else str(count)
        priority = "★ " if hub.zone == ZoneType.PRIORITY else ""
        description = f"{name}: {role}, ocupação {count}/{capacity}"
        if ids:
            description += "; " + ", ".join(ids)
        return (
            f'<g><title>{escape(description)}</title>'
            f'<circle cx="{x}" cy="{y}" r="27" fill="{fill}" '
            f'stroke="{color}" stroke-width="4"{dash}/>'
            f'<text class="count" x="{x}" y="{y + 6}">{label}</text>'
            f'<text class="hub-label" x="{x}" y="{y - 43}">'
            f'{priority}{escape(name)}</text>'
            f'<text class="detail" x="{x}" y="{y + 49}">'
            f'{role} · {count}/{capacity}</text>'
            f'<text class="drone-label" x="{x}" y="{y + 70}">'
            f'{escape(self._short_ids(ids))}</text></g>'
        )

    def _short_ids(self, ids: list[str]) -> str:
        """Encurte a lista de IDs; o tooltip mantém a lista completa."""
        text = ", ".join(ids[:3])
        if len(ids) > 3:
            text += f" +{len(ids) - 3}"
        return text
