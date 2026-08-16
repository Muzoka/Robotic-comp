#!/usr/bin/env python3
"""
run.py - drive the real firmware brain around a simulated maze.

    python3 run.py --map maps/map3_loop.txt
    python3 run.py --all                       # every map, 10 runs each
    python3 run.py --map maps/map1_spiral.txt --mode wallfollow --hand right
    python3 run.py --all --trials 30 --no-gif  # fast statistics sweep

Outputs land in sim/runs/:
    <map>.gif   what happened
    <map>.csv   full telemetry, one row per 20 ms
    summary.txt scoreboard across every run
"""

import argparse
import csv
import glob
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cfg import get                      # noqa: E402
from maze import Maze                    # noqa: E402
from navcore import NavCore              # noqa: E402
from robot import Robot, Params          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")

MODES = {"wallfollow": 0, "tremaux": 1}
HANDS = {"left": 1, "right": -1}


def simulate(map_path, mode=1, hand=1, seed=1, gif=True, csv_out=True,
             max_seconds=240.0, gif_every=8, verbose=True, scale=1.0,
             robot=None):
    maze = Maze(map_path)
    if scale != 1.0:
        maze.scale(scale)
    rng = random.Random(seed)
    prm = Params()
    if robot:
        L, W = robot
        prm.length = L
        prm.width = W
        prm.wheel_base = W - 22
        prm.axle_from_nose = L / 2.0
        prm.sonar_mounts = [(L / 2.0 - 10, 0, 0),
                            (0, W / 2.0 - 7, 90),
                            (0, -(W / 2.0 - 7), -90)]
    bot = Robot(maze, prm, rng)
    nav = NavCore(mode=mode, hand=hand)

    dt_ms = int(get("LOOP_DT_MS"))
    dt = dt_ms / 1000.0

    frames = []
    renderer = None
    if gif:
        from render import Renderer, save_gif
        renderer = Renderer(maze)

    rows = []
    steps = int(max_seconds / dt)
    finished = False
    finish_reason = "timeout"
    t = 0.0
    # sonar refreshes slower than the control loop, exactly like the Uno:
    # front every 2nd tick, each side every 4th
    cached = [int(get("US_MAX_MM"))] * 3

    for n in range(steps):
        fresh = bot.read_sonar()
        if n % 2 == 0:
            cached[0] = fresh[0]
        if n % 4 == 1:
            cached[1] = fresh[1]
        if n % 4 == 3:
            cached[2] = fresh[2]
        bot.sonar = list(cached)

        out = nav.step(cached[0], cached[1], cached[2],
                       bot.gyro_heading, bot.gyro_rate,
                       bot.ticks_l, bot.ticks_r,
                       bot.read_line(),
                       1 if t > 0.2 else 0,
                       dt_ms)

        bot.step(out.pwm_left, out.pwm_right, dt)
        maze.mark_visited(bot.x, bot.y)
        t += dt

        if csv_out:
            rows.append([round(t, 3), nav.state_name(out.state),
                         cached[0], cached[1], cached[2],
                         round(bot.gyro_heading, 2), round(out.dbg_target_deg, 1),
                         out.pwm_left, out.pwm_right,
                         round(bot.x, 1), round(bot.y, 1),
                         round(math.degrees(bot.th), 1),
                         sum(1 for s in maze.sectors if s.scored), bot.bump_episodes])

        if renderer and n % gif_every == 0:
            frames.append(renderer.frame(bot, out, nav.state_name(out.state), t))

        if bot.in_finish():
            finished = True
            finish_reason = "reached finish zone"
            break
        if out.done:
            finished = bot.in_finish()
            finish_reason = "robot decided it was done"
            break

    scored = sum(1 for s in maze.sectors if s.scored)
    coverage = maze.coverage
    result = {
        "coverage": coverage,
        "map": os.path.basename(map_path),
        "name": maze.name,
        "mode": "tremaux" if mode == 1 else "wallfollow",
        "hand": "left" if hand > 0 else "right",
        "seed": seed,
        "finished": finished and coverage > 0.999,
        "reached_exit": finished,
        "reason": finish_reason,
        "sectors": scored,
        "sectors_total": len(maze.sectors),
        "time_s": round(t, 1),
        "bumps": bot.bump_episodes,
        "junctions_remembered": nav.junctions,
        "memory_bytes": nav.memory_bytes,
        "turn_radius_mm": round(bot.turning_radius_needed(), 1),
    }

    os.makedirs(RUNS, exist_ok=True)
    stem = os.path.splitext(os.path.basename(map_path))[0]
    if renderer and frames:
        from render import save_gif
        # keep the gif under control
        if len(frames) > 700:
            step = len(frames) // 700 + 1
            frames = frames[::step]
        save_gif(frames, os.path.join(RUNS, stem + ".gif"))
        result["gif"] = os.path.join("sim", "runs", stem + ".gif")
    if csv_out and rows:
        p = os.path.join(RUNS, stem + ".csv")
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["t_s", "state", "dF", "dL", "dR", "heading", "target",
                        "pwmL", "pwmR", "x", "y", "th", "sectors", "bumps"])
            w.writerows(rows)
        result["csv"] = os.path.join("sim", "runs", stem + ".csv")

    if verbose:
        if result["finished"]:
            flag = "COMPLETE"
        elif finished:
            flag = "left early - only %.0f%% of the road" % (100 * coverage)
        else:
            flag = "did not finish"
        print("  %-26s %-10s %-5s seed %-3d %2d/%-2d sect  road %3.0f%%  %6.1fs  %s"
              % (maze.name[:26], result["mode"], result["hand"], seed,
                 scored, len(maze.sectors), 100 * coverage, t, flag))
    return result


