#!/usr/bin/env python3
"""
build_maps.py - writes the .txt maps.

These are RECONSTRUCTIONS of the three competition maps from the photos:
an inward spiral, a serpentine, and a loop around a central island. The
photos are taken at an angle, so treat the exact millimetres as a guess and
the shape as the point. When you get to see the real maze, re-measure it,
edit the numbers here (or edit the .txt directly - it is just characters)
and re-run:  python3 build_maps.py

Grid: 1 character = 100 mm. Corridors are 3 characters = 300 mm, the middle
of the rulebook's 200-400 mm range. Walls are 1 character.

The written grid is PAD cells bigger than the maze on every side, and that
ring is open floor: that is the start zone and the finish zone.
"""

import os

CELL = 100
PAD = 4
HERE = os.path.dirname(os.path.abspath(__file__))


class Grid:
    def __init__(self, mw, mh):
        self.mw, self.mh = mw, mh
        self.w, self.h = mw + 2 * PAD, mh + 2 * PAD
        self.g = [["." for _ in range(self.w)] for _ in range(self.h)]

    def fill(self, x0, y0, x1, y1, ch="#"):
        x0 += PAD; x1 += PAD; y0 += PAD; y1 += PAD
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.g[y][x] = ch

    def border(self):
        self.fill(0, 0, self.mw - 1, 0)
        self.fill(0, self.mh - 1, self.mw - 1, self.mh - 1)
        self.fill(0, 0, 0, self.mh - 1)
        self.fill(self.mw - 1, 0, self.mw - 1, self.mh - 1)

    def ring(self, x0, y0, x1, y1):
        self.fill(x0, y0, x1, y0)
        self.fill(x0, y1, x1, y1)
        self.fill(x0, y0, x0, y1)
        self.fill(x1, y0, x1, y1)

    def text(self):
        return "\n".join("".join(row) for row in reversed(self.g))


def X(c):
    """maze cell coordinate -> world mm (left/bottom edge of that cell)"""
    return (c + PAD) * CELL


def mid(c):
    return X(c) + CELL / 2.0


def write(fname, name, grid, start, finish, sectors, gates):
    with open(os.path.join(HERE, fname), "w", encoding="utf-8") as fh:
        fh.write("!name %s\n" % name)
        fh.write("!cell %d\n" % CELL)
        fh.write("!start %.0f %.0f %.0f\n" % start)
        fh.write("!finish %.0f %.0f %.0f %.0f\n" % finish)
        for s in sectors:
            fh.write("!sector %.0f %.0f %.0f %.0f\n" % s)
        for g in gates:
            fh.write("!gate %.0f %.0f %.0f %.0f\n" % g)
        fh.write(grid.text() + "\n")
    print("wrote %-24s maze %2d x %-2d cells  (%.1f x %.1f m)  %d sectors"
          % (fname, grid.mw, grid.mh, grid.mw * CELL / 1000.0,
             grid.mh * CELL / 1000.0, len(sectors)))


