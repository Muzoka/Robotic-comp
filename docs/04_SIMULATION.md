# Which program to simulate with — and the honest answer to "can I just build it and win?"

## The short answer

You asked which program to use so you can simulate, test, then assemble once
and win without testing. Here is the straight answer, and then the tools.

**Simulation will get you about 90 % of the way. It will not get you to
100 %, and no simulator will.** What it genuinely does:

- catches every logic bug — wrong turn, spinning in circles, driving back out
  of the start gate — before you have soldered anything;
- tells you what to buy, and what will not fit (see the corridor width
  finding in `docs/02_HARDWARE.md`, which came straight out of this
  simulator);
- lets you tune the control gains against a hundred runs instead of five;
- proves which wall-following direction solves which map.

What it cannot know: how much your specific carpet grips, exactly how weak
your right motor is, whether your ultrasonic has a factory offset, whether
the maze walls are matte or glossy. Those are the last 10 %, and they cost
about two hours on a practice track. **Budget those two hours.** A team that
simulates and then does one afternoon of real tuning beats a team that only
does one or the other.

---

## What we built for you, and why not something off the shelf

The repository contains a **purpose-built simulator** in `sim/`. Its one
unusual property is the reason it exists:

> The simulator runs the *actual firmware*. Not a copy of it, not a Python
> re-implementation — the same `nav_core.cpp` file that gets flashed onto
> the Arduino is compiled into a shared library and driven by the simulator.

So "it worked in simulation" means the code that worked *is* the code you
flash. Most student robot projects fail exactly at this seam: the tested
model and the shipped code drift apart. Here they cannot.

```
        firmware/MazeRunner/nav_core.cpp   ← all the thinking
                   ╱                ╲
      compiled by Arduino IDE    compiled by g++ into libnavcore.so
                 ↓                        ↓
        MazeRunner.ino               sim/run.py
        (pins, I2C, PWM)             (physics, sonar, gyro, maze)
                 ↓                        ↓
          the real robot            an animated GIF
```

### How to run it

```bash
pip install pillow          # the only dependency

cd sim
python3 run.py --map maps/map3_loop.txt        # one map, makes a GIF
python3 run.py --all --compare                 # every map, every strategy
python3 run.py --all --sweep-corridor          # how narrow can the maze be?
python3 run.py --all --trials 20 --no-gif      # statistics, no pictures
```

Outputs land in `sim/runs/`:

| File | What it is |
| --- | --- |
| `<map>.gif` | An animation of the whole run — robot, sonar beams, path, live sector count |
| `<map>.csv` | Every 20 ms: sensor readings, heading, PWM, position, state |
| `summary.txt` | Scoreboard across all runs |

The maps are plain text you can edit in Notepad. `sim/maps/map3_loop.txt`
starts like this:

```
!name Map 3 - Island Loop
!cell 100
!start 150 1550 0
!sector 450 1800 450 2100
...
......................
....##############....
....#............#....
```

`#` is wall, `.` is floor. When you get to see the real maze, trace it onto
this grid and re-run. That takes fifteen minutes and it is the single most
valuable thing you can do on the day before.

---

## Other programs, and when they are worth it

### Wokwi — free, in a browser — **use this too**

<https://wokwi.com>

Wokwi simulates the actual AVR chip, so it runs your compiled `.ino`
including `Wire`, `EEPROM`, interrupts and timing. It has an Arduino Uno, an
HC-SR04 and an MPU-6050 in its parts library.

**What it is good for:** proving that your *firmware* is right — that the
pins are correct, that the I2C talks to the gyro, that the ultrasonic timing
works, that the loop actually runs at 50 Hz, that you have not run out of
SRAM. It will catch a wrong pin number in five minutes.

**What it is not good for:** it has no physics and no maze. It cannot tell
you whether the robot navigates. Use it for the electronics, use `sim/` for
the driving.

### Tinkercad Circuits — free — for teaching, not for this

Good for showing a team member how an H-bridge works. Too limited for a
three-sensor robot with an IMU.

### Webots — free, open source, real 3D physics

<https://cyberbotics.com>

