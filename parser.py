"""Strict line-oriented parser for the format in subject version 2.0."""

import re
from pathlib import Path

from errors import ParseError
from models import Connection, Hub, Network, ZoneType


class MapParser:
    """Validate syntax and construct a network from local text input."""

    _integer = re.compile(r"[+-]?[0-9]+\Z")
    _positive = re.compile(r"[0-9]+\Z")

    def parse_file(self, path: Path) -> Network:
        """Read a UTF-8 file, automatically closing its file handle."""
        with path.open(encoding="utf-8") as source:
            return self.parse(source.read())

    def parse(self, text: str) -> Network:
        """Parse text and identify every syntax failure by line number."""
        hubs: dict[str, Hub] = {}
        edges: dict[tuple[str, str], Connection] = {}
        terminals: dict[str, str] = {}
        count: int | None = None
        lines = text.splitlines()
        for number, raw in enumerate(lines, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            prefix, separator, content = line.partition(":")
            if not separator:
                raise ParseError(number, "expected a declaration with ':'")
            prefix, content = prefix.strip(), content.strip()
            if count is None:
                if prefix != "nb_drones":
                    raise ParseError(number, "first declaration: nb_drones")
                count = self._capacity(content, number)
            elif prefix == "nb_drones":
                raise ParseError(number, "duplicate nb_drones declaration")
            elif prefix in ("start_hub", "end_hub", "hub"):
                hub = self._hub(content, number)
                if hub.name in hubs:
                    raise ParseError(number, f"duplicate zone {hub.name!r}")
                if prefix != "hub":
                    if prefix in terminals:
                        raise ParseError(number, f"duplicate {prefix}")
                    terminals[prefix] = hub.name
                hubs[hub.name] = hub
            elif prefix == "connection":
                edge = self._connection(content, hubs, number)
                if edge.key in edges:
                    raise ParseError(number, "duplicate undirected connection")
                edges[edge.key] = edge
            else:
                raise ParseError(number, f"unknown declaration {prefix!r}")
        eof = len(lines) + 1
        if count is None:
            raise ParseError(eof, "missing nb_drones declaration")
        if "start_hub" not in terminals or "end_hub" not in terminals:
            raise ParseError(eof, "exactly one start_hub and end_hub required")
        return Network(count, hubs, edges, terminals["start_hub"],
                       terminals["end_hub"])

    def _metadata(self, content: str, allowed: set[str],
                  line: int) -> tuple[list[str], dict[str, str]]:
        """Separate the positional fields from one optional metadata block."""
        match = re.fullmatch(r"([^\[\]]*?)(?:\[([^\[\]]*)\])?", content)
        if match is None:
            raise ParseError(line, "malformed metadata brackets")
        fields = match.group(1).split()
        metadata: dict[str, str] = {}
        for token in (match.group(2) or "").split():
            key, separator, value = token.partition("=")
            if not separator or not value or "=" in value:
                raise ParseError(line, f"invalid metadata {token!r}")
            if key not in allowed:
                raise ParseError(line, f"unknown metadata key {key!r}")
            if key in metadata:
                raise ParseError(line, f"duplicate metadata key {key!r}")
            metadata[key] = value
        return fields, metadata

    def _capacity(self, value: str, line: int) -> int:
        """Require a strictly positive decimal integer."""
        if not self._positive.fullmatch(value):
            raise ParseError(line, f"expected positive integer, got {value!r}")
        try:
            result = int(value)
        except ValueError as error:
            raise ParseError(
                line, "integer exceeds interpreter limit",
            ) from error
        if result < 1:
            raise ParseError(line, "capacity and drone count must be positive")
        return result

    def _hub(self, content: str, line: int) -> Hub:
        """Validate a zone's name, coordinates, type, and metadata."""
        fields, metadata = self._metadata(
            content, {"zone", "color", "max_drones"}, line,
        )
        if len(fields) != 3:
            raise ParseError(line, "zone requires: name x y [metadata]")
        name, x, y = fields
        if "-" in name:
            raise ParseError(line, "zone names cannot contain dashes")
        if not all(self._integer.fullmatch(v) for v in (x, y)):
            raise ParseError(line, "coordinates must be integers")
        try:
            zone = ZoneType(metadata.get("zone", "normal"))
        except ValueError as error:
            raise ParseError(line, "invalid zone type") from error
        capacity = self._capacity(metadata.get("max_drones", "1"), line)
        try:
            return Hub(name, int(x), int(y), zone, metadata.get("color"),
                       capacity)
        except ValueError as error:
            raise ParseError(
                line, "coordinate exceeds interpreter limit",
            ) from error

    def _connection(self, content: str, hubs: dict[str, Hub],
                    line: int) -> Connection:
        """Require already defined endpoints and a valid capacity."""
        fields, metadata = self._metadata(
            content, {"max_link_capacity"}, line,
        )
        if len(fields) != 1 or fields[0].count("-") != 1:
            raise ParseError(line, "connection requires: zone1-zone2")
        first, second = fields[0].split("-")
        if first not in hubs or second not in hubs:
            raise ParseError(line, "connection references undefined zone")
        capacity = self._capacity(
            metadata.get("max_link_capacity", "1"), line,
        )
        return Connection(first, second, capacity)
