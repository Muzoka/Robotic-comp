# Hardware — what we have, what to buy, what to check first

## 0. Read this before you spend a riyal

Run this:

```bash
python3 tools/geometry_check.py
```

It prints one number that matters more than anything else in this document:

> turning on the spot sweeps a circle **269 mm** across

A two-wheel robot pivots about the middle of its wheel axle, and the corners
of the body sweep a circle. If that circle is wider than the passage, the
robot **cannot turn around**. Not "turns badly" — cannot turn, at all, no
matter how good the code is.

The rulebook (§4.1) says passages are **200–400 mm**. Our robot needs 269 mm.
So:

| Passage | Verdict |
| --- | --- |
| 200 mm | Impossible. Robot physically cannot turn. |
| 250 mm | Impossible. |
| 300 mm | Tight — 16 mm each side. Works, scrapes sometimes. |
| 350 mm | Fine. |
| 400 mm | Comfortable. |

**Action item #1, before anything else: ask the organisers for the actual
passage width.** The rulebook itself says the dimensions are "tentative, to
be finalised with vendor", so this is a fair question and they will have to
answer it. If the answer is 200–250 mm, no standard 2WD kit robot can
compete and every team has the same problem — worth raising early and in
writing.

Three things you can do to shrink that circle, all free:

1. **Centre the wheel axle.** Mount the motors so the axle is halfway along
   the body. An axle mounted 2/3 of the way back makes the circle bigger for
   no benefit. This is just which mounting holes you use.
2. **Keep everything inside the wheel line.** No sensor, bracket, wire loom
   or battery may stick out past the tyres or past the nose. The ultrasonic
   bracket in particular wants to hang off the front — do not let it.
3. **Mount the battery on top, not behind.** Anything behind the axle adds
   to the tail, and the tail is what sweeps.

---

## 1. What you already have

From the invoice (Electronic Waves Est., Khobar, 06/07/2026, 270.25 SAR) and
the photos:

| # | Item | Qty | Role |
| --- | --- | --- | --- |
| 1 | Arduino Uno R3 (CH340, DIP) | 1 | The one and only brain. Rule §2.2 allows exactly one. |
| 2 | L298N motor driver module | 1 | Drives both wheels. |
| 3 | 2WD car chassis + 2× TT gear motors + 2 wheels + 1 castor | 1 | The body. Cannot be changed (§2.2). |
| 4 | HC-SR04 ultrasonic | 3 | Front, left, right. §2.2 explicitly allows 3. |
| 5 | Breadboard EIC-101 | 1 | The only part you are allowed to remove (§2.2). |
| 6 | Perfboard / stripboard, 2 sizes | 2 | **Use these instead of the breadboard.** |
| 7 | Jumper wires 20 cm | 3 packs | Wiring. |
| 8 | AA battery holder + cells | 1 | Power — needs upgrading, see §3. |
| 9 | Clear acrylic dual-ultrasonic bracket | 1 | Sensor mount. |

### Use the green perfboard, not the white breadboard

You were right that it is lighter, but that is the small reason. The real
reasons:

- A breadboard's spring contacts shake loose. Your robot is a vibrating
  gearbox bolted to a plastic plate; a run ends the moment one 5 V jumper
  lifts 0.3 mm.
- Rule §5.1 prohibits "loose components" and §11 checks "secure mounting".
  A breadboard full of jumper wires is exactly what an inspector looks for.
- §2.2 names the breadboard as the *only* part you may remove. That is the
  rulebook telling you it expects you to solder.

So: solder a small power-distribution and sensor-breakout board on the green
perfboard. One 5 V rail, one GND rail, three 4-pin headers for the
ultrasonics, one 4-pin header for the MPU-6050, two 3-pin headers for the
encoders. Everything else plugs into that.

---

## 2. What to buy — electronics shop (محل إلكترونيات / الموجات الإلكترونية)

**None of this is available at SACO.** Go back to Electronic Waves on King
Fahd Street, or any similar shop.

