# The maps — from the organisers' spreadsheet

Everything here now comes from
`Robotics_Competition_Maps_v2_5x5_grid.xlsx`. No more guessing from photos.

## The numbers

| From the sheet | Value | In millimetres |
| --- | --- | --- |
| Total dimension | 5 ft × 5 ft + wall thickness | 1524 × 1524 + walls |
| Each grid square | 1 ft × 1 ft | **304.8 mm** |
| Wall thickness | 0.75 inch | 19.05 mm |
| Wall height | 7.5 inches | 190.5 mm |
| Time limit | 3 minutes per run | firmware stops itself at 175 s |

Each sheet is a 5 × 5 block of cells, B2:F6. **A blue cell is open floor, a
white cell is a solid block.** Entrance and exit are labelled and are always
on the left and right walls.

So the passage is exactly one foot — **304.8 mm** — everywhere.

## The three sections

```
        MAP 1                 MAP 2                 MAP 3
      3 sectors             5 sectors             9 sectors

      P P P P P             P P P P X             P P X P P
      P X X X P             X X X P X             X P X P X
      P X X X P             X P P P P  ← exit     P P X P P
      P X X X P             X P X P X             P X X X P
in →  P X X X P  → out      X P P P X             P P P P P
                       in ↗                  in ↗            ↘ out
```

| Section | Shape | Road | Route driven | Pivots |
| --- | --- | --- | --- | --- |
| Map 1 | A single U around a 3 × 4 ft block | 13 sq | 12 ft | 2 |
| Map 2 | A dog-leg with a loop hanging off a 4-way crossing | 14 sq | 14 ft | 4 |
| Map 3 | A 1-ft zig-zag, up and down twice | 17 sq | 16 ft | **8** |

Map 3 is the one that decides the competition: it carries 9 of the 17 sector
points, and it asks for a 90° turn in almost every square.

### Map 2 and the crossing — the route the robot drives

Map 2 is the only one with a genuine choice in it. The middle-right square
is a **4-way crossing**, and the exit is one square east of it. A robot that
simply turns towards the exit the first time it arrives there leaves with
half the road undriven.

The route driven now — and it is the one drawn by hand on the photo:

```
  00 → 01 → 02 → 03        east along the top
                 ↓
                13 → 23     south, straight THROUGH the crossing
                     ↓
                    33 → 43     ...and on down to the bottom row
                         ↓
      41 ← 42 ← 43           west along the bottom
       ↓
      31 → 21               north up the left column
            ↓
           22 → 23 → 24     east through the crossing again, and out
```

It enters and leaves the crossing **going straight both times**, and never
pivots in it. That is the whole point: the crossing is the one square on the
course with no wall on either side, so a pivot finishing a few degrees short
there has nothing to correct itself against. Every livelock this project
ever had started in that square.

The rule that produces this is `STRAIGHT_FIRST` in `config.h` — go straight
whenever the way ahead is open, ask the hand rule only when it is not. It is
worth two pivots and about 4 seconds here, and it also means the left-hand
and right-hand rules now drive the identical route, so the hand setting can
no longer cost you a map.

## The combined course

`COURSE` at the top of `sim/maps/build_maps.py` is one line:

```python
COURSE = [("map1", False), ("map3", True), ("map2", True)]
```

`True` means that section is mirrored top-to-bottom. That is what makes the
gates line up: read left to right, every exit lands on the same row as the
next entrance, so the shared wall between two sections has exactly one
opening in it.

```
   map1              map3 mirrored          map2 mirrored
   in left row 5  →  in left row 5      →   in left row 5  →  out right row 3
```

Result: **4.67 m × 1.57 m, a 36 ft route, 17 sector points.** 36 ft is 11 m;
at the tuned cruise speed that is roughly 45 seconds of driving plus about a
minute of turning, so the 3-minute limit is achievable but not generous.

**If the organisers butt the sections together in a different order or
orientation, change that one line and re-run `python3 build_maps.py`.**
Nothing else needs touching. Tell me the arrangement and I will set it.

## Sector line positions — an assumption

The spreadsheet gives the *count* per section (3, 5, 9) but not the
positions. They are laid out evenly along the route, each one on a **square
boundary the route crosses head-on** — never in the middle of a corner,
because "all three wheels completely passes the sector line" (§6.1) is a
matter of luck while pivoting.

