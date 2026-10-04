"""Represent the cube's 48 movable stickers and solve it with NCGE."""

import json
from math import prod
from pathlib import Path
from ncge_table import NCGETable

def identity(size: int):
    return tuple(range(size))

def invert_perm(permutation):
    inverse = [0] * len(permutation)
    for source, destination in enumerate(permutation):
        inverse[destination] = source
    return tuple(inverse)

def compose(first, second):
    return tuple(first[index] for index in second)

# Number each face left to right, top to bottom, skipping its center.
# Each label identifies the physical piece carrying that sticker.
FACE_PIECES = {
    "U": ("UBL", "UB", "URB", "UL", "UR", "ULF", "UF", "UFR"),
    "R": ("UFR", "UR", "URB", "FR", "BR", "DFR", "DR", "DRB"),
    "F": ("ULF", "UF", "UFR", "FL", "FR", "DLF", "DF", "DFR"),
    "D": ("DLF", "DF", "DFR", "DL", "DR", "DBL", "DB", "DRB"),
    "L": ("UBL", "UL", "ULF", "BL", "FL", "DBL", "DL", "DLF"),
    "B": ("URB", "UB", "UBL", "BR", "BL", "DRB", "DB", "DBL"),
}

# A clockwise turn changes stickers between these faces in order.
FACE_CYCLES = {
    "U": ("F", "L", "B", "R"),
    "D": ("F", "R", "B", "L"),
    "R": ("U", "B", "D", "F"),
    "L": ("U", "F", "D", "B"),
    "F": ("U", "R", "D", "L"),
    "B": ("U", "L", "D", "R"),
}

STICKERS = []
for sticker_face, pieces in FACE_PIECES.items():
    for piece in pieces:
        STICKERS.append((frozenset(piece), sticker_face))

STICKER_INDICES = {}
for index, sticker in enumerate(STICKERS):
    STICKER_INDICES[sticker] = index

def face_turn(face):
    """Return a clockwise 90 degree turn of the given face."""
    cycle = FACE_CYCLES[face]
    rotated_faces = {}
    for index, adjacent_face in enumerate(cycle):
        rotated_faces[adjacent_face] = cycle[(index + 1) % len(cycle)]

    permutation = list(identity(48))
    for source, (piece_faces, sticker_face) in enumerate(STICKERS):
        if face not in piece_faces:
            continue

        destination_faces = []
        for piece_face in piece_faces:
            destination_faces.append(rotated_faces.get(piece_face, piece_face))
        destination_face = rotated_faces.get(sticker_face, sticker_face)
        destination = STICKER_INDICES[(frozenset(destination_faces), destination_face)]
        permutation[destination] = source

    return tuple(permutation)

generators = {}
for face in FACE_CYCLES:
    generators[face] = face_turn(face)
for face, permutation in list(generators.items()):
    generators[face + "'"] = invert_perm(permutation)

class CubeSolver:
    def __init__(self, cache_path=None):
        self.table = None
        if cache_path is None:
            cache_path = Path(__file__).with_name("ncge_cache.json")
        self.cache_path = Path(cache_path)

    def _load_table(self):
        try:
            with self.cache_path.open(encoding="utf-8") as cache_file:
                data = json.load(cache_file)
            expected_generators = {name: list(move) for name, move in generators.items()}
            if data["version"] != 1 or data["generators"] != expected_generators:
                return None

            table = NCGETable(48)
            for pivot, target, permutation, word in data["entries"]:
                if sorted(permutation) != list(range(48)):
                    return None
                permutation = tuple(permutation)
                if table.pivot(permutation) != (pivot, target):
                    return None
                if not isinstance(word, list):
                    return None
                evaluated = table.ID
                for move in word:
                    evaluated = compose(evaluated, generators[move])
                if evaluated != permutation or (pivot, target) in table.table:
                    return None
                table.table[(pivot, target)] = (permutation, word)

            row_sizes = [1] * 48
            for pivot, target in table.table:
                row_sizes[pivot] += 1
            if prod(row_sizes) != 43252003274489856000:
                return None

            for name, permutation in generators.items():
                table.generator_orders[name.rstrip("'")] = table.permutation_order(permutation)
            return table
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None

    def _save_table(self):
        entries = []
        for (pivot, target), (permutation, word) in self.table.table.items():
            entries.append([pivot, target, permutation, word])
        data = {"version": 1, "generators": generators, "entries": entries}

        with self.cache_path.open("w", encoding="utf-8") as cache_file:
            json.dump(data, cache_file)

    def prepare_table(self, on_status=None):
        if self.table is not None:
            return
        if self.cache_path.is_file():
            if on_status is not None:
                on_status("Loading table...")
            self.table = self._load_table()
        if self.table is None:
            if on_status is not None:
                on_status("Generating table...")
            table = NCGETable(48)
            table.build(generators)
            self.table = table
            self._save_table()

    def solve(self, permutation, on_status=None):
        if sorted(permutation) != list(range(48)):
            raise ValueError("The cube state must be a permutation of 0 to 47.")

        self.prepare_table(on_status)
        return self.table.reduce(permutation)
