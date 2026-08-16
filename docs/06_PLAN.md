# The plan

Ordered so that the things which could kill the project happen first, and
nothing gets built before the thing it depends on is known.

---

## Phase 0 — before you spend money (today, 1 hour)

| # | Task | Why it is first |
| --- | --- | --- |
| 0.1 | **Email the organisers.** See the questions below. | One answer can invalidate the whole build |
| 0.2 | Measure your robot with a tape measure: length, width, wheelbase, wheel diameter, nose-to-axle | Everything else uses these numbers |
| 0.3 | Put them in `firmware/MazeRunner/config.h` and run `python3 tools/geometry_check.py` | Tells you whether the robot fits |
| 0.4 | Run `cd sim && python3 run.py --all --compare` and watch the GIFs | See it work before you buy |

### The email — send it today

> 1. What is the final **passage width**? §4.1 says 200–400 mm, "tentative,
>    to be finalised with vendor". A standard 2WD kit robot sweeps a ~270 mm
>    circle when it turns on the spot and physically cannot turn in a 200 mm
>    passage.
> 2. Is the **Finish Zone always on the outer edge** of the maze, or can it
>    be an enclosed chamber in the middle?
> 3. Is there a **time limit** per run, and what is the **maximum robot size**?
> 4. Are **sector lines** always straight across the passage, and what colour
>    and width are they?
> 5. Are teams allowed to **look at the map before their run**?
> 6. Can we bring **identical spare parts** (a spare motor, a spare
>    ultrasonic) to swap in if one fails before inspection?

Questions 1 and 2 change what you build. Question 5 changes your strategy.

---

## Phase 1 — buy and build (2 days)

| # | Task | Output |
| --- | --- | --- |
| 1.1 | Shopping trip — electronics shop then SACO (`docs/02_HARDWARE.md` §8) | Parts on the bench |
| 1.2 | Build the **practice track** first, before touching the robot | 2 m × 2 m, foam board walls 120 mm tall, corridors at the confirmed width, black tape sector lines, striped gates |
| 1.3 | Assemble the chassis with the **wheel axle centred** | Smallest possible turning circle |
| 1.4 | Solder the perfboard: 5 V rail, GND rail, headers for 3 sonars, gyro, 2 encoders, line sensor | No breadboard on the robot |
| 1.5 | Wire per `docs/03_WIRING.md`. Check every rail with the multimeter **before** plugging in the Arduino | No smoke |
| 1.6 | Mount sensors. Measure where they actually ended up; update `config.h` | Code and metal agree |

Build the practice track first because it is the thing you will be tempted to
skip, and it is the thing that decides the result.

---

## Phase 2 — bring it to life (1 day)

Do these in order. Each one is a separate `.ino` you throw away — do not try
to debug three things at once.

| # | Test | Pass condition |
| --- | --- | --- |
| 2.1 | Motors: drive each wheel forward and back | Correct wheel, correct direction. Fix with `MOTOR_L_SIGN` / `MOTOR_R_SIGN`, never by rewiring |
| 2.2 | Encoders: spin each wheel by hand, print counts | 20 counts per revolution, both wheels |
| 2.3 | Sonars: print all three, wave a book at each | Sensible mm, no cross-talk. Check at 50 / 100 / 300 / 1000 mm against a ruler |
| 2.4 | Gyro: print heading, turn the robot 90° by hand against a square | Reads 90 ± 3° |
| 2.5 | Line sensor: pass it over black tape | Clean HIGH/LOW, adjust the trimmer |
| 2.6 | Flash the real `MazeRunner.ino` on blocks so the wheels spin free | Serial telemetry looks sane, state machine advances |

`tools/serial_check.md` has the snippets for each of these.

---

## Phase 3 — tune on the practice track (1 day, the important one)

| # | Task |
| --- | --- |
| 3.1 | One straight corridor, 2 m. Does it drive straight and centred? Tune `KP_WALL`, `KD_WALL` |
| 3.2 | One 90° corner. Does it stop in the right place and come out centred? Tune `FRONT_PIVOT_MM`, `CREEP_AFTER_OPEN_MM` |
| 3.3 | A dead end. Does it turn around without touching a wall? |
| 3.4 | Rebuild the practice track into the shape of each competition map. Run it ten times |
| 3.5 | Every change goes into `config.h`, then gets re-checked in the simulator before it goes on the robot |
| 3.6 | Record the telemetry (`tools/telemetry_log.py`) and compare it against the simulator's CSV for the same shape |

Step 3.6 is what makes the simulator worth having: when the real robot and
the simulated one disagree, the difference tells you which parameter in
`sim/robot.py` is wrong, and after you correct it the simulator predicts the
real robot properly for the rest of the project.

---

## Phase 4 — reliability (half a day)

Speed does not score. Reliability does. §6.1 gives a point per sector line
crossed and only uses time to break ties.

| # | Task |
| --- | --- |
| 4.1 | Run each map shape 10 times without touching the robot. Log points scored |
| 4.2 | Anything that fails twice, fix. Anything that fails once, understand |
| 4.3 | Deliberately start the robot 30 mm off-centre and 10° crooked. It must still work — the judges will not place it perfectly |
| 4.4 | Run with half-flat batteries. The robot behaves differently at 5 V |
| 4.5 | Lower `PWM_CRUISE` until the failure rate hits zero, then leave it there |

Rule §3.3 gives 2–3 attempts **only if the robot did not complete the map**.
A robot that finishes slowly beats a robot that fails fast.

---

## Phase 5 — competition day

See `docs/07_COMPETITION_DAY.md`. Print it and take it with you.

---

## Splitting the work (§8.1 allows 2–3 students)

| Role | Owns |
| --- | --- |
| **Programmer** | `nav_core.cpp`, `config.h`, the simulator, tuning |
| **Builder** | Chassis, soldering, wiring, mounting, inspection checklist |
| **Track & test** | Practice track, running the tests, logging results, the spares box |

One person can do all three, but then the practice track never gets built.

---

## Risks, and what to do about them

| Risk | How likely | What to do |
| --- | --- | --- |
| Passage is 200–250 mm and the robot cannot turn | Medium | Ask now (Phase 0.1). If confirmed, every team has the same problem — raise it with the organisers in writing, early |
| Finish is an enclosed chamber in the middle | Medium | Wall-following cannot solve it; the memory mode gets most of the sector points. Ask in Phase 0.1 |
| Ultrasonic loses a wall it meets at an angle | High | Already handled: two consecutive misses before believing it, median-of-3 filter |
| Motors brown out the Arduino | High with 4×AA | 6×AA or 2×18650, plus the 1000 µF capacitor |
| Gyro drifts and corners go wrong | High if naive | Already handled: bias re-measured at every stop, heading re-zeroed after every turn |
| A part fails on the day | Medium | Spare MPU-6050, spare HC-SR04, spare batteries, a soldering iron in the bag |
| Robot drives back out of the start gate | High for a naive wall follower | Already handled: the start gate is marked "used" at the first junction |
| Loose wire on a breadboard | Very high | Do not put a breadboard on the robot |
