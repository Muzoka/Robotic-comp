"""
render.py - draws what is happening, using Pillow only.

Produces an animated GIF you can scrub through, plus a still of the path.
No pygame, no matplotlib, no numpy: `pip install pillow` and you are done.
"""

import math
import os

from PIL import Image, ImageDraw

WALL = (38, 40, 46)
FLOOR = (247, 247, 245)
GRID = (226, 226, 222)
SECTOR = (24, 24, 24)
SECTOR_DONE = (34, 160, 92)
GATE_A = (30, 30, 30)
GATE_B = (250, 250, 250)
TRAIL = (60, 130, 245)
BODY = (222, 76, 60)
BODY_DK = (150, 40, 30)
BEAM = (250, 176, 46)
TEXT = (25, 25, 25)
PANEL = (255, 255, 255)


class Renderer:
    def __init__(self, maze, px_per_mm=0.26, hud_h=118):
        self.m = maze
        self.k = px_per_mm
        self.hud = hud_h
        self.W = int(maze.width_mm * self.k)
        self.H = int(maze.height_mm * self.k) + hud_h
        self._bg = self._draw_static()

    # ------------------------------------------------------------------
    def _p(self, x, y):
        """world mm -> pixel, flipping Y so up is up"""
        return (x * self.k, (self.m.height_mm - y) * self.k)

    def _draw_static(self):
        img = Image.new("RGB", (self.W, self.H), PANEL)
        d = ImageDraw.Draw(img)
        c = self.m.cell

        d.rectangle([0, 0, self.W, self.m.height_mm * self.k], fill=FLOOR)

        for gx in range(self.m.w + 1):
            x = gx * c * self.k
            d.line([(x, 0), (x, self.m.height_mm * self.k)], fill=GRID)
        for gy in range(self.m.h + 1):
            y = (self.m.height_mm - gy * c) * self.k
            d.line([(0, y), (self.W, y)], fill=GRID)

        for gy in range(self.m.h):
            for gx in range(self.m.w):
                if self.m.solid[gy][gx]:
                    x0, y0 = self._p(gx * c, (gy + 1) * c)
                    x1, y1 = self._p((gx + 1) * c, gy * c)
                    d.rectangle([x0, y0, x1, y1], fill=WALL)

        for g in self.m.gates:
            x1, y1, x2, y2 = g
            horiz = abs(x2 - x1) > abs(y2 - y1)
            n = int(max(abs(x2 - x1), abs(y2 - y1)) // 40) + 1
            for i in range(n):
                col = GATE_A if i % 2 == 0 else GATE_B
                if horiz:
                    a = min(x1, x2) + i * 40
                    p0 = self._p(a, max(y1, y2))
                    p1 = self._p(min(a + 40, max(x1, x2)), min(y1, y2))
                else:
                    a = min(y1, y2) + i * 40
                    p0 = self._p(min(x1, x2), min(a + 40, max(y1, y2)))
                    p1 = self._p(max(x1, x2), a)
                d.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=col)

        if self.m.finish:
            x1, y1, x2, y2 = self.m.finish
            p0 = self._p(min(x1, x2), max(y1, y2))
            p1 = self._p(max(x1, x2), min(y1, y2))
            d.rectangle([p0[0], p0[1], p1[0], p1[1]],
                        outline=SECTOR_DONE, width=3)

        sx, sy, sh = self.m.start
        p = self._p(sx, sy)
        d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7],
                  outline=(40, 120, 220), width=3)
        a = math.radians(sh)
        d.line([p, (p[0] + 34 * math.cos(a), p[1] - 34 * math.sin(a))],
               fill=(40, 120, 220), width=3)
        return img

    # ------------------------------------------------------------------
    def frame(self, robot, nav_out, state_name, elapsed):
        img = self._bg.copy()
        d = ImageDraw.Draw(img)

        for s in self.m.sectors:
            col = SECTOR_DONE if s.scored else SECTOR
            d.line([self._p(s.x1, s.y1), self._p(s.x2, s.y2)],
                   fill=col, width=4 if s.scored else 3)

        if len(robot.trail) > 1:
            pts = [self._p(x, y) for (x, y) in robot.trail[::2]]
            d.line(pts, fill=TRAIL, width=2)

        # sonar beams
        for i, (mx, my, mang) in enumerate(robot.p.sonar_mounts):
            c, s = math.cos(robot.th), math.sin(robot.th)
            ox = robot.x + mx * c - my * s
            oy = robot.y + mx * s + my * c
            ang = robot.th + math.radians(mang)
            dist = min(robot.sonar[i], 900)
            d.line([self._p(ox, oy),
                    self._p(ox + dist * math.cos(ang), oy + dist * math.sin(ang))],
                   fill=BEAM, width=2)

        pts = [self._p(x, y) for (x, y) in robot.corners()]
        d.polygon(pts, fill=BODY, outline=BODY_DK)
        nose = self._p(robot.x + robot.p.axle_from_nose * math.cos(robot.th),
                       robot.y + robot.p.axle_from_nose * math.sin(robot.th))
        d.ellipse([nose[0] - 4, nose[1] - 4, nose[0] + 4, nose[1] + 4], fill=(20, 20, 20))

        # ---- HUD ----
        y0 = self.m.height_mm * self.k + 6
        d.rectangle([0, y0 - 6, self.W, self.H], fill=PANEL)
        total = len(self.m.sectors)
        got = sum(1 for s in self.m.sectors if s.scored)
        lines = [
            "%-26s  t = %5.1f s" % (self.m.name, elapsed),
            "state %-11s  sectors %d / %d   bumps %d" % (state_name, got, total, robot.bumps),
            "sonar  F %4d   L %4d   R %4d  mm" % tuple(robot.sonar),
            "heading %7.1f deg   target %7.1f deg   pwm %4d / %4d"
            % (robot.gyro_heading, nav_out.dbg_target_deg,
               nav_out.pwm_left, nav_out.pwm_right),
        ]
        for i, t in enumerate(lines):
            d.text((10, y0 + i * 17), t, fill=TEXT)
        return img


def save_gif(frames, path, fps=15):
    if not frames:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0, optimize=True)
