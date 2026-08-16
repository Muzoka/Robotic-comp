#!/usr/bin/env python3
"""
test_start.py - the robot must not start its own run.

This exists because it did. On power-up the front sonar's median-of-3
history was zero-initialised, so the first reading came out as 0 mm - a
wall against the nose. ST_WAIT_START read that as a hand held up to arm the
start, and two pings later, when the history filled and the reading jumped
to its true value, it read that as the hand being taken away. The run began
about three seconds after switch-on with nobody touching the robot.

It was invisible to sim/run.py, which held the GO signal high from the first
tick and so never entered the arming path at all.

    python3 tools/test_start.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sim"))

from cfg import get                                  # noqa: E402
from navcore import NavCore                          # noqa: E402

DT = int(get("LOOP_DT_MS"))
FAR = int(get("US_MAX_MM"))
ST_WAIT_START = 1
ST_COUNTDOWN = 2

failures = []


def run(name, feed, ticks=400, expect_started=False):
    """feed(n) -> (front_mm, left_mm, right_mm); returns True if it started."""
    nav = NavCore(mode=int(get("DEFAULT_MODE")), hand=int(get("WALL_HAND")))
    started_at = None
    for n in range(ticks):
        f, l, r = feed(n)
        out = nav.step(f, l, r, 0.0, 0.0, 0, 0, 0, 0, DT)
        if out.state > ST_WAIT_START and started_at is None:
            started_at = n * DT
    ok = (started_at is not None) == expect_started
    verdict = "OK  " if ok else "FAIL"
    when = "never" if started_at is None else "%d ms" % started_at
    print("  %s  %-46s started: %s" % (verdict, name, when))
    if not ok:
        failures.append(name)
    return started_at


print("\nstart-up behaviour, driven through the real firmware\n")

# 1. THE REGRESSION. Sonar reports 0 mm for its first few reads - exactly
#    what a zero-primed median filter produces - then settles. Nobody
#    touches the robot. It must sit still.
run("sonar reads 0 mm at boot, then settles",
    lambda n: (0, 0, 0) if n < 3 else (602, 90, 90),
    expect_started=False)

# 2. Same, but the bad reading lasts much longer.
run("sonar reads 0 mm for a whole second",
    lambda n: (0, 0, 0) if n < 50 else (602, 90, 90),
    expect_started=False)

# 3. Sitting in the start pocket, nothing in front. Must not start.
run("left alone on the start line",
    lambda n: (602, 90, 90),
    expect_started=False)

# 4. A single glitched ping in the middle of waiting. Must not start.
run("one glitched 30 mm ping while waiting",
    lambda n: (30, 90, 90) if n == 100 else (602, 90, 90),
    expect_started=False)

# 5. The GO button, a short press. Must start.
nav = NavCore(mode=int(get("DEFAULT_MODE")), hand=int(get("WALL_HAND")))
started = None
for n in range(400):
    out = nav.step(602, 90, 90, 0.0, 0.0, 0, 0, 0,
                   1 if 50 <= n < 55 else 0, DT)
    if out.state > ST_WAIT_START and started is None:
        started = n * DT
ok = started is not None
print("  %s  %-46s started: %s"
      % ("OK  " if ok else "FAIL", "GO button, 100 ms press at 1.0 s",
         "never" if started is None else "%d ms" % started))
if not ok:
    failures.append("GO button")

# 6. The hand wave: hand held at 50 mm for 800 ms, then taken away.
#    Must start - this is the no-laptop backup if the button fails.
run("hand held 800 ms then withdrawn",
    lambda n: (50, 90, 90) if 25 <= n < 65 else (602, 90, 90),
    expect_started=True)

# 7. A hand that appears for only 100 ms - shorter than START_ARM_MS -
#    must NOT be enough.
run("hand flicks past for 100 ms",
    lambda n: (50, 90, 90) if 25 <= n < 30 else (602, 90, 90),
    expect_started=False)

print()
if failures:
    print("FAILED: %s" % ", ".join(failures))
    sys.exit(1)
print("all start-up checks passed")
