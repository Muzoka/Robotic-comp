#!/usr/bin/env python3
"""
build_maps.py - the three competition maps, straight out of the organisers'
spreadsheet (Robotics_Competition_Maps_v2_5x5_grid.xlsx), plus the combined
course.

From the Specifications column of that file:

    Total dimension  = 5 ft x 5 ft  + total wall thickness
    Each grid        = 1 ft x 1 ft          -> passage = 304.8 mm
    Wall thickness   = 0.75 inch            -> 19.05 mm
    Wall height      = 7.5 inches           -> 190.5 mm

Each sheet is a 5 x 5 block of cells B2:F6. A blue cell is open floor, a
white cell is a solid block. Entrance and exit are labelled on the sheet and
are always on the LEFT and RIGHT walls.

Sector counts are the ones printed on the sheets: 3, 5 and 9. They are laid
out evenly along the route, because the sheet does not say where they go.

GRID: one character = 1 inch = 25.4 mm, so one foot is exactly 12
characters. Nothing is rounded.

Re-run after any edit:   python3 build_maps.py
"""

import os
from collections import deque

CELL = 25.4                  # mm per character = 1 inch
FOOT = 12                    # characters per foot
PAD = 26                     # open floor around the maze
POCKET = 20                  # depth of the walled start / finish zones, chars
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------- #
# The three sheets. Rows run top (spreadsheet row 2) to bottom (row 6),
# columns B..F. 'P' = blue = open floor, 'X' = white = solid block.
# ---------------------------------------------------------------------- #
SHEETS = {
    "map1": {
        "grid": ["PPPPP",
                 "PXXXP",
                 "PXXXP",
                 "PXXXP",
                 "PXXXP"],
        "entrance": (4, 0),          # B6, on the left wall
        "exit":     (4, 4),          # F6, on the right wall
        "sectors":  3,
        "title": "Map 1",
    },
    "map2": {
        "grid": ["PPPPX",
                 "XXXPX",
                 "XPPPP",
                 "XPXPX",
                 "XPPPX"],
        "entrance": (0, 0),          # B2
        "exit":     (2, 4),          # F4
        "sectors":  5,
        "title": "Map 2",
    },
    "map3": {
        "grid": ["PPXPP",
                 "XPXPX",
                 "PPXPP",
                 "PXXXP",
                 "PPPPP"],
        "entrance": (0, 0),          # B2
        "exit":     (0, 4),          # F2
        "sectors":  9,
        "title": "Map 3",
    },
}

# ---------------------------------------------------------------------- #
# How the three sections are joined into the final course.
#
# Each entry is (sheet name, mirror vertically?). Mirroring is what makes
# the gates line up: read left to right, every exit lands on the same row as
# the next entrance, so the shared wall has ONE opening in it.
#
#   map1            in left row 5  ->  out right row 5
#   map3 mirrored   in left row 5  ->  out right row 5
#   map2 mirrored   in left row 5  ->  out right row 3   (the finish)
#
# If the organisers butt the sections together in a different order, change
# this one list and re-run. Nothing else needs touching.
# ---------------------------------------------------------------------- #
COURSE = [("map1", False), ("map3", True), ("map2", True)]


# ---------------------------------------------------------------------- #
def mirror(sheet):
    """Flip a sheet top-to-bottom."""
    g = list(reversed(sheet["grid"]))
    n = len(sheet["grid"]) - 1
    out = dict(sheet)
    out["grid"] = g
    out["entrance"] = (n - sheet["entrance"][0], sheet["entrance"][1])
    out["exit"] = (n - sheet["exit"][0], sheet["exit"][1])
    return out


DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]      # E, S, W, N  (row, col)


def coverage_walk(grid, ent, goal, hand=-1, limit=600):
    """Walk the maze exactly as the robot does - keeping one hand on the
    wall - and return every square it steps on, in order.

    This is what the route really is. The robot is required to drive the
    WHOLE road before it leaves, not the shortest way across, so the sector
    lines and the length estimate have to follow the same walk."""
    R, C = len(grid), len(grid[0])

    def is_open(r, c):
        return 0 <= r < R and 0 <= c < C and grid[r][c] == "P"

    r, c = ent
    d = 0                                       # entering heading east
    path = [(r, c)]
    seen = {(r, c)}
    for _ in range(limit):
        if (r, c) == goal and len(seen) == sum(row.count("P") for row in grid):
            break
        order = ([(d + 3) % 4, d, (d + 1) % 4, (d + 2) % 4] if hand > 0
                 else [(d + 1) % 4, d, (d + 3) % 4, (d + 2) % 4])
        for nd in order:
            dr, dc = DIRS[nd]
            if is_open(r + dr, c + dc):
                d = nd
                r += dr
                c += dc
                path.append((r, c))
                seen.add((r, c))
                break
        else:
            break
    return path


