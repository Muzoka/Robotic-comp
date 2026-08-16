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

| Section | Shape | Route | Turns |
| --- | --- | --- | --- |
| Map 1 | A single U around a 3 × 4 ft block | 12 ft | 2 |
| Map 2 | A short dog-leg, with a loop hanging off it as a distractor | 6 ft | 3 |
| Map 3 | A 1-ft zig-zag, up and down twice | 16 ft | **8** |

Map 3 is the one that decides the competition: it carries 9 of the 17 sector
points, and it asks for a 90° turn in almost every square.

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
positions. They are laid out evenly along the route, each one in the middle
of a square the route passes straight through — never on a corner, because
"all three wheels completely passes the sector line" (§6.1) is hard to
satisfy while pivoting.

If you can get the real positions, they go in
`sim/maps/build_maps.py`. They do not change how the robot drives — it
cannot see them except with the floor sensor — only how the score is counted
in simulation.

## What the simulator says today

Robot as measured (250 × 150 mm), passage 304.8 mm, 3-minute limit:

| Section | Sector points | Time | Wall scrapes |
| --- | --- | --- | --- |
| Map 1 | 3 / 3 | 51 s | 12 |
| Map 2 | 4 / 5 | 28 s | 5 |
| Map 3 | 1 / 9 | ran out of time | 261 |

Maps 1 and 2 are solved. **Map 3 is not**, and it is worth more than the
other two put together.

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
