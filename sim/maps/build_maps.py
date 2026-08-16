#!/usr/bin/env python3
"""
build_maps.py - the three competition maps, at the real measured sizes.

Dimensions come from the marked-up photos (all in cm):

  MAP 1  outer 120 x 90    inner walls 85 and 60, centre block 30 x 30,
                           exit chute 30 x 30 on the right, 60 below it
  MAP 2  outer 150 x 150   island 120 x 88, both gates on the left
  MAP 3  outer 150 x 118   two 60-wide arms at the top, 88 tall body

Every passage is 30 cm. Sector lines are black, straight across the
passage, 30 cm long. Start and finish are always outside the maze.

GRID: one character = 5 cm, so a passage is 6 characters and a wall is 1.
Real walls are about 2 cm, so each map comes out a few cm larger than the
tape measure says. The passage width - the number that decides whether the
robot fits - is exact, and that is the one that matters.

Re-run after any edit:   python3 build_maps.py
"""

import os

CELL = 30           # mm per character
PAD = 14            # characters of open floor around the maze (start/finish)
HERE = os.path.dirname(os.path.abspath(__file__))

CORR = 10           # 30 cm passage = 10 characters; a wall is 1 = 3 cm


def c(cm):
    """centimetres -> characters"""
    return int(round(cm * 10.0 / CELL))


class Grid:
    """Coordinates are in CHARACTERS, measured from the maze's own
    bottom-left corner. PAD is added when writing."""

    def __init__(self, w_cm, h_cm):
        self.mw, self.mh = c(w_cm) + 2, c(h_cm) + 2      # +2 for outer walls
        self.w, self.h = self.mw + 2 * PAD, self.mh + 2 * PAD
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

    def text(self):
        return "\n".join("".join(r) for r in reversed(self.g))


def X(ch):
    """maze character coordinate -> world mm"""
    return (ch + PAD) * CELL


def mid(ch):
    return X(ch) + CELL / 2.0


def write(fname, name, g, start, finish, sectors, gates):
    with open(os.path.join(HERE, fname), "w", encoding="utf-8") as fh:
        fh.write("!name %s\n!cell %d\n" % (name, CELL))
        fh.write("!start %.0f %.0f %.0f\n" % start)
        fh.write("!finish %.0f %.0f %.0f %.0f\n" % finish)
        for s in sectors:
            fh.write("!sector %.0f %.0f %.0f %.0f\n" % s)
        for gt in gates:
            fh.write("!gate %.0f %.0f %.0f %.0f\n" % gt)
        fh.write(g.text() + "\n")
    print("wrote %-22s %5.0f x %-4.0f cm   %2d sector lines"
          % (fname, (g.mw - 2) * CELL / 10.0, (g.mh - 2) * CELL / 10.0,
             len(sectors)))


