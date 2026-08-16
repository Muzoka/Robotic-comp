"""
robot.py - the physical robot: motors that are never quite matched, sonar
that loses walls it meets at a slant, a gyro that drifts, and encoders
coarse enough to matter.

Everything here is deliberately pessimistic. A controller that survives
this file will survive a carpeted school hall.
"""

import math
import random

from cfg import get


class Params:
    """One place for every 'how bad is the hardware' knob."""

    def __init__(self):
        # ---- geometry (from config.h, so the firmware agrees) ----
        self.length = get("ROBOT_LENGTH_MM")
        self.width = get("ROBOT_WIDTH_MM")
        self.wheel_base = get("WHEEL_BASE_MM")
        self.wheel_diam = get("WHEEL_DIAM_MM")
        self.axle_from_nose = get("AXLE_FROM_NOSE_MM")

        self.sonar_mounts = [
            (get("US_F_X_MM"), get("US_F_Y_MM"), get("US_F_ANG")),
            (get("US_L_X_MM"), get("US_L_Y_MM"), get("US_L_ANG")),
            (get("US_R_X_MM"), get("US_R_Y_MM"), get("US_R_ANG")),
        ]

        # ---- drivetrain ----
        self.v_max = 380.0          # mm/s at PWM 255, loaded, fresh cells
        self.pwm_deadband = 50.0    # a TT motor below this only hums
        self.tau = 0.13             # s, motor + gearbox spin-up
        self.gain_left = 1.00       # mismatch is set per-run in reset()
        self.gain_right = 0.94      # right motor 6% weaker: the classic veer
        self.slip_sigma = 0.010     # random per-wheel slip, fraction
        self.batt_sag = 0.00        # 0.15 = motors 15% slower by the end

        # ---- sonar ----
        self.us_max = get("US_MAX_MM")
        self.us_min = get("US_MIN_MM")
        self.beam_deg = 15.0        # HC-SR04 is about +/-7.5 deg
        self.beam_rays = 7
        self.max_incidence = 62.0   # past this the echo bounces away, gone
        self.noise_sigma = 4.0      # mm
        self.dropout_p = 0.02       # random missed ping
        self.quantise = 3.0         # mm

        # ---- gyro ----
        self.gyro_bias_dps = 0.35   # left over after calibration
        self.gyro_noise_dps = 0.6
        self.gyro_walk_dps = 0.05   # random-walk of the bias, per sqrt(s)
        self.gyro_scale_err = 1.01  # 1% scale-factor error

        # ---- encoders ----
        self.ticks_per_rev = get("ENC_TICKS_PER_REV")
        self.mm_per_tick = math.pi * self.wheel_diam / self.ticks_per_rev

        # ---- floor ----
        self.line_offset = 60.0     # mm forward of the axle, looking down