# ===================================================================== #
# MAP 1 - inward spiral, finish in the middle chamber (photo 1)
# ===================================================================== #
def map1():
    g = Grid(21, 21)
    g.border()
    g.ring(4, 4, 16, 16)
    g.ring(8, 8, 12, 12)
    g.fill(0, 9, 0, 11, ".")       # way in, left-middle
    g.fill(9, 4, 11, 4, ".")       # gap down into the middle corridor
    g.fill(9, 12, 11, 12, ".")     # gap up into the centre chamber

    start = (X(0) - 250, mid(10), 0)
    finish = (X(9), X(9), X(12), X(12))
    sectors = [
        (X(0.5), X(9),    X(0.5),  X(12)),
        (X(1),   X(4.5),  X(4),    X(4.5)),
        (X(16.5), X(1),   X(16.5), X(4)),
        (X(17),  X(16.5), X(20),   X(16.5)),
        (X(5),   X(8.5),  X(8),    X(8.5)),
        (X(12.5), X(5),   X(12.5), X(8)),
        (X(9),   X(12.5), X(12),   X(12.5)),
    ]
    gates = [(X(0) - 60, X(9), X(0.6), X(12)),
             (X(9), X(12.4), X(12), X(13))]        # finish gate, centre chamber
    write("map1_spiral.txt", "Map 1 - Inward Spiral", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 2 - serpentine, in top-left, out bottom-left (photo 2)
# ===================================================================== #
def map2():
    g = Grid(24, 17)
    g.border()
    g.fill(1, 12, 19, 12)          # band A -> B, gap on the right
    g.fill(4, 8, 22, 8)            # band B -> C, gap on the left
    g.fill(1, 4, 19, 4)            # band C -> D, gap on the right
    g.fill(0, 13, 0, 15, ".")      # way in,  top-left
    g.fill(0, 1, 0, 3, ".")        # way out, bottom-left

    start = (X(0) - 250, mid(14), 0)
    finish = (X(0) - 400, X(1), X(0), X(4))
    sectors = [
        (X(0.5), X(13), X(0.5), X(16)),
        (X(8),   X(13), X(8),   X(16)),
        (X(16),  X(13), X(16),  X(16)),
        (X(20.5), X(9), X(23),  X(9)),
        (X(12),  X(9),  X(12),  X(12)),
        (X(4),   X(9),  X(4),   X(12)),
        (X(1),   X(6.5), X(4),  X(6.5)),
        (X(12),  X(5),  X(12),  X(8)),
        (X(20),  X(5),  X(20),  X(8)),
        (X(16),  X(1),  X(16),  X(4)),
        (X(8),   X(1),  X(8),   X(4)),
        (X(0.5), X(1),  X(0.5), X(4)),
    ]
    gates = [(X(0) - 60, X(13), X(0.6), X(16)),
             (X(0) - 60, X(1),  X(0.6), X(4))]
    write("map2_serpentine.txt", "Map 2 - Serpentine", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 3 - loop around a central island (photo 3)
# ===================================================================== #
def map3():
    g = Grid(24, 18)
    g.border()
    g.fill(4, 4, 19, 13)           # the island
    g.fill(1, 8, 3, 8)             # stub, forces the long way round
    g.fill(0, 14, 0, 16, ".")      # way in,  top-left
    g.fill(0, 1, 0, 3, ".")        # way out, bottom-left

    start = (X(0) - 250, mid(15), 0)
    finish = (X(0) - 400, X(1), X(0), X(4))
    sectors = [
        (X(0.5), X(14), X(0.5), X(17)),
        (X(6),   X(14), X(6),   X(17)),
        (X(14),  X(14), X(14),  X(17)),
        (X(20),  X(14), X(23),  X(14)),
        (X(20),  X(9),  X(23),  X(9)),
        (X(20),  X(4),  X(23),  X(4)),
        (X(16),  X(1),  X(16),  X(4)),
        (X(8),   X(1),  X(8),   X(4)),
        (X(0.5), X(1),  X(0.5), X(4)),
    ]
    gates = [(X(0) - 60, X(14), X(0.6), X(17)),
             (X(0) - 60, X(1),  X(0.6), X(4))]
    write("map3_loop.txt", "Map 3 - Island Loop", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 4 - the first thing you should ever run: one corner
# ===================================================================== #
def map4():
    g = Grid(14, 12)
    g.border()
    g.fill(4, 4, 12, 10)
    g.fill(0, 7, 0, 9, ".")
    g.fill(5, 0, 7, 0, ".")

    start = (X(0) - 250, mid(8), 0)
    finish = (X(5), X(0) - 400, X(8), X(0))
    sectors = [
        (X(0.5), X(7), X(0.5), X(10)),
        (X(2.5), X(1), X(2.5), X(4)),
        (X(5), X(0.5), X(8), X(0.5)),
    ]
    gates = [(X(0) - 60, X(7), X(0.6), X(10)),
             (X(5), X(0) - 60, X(8), X(0.6))]
    write("map4_practice.txt", "Map 4 - Practice Corner", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 5 - dead ends and a loop: the map that separates a plain wall
# follower from a robot that remembers where it has been.
# ===================================================================== #
def map5():
    g = Grid(24, 20)
    g.border()
    g.fill(4, 4, 8, 15)
    g.fill(12, 8, 19, 15)
    g.fill(12, 4, 15, 5)
    g.fill(19, 1, 19, 5)
    g.fill(0, 16, 0, 18, ".")      # way in,  top-left
    g.fill(20, 0, 22, 0, ".")      # way out, bottom-right

    start = (X(0) - 250, mid(17), 0)
    finish = (X(20), X(0) - 400, X(23), X(0))
    sectors = [
        (X(0.5), X(16), X(0.5), X(19)),
        (X(10),  X(16), X(10),  X(19)),
        (X(20),  X(16), X(20),  X(19)),
        (X(20),  X(6.5), X(23), X(6.5)),
        (X(10),  X(2),  X(10),  X(3.5)),
        (X(2),   X(2.5), X(3.5), X(2.5)),
        (X(20),  X(0.5), X(23), X(0.5)),
    ]
    gates = [(X(0) - 60, X(16), X(0.6), X(19)),
             (X(20), X(0) - 60, X(23), X(0.6))]
    write("map5_deadends.txt", "Map 5 - Dead Ends and a Loop", g, start, finish, sectors, gates)


if __name__ == "__main__":
    map1(); map2(); map3(); map4(); map5()
    print("\nThe .txt files are plain characters - edit a wall by hand any time.")
