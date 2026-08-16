# The rulebook, condensed to what changes a decision

Source: *Robotics Navigation Challenge*, sections 1–11. Read the original
too; this is only the parts that affect what we build.

## What we may and may not do

| § | Rule | What it means for us |
| --- | --- | --- |
| 2.1 | Must use the official kit | Chassis, motors, Uno, L298N all stay |
| 2.2 | May not remove, replace, disable or bypass any original part — **except the breadboard** | The rulebook is telling us to solder. We will |
| 2.2 | May not alter the DC motors | No re-gearing, no swapping for better motors |
| 2.2 | **No additional microcontrollers** (ESP32, Raspberry Pi…) | One Uno. Not even an unused module on the board |
| 2.2 | Exactly one Arduino Uno R3 | ✔ |
| 2.2 | Each battery ≤ 12 V, total ≤ 20 V | 7.4 V (2×18650) or 9 V (6×AA) is fine |
| 2.2 | **Multiple sensors allowed** — "example. Use of 3 Ultra-sonic sensors" | 3 sonars, a gyro and 2 wheel encoders are all legal |
| 2.2 | Additional motors allowed (servo, stepper) | We do not need any |
| 2.3 | Add-ons must not replace originals, must be safe and securely mounted, within size/weight limits | Bolt everything down |
| 2.4 / 11 | Technical inspection before competing | Checklist in `docs/03_WIRING.md` |
| 3.1 | Fully autonomous once started. No remote control, no manual adjustment | Our start is a hand gesture at the nose. No radio on board at all |
| 3.4 | Judges may stop a stuck robot. **Students may not touch it during a run** | A stuck robot is a lost run — hence the jam-recovery watchdog |
| 5.1 | No exposed wiring, sharp edges, loose components, overheating parts | Heat-shrink everything, file cut screws |
| 5.2 | Must not damage the maze | Drive at a speed that does not ram walls |
| 10 | Disqualification for unauthorised parts, manual control, exceeding limits | Nothing that looks like a radio |

## The maze

| § | Spec | Note |
| --- | --- | --- |
| 4.1 | 2 m × 2 m to 4 m × 4 m | Our maps are ~2.5–3 m |
| 4.1 | Wall height 100–150 mm | Practice track walls: 120 mm |
| 4.1 | **Passage width 200–400 mm** | **The one number that could sink us.** See `docs/02_HARDWARE.md` §0 |
| 4.1 | "tentative, to be finalised with vendor" | So it is fair to ask, and they must answer |
| 4.2 | Marked start and finish zones, plus sector points | The striped gates in the photos |
| 4.3 | Smooth non-slip floor, indoor light, no reflective surfaces, no external markers | Good for ultrasound. Practice on a similar surface |

## How you win

| § | Rule | Consequence |
| --- | --- | --- |
| 6.1 | **One point per sector line, awarded only when all three wheels completely cross it. No partial points** | The castor counts. Do not stop with one wheel on the line |
| 6.1 | Winner = most sector points across all three maps | **Finishing is not required to score** |
| 6.1 / 6.3 / 9.1 | Ties broken by total/average time | Speed is a tie-breaker, nothing more |
| 3.3 | 2–3 attempts, **only if the robot did not complete the map**. Best performance recorded | Completing slowly beats failing quickly |
| 6.2 | Penalties for touching the robot, damaging the maze, unsafe operation, kit violations | |
| 7.3 | Appeals within 10 minutes | |

### The strategic consequence

Because points come from lines crossed and not from finishing, **the robot
that never gets permanently stuck wins.** Given a choice between a
configuration that is fast but jams once in five runs, and one that is slow
and never jams, take the slow one. Every tuning decision in this repository
follows from that.

## Team (§8.1)

2–3 students, one team leader, one programmer (may be the same person).
Register team name and member list.