class Robot:
    def __init__(self, maze, params=None, rng=None):
        self.maze = maze
        self.p = params or Params()
        self.rng = rng or random.Random(1234)
        self.reset()

    # ------------------------------------------------------------------
    def reset(self):
        x, y, h = self.maze.start
        self.x, self.y = float(x), float(y)
        self.th = math.radians(h)

        self.vl = self.vr = 0.0          # actual wheel speeds, mm/s
        self.dist_l = self.dist_r = 0.0  # cumulative wheel travel, mm
        self.ticks_l = self.ticks_r = 0

        self.gyro_heading = 0.0
        self.gyro_bias = self.p.gyro_bias_dps * self.rng.uniform(-1, 1)
        self.gyro_rate = 0.0

        self.t = 0.0
        self.bumps = 0
        self.bump_episodes = 0
        self._bumping = False
        self.score = 0
        self.trail = [(self.x, self.y)]
        self.sonar = [self.p.us_max] * 3
        self._hist = [[self.p.us_max] * 3 for _ in range(3)]
        self._miss = [0, 0, 0]
        self.prev_pts = self.contact_points()

        # a fresh mismatch every run - never tune against one lucky pairing
        self.p.gain_left = 1.0 + self.rng.uniform(-0.04, 0.04)
        self.p.gain_right = 1.0 + self.rng.uniform(-0.08, 0.02)

    # ------------------------------------------------------------------
    def corners(self):
        """Body outline in world coordinates."""
        p = self.p
        front = p.axle_from_nose
        back = p.length - p.axle_from_nose
        hw = p.width / 2.0
        local = [(front, hw), (front, -hw), (-back, -hw), (-back, hw)]
        c, s = math.cos(self.th), math.sin(self.th)
        return [(self.x + lx * c - ly * s, self.y + lx * s + ly * c)
                for (lx, ly) in local]

    def contact_points(self):
        """Left wheel, right wheel and the free castor - the three wheels
        the rulebook wants completely past a sector line."""
        p = self.p
        hb = p.wheel_base / 2.0
        local = [(0.0, hb), (0.0, -hb), (p.axle_from_nose - 25.0, 0.0)]
        c, s = math.cos(self.th), math.sin(self.th)
        return [(self.x + lx * c - ly * s, self.y + lx * s + ly * c)
                for (lx, ly) in local]

    def line_point(self):
        c, s = math.cos(self.th), math.sin(self.th)
        return (self.x + self.p.line_offset * c, self.y + self.p.line_offset * s)

    # ------------------------------------------------------------------
    def _pwm_to_speed(self, pwm, gain):
        p = self.p
        a = abs(pwm)
        if a <= p.pwm_deadband:
            return 0.0
        frac = (a - p.pwm_deadband) / (255.0 - p.pwm_deadband)
        v = frac * p.v_max * gain
        v *= (1.0 - p.batt_sag * min(1.0, self.t / 180.0))
        return v if pwm > 0 else -v

    def step(self, pwm_l, pwm_r, dt):
        p = self.p
        tl = self._pwm_to_speed(pwm_l, p.gain_left)
        tr = self._pwm_to_speed(pwm_r, p.gain_right)

        k = 1.0 - math.exp(-dt / p.tau)
        self.vl += (tl - self.vl) * k
        self.vr += (tr - self.vr) * k

        vl = self.vl * (1.0 + self.rng.gauss(0, p.slip_sigma))
        vr = self.vr * (1.0 + self.rng.gauss(0, p.slip_sigma))

        v = 0.5 * (vl + vr)
        omega = (vr - vl) / p.wheel_base

        nx = self.x + v * math.cos(self.th) * dt
        ny = self.y + v * math.sin(self.th) * dt
        nth = self.th + omega * dt

        old = (self.x, self.y, self.th)
        self.x, self.y, self.th = nx, ny, nth
        if self.maze.rect_hits_wall(self.corners()):
            # Scraped a wall. A real robot does not stop dead - it grinds
            # along the surface - so try the move again with one component
            # removed. Whatever still fits, we keep.
            self.bumps += 1
            if not self._bumping:
                self.bump_episodes += 1
                self._bumping = True
            options = (
                (old[0], old[1], nth),      # rotate on the spot only
                (nx, ny, old[2]),           # slide without turning
                (old[0] + (nx - old[0]) * 0.3,
                 old[1] + (ny - old[1]) * 0.3,
                 old[2] + (nth - old[2]) * 0.3),
            )
            placed = False
            for cand in options:
                self.x, self.y, self.th = cand
                if not self.maze.rect_hits_wall(self.corners()):
                    placed = True
                    break
            if not placed:
                self.x, self.y, self.th = old
                vl = vr = 0.0
                omega = 0.0
            else:
                vl *= 0.35
                vr *= 0.35
            self.vl *= 0.35
            self.vr *= 0.35

        else:
            self._bumping = False

        # odometry: what the wheels actually turned
        self.dist_l += vl * dt
        self.dist_r += vr * dt
        self.ticks_l = int(self.dist_l / p.mm_per_tick)
        self.ticks_r = int(self.dist_r / p.mm_per_tick)

        # gyro
        self.gyro_bias += self.rng.gauss(0, p.gyro_walk_dps) * math.sqrt(dt)
        true_dps = math.degrees(omega)
        self.gyro_rate = (true_dps * p.gyro_scale_err
                          + self.gyro_bias
                          + self.rng.gauss(0, p.gyro_noise_dps))
        self.gyro_heading += self.gyro_rate * dt

        self.t += dt
        now_pts = self.contact_points()
        self.score += self.maze.update_sectors(self.prev_pts, now_pts)
        self.prev_pts = now_pts
        self.trail.append((self.x, self.y))

    # ------------------------------------------------------------------
    def read_sonar(self):
        p = self.p
        out = []
        for (mx, my, mang) in p.sonar_mounts:
            c, s = math.cos(self.th), math.sin(self.th)
            ox = self.x + mx * c - my * s
            oy = self.y + mx * s + my * c
            base = math.degrees(self.th) + mang

            best = None
            for i in range(p.beam_rays):
                frac = (i / (p.beam_rays - 1.0)) - 0.5 if p.beam_rays > 1 else 0.0
                ang = base + frac * p.beam_deg
                d, inc = self.maze.raycast(ox, oy, ang, p.us_max)
                if d is None:
                    continue
                if inc is not None and inc > p.max_incidence:
                    continue        # echo skated off the wall, never came back
                if best is None or d < best:
                    best = d

            i = len(out)
            if best is None or self.rng.random() < p.dropout_p:
                # No echo. The firmware wants two misses in a row before it
                # believes a wall has gone away, so one lost ping holds the
                # last good reading instead of reading as open space.
                self._miss[i] += 1
                out.append(int(p.us_max) if self._miss[i] >= 2 else int(self.sonar[i]))
                continue
            self._miss[i] = 0

            d = best + self.rng.gauss(0, p.noise_sigma)
            d = max(p.us_min, min(p.us_max, d))
            d = round(d / p.quantise) * p.quantise

            # median of the last three pings, exactly as MazeRunner.ino does
            h = self._hist[i]
            h.pop(0); h.append(int(d))
            out.append(sorted(h)[1])

        self.sonar = out
        return out

    def read_line(self):
        return 1 if self.maze.on_black(self.line_point()) else 0

    # ------------------------------------------------------------------
    def in_finish(self):
        f = self.maze.finish
        if not f:
            return False
        x1, y1, x2, y2 = f
        pts = self.contact_points()
        return all(min(x1, x2) <= px <= max(x1, x2) and
                   min(y1, y2) <= py <= max(y1, y2) for (px, py) in pts)

    # ------------------------------------------------------------------
    def turning_radius_needed(self):
        """Radius of the circle the body sweeps when it pivots on the spot.
        If 2 x this is wider than the corridor, the robot physically cannot
        turn around in place. Worth knowing before you buy anything."""
        p = self.p
        front = p.axle_from_nose
        back = p.length - p.axle_from_nose
        hw = p.width / 2.0
        return max(math.hypot(front, hw), math.hypot(back, hw))