| Item | Arabic | Qty | ~SAR | Why |
| --- | --- | --- | --- | --- |
| **MPU-6050 (GY-521) gyro module** | حساس جيروسكوب MPU-6050 | 2 | 15–25 ea | **The single most valuable thing you can add.** See §5. Buy two — they are cheap and one dead module on competition day ends your event. |
| **LM393 slot / speed encoder module** | حساس سرعة العجلة LM393 | 2–4 | 8–12 ea | Measures how far each wheel actually turned. The black slotted discs are already in your kit. |
| ~~TCRT5000 IR line sensor~~ | ~~حساس خط~~ | **0** | — | **Do not buy.** Removed from the design — see §6 for the measurement that killed it. |
| **6×AA battery holder** *or* 2× 18650 cells + holder + charger | بيت بطاريات ٦ حبات | 1 | 15 / 60 | 4×AA is not enough — see §3. |
| **Rocker or toggle switch, 3 A** | مفتاح تشغيل | 2 | 5 | Master power switch. Required for a sane inspection. |
| **Male + female pin header strips** | هيدر ذكر وأنثى | few | 10 | So sensors plug in instead of being soldered permanently. |
| **22 AWG stranded hookup wire**, red/black/other | سلك ٢٢ | 3 colours | 15 | Real wiring, not jumper leads. |
| **1000 µF 16 V electrolytic capacitor** | مكثف ١٠٠٠ مايكرو | 2 | 3 ea | Across the motor supply. Stops motor surges resetting the Arduino. |
| **100 nF ceramic capacitors** | مكثف ١٠٠ نانو | 10 | 1 ea | One across each motor terminal — kills the brush noise that upsets the gyro and the sonar. |
| **Heat-shrink tubing assortment** | حرارية | 1 | 15 | §5.1 forbids exposed wiring. |
| **Spare HC-SR04** | حساس مسافة | 1–2 | 20 ea | They die. Have spares. |
| **Spare TT motor + wheel** | موتور + عجلة | 1 | 20 | Check first — §2.2 says you may not *replace* kit parts, so keep the spare identical and only use it if one fails before inspection. Ask a judge first. |

Rough total: **250–350 SAR**.

### Do NOT buy

- **ESP32, Raspberry Pi, Arduino Nano, or any second microcontroller.** §2.2:
  instant disqualification.
- **An external EEPROM / SD card / memory module.** You do not need one — see
  §7. Save the money.
- **A servo to sweep one ultrasonic.** Allowed by the rules, but with three
  fixed sensors it only adds lag and a failure point.
- **A magnetometer / digital compass (HMC5883L, QMC5883).** It will read the
  motor magnets and the steel in the floor and lie to you. The gyro is the
  right sensor.

---

## 3. Power — this is where robots quietly lose

Your kit ships with 4×AA = 6 V nominal, which sags to ~5 V under load. The
L298N is an old bipolar driver and drops about **2 V** internally. That
leaves roughly **3 V at the motors** — they will be slow, weak, and will
stall on carpet. Worse, the voltage dip when both motors start can brown out
the Arduino and reset it mid-run.

Fix, in order of preference:

1. **2× 18650 Li-ion in series (7.4 V) + holder + charger** — best. Light,
   rechargeable, holds voltage under load. ~60 SAR all in.
2. **6×AA alkaline (9 V)** — simplest. Works well. Buy plenty of spares.
3. 4×AA — only if you have no choice, and expect trouble.

Rule check: §2.2 says each supply ≤ 12 V and total ≤ 20 V. 7.4 V or 9 V is
comfortably legal.

**Wiring the power (important):**

```
Battery + ──┬── L298N  +12V terminal
            └── Arduino VIN pin  (or the barrel jack)

Battery − ──┬── L298N  GND
            ├── Arduino GND          <-- one common ground, always
            └── sensor GND rail

Arduino 5V ──── sensor 5V rail (HC-SR04 ×3, MPU-6050, encoders)
```