# ===================================================================== #
# MAP 1 - 120 x 90 outer, three 30 cm bands.
# In at the top-left, east along the top, down on the right, west along
# the middle, down on the left, east along the bottom, out on the right.
# BEST GUESS from the photo - see docs/10_MAP_NOTES.md.
# ===================================================================== #
def map1():
    g = Grid(120, 96)
    g.border()
    w, h = c(120), c(96)                       # 40 x 32 characters

    # wall between the top and middle bands: gap on the RIGHT
    g.fill(1, 1 + 2 * CORR + 1, w - CORR, 1 + 2 * CORR + 1)
    # wall between the middle and bottom bands: gap on the LEFT
    g.fill(1 + CORR, 1 + CORR, w, 1 + CORR)

    g.fill(0, h - CORR + 1, 0, h, ".")                     # way in,  top-left
    g.fill(w + 1, 1, w + 1, CORR, ".")                     # way out, bottom-right

    start = (X(0) - 220, mid(h - CORR // 2), 0)
    finish = (X(w + 1), X(1), X(w + 1) + 500, X(CORR))
    sectors = [
        (X(3),      X(h - CORR + 1), X(3),      X(h)),
        (X(20),     X(h - CORR + 1), X(20),     X(h)),
        (X(w - 14), X(h - CORR + 1), X(w - 14), X(h)),
        (X(w - 4),  X(1 + CORR + 2), X(w - 4),  X(1 + 2 * CORR)),
        (X(20),     X(1 + CORR + 2), X(20),     X(1 + 2 * CORR)),
        (X(4),      X(1 + CORR + 2), X(4),      X(1 + 2 * CORR)),
        (X(14),     X(1), X(14), X(CORR)),
        (X(30),     X(1), X(30), X(CORR)),
    ]
    gates = [(X(0) - 60, X(h - CORR + 1), X(0), X(h)),
             (X(w + 1), X(1), X(w + 2), X(CORR))]
    write("map1.txt", "Map 1 - 120x90 serpentine", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 2 - 150 x 150, island 120 x 90 against the left wall.
# In at the top-left, round the outside of the island, out at the
# bottom-left. No dead ends.
# ===================================================================== #
def map2():
    W, H = 150, 150
    g = Grid(W, H)
    g.border()
    w, h = c(W), c(H)            # 30 x 30

    # the island: 120 wide, 90 tall, flush against the left wall
    g.fill(1, 1 + CORR, c(120), h - CORR)

    g.fill(0, h - CORR + 1, 0, h, ".")     # way in,  top-left
    g.fill(0, 1, 0, CORR, ".")             # way out, bottom-left

    start = (X(0) - 220, mid(h - CORR // 2), 0)
    finish = (X(0) - 500, X(1), X(0), X(CORR))
    sectors = [
        (X(2),  X(h - CORR + 1), X(2),  X(h)),
        (X(12), X(h - CORR + 1), X(12), X(h)),
        (X(22), X(h - CORR + 1), X(22), X(h)),
        (X(w - CORR + 1), X(22), X(w), X(22)),
        (X(w - CORR + 1), X(12), X(w), X(12)),
        (X(22), X(1), X(22), X(CORR)),
        (X(12), X(1), X(12), X(CORR)),
        (X(2),  X(1), X(2),  X(CORR)),
    ]
    gates = [(X(0) - 60, X(h - CORR + 1), X(0), X(h)),
             (X(0) - 60, X(1), X(0), X(CORR))]
    write("map2.txt", "Map 2 - 150x150 island loop", g, start, finish, sectors, gates)


# ===================================================================== #
# MAP 3 - 150 x 120 outer. A spine hangs down from the top wall between
# two 60 cm arms; blocks either side of it leave a snake, plus one
# dead-end stub off the bottom passage.
# BEST GUESS from the photo - see docs/10_MAP_NOTES.md.
# ===================================================================== #
def map3():
    g = Grid(150, 120)
    g.border()
    w, h = c(150), c(120)                      # 50 x 40 characters

    sp = 1 + 2 * CORR                          # spine starts 60 cm in
    g.fill(sp, h - 2 * CORR, sp + CORR - 1, h)         # the central spine
    g.fill(1 + CORR, 1 + CORR, sp - 1, h - 2 * CORR - 1)          # left block
    g.fill(sp + CORR, 1 + CORR, w - CORR, h - 2 * CORR - 1)       # right block
    g.fill(sp, 1 + CORR, sp + CORR - 1, h - 3 * CORR - 1)         # closes the stub

    g.fill(0, h - CORR + 1, 0, h, ".")                 # way in,  top-left
    g.fill(w + 1, h - CORR + 1, w + 1, h, ".")         # way out, top-right

    start = (X(0) - 220, mid(h - CORR // 2), 0)
    finish = (X(w + 1), X(h - CORR + 1), X(w + 1) + 500, X(h))
    sectors = [
        (X(3),      X(h - CORR + 1), X(3),      X(h)),
        (X(1),      X(h - CORR - 4), X(CORR),   X(h - CORR - 4)),
        (X(1),      X(6),  X(CORR), X(6)),
        (X(18),     X(1),  X(18),   X(CORR)),
        (X(32),     X(1),  X(32),   X(CORR)),
        (X(w - CORR + 1), X(6), X(w), X(6)),
        (X(w - CORR + 1), X(h - CORR - 4), X(w), X(h - CORR - 4)),
        (X(w - 3),  X(h - CORR + 1), X(w - 3), X(h)),
    ]
    gates = [(X(0) - 60, X(h - CORR + 1), X(0), X(h)),
             (X(w + 1), X(h - CORR + 1), X(w + 2), X(h))]
    write("map3.txt", "Map 3 - 150x120 spine snake", g, start, finish, sectors, gates)


# ===================================================================== #
# Practice: one corner. Build this on your floor first.
# ===================================================================== #
def practice():
    W, H = 120, 90
    g = Grid(W, H)
    g.border()
    w, h = c(W), c(H)
    g.fill(1 + CORR, 1 + CORR, w, h)          # one big block, leaving an L
    g.fill(0, h - CORR + 1, 0, h, ".")
    g.fill(1, 0, CORR, 0, ".")

    start = (X(0) - 220, mid(h - CORR // 2), 0)
    finish = (X(1), X(0) - 500, X(CORR), X(0))
    sectors = [
        (X(2), X(h - CORR + 1), X(2), X(h)),
        (X(1), X(6), X(CORR), X(6)),
    ]
    gates = [(X(0) - 60, X(h - CORR + 1), X(0), X(h)),
             (X(1), X(0) - 60, X(CORR), X(0))]
    write("practice.txt", "Practice - one corner", g, start, finish, sectors, gates)


if __name__ == "__main__":
    map1(); map2(); map3(); practice()
    print("\npassage width: %d cm everywhere" % (CORR * CELL / 10))
