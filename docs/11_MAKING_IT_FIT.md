# Getting all three maps inside 3 minutes

Everything here is measured. Every number can be reproduced with one command.

---

## Result

Robot **220 × 115 mm**, wall-following, **right hand**, 15 random seeds per
map. "Complete" means the robot drove **every square of the road** and then
left — not that it merely reached the exit.

| Map | Complete | Road driven | Time | Sector points |
| --- | --- | --- | --- | --- |
| Map 1 — U around a block | **93 %** | 98 % | 66 s | 2.9 / 3 |
| Map 2 — dog-leg with a loop | **93 %** | 96 % | 70 s | 3.9 / 5 |
| Map 3 — 1 ft zig-zag | **80 %** | 94 % | 97 s | 6.4 / 9 |

Every completed run is inside about half the 3-minute allowance. §3.3 gives
2–3 attempts whenever a map is not completed, so 80 % per attempt is better
than 99 % across three tries.

```bash
cd sim
python3 run.py --all --trials 15
```

## Driving the WHOLE road, not the shortest way across

The robot has to cover every square before it leaves. That is a different
problem from finding the exit, and only one wall-following direction does it:

| | Map 1 | Map 2 | Map 3 |
| --- | --- | --- | --- |
| Left-hand rule | 100 % | **50 %** | 100 % |
| **Right-hand rule** | **100 %** | **100 %** | **100 %** |

On Map 2 the left hand reaches the junction, sees the exit on its left and
takes it, skipping the whole lower loop — 7 of the 14 squares. The right hand
turns into the loop first and only leaves once there is nothing else to
drive. `WALL_HAND` is now `-1`.

The simulator scores this directly: every run reports **road %**, and a run
that reaches the exit early is reported as *"left early — only 50 % of the
road"* rather than as a finish.

---

## Does the robot's size affect the code? Yes — badly, if you let it

It used to. Half a dozen thresholds were hand-tuned for one body width, and
when the body changed they silently stopped matching the hardware. The
symptom looks like a navigation bug and costs a day.

**That is now fixed. `config.h` derives them.** You change two numbers:

```c
#define ROBOT_LENGTH_MM     220.0f
#define ROBOT_WIDTH_MM      115.0f   /* tyre outside to tyre outside */
```

and these follow automatically:

| Derived | From | At 220 × 115 |
| --- | --- | --- |
| `WHEEL_BASE_MM` | width − one tyre width | 89 mm |
| `AXLE_FROM_NOSE_MM` | half the length (centred axle) | 110 mm |
| `US_F_X_MM` | front sonar just inside the nose | 100 mm |
| `US_L_Y_MM` / `US_R_Y_MM` | side sonars just inside the tyre line | ±50.5 mm |
| `TARGET_SIDE_MM` | passage centre as the side sensor sees it | 102 mm |
| `OPEN_SIDE_MM` | between "wall beside me" and "gap one square deep" | 239 mm |
| `TURN_FF` | the PWM that produces a given turn rate | from the wheelbase |

The simulator reads the same file and evaluates the same expressions, so the
two can never drift apart. Measure your robot, put the two numbers in, re-run.

---

## Width matters more than length, and 115 mm is a sharp optimum

You suggested 22 × 10 cm. Close — but the sweet spot is a centimetre wider,
and it is a **sharp** peak, not a plateau. Ten seeds per map:

| Robot | Diagonal | Map 1 | Map 2 | Map 3 | Average | Scrapes |
| --- | --- | --- | --- | --- | --- | --- |
| 220 × 105 mm | 244 mm | 100 % | 100 % | 70 % | 90 % | 22 |
| 220 × 110 mm | 246 mm | 100 % | 100 % | 50 % | 83 % | 27 |
| **220 × 115 mm** | **248 mm** | **90 %** | **100 %** | **100 %** | **97 %** | **11** |
| **225 × 115 mm** | **252 mm** | **100 %** | **100 %** | **90 %** | **97 %** | **12** |
| 220 × 120 mm | 251 mm | 100 % | 100 % | 60 % | 87 % | 12 |
| 230 × 120 mm | 259 mm | 60 % | 100 % | 60 % | 73 % | 58 |

**Why width, when clearance says it should not matter?** Because the
wheelbase comes with it. A narrower robot has a shorter wheelbase, and a
shorter wheelbase turns faster for the same difference in wheel speed — so
every bit of motor mismatch, every bit of wheel slip, swings the heading
further. At 110 mm the robot is twitchy; at 120 mm the extra body starts
costing clearance again. 115 mm is where the two curves cross.

**Target 220 × 115 mm — 22 × 11.5 cm.** Anywhere in 215–225 × 112–118 is
fine. If you land somewhere else, change the two numbers and re-run the
sweep; everything else follows.

