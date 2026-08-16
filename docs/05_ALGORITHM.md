# How the robot thinks

All of this lives in `firmware/MazeRunner/nav_core.cpp`. It contains no
Arduino code at all, which is what lets the simulator run it.

## The loop, 50 times a second

```
  sonar (front, left, right)  ─┐
  gyro rate                    ├──►  nav_step()  ──►  left PWM, right PWM
  wheel encoder counts         │
  GO button                   ─┘
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

**First, before anything else: if the way ahead is open, go straight.**

This one line (`STRAIGHT_FIRST` in `config.h`) decides what the route looks
like, because on a maze the robot has not seen before nearly every junction
is otherwise a coin-toss between equally good exits.

Why it is worth having:

- **It is the fastest thing you can do.** Not turning costs nothing; a pivot
  costs about a second, plus the settle time before and after it.
- **It avoids the worst pivots.** Map 2 has one 4-way crossing. Turning
  there is the hardest turn on the whole course, because once the robot has
  pivoted there is no wall on either side to check itself against — the
  corridor-parallel correction below has nothing to work with, so a turn
  that finishes 8° short *stays* 8° short. Every livelock this project had
  began in that square. Straight-first drives through it twice, turning
  neither time, and Map 2 drops from 6 pivots to 4.
- **It makes the hand choice stop mattering.** Left and right now produce
  the identical route on all three maps. The left-hand rule used to turn
  straight out of the Map 2 exit and skip the entire lower loop.

The limitation, stated plainly: **straight-first alone is not a complete
coverage rule.** In a maze with a dead-end stub, the robot can go straight
into the stub, U-turn at the end, come back to the crossing, and go straight
again — right past two arms it has never driven. On a test maze built to
provoke exactly that it covered 5 squares of 11. None of the three
competition maps has a dead end; `build_maps.py` checks every map and prints
`SET STRAIGHT_FIRST 0` if one ever appears.

**Mode 0 — wall following, the default.** After the straight-first check:
keep one hand on the wall — try left, then right, then turn around (or
mirrored, for the right hand). Simple, and it solves any maze whose finish is
connected to the wall you are holding.

**Mode 1 — Trémaux.** The robot remembers junctions and prefers the exit it
has used least:

- arriving at a junction, mark the passage you came in through;
- choose the open exit with the fewest marks;
- break ties straight-first, then in wall-following order, so on fresh
  ground it takes exactly the route above;
- mark the exit you chose.

Each passage gets used at most twice, which is what makes it terminate.
**This is the mode that closes the dead-end hole**: on the test maze that
defeats plain straight-first, straight-first-inside-Trémaux covers 11 of 11.
It costs 4 bytes per junction of the Uno's own SRAM and nothing to buy, so
if a combined map ever turns up with a stub in it, this is the switch to
flip. On the three maps as they stand, both modes drive the same route in
the same time.

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

Two ways, either of which ends the run:

1. **Open on all sides**, and more than 800 mm from where it started, for
   450 mm of travel. The distance condition is what stops the robot calling
   its own start gate a finish. This is the one that fires in practice — on
   every run in this repository.
2. The run timeout.

There used to be a third: a burst of stripes under a floor sensor. It has
been removed along with the sensor. A TCRT5000 chatters as it crosses tape
at an angle, four edges inside 350 ms is easy to produce by accident, and
the consequence was the robot stopping dead in the middle of a map. It was
the only sensor on the robot that could end a run by itself and the only one
that steered nothing. See `HAS_LINE_SENSOR` in `config.h`.

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