# ---------------------------------------------------------------------- #
def sweep_corridor(maps, args):
    """How wide does the passage have to be before the robot stops
    scraping? This is the number to take to the organisers."""
    from robot import Robot, Params
    from maze import Maze as _M
    widths = [200, 250, 300, 350, 400]
    print("\ncorridor width sweep - %d maps x %d seeds each\n" % (len(maps), args.trials))
    print("%-8s %-9s %8s %9s %8s %8s" %
          ("passage", "can turn?", "finish%", "sectors%", "time", "bumps"))
    for w in widths:
        k = w / 300.0
        m0 = _M(maps[0]); m0.scale(k)
        bot = Robot(m0, Params())
        r = bot.turning_radius_needed()
        fits = (2 * r) <= w
        fin = tot = sec = secmax = 0
        tsum = 0.0
        bumps = 0
        for mp in maps:
            for j in range(args.trials):
                for hand in (1, -1):
                    res = simulate(mp, 1, hand, args.seed + j, gif=False,
                                   csv_out=False, max_seconds=args.seconds,
                                   scale=k, verbose=False)
                    tot += 1
                    fin += 1 if res["finished"] else 0
                    sec += res["sectors"]
                    secmax += res["sectors_total"]
                    tsum += res["time_s"]
                    bumps += res["bumps"]
        print("%-8d %-9s %7.0f%% %8.0f%% %7.0fs %8.1f" %
              (w, "yes" if fits else "NO", 100.0 * fin / tot,
               100.0 * sec / secmax, tsum / tot, bumps / float(tot)))
    print("\n'can turn?' is pure geometry: the robot sweeps a circle of "
          "%.0f mm across\nwhen it pivots, and that circle has to fit "
          "between the walls.\n" % (2 * r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mode", default="wallfollow", choices=list(MODES))
    ap.add_argument("--hand", default="right", choices=list(HANDS))
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-gif", action="store_true")
    ap.add_argument("--seconds", type=float, default=240.0)
    ap.add_argument("--robot", default=None, metavar="LxW",
                    help="try a different body size in mm, e.g. --robot 220x140")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="stretch the maps; 1.0 = 300 mm corridors, 1.33 = 400 mm")
    ap.add_argument("--sweep-corridor", action="store_true",
                    help="run every map at 200/250/300/350/400 mm corridors")
    ap.add_argument("--compare", action="store_true",
                    help="try every mode/hand combination and rank them")
    args = ap.parse_args()
    robot = None
    if args.robot:
        L, W = args.robot.lower().split("x")
        robot = (float(L), float(W))

    maps = []
    if args.all or not args.map:
        maps = sorted(glob.glob(os.path.join(HERE, "maps", "*.txt")))
    else:
        maps = [args.map if os.path.isabs(args.map)
                else os.path.join(HERE, args.map)]

    combos = []
    if args.compare:
        for m in ("wallfollow", "tremaux"):
            for h in ("left", "right"):
                combos.append((m, h))
    else:
        combos.append((args.mode, args.hand))

    if args.sweep_corridor:
        return sweep_corridor(maps, args)

    results = []
    for mp in maps:
        print("\n%s" % os.path.basename(mp))
        for (mode, hand) in combos:
            for k in range(args.trials):
                results.append(simulate(
                    mp, MODES[mode], HANDS[hand], args.seed + k,
                    gif=(not args.no_gif) and k == 0,
                    max_seconds=args.seconds, scale=args.scale, robot=robot))

    # ---- scoreboard ----
    print("\n" + "=" * 78)
    print("SCOREBOARD")
    print("=" * 78)
    agg = {}
    for r in results:
        key = (r["map"], r["mode"], r["hand"])
        a = agg.setdefault(key, {"n": 0, "fin": 0, "sec": 0, "tot": r["sectors_total"],
                                 "t": 0.0, "bumps": 0, "cov": 0.0})
        a["n"] += 1
        a["fin"] += 1 if r["finished"] else 0
        a["sec"] += r["sectors"]
        a["t"] += r["time_s"]
        a["bumps"] += r["bumps"]
        a["cov"] += r["coverage"]

    print("%-16s %-11s %-6s %7s %6s %9s %8s %7s" %
          ("map", "mode", "hand", "complete", "road", "sectors", "time", "bumps"))
    for key in sorted(agg):
        a = agg[key]
        print("%-16s %-11s %-6s %6.0f%% %5.0f%% %6.1f/%-2d %7.1fs %7.1f" %
              (key[0][:16], key[1], key[2],
               100.0 * a["fin"] / a["n"], 100.0 * a["cov"] / a["n"],
               a["sec"] / a["n"], a["tot"],
               a["t"] / a["n"], a["bumps"] / a["n"]))

    os.makedirs(RUNS, exist_ok=True)
    with open(os.path.join(RUNS, "summary.txt"), "w", encoding="utf-8") as fh:
        for key in sorted(agg):
            a = agg[key]
            fh.write("%s | %s | %s | finish %.0f%% | sectors %.1f/%d | %.1fs | bumps %.1f\n"
                     % (key[0], key[1], key[2], 100.0 * a["fin"] / a["n"],
                        a["sec"] / a["n"], a["tot"], a["t"] / a["n"], a["bumps"] / a["n"]))
    total_runs = len(results)
    total_fin = sum(1 for r in results if r["finished"])
    print("\n%d runs, %d completed the whole road and left (%.0f%%)"
          % (total_runs, total_fin, 100.0 * total_fin / max(1, total_runs)))
    print("artefacts in sim/runs/")


if __name__ == "__main__":
    main()