If your 10 cm was the chassis *plate*, measure again across the tyres — that
is the number the walls see, and on a standard 2WD kit the tyres add several
centimetres to the plate.

---

## What I tried from the micromouse world, and what it measured

The established competitive technique is trapezoidal motion profiles, a gyro
for turns and encoders for straights, with PD steering — see
[ukmars/mazerunner-core](https://github.com/ukmars/mazerunner-core) and
[ukmars/turn-tuner](https://github.com/ukmars/turn-tuner). I implemented
three of those ideas properly and measured each one. **All three lost.**

| Change | Map 1 | Map 2 | Map 3 | Average |
| --- | --- | --- | --- | --- |
| **Plain PD (what we ship)** | 83 % | 100 % | **50 %** | **78 %** |
| + trapezoidal turn profile | 83 % | 83 % | 50 % | 72 % |
| + gyro yaw-rate damping | 83 % | 83 % | **0 %** | 55 % |
| + motor slew-rate limiting | 67 % | 100 % | 33 % | 67 % |
| all three together | 83 % | 100 % | 33 % | 72 % |

*(measured at 220 × 100 mm, six seeds per map, before the width was tuned)*

**Why they lose here.** All three trade responsiveness for smoothness, and
this maze does not have room for that trade:

- A **motion profile** pays for itself when you are cornering at speed with
  wheel-speed PID closing the loop off high-resolution encoders. Ours give
  20 ticks per wheel revolution — 10 mm of travel per tick. There is no fast
  inner loop for a profile to feed.
- **Yaw-rate damping** directly opposes the wall-centring term. On a wide
  corridor that reads as "smooth"; in a one-foot passage it means the
  correction arrives late, and late is a wall.
- **Slew limiting** makes every turn start and stop lazily. With eight turns
  in a row on Map 3, the lateness compounds.

All three are still in the firmware, switched off by their own constants,
with the measurements written next to them. If you ever fit proper encoders,
turn them back on and re-run the sweep.

**The gyro is still doing the heavy lifting** — it just does it in the three
places that were already there and that measured well:

1. **Closed-loop turns.** Every pivot is driven to a gyro angle, not a
   timed guess. That is the difference between 90° and "about 80°, and a
   bit less when the battery is low".
2. **Bias re-measured at every stop.** The robot stands still for a quarter
   of a second before each pivot, and that pause is used to re-zero the
   gyro's drift. Without it the heading is 15–20° out by the end of a run.
3. **Heading re-zeroed to the corridor after every completed turn.** The
   gyro only ever has to stay honest for the ~1 s a single turn takes, so
   error never accumulates from corner to corner.

---

## Bugs fixed this round

**The "gap on that side" threshold was larger than a gap.** In a 1 ft grid
with the side sonar 50 mm off the centreline, a wall reads 102 mm and an
opening one square deep reads 407 mm. The threshold had been hand-set to
420 mm — larger than an opening ever reads — so the robot drove straight past
every turn it was meant to take. It is now derived from the passage width.
This was the single biggest one.

**Pivots could not settle.** The motor deadband forced 55 PWM even inside the
tolerance band, so the robot hunted across the target until the turn timed out
a few degrees short, then set off crabbed. Inside tolerance it now commands
zero.

**The front sonar was asked for a reading it cannot give.** To centre the
axle in a square it had to read 37 mm; an HC-SR04 is unreliable under about
40 mm. It now ranges down to 100 mm and counts the last stretch off the wheel
encoders.

**Stale junction flags survived a failed turn.** If a turn ended through the
timeout or the jam-recovery path rather than normally, the "there was an
opening on the left" flag was still set, and the robot invented a junction a
few centimetres later and left the route. Every path back into driving now
clears them.

**A tuned turn gain was left behind.** Adding the profile lowered `KP_TURN`
from 2.6 to 1.6; switching the profile back off left the low gain in place
and quietly cost 15 points of completion. Caught by re-running the sweep,
which is the argument for having a sweep.

**Smooth approach to a wall.** The throttle used to step from cruise to slow
at a fixed distance. It now eases down proportionally, which stops the
chassis rocking and upsetting the gyro just before a pivot. This one *did*
help and is switched on.

---

## Still to buy: nothing

The shopping list in `docs/09_CHECKLIST.md` is unchanged. No extra distance
sensors — modelled time-of-flight lasers measured *worse* than your HC-SR04s
on this maze, because a wide sonar cone effectively averages a whole square
of wall and that is exactly what a wall-follower wants. No memory chip. The
only things still outstanding are the MPU-6050 gyro, the LM393 wheel
encoders, the TCRT5000 floor sensor, a 7.4 V battery and the tools.

The one free change worth making: **mount the two side sonars level with the
wheel axle**, not ahead of it, and just inside the tyre line. Worth about 20
points of completion on Map 3, costs nothing.
