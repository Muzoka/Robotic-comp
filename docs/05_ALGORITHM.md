# How the robot thinks

All of this lives in `firmware/MazeRunner/nav_core.cpp`. It contains no
Arduino code at all, which is what lets the simulator run it.

## The loop, 50 times a second

```
  sonar (front, left, right)  ─┐
  gyro rate                    ├──►  nav_step()  ──►  left PWM, right PWM
  wheel encoder counts         │
  floor sensor                ─┘
```

## States

```
   WAIT_START ──► COUNTDOWN ──► DRIVE ──┬──► CREEP ──► TURN ──┐
                                        │                     │
                                        ├──► BACKUP ──────────┤
                                        │                     │
                                        └──► STUCK_RECOVER ───┘
                                                              │
                                                        (back to DRIVE)
   ... and FINISH when the maze is behind us.
```

### DRIVE — going down a corridor

Two things happen at once.

**Staying centred.** A PD controller on the side sensors:

- both walls visible → aim for `dLeft == dRight`
- only one wall → hold `TARGET_SIDE_MM` (90 mm) off it
- neither wall → the gyro is all we have; hold the heading

The sign convention is written down in the source because getting it
backwards makes the robot steer *into* the wall it is too close to — which is
exactly the bug the simulator caught.

**Holding the heading.** A gyro term is always mixed in, weighted at 35 %
when walls are visible and 100 % when they are not. That is what keeps the
robot straight in a doorway, and what stops the mismatched motors curving it
into a wall over a long straight.

### Spotting a junction

Two triggers:

- **A wall appears ahead** — `dFront < 200 mm`.
- **A side wall disappears** — a *rising edge* from "wall" to "open".

The edge matters. Level-triggering ("is the side open right now?") fires the
instant the robot rolls out of the start gate into the open floor of the
start zone, before it has ever seen a wall, and the robot turns into the
first wall it meets. Every run. The edge is also debounced over nine loops,
because a single dropped ultrasonic ping otherwise invents a junction that
is not there.

### CREEP — the step most people skip

When a junction is spotted, the robot does **not** turn. It creeps forward
until the **wheel axle** — not the nose — is in the middle of the junction
square, and turns from there.

Why: the ultrasonic sits ~95 mm ahead of the axle. Stop when the sensor sees
the wall and the axle is still 95 mm short of centre. Pivot from there and
the robot ends up ~95 mm off the centreline of the new corridor — which in a
300 mm passage, with an 80 mm half-width robot, means hitting the wall.

Two ways to get to the middle:

- **wall ahead:** creep until the front sensor reads `FRONT_PIVOT_MM` = 55 mm,
  which is `corridor/2 − sensor offset`. Ranging off a wall is far more
  accurate than dead reckoning.
- **no wall ahead, just a side opening:** count `CREEP_AFTER_OPEN_MM` = 145 mm
  off the encoders.

### TURN — pivoting

1. Stop completely for 260 ms. Pivoting while still rolling forward is what
   puts a corner of the chassis into a wall. That pause is also when the gyro
   bias gets re-measured.
2. PD on the gyro heading until the error is under 3° and stays there for
   120 ms.
3. **Re-zero the heading to the target.** We have just lined up with a
   corridor, so this is the most trustworthy heading we will ever have.
   Calling it exact means gyro error never accumulates from one corner to
   the next — it only has to survive one turn.
4. If the turn times out, back up 90 mm and try the same turn again (twice)
   rather than setting off at an angle. A timed-out turn is almost always a
   body corner touching a wall.

### Which way to turn

**Mode 0 — wall following.** Keep one hand on the wall: try left, then
straight, then right, then turn around (or mirrored, for the right hand).
Simple, and it solves any maze whose finish is connected to the wall you are
holding.

**Mode 1 — Trémaux, the default.** The robot remembers junctions and prefers
the exit it has used least:

- arriving at a junction, mark the passage you came in through;
- choose the open exit with the fewest marks;
- break ties in wall-following order, so when nothing has been visited it
  behaves exactly like a wall follower and takes the short, tidy path;
- mark the exit you chose.

Each passage gets used at most twice, which is what makes it terminate. It
beats plain wall-following on maps with loops and islands — on the serpentine
map it scores 9.8/12 sectors against 8/12.

One special rule: **at the very first junction, the passage behind you is the
start gate, so it gets marked "fully used" immediately.** Without it, a
wall-following robot that laps the outer ring calmly drives back out of its
own front door and scores nothing. That is the most common way to lose this
kind of event.

## Memory — no extra chip needed

Each junction is **4 bytes**: position (in 50 mm units) plus 2 bits per
compass direction recording how many times that exit was used.

```
48 junctions × 4 bytes = 192 bytes
Arduino Uno has 2048 bytes of SRAM and 1024 bytes of EEPROM.
```

So the answer to "can the code act as the memory, since we probably cannot
find a memory module?" is yes, comfortably, and you also already own
non-volatile memory: `EEPROM.h` ships with the IDE. `MazeRunner.ino` saves
the junction map to EEPROM at the end of a run. If a judge stops you and you
get another attempt, uncommenting one line makes attempt 2 start with what
attempt 1 learned.

### Position estimate, and why it survives

Junctions are matched **by proximity, not by an exact grid index**, within
260 mm. Two consequences:

- After several metres the encoders have drifted; an exact index would file
  the same corner twice and the memory would be worthless.
- When a junction *is* recognised, the robot snaps its position back onto the
  one it recorded the first time. That is loop closure, and it stops drift
  accumulating lap after lap.

There is also one deliberate omission in the odometry: **translation is
discarded while pivoting.** The two wheels are never perfectly matched, so
`(dLeft + dRight)/2` comes out a few millimetres short of zero on every turn.
Forty turns later the robot thinks it is a quarter of a metre from where it
is. Detecting the pivot and throwing that away removes the largest single
source of drift.

## Knowing when to stop

Three ways, any of which ends the run:

1. **Open on all sides**, and more than 800 mm from where it started, for
   450 mm of travel. The distance condition is what stops the robot calling
   its own start gate a finish.
2. **A burst of stripes under the floor sensor.** The start and finish gates
   in the photos are painted with black/white stripes — nothing else in the
   maze produces four black/white edges in 350 ms.
3. Four minutes elapsed.

## Recovering from trouble

A watchdog runs in every state that is supposed to be moving: motors
commanded above the deadband but the encoders are not counting for 900 ms
means something is jammed. The robot reverses, turns slightly — alternating
direction each time so it does not repeat the same failed escape — and
carries on. Without this a single wedge ends the run; with it the robot
usually frees itself in under two seconds.

## Where the numbers live

Everything tunable is in `firmware/MazeRunner/config.h`, and the simulator
reads that same file. Change a number there, re-run `sim/run.py`, see the
effect, then flash. The most useful ones:

| Name | Default | What it does |
| --- | --- | --- |
| `PWM_CRUISE` | 150 | Straight-line speed. Lower = calmer, higher = faster and clumsier |
| `KP_WALL` | 0.42 | How hard it corrects sideways. Too high = weaving |
| `KP_HEADING` | 3.2 | How hard it holds a straight line |
| `FRONT_PIVOT_MM` | 55 | Where it stops before turning — see CREEP above |
| `OPEN_SIDE_MM` | 420 | Above this, a side reading counts as an opening |
| `WALL_HAND` | +1 | +1 left, −1 right (also selectable at the start line) |
| `DEFAULT_MODE` | Trémaux | 0 for plain wall following |
