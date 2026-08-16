# Getting the robot to finish all three maps inside 3 minutes

This is the result of driving the three spreadsheet maps thousands of times
in simulation. Everything below is measured, and every measurement can be
reproduced with one command.

---

## Result

| Map | Completed | Time | Sector points | Wall scrapes |
| --- | --- | --- | --- | --- |
| Map 1 | **100 %** | 65 s | 3 / 3 | 9 |
| Map 2 | **100 %** | 42 s | 4 / 5 | 5 |
| Map 3 | **100 %** | 92 s | 7 / 9 | 16 |

All three finish comfortably inside the 3-minute limit — the slowest is Map 3
at about **92 seconds**, half the allowance.

**That result needs one physical change: the robot has to come down from
250 × 150 mm to about 220 × 140 mm.** At its current size Map 3 completes
only 20 % of the time.

```bash
cd sim
python3 run.py --all --trials 5                    # as the robot is today
python3 run.py --all --trials 5 --robot 220x140    # after the change
```

---

## Why 2 cm matters so much

Turning on the spot, a robot sweeps a circle as wide as its own body
diagonal. The passage is one foot — **304.8 mm**.

| Robot | Body diagonal | Clearance each side | Map 3 completed |
| --- | --- | --- | --- |
| 250 × 150 mm *(today)* | 292 mm | 6.4 mm | 20 % |
| 235 × 145 mm | 276 mm | 14 mm | 100 % |
| **220 × 140 mm** *(target)* | **261 mm** | **22 mm** | **100 %** |

There is a cliff at a diagonal of about **280 mm**. Above it the robot
grinds its way round every corner and eventually wedges; below it, corners
are uneventful. Map 1 has two turns and Map 2 has three, so they survive
either way. Map 3 asks for **eight**, several in adjacent squares, and eight
marginal turns in a row is not a thing you get away with.

Losing **3 cm of length and 1 cm of width** is enough.

## Where to find 3 cm

Measure the true outer envelope with a tape measure — nose to tail including
anything that protrudes, and tyre-outside to tyre-outside. Then:

1. **The front ultrasonic bracket.** On most 2WD builds this hangs off the
   nose and is worth 20–30 mm on its own. Move it back so it sits over the
   chassis plate, looking forward through the gap. This is usually the whole
   3 cm by itself.
2. **The battery.** If it sits behind the rear axle it is adding to the tail.
   Stack it on top of the plate instead, over the wheels.
3. **Screw heads and standoffs at the corners.** Use countersunk screws and
   move mounting holes inboard.
4. **The castor bracket.** Tuck it under the plate rather than ahead of it.
5. **Cable loom.** Anything bulging past the outline counts.

If after all that the chassis plate itself is still longer than ~230 mm,
ask a judge before cutting anything — §2.2 forbids removing or replacing
kit parts, and a trimmed chassis is a conversation you want to have *before*
inspection, not during it.

---

## Sensor changes — and what NOT to buy

You asked whether to move the sensors and what to shop for. Both answers are
measured.

### Move the two side ultrasonics back onto the wheel-axle line — free

They were 40 mm ahead of the axle. Put them **level with the axle**, so a gap
is seen at the instant the axle draws level with it, which is the moment the
robot needs to act on. Worth about **20 percentage points** of completion on
Map 3, and it costs nothing but remounting. `US_L_X_MM` / `US_R_X_MM` in
`config.h` are now `0`.

Keep them square to the wall (90° out), as far forward *sideways* as the
wheel line allows but never past it, and at a height where they see the wall,
not the floor.

### Do NOT buy laser distance sensors — buy nothing

Time-of-flight modules (VL53L0X / VL53L1X) look like an obvious upgrade:
narrow beam, no acoustic crosstalk, no specular dropout. I modelled them —
4° beam, no dropout, low noise — and they came out **worse**:

| Sensors | Map 1 | Map 2 | Map 3 |
| --- | --- | --- | --- |
| HC-SR04 (what you have) | 100 % | 100 % | **100 %** |
| ToF laser, same robot size | 80 % | 100 % | **40 %** |

A narrow beam sees a single point. The HC-SR04's wide cone effectively
averages across a whole square of wall, which is exactly what a
wall-following controller wants, and it notices an opening a little early
rather than a little late. **Save the money.** Your three HC-SR04s are the
right sensor for this maze.

### Shopping list, unchanged

Nothing new is needed for this. The list in `docs/09_CHECKLIST.md` still
stands: MPU-6050 gyro ×2, LM393 wheel encoders ×2, TCRT5000 floor sensor ×2,
a 7.4 V battery, and the tools. **No extra distance sensors, no laser
modules, no memory chip.**

---

## Firmware changes behind the result

Five bugs, all found by driving the real map geometry:

**1. The "there is a gap on that side" threshold was larger than a gap.**
In a 1 ft grid with the side sonar 68 mm off the centreline, a wall beside
the robot reads 84 mm and an opening one square deep reads 389 mm. The
threshold was set to 420 mm — larger than an opening ever reads — so the
robot drove straight past every turn it was supposed to take. It is now
200 mm, which is derived from the maze geometry rather than guessed.

**2. Pivots could never settle.** The motor deadband forced 55 PWM even
inside the tolerance band, so the robot hunted across the target until the
turn timed out a few degrees short, then set off crabbed. Inside tolerance
it now commands zero.

**3. The front sonar was asked for a reading it cannot give.** To put the
axle in the centre of a square it had to read 37 mm; an HC-SR04 is unreliable
below about 40 mm. It now ranges down to 100 mm and counts the last stretch
off the wheel encoders.

**4. Stale junction flags survived a failed turn.** If a turn ended through
the timeout or jam-recovery path rather than normally, the "there was an
opening on the left" flag was still set, and the robot invented a junction a
few centimetres later and turned off the route. Every path back into driving
now clears them.

**5. Where you stop before a corner matters.** A full 360° pivot sweeps the
same circle wherever you stand, but a *quarter* turn does not — stopping
short of the centre gives the front corner room to swing into. Measured
across all three maps:

| Stop point | Completed | Points | Scrapes |
| --- | --- | --- | --- |
| Dead centre of the square | 42 % | 49 % | 218 |
| **40 mm back** | 61 % | **56 %** | **72** |

And one strategy change: **wall following, not the memory mode.** All three
maps are published in advance and none needs memory — the left-hand rule
picks the correct exit at every decision point on all three. The Trémaux mode
measured *worse*, because recognising a junction it has seen before depends
on odometry, and odometry is the least trustworthy thing on the robot. It is
still in the firmware for a map with a real loop; it is no longer the
default.

---

## The one thing to keep in mind on the day

At 220 × 140 mm the robot completes every map with about half the time limit
to spare. Do not spend that margin on speed. `PWM_CRUISE` is set to 110, well
below what the motors can do, because §6.1 scores sector lines and §6.3 only
uses time to break ties. If anything looks marginal on the practice track,
lower it further.