def route(grid, start, goal, joins=None):
    """Shortest path between two cells, as a list of (row, col).

    joins maps a section boundary (the column to its left) to the one row
    where the wall between two sections is open. Without it the search
    happily walks through the wall and the sector lines land inside it."""
    joins = joins or {}
    R, C = len(grid), len(grid[0])
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        r, c = cur
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb = (r + dr, c + dc)
            if not (0 <= nb[0] < R and 0 <= nb[1] < C):
                continue
            if grid[nb[0]][nb[1]] != "P" or nb in prev:
                continue
            if dc != 0:
                left = min(c, nb[1])
                if (left + 1) % 5 == 0 and joins.get(left) != r:
                    continue          # that is a wall between two sections
            prev[nb] = cur
            q.append(nb)
    if goal not in prev:
        raise ValueError("no route from %s to %s" % (start, goal))
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return list(reversed(path))


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [["." for _ in range(w)] for _ in range(h)]

    def fill(self, x0, y0, x1, y1, ch="#"):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.g[y][x] = ch

    def text(self):
        return "\n".join("".join(r) for r in reversed(self.g))


def build(name, title, sections, fname):
    """sections: list of (sheet, mirrored). They sit side by side, sharing a
    wall column, and the shared wall carries a single opening."""
    rows = 5
    cols_total = 5 * len(sections)

    # character size: outer wall 1 char, then 5 cells of 12 chars per section
    sec_w = 5 * FOOT + 1               # 61: five feet plus the wall on its right
    W = 1 + sec_w * len(sections)
    H = 1 + 5 * FOOT + 1

    cv = Canvas(W + 2 * PAD, H + 2 * PAD)

    def cx(col):                        # left edge of a cell column
        return PAD + 1 + col * FOOT + (col // 5)

    def cy(row):                        # bottom edge of a cell row (row 0 = top)
        return PAD + 1 + (rows - 1 - row) * FOOT

    # outer wall of the whole course
    cv.fill(PAD, PAD, PAD + W - 1, PAD)
    cv.fill(PAD, PAD + H - 1, PAD + W - 1, PAD + H - 1)
    cv.fill(PAD, PAD, PAD, PAD + H - 1)
    cv.fill(PAD + W - 1, PAD, PAD + W - 1, PAD + H - 1)

    # wall columns between sections
    for i in range(1, len(sections)):
        x = PAD + i * sec_w
        cv.fill(x, PAD, x, PAD + H - 1)

    # the solid blocks
    for si, (sheet, _) in enumerate(sections):
        for r in range(rows):
            for c in range(5):
                if sheet["grid"][r][c] == "X":
                    col = si * 5 + c
                    cv.fill(cx(col), cy(r), cx(col) + FOOT - 1, cy(r) + FOOT - 1)

    # gates: the course entrance, the joins, and the finish
    first, last = sections[0][0], sections[-1][0]
    ent_row = first["entrance"][0]
    fin_row = last["exit"][0]
    cv.fill(PAD, cy(ent_row), PAD, cy(ent_row) + FOOT - 1, ".")
    cv.fill(PAD + W - 1, cy(fin_row), PAD + W - 1, cy(fin_row) + FOOT - 1, ".")
    for i in range(1, len(sections)):
        x = PAD + i * sec_w
        r = sections[i][0]["entrance"][0]
        assert r == sections[i - 1][0]["exit"][0], \
            "section %d exit row does not meet section %d entrance row" % (i - 1, i)
        cv.fill(x, cy(r), x, cy(r) + FOOT - 1, ".")

    # ---- route and sector lines ----
    grid = ["".join(sheet["grid"][r][c] for (sheet, _) in sections for c in range(5))
            for r in range(rows)]
    start = (ent_row, 0)
    goal = (fin_row, cols_total - 1)
    path = coverage_walk(grid, start, goal, hand=-1)
    n_open = sum(row.count("P") for row in grid)
    covered = len(set(path))

    n_sect = sum(sheet["sectors"] for (sheet, _) in sections)

    # A sector line is painted straight across a passage, so put each one in
    # the MIDDLE of a cell the route passes straight through. Putting one on
    # a corner is unfair to the robot and to the rulebook: "all three wheels
    # completely passes the sector line" is hard to satisfy while pivoting.
    # Put each sector line on a boundary the route crosses, so the robot
    # always meets it square-on and all three wheels pass it cleanly. A line
    # in the middle of a corner square would be crossed while pivoting, and
    # "all three wheels completely passes the sector line" (SS6.1) is then a
    # matter of luck.
    nb = len(path) - 1
    sectors = []
    for k in range(n_sect):
        i = int(round((k + 0.5) * nb / float(n_sect)))
        i = max(0, min(nb - 1, i))
        (r0, c0), (r1, c1) = path[i], path[i + 1]
        if r0 == r1:                                   # crossing sideways
            x = cx(max(c0, c1)) * CELL
            sectors.append((x, cy(r0) * CELL, x, (cy(r0) + FOOT) * CELL))
        else:                                          # crossing up or down
            y = cy(min(r0, r1)) * CELL + FOOT * CELL
            sectors.append((cx(c0) * CELL, y, (cx(c0) + FOOT) * CELL, y))

    # Walled start and finish pockets. Without them the robot can reverse
    # out of its own start gate, drive round the outside of the maze and
    # walk into the finish zone - which the simulator would score as a
    # completed run and a judge would score as nothing at all.
    for (side, row) in (("L", ent_row), ("R", fin_row)):
        y0, y1 = cy(row), cy(row) + FOOT - 1
        if side == "L":
            x0, x1 = PAD - POCKET, PAD - 1
        else:
            x0, x1 = PAD + W, PAD + W + POCKET - 1
        cv.fill(x0, y0 - 1, x1, y0 - 1)          # below
        cv.fill(x0, y1 + 1, x1, y1 + 1)          # above
        end = x0 if side == "L" else x1
        cv.fill(end, y0 - 1, end, y1 + 1)        # closed far end
        cv.fill(x0 + (1 if side == "L" else 0), y0,
                x1 - (0 if side == "L" else 1), y1, ".")

    gates = [((PAD - 2) * CELL, cy(ent_row) * CELL,
              PAD * CELL, (cy(ent_row) + FOOT) * CELL),
             ((PAD + W - 1) * CELL, cy(fin_row) * CELL,
              (PAD + W + 1) * CELL, (cy(fin_row) + FOOT) * CELL)]

    start_mm = ((PAD - POCKET + 10) * CELL, (cy(ent_row) + FOOT / 2.0) * CELL, 0)
    finish_mm = ((PAD + W + 2) * CELL, cy(fin_row) * CELL,
                 (PAD + W + POCKET - 2) * CELL, (cy(fin_row) + FOOT) * CELL)

    with open(os.path.join(HERE, fname), "w", encoding="utf-8") as fh:
        fh.write("!name %s\n!cell %.4f\n" % (title, CELL))
        fh.write("!grid %.1f %.1f %.1f %d %d\n"
                 % (cx(0) * CELL, cy(rows - 1) * CELL, FOOT * CELL,
                    cols_total, rows))
        fh.write("!start %.0f %.0f %.0f\n" % start_mm)
        fh.write("!finish %.0f %.0f %.0f %.0f\n" % finish_mm)
        for s in sectors:
            fh.write("!sector %.0f %.0f %.0f %.0f\n" % s)
        for g in gates:
            fh.write("!gate %.0f %.0f %.0f %.0f\n" % g)
        fh.write(cv.text() + "\n")

    print("%-10s %4.2f x %-4.2f m  road %2d squares  walk %2d ft  covers %2d/%-2d %s  %2d sectors"
          % (fname, W * CELL / 1000.0, H * CELL / 1000.0, n_open,
             len(path) - 1, covered, n_open,
             "OK " if covered == n_open else "!! ", len(sectors)))


if __name__ == "__main__":
    for key in ("map1", "map2", "map3"):
        s = SHEETS[key]
        build(key, "%s - 5x5 ft, %d sectors" % (s["title"], s["sectors"]),
              [(s, False)], key + ".txt")

    # The three maps are run as three separate courses, so no combined
    # course is generated. If that ever changes, uncomment this:
    #
    # secs = [(mirror(SHEETS[k]) if m else SHEETS[k], m) for (k, m) in COURSE]
    # build("course", "Combined course", secs, "course.txt")

    print("\npassage 304.8 mm (1 ft)   wall 19 mm   wall height 190 mm")