`build_maps.py` now asserts this: every generated line has to sit on a
boundary between two squares the route drives one after the other. That
check found a real bug — horizontal lines were being placed a whole cell too
high, so on Map 3 two of them sat **inside a solid block** and one sat
outside the maze entirely. Three of the nine points were unscoreable by any
robot, and the only symptom was a scoreboard quietly reading 7/9.

If you can get the real positions, they go in `sim/maps/build_maps.py`. They
do not change how the robot drives — it cannot see them at all now the floor
sensor is gone — only how the score is counted in simulation.

## What the simulator says today

Robot 220 × 115 mm, passage 304.8 mm, `PWM_CRUISE 200`, 3-minute limit,
8 seeds × 4 strategy combinations per map:

| Section | Complete | Road driven | Sector points | Time | Wall contact |
| --- | --- | --- | --- | --- | --- |
| Map 1 | 100 % | 100 % | 3 / 3 | 32 s | none |
| Map 2 | 100 % | 100 % | 5 / 5 | 36 s | none |
| Map 3 | 100 % | 100 % | 9 / 9 | 48 s | none |

All three are solved, with every sector point taken, in about a third of the
time allowed. Map 3 — the one that used to run out of time — is still the
hardest, and it is the one to practise on physically.

## Why map 3 is hard, and what to do about it

Your robot is 250 × 150 mm. Turning on the spot it sweeps a circle the width
of its own diagonal — **292 mm** — inside a **304.8 mm** passage. That is
**6.5 mm of clearance each side.**

Map 1 has two turns and map 2 has three, so the robot gets away with it. Map
3 asks for eight, several of them in adjacent squares, and 6.5 mm is not
enough margin to do that eight times in a row.

Two things came out of measuring this, and both are already in the firmware:

**1. Where you stop before a corner matters.** A full 360° pivot sweeps the
same circle wherever you stand, but a *quarter* turn does not — stopping a
little further back from the wall ahead gives the front corner room to swing
into. Measured across all three maps:

| Stop distance before the square's centre | Finished | Points | Scrapes |
| --- | --- | --- | --- |
| 0 mm (dead centre) | 42 % | 49 % | 218 |
| **20 mm back** | **75 %** | **53 %** | 148 |
| 40 mm back | 67 % | 49 % | **97** |
| 60 mm back | 50 % | 47 % | 128 |
| 80 mm+ | 50 % | 46 % | 149 |

`PIVOT_BACKOFF_MM` in `config.h`.

**2. The front sonar cannot be trusted for the last few centimetres.** To
put the axle in the middle of a square, the front sensor — mounted 115 mm
ahead of the axle — would have to read 37 mm, and an HC-SR04 is unreliable
below about 40 mm. The firmware now ranges off the wall down to 100 mm and
then counts the last stretch off the wheel encoders.

**3. The robot still has to get smaller.** Measured on map 3 alone, six runs
per size:

| Robot | Swept circle | Finished | Points |
| --- | --- | --- | --- |
| 250 × 150 mm *(yours)* | 292 mm | 17 % | 1.3 / 9 |
| 220 × 140 mm | 261 mm | 0 % | 2.2 / 9 |
| **200 × 130 mm** | **239 mm** | **33 %** | **3.7 / 9** |
| 180 × 120 mm | 216 mm | 17 % | 3.2 / 9 |
| 140 × 100 mm | 172 mm | 67 % | 3.3 / 9 |

Smaller is clearly better, but even a tiny robot does not solve map 3
outright — so this is **not only a size problem**. The turn-by-turn logic
needs more work for squares where a corner comes immediately after a corner,
and that is the next job. Being able to reproduce it in the simulator in two
seconds is what makes that job tractable.

## Editing a map yourself

The `.txt` files are plain characters: `#` is wall, `.` is floor, one
character = 1 inch. To change a shape, edit the five-line `grid` for that
sheet at the top of `sim/maps/build_maps.py` — `P` for blue, `X` for white,
exactly as the spreadsheet reads — and run:

```bash
cd sim/maps && python3 build_maps.py
cd .. && python3 run.py --all --compare
```