- Leave the L298N **5V-EN jumper fitted** (it powers the driver's own logic).
- Do **not** wire the L298N's 5 V output to the Arduino 5 V pin.
- Put a **1000 µF capacitor** across the battery at the L298N terminals, and
  a **100 nF** across each motor's two terminals, soldered at the motor.
- **Remove the ENA and ENB jumpers** on the L298N. If you leave them on, the
  speed pins do nothing and the robot only knows full speed.
- Put the master switch in the **battery +** line, before everything.

---

## 4. Answer: should we add a direction sensor?

**Yes. It is the highest-value addition you can make, and it is legal** —
§2.2 explicitly permits "use of multiple sensors", and an MPU-6050 is a
sensor, not a microcontroller.

What it buys you, concretely:

- **Turns that are actually 90°.** Without it you turn by guessing "run the
  motors in opposite directions for 400 ms". That is wrong by 5–15° every
  time, because it depends on battery voltage, floor friction and which
  motor is stronger today. Those errors add up: four corners and the robot
  is 40° crooked and wedges itself.
- **Straight lines.** Your two TT motors are not matched — in simulation the
  right one is typically 6 % weaker. Without a heading reference the robot
  curves into a wall in a long corridor. With one, the code corrects it
  continuously.
- **Turning in a doorway.** Where there are no side walls to reference, the
  gyro is the only thing that knows which way the robot is pointing.

What it does *not* do: an MPU-6050 drifts, roughly 0.1–0.5 °/s of bias. Over
a 4-minute run that is 25–120° of error if you just integrate it. The
firmware handles that in two ways (both in `nav_core.cpp`, both tested in the
simulator):

1. **Re-measures the zero-rate bias every time the robot stops** — which it
   does for a quarter of a second before every single turn.
2. **Re-zeros the heading to the corridor after every completed turn**, so
   error never accumulates from one corner to the next. The gyro only has to
   stay honest for the ~1.5 s that one turn takes.

In simulation, removing the gyro roughly doubles the number of wall scrapes
and loses about a third of the sector points. Buy the gyro.

**Also buy the wheel encoders** (LM393 slot sensors). They are 10 SAR and
they tell the code how far it has actually travelled, which is what puts the
wheel axle in the middle of a junction before it pivots. The slotted discs
are already in your kit box.

---

## 5. Answer: can the code work as memory, without a memory module?

**Yes — and you do not need a memory module at all, because the Arduino Uno
already has one built in.**

The ATmega328P on your Uno contains:

- **2048 bytes of SRAM** — working memory while running.
- **1024 bytes of EEPROM** — non-volatile, survives power-off, and is used
  through `#include <EEPROM.h>`, already installed with the Arduino IDE.

Our map memory uses **4 bytes per junction** (position + which exits have
been used, 2 bits each for 4 directions). With `MAX_JUNCTIONS = 48` that is
**192 bytes** — under 10 % of SRAM, and it fits in EEPROM five times over.
A maze of the size in §4.1 has maybe 10–20 junctions.

So the honest answer to your question: the direction sensor is useful
*regardless*, and the memory question is a non-issue — you already own the
memory. Nothing to buy, nothing to add, no rule to worry about.

`firmware/MazeRunner/MazeRunner.ino` writes the junction map into EEPROM when
a run ends, so if a judge stops the robot and you get another attempt, run 2
can start knowing what run 1 learned. That is optional — one line to
uncomment — and off by default, because for a fresh map you want a clean
slate.

---

## 6. The line sensor — removed, and why that was the right call

An earlier version of this document recommended a TCRT5000 under the nose.
**Do not fit one.** The reasoning changed after it was measured, and the
change is worth reading because it is a good example of a part that looks
free and is not.

What it was supposed to buy:

- a live score count — nice to have, steers nothing;
- an odometry fix at each known line — real, but the corridor-parallel
  correction and the loop closure at junctions already cover this;
- **gate detection**: the start and finish are painted with black-and-white
  stripes, so four black/white edges inside 350 ms meant "I am out".

That last one is where it went wrong. A TCRT5000 is a comparator with a
trim pot. Crossing a strip of tape at an angle, its output **chatters**
around the threshold — four edges is easy to produce by accident, in the
middle of the maze, over an ordinary sector line. The robot would then stop
and declare itself finished with half the road undriven.

So the only thing it did for navigation was give the run a way to end early,
and it was the single sensor on the robot capable of ending a run by itself.

Measured with it removed: **24 runs, 24 complete, times identical to a tenth
of a second, every sector line still crossed.** The finish is detected by
driving into open space on all three sonars — which is what fired on every
run in this project even when the stripe detector was fitted.

Removed: ~8 g, one solder job, one calibration against a floor colour you
have not seen, one shopping item, and one way to lose a map. D12 is now
free. The code survives behind `HAS_LINE_SENSOR` in `config.h`.

---

## 7. What to buy at SACO (ساكو) — tools and materials

SACO has no electronics worth using for this. Go there for tools, fasteners
and the practice maze.

### Fasteners — المسامير (~60 SAR)

| Item | Arabic | Qty |
| --- | --- | --- |
| M3 machine screws, assorted 6/8/10/12/20 mm | مسامير M3 | 1 box |
| M3 nuts + M3 nylon lock nuts | صواميل M3 | 1 box each |
| M3 washers | ورد M3 | 1 box |
| M3 nylon standoffs / spacers, 10–25 mm, M/F | فواصل نايلون M3 | 1 set |
| M2 small screws (for sensor modules) | مسامير M2 | 1 box |
| Zip ties, 100 mm and 200 mm | ربطات بلاستيك | 2 bags |
| Self-adhesive zip-tie mounts | قواعد لاصقة للربطات | 1 bag |

### Tools — العدة والمفكات (~250 SAR)

| Item | Arabic | Why |
| --- | --- | --- |
| Precision screwdriver set (PH0/PH1, flat) | طقم مفكات دقيقة | The kit's screws are small |
| PH1 + PH2 screwdriver | مفك صليبة | Everything else |
| Needle-nose pliers | زرادية دقيقة | Holding nuts in tight spots |
| Side cutters / flush cutters | قصافة أسلاك | Trimming wires and zip ties |
| Wire strippers | مقشر أسلاك | Do not strip with your teeth |
| **Soldering iron 40–60 W + stand** | كاوي لحام | Needed for the perfboard |
| **Solder wire + flux** | قصدير + معجون لحام | |
| Desoldering braid or pump | شفاط لحام | For when you get it wrong |
| **Digital multimeter** | افوميتر | Non-negotiable. Checking 5 V and continuity is how you avoid burning the Arduino |
| Digital caliper (optional, ~60 SAR) | قدمة ذات ورنية | For measuring the robot accurately for `config.h` |
| Steel ruler + tape measure | مسطرة + متر | Measuring the robot and the maze |
| Small file set | مبارد | Cleaning up holes |
| Craft knife | كتر | |
| Hot glue gun + sticks | شمع لاصق | Strain relief on wires — **not** for structural mounting, inspectors dislike it |
| Double-sided foam tape (3M VHB if available) | لاصق وجهين | Mounting the gyro flat and rigid |
| Electrical tape | شريط عازل | |
| Thread-lock (blue) | مثبت مسامير | Vibration loosens every screw on this robot |
| Safety glasses | نظارة أمان | §5.1 |
| Small parts organiser box | علبة تنظيم قطع | You will lose the M3 nuts otherwise |

### Practice maze materials — buy these, they matter most (~150 SAR)

You cannot tune a maze robot without a maze. Build a 2 m × 2 m practice
track:

| Item | Arabic | Qty |
| --- | --- | --- |
| Foam board / PVC board sheets, 5 mm, ~50 × 70 cm | فوم بورد | 10–14 sheets |
| Wide black electrical or gaffer tape | شريط لاصق أسود عريض | 3 rolls |
| Wide white paper roll or white poster board | ورق أبيض / كرتون أبيض | for the floor |
| Masking tape | شريط لاصق ورقي | 2 rolls |
| Right-angle brackets or hot glue | زوايا تثبيت | to stand the walls up |
| Black marker, thick | قلم أسود عريض | drawing the sector lines |

Cut the sheets to **wall height 120 mm** (rulebook says 100–150 mm) and stand
them up to make corridors. Make the corridors the width the organisers
confirm. Draw sector lines across the corridor with the black tape. Paint or
tape a striped gate at each end.

**Do not skip this.** Every hour on a real practice track is worth ten hours
of guessing.

---

## 8. Summary shopping list

| Where | What | Budget |
| --- | --- | --- |
| Electronics shop | 2× MPU-6050, 2–4× LM393 encoders, 2× push buttons, 5× 330 Ω, battery + holder, switches, headers, wire, caps, heat-shrink, spare HC-SR04 | 240–330 SAR |
| SACO — fasteners | M3/M2 screws, nuts, washers, standoffs, zip ties | ~60 SAR |
| SACO — tools | screwdrivers, pliers, cutters, strippers, **soldering iron + solder**, **multimeter**, glue gun, tapes | ~250 SAR |
| SACO — practice maze | foam board, black tape, white board, masking tape | ~150 SAR |
| **Total** | | **~700–800 SAR** |

If the budget is tight, the three things you must not cut are: **the
MPU-6050, the multimeter, and the practice maze materials.**
