# MazeRunner — Robotics Navigation Challenge

Autonomous maze robot: Arduino Uno R3, L298N, 3× HC-SR04, MPU-6050 gyro,
2× wheel encoders, one GO button. Built to the competition rulebook
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
    sketch.ino        the whole firmware in ONE file - paste this, not the
                      one in firmware/. Generated, never hand-edited
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
    make_wokwi_sketch.py  regenerate wokwi/sketch.ino from the firmware
    check_wokwi_sketch.sh compile it the way ARDUINO does, not just g++
                          (`make wokwi` runs both)
    test_start.py     the robot must never start its own run (`make test`)
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
    10_MAP_NOTES.md        the three maps, straight from the spreadsheet
    11_MAKING_IT_FIT.md    how all three maps got inside 3 minutes  ← read this
    12_STARTING_THE_ROBOT.md  the start procedure on the day
```

---

## The three things that matter most

### 1. The robot has to get smaller — 3 cm shorter, 1 cm narrower

Turning on the spot sweeps a circle as wide as the body diagonal. The passage
is one foot, 304.8 mm.

| Robot | Diagonal | Clearance | Map 3 completed |
| --- | --- | --- | --- |
| 250 × 150 mm *(today)* | 292 mm | 6.4 mm | 12 % |
| **220 × 140 mm** | **261 mm** | **22 mm** | **100 %** |

There is a cliff at about 280 mm of diagonal. Most builds find the whole 3 cm
in the front ultrasonic bracket alone.

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

Three separate maps from the organisers' spreadsheet, 1 ft passages, 3
minutes each. The robot must drive **every square of the road** before it
leaves. Robot **220 × 115 mm**, `PWM_CRUISE 200`:

| Map | Complete | Road driven | Sector points | Time | Wall contact |
| --- | --- | --- | --- | --- | --- |
| Map 1 | **100 %** | 100 % | 3 / 3 | 32 s | none |
| Map 2 | **100 %** | 100 % | 5 / 5 | 36 s | none |
| Map 3 | **100 %** | 100 % | 9 / 9 | 48 s | none |

**96 runs, 96 completed, every sector line crossed every time.** Re-run with
deliberately bad hardware — 2.5× the wheel slip, four times the sensor
noise, three times the sonar dropout, 15 % battery sag, up to 15 % motor
mismatch — it still completes **100 %** of 78 runs, still scoring 442 of 442
sector points, still without touching a wall.

Those four rows are the same for **every** strategy setting: left hand or
right hand, wall-following or Trémaux memory, all four combinations now
drive the identical route. Picking the wrong one at the start line used to
cost a whole map. It cannot any more — see `STRAIGHT_FIRST` below.

All three finish in about a third of the time allowed. See
`docs/11_MAKING_IT_FIT.md` for how, `docs/09_CHECKLIST.md` for the shopping
list, and `docs/12_STARTING_THE_ROBOT.md` for the start procedure.

### The rule that does the work: go straight if you can

At a junction the robot checks straight ahead **first**, and only asks the
hand rule when the way ahead is blocked.

It sounds trivial. On Map 2 it is the difference between the route you drew
and the one the robot used to take, and it is worth:

- **two fewer pivots** — and both of the deleted ones were in the open
  4-way crossing, the single worst place on the course to turn, because
  there is no wall on either side to square up against afterwards. Every
  livelock this project ever had started in that square.
- **the speed ceiling lifted**, 170 → 200 PWM, because Map 2 was what used
  to break first.
- **left hand and right hand producing the same route**, on all three maps.

The honest limitation is in `config.h` beside the switch: straight-first on
its own is not a complete coverage rule in a maze with **dead-end stubs**.
None of these three maps has one — `build_maps.py` checks and will tell you
in capital letters if a future map does.

---

## The maps

Generated straight from the organisers' spreadsheet by
`sim/maps/build_maps.py`. Each section is the 5 × 5 grid off its sheet —
`P` where the sheet is blue, `X` where it is white:

```python
"map3": {"grid": ["PPXPP",
                  "XPXPX",
                  "PPXPP",
                  "PXXXP",
                  "PPPPP"], ...}
```

The combined course is one line — `COURSE = [("map1", False), ("map3", True),
("map2", True)]`, where `True` mirrors that section so the gates line up.
Change it, re-run, done.

`build_maps.py` also prints, for each map, the route length, the number of
pivots, whether the walk covers every square of road, and whether the map
contains a dead end. It asserts that every sector line sits on a boundary
the route actually crosses — a line the robot cannot reach is a point nobody
can score, and the only symptom is a scoreboard quietly reading 7/9.

---

## Notes

- Requires Python 3 with **Pillow** only, plus `g++` to build the shared
  library (already present on macOS and Linux; on Windows use WSL or MinGW).
- The Arduino sketch needs **no libraries** — `Wire` and `EEPROM` ship with
  the IDE.
- Numbers in `config.h` are read by the simulator too, so tune once.
