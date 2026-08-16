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
wokwi/
    diagram.json      drop into wokwi.com to test the firmware in a browser
    README.md         setup, and what Wokwi can and cannot show you

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
    02_HARDWARE.md         what to buy, where, and why
    03_WIRING.md           pin map, power, mounting, inspection checklist
    wiring_diagram.svg     the picture to copy when you build it
    04_SIMULATION.md       which simulator to use, and what ours found
    05_ALGORITHM.md        how the robot thinks
    06_PLAN.md             phase-by-phase plan
    07_COMPETITION_DAY.md  print this and take it
    08_SOFTWARE_AND_STEPS.md  what to install, and every step  ← start here
    09_CHECKLIST.md        every item, with alternatives  ← shopping list
    10_MAP_NOTES.md        the three maps and what still needs checking
```

---

## The three things that matter most

### 1. The robot has to get smaller

`tools/geometry_check.py` prints:

> turning on the spot sweeps a circle **292 mm** across

Your robot is 25 × 15 cm and the passages are 30 cm, so it has **4 mm of
clearance each side** while turning. Measured over the three real maps, both
wall-following directions:

| Robot | Swept circle | Maps solved | Sector points | Scrapes/run |
| --- | --- | --- | --- | --- |
| 250 × 150 mm *(today)* | 292 mm | 56 % | 63 % | 100 |
| 210 × 130 mm | 247 mm | 56 % | 66 % | 84 |
| **190 × 130 mm** | **230 mm** | **75 %** | **72 %** | 73 |

Target about **21 × 13 cm**: sensors inside the wheel line, nothing hanging
off the nose or tail, battery stacked on top, wheel axle exactly central.

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

Real robot size, real map dimensions, 30 cm passages, 3-minute limit:

| Map | Sector points | Time | Wall scrapes |
| --- | --- | --- | --- |
| Map 2 — island loop | **8 / 8** | 38 s | 11 |
| Map 1 — serpentine | 3–4 / 8 | ran out of time | 100–270 |
| Map 3 — spine snake | 1–2 / 8 | ran out of time | 18–230 |

Map 2 matches the photo and is solved cleanly. Maps 1 and 3 are best guesses
at the shape and are where the tight-clearance problem shows up — see
`docs/10_MAP_NOTES.md` for what would let us draw them exactly.

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
