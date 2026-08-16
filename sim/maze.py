"""
maze.py - the maze the robot drives in.

A map is a plain text file you can edit in Notepad. Every character is one
square cell:

    #   wall
    .   free floor
    space  also free floor

Header lines start with '!' :

    !name    <text>
    !cell    <mm per character>        e.g. 100
    !start   <x_mm> <y_mm> <heading_deg>
    !finish  <x1> <y1> <x2> <y2>       rectangle, mm
    !sector  <x1> <y1> <x2> <y2>       a black line worth one point
    !gate    <x1> <y1> <x2> <y2>       striped start/finish marking

The bottom-left corner of the grid is (0, 0). X grows right, Y grows up,
headings are degrees counter-clockwise from +X. That matches the firmware.
"""

import math
import os


class Sector:
    __slots__ = ("x1", "y1", "x2", "y2", "passed", "scored")

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.passed = [False, False, False]   # left wheel, right wheel, caster
        self.scored = False


class Maze:
    def __init__(self, path):
        self.name = os.path.basename(path)
        self.cell = 100.0
        self.start = (300.0, 300.0, 0.0)
        self.finish = None
        self.sectors = []
        self.gates = []
        self.solid = []          # solid[gy][gx], gy = 0 is the BOTTOM row
        self._load(path)

    # ------------------------------------------------------------------
    def _load(self, path):
        rows = []
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if line.startswith("!"):
                    self._header(line[1:].strip())
                elif line.startswith("#!") or line.strip().startswith(";"):
                    continue
                elif line.strip() == "" and not rows:
                    continue
                else:
                    rows.append(line)

        while rows and rows[-1].strip() == "":
            rows.pop()
        if not rows:
            raise ValueError("%s has no grid" % path)

        w = max(len(r) for r in rows)
        # text row 0 is the TOP of the map, so flip it into world order
        self.solid = []
        for r in reversed(rows):
            r = r.ljust(w)
            self.solid.append([c == "#" for c in r])
        self.h = len(self.solid)
        self.w = w

    def _header(self, s):
        if not s:
            return
        parts = s.split()
        key = parts[0].lower()
        v = [float(x) for x in parts[1:]] if key != "name" else None
        if key == "name":
            self.name = s[4:].strip()
        elif key == "cell":
            self.cell = v[0]
        elif key == "start":
            self.start = (v[0], v[1], v[2] if len(v) > 2 else 0.0)
        elif key == "finish":
            self.finish = (v[0], v[1], v[2], v[3])
        elif key == "sector":
            self.sectors.append(Sector(v[0], v[1], v[2], v[3]))
        elif key == "gate":
            self.gates.append((v[0], v[1], v[2], v[3]))

    # ------------------------------------------------------------------
    def scale(self, k):
        """Stretch the whole map by k. The shape is unchanged, only the
        corridor width, so this is how you ask 'does the robot still fit
        if the passages are 400 mm instead of 300 mm?'"""
        self.cell *= k
        self.start = (self.start[0] * k, self.start[1] * k, self.start[2])
        if self.finish:
            self.finish = tuple(v * k for v in self.finish)
        for s in self.sectors:
            s.x1 *= k; s.y1 *= k; s.x2 *= k; s.y2 *= k
        self.gates = [tuple(v * k for v in g) for g in self.gates]
        self.name = "%s  [corridor %.0f mm]" % (self.name.split("  [")[0],
                                                3 * self.cell)

    @property
    def width_mm(self):
        return self.w * self.cell

    @property
    def height_mm(self):
        return self.h * self.cell

    def is_solid(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= self.w or gy >= self.h:
            return True          # outside the sheet counts as wall
        return self.solid[gy][gx]

    def solid_at(self, x, y):
        return self.is_solid(int(math.floor(x / self.cell)),
                             int(math.floor(y / self.cell)))

    # ------------------------------------------------------------------
    def raycast(self, ox, oy, ang_deg, max_mm):
        """Shoot a ray and return (distance_mm, incidence_deg).

        incidence is the angle between the ray and the surface normal it
        hit; 0 means dead-on. Ultrasound needs a small incidence to come
        back, which is exactly why sonar loses walls it meets at a slant.
        Returns (None, None) when the ray hits nothing inside max_mm.
        """
        c = self.cell
        a = math.radians(ang_deg)
        dx, dy = math.cos(a), math.sin(a)

        gx = int(math.floor(ox / c))
        gy = int(math.floor(oy / c))

        if self.is_solid(gx, gy):
            return 0.0, 0.0

        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1
        inf = float("inf")

        t_dx = abs(c / dx) if dx != 0 else inf
        t_dy = abs(c / dy) if dy != 0 else inf

        if dx > 0:
            t_max_x = ((gx + 1) * c - ox) / dx
        elif dx < 0:
            t_max_x = (gx * c - ox) / dx
        else:
            t_max_x = inf

        if dy > 0:
            t_max_y = ((gy + 1) * c - oy) / dy
        elif dy < 0:
            t_max_y = (gy * c - oy) / dy
        else:
            t_max_y = inf

        t = 0.0
        guard = 0
        while t <= max_mm and guard < 4096:
            guard += 1
            if t_max_x < t_max_y:
                gx += step_x
                t = t_max_x
                t_max_x += t_dx
                normal = (-step_x, 0)
            else:
                gy += step_y
                t = t_max_y
                t_max_y += t_dy
                normal = (0, -step_y)

            if t > max_mm:
                return None, None
            if self.is_solid(gx, gy):
                cosang = -(dx * normal[0] + dy * normal[1])
                cosang = max(-1.0, min(1.0, cosang))
                return t, math.degrees(math.acos(abs(cosang)))
        return None, None

    # ------------------------------------------------------------------
    def rect_hits_wall(self, corners):
        """corners: 4 (x, y) points of the robot body, in order."""
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        c = self.cell
        gx0 = int(math.floor(min(xs) / c))
        gx1 = int(math.floor(max(xs) / c))
        gy0 = int(math.floor(min(ys) / c))
        gy1 = int(math.floor(max(ys) / c))

        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                if not self.is_solid(gx, gy):
                    continue
                box = [(gx * c, gy * c), ((gx + 1) * c, gy * c),
                       ((gx + 1) * c, (gy + 1) * c), (gx * c, (gy + 1) * c)]
                if _sat_overlap(corners, box):
                    return True
        return False

    # ------------------------------------------------------------------
    def update_sectors(self, prev_pts, now_pts):
        """prev_pts / now_pts: the three wheel contact points.
        Returns how many new sector points were earned this tick."""
        gained = 0
        for s in self.sectors:
            if s.scored:
                continue
            for i in range(3):
                if s.passed[i]:
                    continue
                if _seg_cross(prev_pts[i], now_pts[i],
                              (s.x1, s.y1), (s.x2, s.y2)):
                    s.passed[i] = True
            if all(s.passed):
                s.scored = True
                gained += 1
        return gained

    def on_black(self, pt):
        """Is the floor sensor over a black mark right now?"""
        for s in self.sectors:
            if _point_near_seg(pt, (s.x1, s.y1), (s.x2, s.y2)) < 12.0:
                return True
        for g in self.gates:
            # gates are painted as ~40 mm stripes with 40 mm gaps
            x1, y1, x2, y2 = g
            if min(x1, x2) - 5 <= pt[0] <= max(x1, x2) + 5 and \
               min(y1, y2) - 5 <= pt[1] <= max(y1, y2) + 5:
                along = pt[0] if abs(x2 - x1) > abs(y2 - y1) else pt[1]
                if int(along // 40) % 2 == 0:
                    return True
        return False


# ---------------------------------------------------------------------- #
# geometry helpers
# ---------------------------------------------------------------------- #
def _sat_overlap(a, b):
    """Separating-axis test for two convex polygons."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            ax, ay = -(y2 - y1), (x2 - x1)
            amin = amax = None
            bmin = bmax = None
            for (px, py) in a:
                v = px * ax + py * ay
                amin = v if amin is None or v < amin else amin
                amax = v if amax is None or v > amax else amax
            for (px, py) in b:
                v = px * ax + py * ay
                bmin = v if bmin is None or v < bmin else bmin
                bmax = v if bmax is None or v > bmax else bmax
            if amax < bmin or bmax < amin:
                return False
    return True


def _side(p, a, b):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _seg_cross(p1, p2, q1, q2):
    d1 = _side(p1, q1, q2)
    d2 = _side(p2, q1, q2)
    d3 = _side(q1, p1, p2)
    d4 = _side(q2, p1, p2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _point_near_seg(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
    cx, cy = a[0] + t * vx, a[1] + t * vy
    return math.hypot(p[0] - cx, p[1] - cy)
