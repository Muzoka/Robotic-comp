#!/usr/bin/env python3
"""
geometry_check.py - the five minutes that decide whether this robot can
compete at all.

Before you buy a single screw, measure your robot with a tape measure, put
the numbers in firmware/MazeRunner/config.h, and run this.

    python3 tools/geometry_check.py
    python3 tools/geometry_check.py --corridor 250

A differential-drive robot turning on the spot sweeps a circle. If that
circle is wider than the passage, the robot cannot turn round. Not "turns
badly" - cannot turn, at all, ever, no matter how good the code is. The
rulebook allows passages from 200 mm to 400 mm, and a standard 2WD kit
chassis does not fit in the narrow end of that range.
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from cfg import CONFIG_H, load          # noqa: E402


def check(cfg, corridor):
    L = cfg["ROBOT_LENGTH_MM"]
    W = cfg["ROBOT_WIDTH_MM"]
    A = cfg["AXLE_FROM_NOSE_MM"]
    front, back = A, L - A
    hw = W / 2.0

    r_pivot = max(math.hypot(front, hw), math.hypot(back, hw))
    d_pivot = 2 * r_pivot
    r_best = math.hypot(L / 2.0, hw)     # if the axle were dead centre

    print("=" * 66)
    print("ROBOT GEOMETRY CHECK          (numbers from %s)" %
          os.path.relpath(CONFIG_H))
    print("=" * 66)
    print("  body                 %6.0f mm long  x %5.0f mm wide" % (L, W))
    print("  wheel axle           %6.0f mm behind the nose "
          "(%.0f mm of tail behind it)" % (A, back))
    print("  wheel base           %6.0f mm" % cfg["WHEEL_BASE_MM"])
    print()
    print("  turning on the spot sweeps a circle %.0f mm across" % d_pivot)
    if abs(A - L / 2.0) > 5:
        print("  -> with the axle centred it would be %.0f mm  "
              "(move the motors, it is free)" % (2 * r_best))
    print()

    print("%-10s %-9s %-9s %s" % ("passage", "clearance", "verdict", "what it means"))
    print("-" * 66)
    for c in (200, 250, 300, 350, 400):
        gap = (c - d_pivot) / 2.0
        if gap < 0:
            v, note = "IMPOSSIBLE", "cannot turn round - would need a smaller robot"
        elif gap < 15:
            v, note = "no", "scrapes every corner, will jam"
        elif gap < 35:
            v, note = "tight", "works if it centres itself well"
        else:
            v, note = "fine", "comfortable"
        mark = " <-- asked for" if c == corridor else ""
        print("%-10d %6.0f mm %-9s %s%s" % (c, gap, v, note, mark))
    print("-" * 66)

    straight = (corridor - W) / 2.0
    print("\ndriving straight down a %d mm passage leaves %.0f mm each side"
          % (corridor, straight))
    if straight < 30:
        print("  that is not enough - the robot will rub the walls even when "
              "perfectly\n  centred, and ultrasound cannot hold it that "
              "accurately")

    need = d_pivot
    print("\nBOTTOM LINE")
    print("  ask the organisers for the passage width before the build.")
    print("  this robot needs at least %.0f mm, and %.0f mm to be comfortable."
          % (need, need + 70))
    if cfg["ROBOT_WIDTH_MM"] > 165:
        print("  the body is wide. Anything you bolt on must stay INSIDE the")
        print("  wheel line - no sensors sticking out sideways.")
    return d_pivot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corridor", type=float, default=300)
    a = ap.parse_args()
    check(load(), a.corridor)


if __name__ == "__main__":
    main()