A professional robot simulator. Has differential-drive robots, distance
sensors, IMUs and proper rigid-body physics out of the box, and you can build
the maze in its editor.

**Worth it if:** you want a realistic 3D view for the presentation, or you
want to check something our 2D model does not cover (the robot tipping, a
wheel climbing a wall). **The catch:** controllers are written in C/Python
against Webots' own API, so it will *not* be running your firmware. You would
be testing a second, different program. For this competition the cost
outweighs the benefit — but it is the right next step if you carry on with
robotics.

### Gazebo / ROS 2, CoppeliaSim, MATLAB Simulink

All excellent, all far too much machinery for an Arduino Uno with three
ultrasonics. Skip them.

### Recommended combination

| Tool | Use it for | Time to set up |
| --- | --- | --- |
| **`sim/` (this repo)** | Navigation logic, tuning, strategy, corridor-width risk | done |
| **Wokwi** | Pin map, I2C, timing, memory usage — firmware sanity | 30 min |
| **A real practice track** | The last 10 % | one afternoon |

---

## What the simulator already told us

These are results, not predictions. Every one came out of a run you can
repeat.

**1. A geometry problem that would have ended the project.**
The robot sweeps a 269 mm circle when it pivots. At the rulebook's minimum
200 mm passage it cannot turn at all. Measured success rate against passage
width, 5 maps × both directions:

| Passage | Can it turn? | Finished | Sector points |
| --- | --- | --- | --- |
| 200 mm | **no** | 0 % | 0 % |
| 250 mm | **no** | 10 % | 33 % |
| 300 mm | yes, 16 mm to spare | 60 % | 72 % |
| 350 mm | yes | 70 % | 71 % |
| 400 mm | yes | 70 % | 78 % |

→ Ask the organisers for the passage width before you build anything.

**2. Two real bugs, found before any hardware existed.**
The wall-centring term had an inverted sign — the robot steered *into*
whichever wall it was too close to. Fixing it dropped wall scrapes from
~2 500 per run to under 100. And the junction detector originally triggered
on the open floor of the start zone, so the robot turned into a wall in the
first two seconds of every run.

**3. Gyro drift is worth 15–20° per run if you ignore it.**
Straight integration of an MPU-6050 put the robot 22° out of square after
50 seconds, which is enough to wedge it in the next corner. The fix (re-zero
the bias at every stop, re-zero the heading after every completed turn) is in
the firmware and is the reason the corners work.

**4. Which direction to follow, per map.**
Measured over 4 seeds per map at 350 mm passages:

| Map | Left-hand rule | Right-hand rule |
| --- | --- | --- |
| Spiral (goal in the middle) | 5.0 / 7 sectors, never finished | 4.8 / 7, finished 25 % |
| Serpentine | **9.8 / 12, finished 75 %** | 9.8 / 12, finished 75 % |
| Island loop | **9.0 / 9, finished 100 %** | 6.0 / 9, finished 75 % |
| Practice corner | **2.2 / 3, finished 100 %** | 2.2 / 3, finished 75 % |
| Dead ends + loop | **5.0 / 7, finished 100 %** | 3.2 / 7, finished 50 % |

→ **Left-hand rule is the default.** But it is not right for every shape,
which is why the robot lets you choose the direction at the start line
without a laptop (§`docs/07_COMPETITION_DAY.md`).

**5. A map shape that wall-following cannot solve, ever.**
If the finish is a chamber in the *middle* of the maze, enclosed by its own
ring of wall (which is what photo 1 looks like), then no wall-following robot
can reach it — the goal is not connected to the wall you are following. This
is a known result in maze theory, not a bug. Our memory mode gets 5–6 of the
7 sector points on that map and occasionally finishes; a plain wall follower
gets 4. If the real map 1 has its finish gate on the **outer edge** (which
the striped marking in the photo suggests), the problem disappears.

**Which matters more than it sounds**, because of how scoring works: §6.1
awards a point per sector line crossed, and the winner is whoever has the
most points. Finishing is not required to score. A robot that never gets
stuck and keeps crossing lines beats a robot that solves two maps perfectly
and jams on the third.
