# Software to install, and every step from here to the finish line

## Part 1 — What to download

| # | Software | Where | Why | Required? |
| --- | --- | --- | --- | --- |
| 1 | **Arduino IDE 2.x** | arduino.cc/en/software | Writes the firmware onto the Uno. Nothing else can | **yes** |
| 2 | **CH340 USB driver** | wch-ic.com/downloads/ch341ser_exe.html (Windows) | Your Uno is the CH340 clone. Windows will not see it without this. macOS Sonoma and Linux already have it | **yes, Windows** |
| 3 | **Python 3.11+** | python.org/downloads — tick *"Add Python to PATH"* during install | Runs the maze simulator | **yes** |
| 4 | **Pillow** | terminal: `pip install pillow` | The simulator's only dependency | **yes** |
| 5 | **Git** | git-scm.com | Downloads this project and keeps your changes | recommended |
| 6 | A **Wokwi** account | wokwi.com | Browser firmware simulator. Nothing to install | recommended |
| 7 | **VS Code** | code.visualstudio.com | Nicer editing than the Arduino IDE. Optional | optional |
| 8 | **g++ compiler** | Windows: install **MSYS2** or use **WSL**. macOS: `xcode-select --install`. Linux: already there | Builds the simulator's shared library | **yes**, for the simulator |

**No Arduino libraries to install.** `Wire` and `EEPROM` ship with the IDE.
The firmware deliberately uses nothing else, so there is no version of this
project that fails because a library would not download.

### Windows: the shortest path

If setting up g++ on Windows looks painful, install **WSL** instead — one
command in PowerShell as administrator:

```powershell
wsl --install
```

Restart, open "Ubuntu" from the Start menu, then:

```bash
sudo apt update && sudo apt install -y g++ python3 python3-pip git
pip3 install pillow
```

The Arduino IDE still runs on Windows normally; only the simulator lives in
WSL.

---

## Part 2 — Get the project

```bash
git clone https://github.com/Muzoka/Robotic-comp.git
cd Robotic-comp
git checkout claude/robot-competition-setup-ingek7
```

Or download the ZIP from the GitHub page if you would rather not use Git.

---

## Part 3 — Before you buy anything (30 minutes)

```bash
# 1. Measure your robot with a tape measure, then put the numbers in
#    firmware/MazeRunner/config.h  (ROBOT_LENGTH_MM, ROBOT_WIDTH_MM,
#    WHEEL_BASE_MM, AXLE_FROM_NOSE_MM, WHEEL_DIAM_MM)

# 2. Ask the one question that matters
python3 tools/geometry_check.py --corridor 300

# 3. Watch the robot drive your three maps
cd sim
pip install pillow
python3 run.py --all --compare
```

Open the GIFs in `sim/runs/`. If step 2 says "IMPOSSIBLE" or "no", read
`docs/02_HARDWARE.md` §0 before you spend money — the robot has to get
smaller first.

---

## Part 4 — Prove the firmware in Wokwi (1 hour)

Follow `wokwi/README.md`. You are checking that the pin map is right, the
gyro talks over I2C, the state machine advances and the sketch fits in the
Uno's memory. Do this before you own the parts; it costs nothing and it is
the cheapest bug-finding you will ever do.

---

## Part 5 — Build (2 days)

**Build the practice track first.** 14 sheets of foam board, walls 12 cm
tall, passages 30 cm wide, black tape 30 cm across for sector lines. Copy
the shape of Map 2 first — it is the simplest.

Then the robot, in this order:

1. Chassis and motors, **axle centred**. Nothing behind the axle if you can
   help it.
2. Castor wheel on the front.
3. Encoder discs on the inside of each wheel; LM393 sensors straddling them.
4. Green perfboard mounted in the **middle** of the chassis on M3 standoffs.
   Solder a 5 V rail, a GND rail, and the headers.
5. Arduino on standoffs. L298N on standoffs.
6. Sensors: front sonar at the nose, side sonars square to the walls,
   MPU-6050 flat and rigid near the centre, GO button somewhere you can reach
   off the floor.
7. Battery on **top**, retained mechanically. Master switch where you can
   reach it.
8. Wire it per `docs/wiring_diagram.svg`. Cut each wire after routing it.
9. **Check every rail with the multimeter before the Arduino goes in.**
10. Measure where the sensors actually ended up and update `config.h`.

---

## Part 6 — First power-up (in this order, do not skip)

Robot **on a block, wheels free**. Run each bench test from
`tools/serial_check.md`:

| # | Test | Pass |
| --- | --- | --- |
| 1 | Motors | Correct wheel, correct direction, both speeds |
| 2 | Encoders | 20 counts per wheel revolution |
| 3 | Ultrasonics | Correct mm at 5 / 10 / 30 / 100 cm; no cross-talk |
| 4 | Gyro | 90 ± 3° when you turn the robot 90° against a square |
| 5 | Line sensor | Clean switch between white floor and black tape |

Only then flash the real firmware.

### Flashing

1. Arduino IDE → **File → Open** → `firmware/MazeRunner/MazeRunner.ino`.
   The other three files appear as tabs automatically.
2. **Tools → Board → Arduino Uno.**
3. **Tools → Port →** the CH340 port (`COM3` on Windows,
   `/dev/ttyUSB0` on Linux, `/dev/cu.wchusbserial…` on macOS).
4. **Upload** (→ arrow).
5. **Tools → Serial Monitor**, set to **115200 baud**.

---

## Part 7 — Tune on the track (1 day)

1. Straight 2 m passage. Does it drive straight and centred? Adjust
   `KP_WALL`, `KD_WALL` in `config.h`.
2. One 90° corner. Does it stop in the right place and come out centred?
   Adjust `FRONT_PIVOT_MM`, `CREEP_AFTER_OPEN_MM`.
3. Build each map shape and run it ten times.
4. Record the robot's own telemetry and compare it with the simulator's:
   ```bash
   pip install pyserial
   python3 tools/telemetry_log.py --port COM3 --out real_run1.csv
   ```
   Where the real robot and the simulated one disagree tells you which number
   in `sim/robot.py` is wrong. Fix that once, and from then on the simulator
   predicts *your* robot rather than a generic one.
5. Every change goes into `config.h` first, gets checked in the simulator,
   and only then gets flashed.

---

## Part 8 — Competition day

Full sheet in `docs/07_COMPETITION_DAY.md`. The short version:

1. **Measure the real maze.** Passage width, wall height, overall size.
2. **Trace each map** into `sim/maps/` — 15 minutes each, they are plain text.
3. Run `python3 run.py --map maps/real1.txt --compare`. It tells you which
   wall-following direction wins on that map, before your run.
4. Pass technical inspection (§11 checklist in `docs/03_WIRING.md`).
5. Start the robot with the hand gesture at the nose:
   **quick tap = left-hand rule, long hold = right-hand rule.**
   The countdown blinks slow for left, fast for right — check it matches.
6. Step back. Do not touch it (§3.4).
7. Fresh battery between every run.

---

## Timing, given the 3-minute limit per map

The firmware stops itself at **175 seconds** so it never overruns. In
simulation, Map 2 takes about 38 seconds at the default cruise speed, so
there is a large margin. That margin is worth spending on reliability:
if the robot is scraping walls, **lower `PWM_CRUISE` from 150 to 120** and
re-test. Slower is almost always more points, and time only breaks ties
(§6.3).
