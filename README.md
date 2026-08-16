# MazeRunner — Robotics Navigation Challenge

Autonomous maze robot: Arduino Uno R3, L298N, 3× HC-SR04, MPU-6050 gyro,
2× wheel encoders, 1× floor line sensor. Built to the competition rulebook
in `docs/01_RULES.md`.

The unusual part of this repository: **the simulator runs the real
firmware.** `nav_core.cpp` is compiled twice — once by the Arduino IDE onto
the Uno, once by `g++` into a shared library that the Python simulator
drives. Whatever you see in a simulated run is the behaviour of the code you
flash.

---

## Start here

```bash
pip install pillow

# 1. Will the robot physically fit in the maze?  Answer this first.
python3 tools/geometry_check.py

# 2. Watch it drive the three competition maps.
cd sim && python3 run.py --all --compare
```

The GIFs land in `sim/runs/`.

---

## What is in here

```
firmware/MazeRunner/
    MazeRunner.ino    hardware only: pins, I2C, PWM, EEPROM
    nav_core.cpp/.h   ALL the navigation. No Arduino code. Shared with the sim
    config.h          every tunable number, read by both sides

sim/
    run.py            the simulator - GIFs, CSV telemetry, scoreboards
    maze.py           maze geometry, ultrasonic ray-casting, sector scoring
    robot.py          drivetrain, sonar, gyro and encoder models
    navcore.py        loads the firmware brain as a shared library
    maps/*.txt        the maps, as plain editable text

tools/
    geometry_check.py can the robot turn in the corridor?  Run this first
    telemetry_log.py  record the real robot's serial output for comparison
    serial_check.md   bench tests, one subsystem at a time

docs/
    01_RULES.md            the rulebook, condensed to what changes decisions
    02_HARDWARE.md         what to buy, where, and why  ← shopping list
    03_WIRING.md           pin map, power, mounting, inspection checklist
    04_SIMULATION.md       which simulator to use, and what ours found
    05_ALGORITHM.md        how the robot thinks
    06_PLAN.md             phase-by-phase plan  ← what to do next
    07_COMPETITION_DAY.md  print this and take it
```

---

## The three things that matter most

### 1. Ask the organisers how wide the passages are — today

`tools/geometry_check.py` prints:

> turning on the spot sweeps a circle **269 mm** across

The rulebook allows passages of 200–400 mm and says the figure is still
"tentative". Measured across 5 maps in simulation:

| Passage | Can it turn? | Finished | Sector points |
| --- | --- | --- | --- |
| 200 mm | **no** | 0 % | 0 % |
| 250 mm | **no** | 10 % | 33 % |
| 300 mm | yes, 16 mm spare | 60 % | 72 % |
| 350 mm | yes | 70 % | 71 % |
| 400 mm | yes | 70 % | 78 % |

At 200 mm no standard 2WD kit robot can turn around, whatever the code does.
`docs/06_PLAN.md` has the email to send.

### 2. Yes, add the gyro. No, you do not need a memory module.

**Gyro (MPU-6050, ~20 SAR):** the highest-value part you can add and
explicitly legal under §2.2 ("use of multiple sensors"). It is what makes a
turn actually 90° instead of "run the motors for 400 ms and hope", and what
keeps the robot straight when the two mismatched TT motors want to curve it
into a wall. Removing it in simulation roughly doubles the wall scrapes and
loses a third of the sector points.

**Memory:** you already own it. The Uno has **2 KB of SRAM and 1 KB of
EEPROM** built in. The junction map costs 4 bytes per junction — 192 bytes
for 48 junctions. Nothing to buy, nothing to add, no rule to worry about.
`docs/05_ALGORITHM.md` explains the Trémaux memory that uses it.

### 3. Score points, do not chase speed

§6.1 awards one point per sector line all three wheels fully cross, and time
is only a tie-breaker (§6.3). A robot that never gets stuck and keeps
crossing lines beats a robot that solves two maps perfectly and jams on the
third. Every tuning decision in this repository is made that way.

---

## Where it stands today

5 maps × 4 random seeds, 350 mm passages, Trémaux memory, left-hand rule:

| Map | Finished | Sector points | Wall scrapes |
| --- | --- | --- | --- |
| Inward spiral (goal in the middle) | 0 % | 5.0 / 7 | 155 |
| Serpentine | 75 % | 9.8 / 12 | 115 |
| Island loop | 100 % | 9.0 / 9 | 2 |
| Practice corner | 100 % | 2.2 / 3 | 108 |
| Dead ends + loop | 100 % | 5.0 / 7 | 1 |

The spiral is the honest weak spot: if the finish is a chamber in the
*middle* of the maze, enclosed by its own ring of wall, **no wall-following
robot can ever reach it** — that is maze theory, not a bug. The memory mode
still collects 5–6 of the 7 sector points. If the real map 1 has its finish
gate on the outer edge, as the striped marking in the photo suggests, the
problem disappears. That is question 2 in the email.

---

## The maps

`sim/maps/*.txt` are reconstructions from the photos — the *shapes* are
right, the exact millimetres are a guess. They are plain characters:

```
....................
....##############..
....#............#..
........##########..
```

`#` is wall, `.` is floor, one character = 100 mm. When you get to see the
real maze, trace it into these files and re-run. Fifteen minutes each, and it
tells you which wall-following direction to use before your run.

---

## Notes

- Requires Python 3 with **Pillow** only, plus `g++` to build the shared
  library (already present on macOS and Linux; on Windows use WSL or MinGW).
- The Arduino sketch needs **no libraries** — `Wire` and `EEPROM` ship with
  the IDE.
- Numbers in `config.h` are read by the simulator too, so tune once.
