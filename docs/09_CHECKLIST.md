# Shopping list — take this to the shop

Two trips: an electronics shop, then SACO. Roughly **700–800 SAR** all in.

Every row says which option is the **reliable** one and which is the
**lighter/faster** one. Read the strategy note first — it tells you which
column to buy from.

---

## Which column to buy from

Scoring is §6.1 sector points first, §6.3 time only as a tie-breaker. So:

1. **Reliability wins the event.** A robot that finishes all three maps
   beats one that is quick on two and jams on the third.
2. **Weight is the tie-breaker.** Lighter means faster acceleration, less
   momentum into a wall, and longer battery life — all free speed with no
   loss of reliability.

Right now the robot finishes the three maps in **32 s, 36 s and 48 s** of the
180 s allowed, scoring **every sector line on every map** (3/3, 5/5, 9/9),
with zero wall contact across 96 simulated runs. There is a lot of margin.
**Buy from the reliable column; take the light option only where it costs
nothing.** Where the two conflict, buy reliable.

---

## 1. Electronics shop (الموجات الإلكترونية, King Fahd St, Khobar)

| ✓ | Item | Arabic | Qty | SAR | Reliable vs light |
| --- | --- | --- | --- | --- | --- |
| ☐ | **MPU-6050 / GY-521 gyro** | حساس جيروسكوب | **2** | 15–25 ea | Only 3 g — no trade-off. Buy two; a dead gyro on the day ends your event. Substitutes: MPU-9250, MPU-6500, any GY-521 clone. **Not** a compass module (HMC5883L/QMC5883) — the motors fool it |
| ☐ | **LM393 slot encoder** | حساس سرعة العجلة | **2** (+2 spare) | 8–12 ea | 5 g each. No alternative worth having — the slotted discs in your kit only fit these |
| ~~☒~~ | ~~**TCRT5000 line sensor**~~ | ~~حساس خط~~ | **0** | — | **DO NOT BUY — removed from the design.** It steered nothing, and its one job (spotting the finish) had a failure mode that could stop the robot in the middle of a map. Details below |
| ☐ | **Push button, momentary** | زر ضغط | **2** | 2 ea | The GO button, on D12. Two wires: pin to button, button to GND. Any 6 mm tactile switch or panel-mount push button |
| ☐ | **330 Ω resistor** | مقاومة ٣٣٠ أوم | 5 | 1 | Handy to have, but **no longer needed for the GO button** — it moved to D12 and wires straight to GND |
| ☐ | **2 × 18650 Li-ion + 2-cell holder + charger** | بطاريات ١٨٦٥٠ + بيت + شاحن | 1 set | ~60 | **RELIABLE choice, buy this.** 7.4 V, ~95 g, rechargeable, holds voltage under load |
| ☐ | *or* 2S LiPo 850–1500 mAh + balance charger | بطارية ليبو ٢ خلية | 1 | ~90 | **LIGHTER choice, ~55 g.** Saves 40 g and gives a stiffer voltage — genuinely faster. Only if someone on the team has used LiPo before: they need a fireproof bag and never to over-discharge |
| ☐ | *fallback* 6 × AA holder + alkalines | بيت بطاريات ٦ حبات | 1 | ~15 | Works, but ~140 g and it sags. Last resort |
| ☐ | **Rocker/toggle switch, 3 A** | مفتاح تشغيل | 2 | 5 ea | Master power. One is enough, buy a spare |
| ☐ | **Inline fuse holder + 3 A fuse** | حامل فيوز | 1 | 8 | 8 SAR of insurance against a shorted motor lead |
| ☐ | **1000 µF 16 V capacitor** | مكثف ١٠٠٠ مايكرو | 2 | 3 ea | Across the L298N supply. Stops motor surges resetting the Arduino |
| ☐ | **100 nF ceramic ("104")** | مكثف ١٠٤ | 10 | 1 ea | One across each motor's terminals. Kills the brush noise that upsets the gyro |
| ☐ | **JST-XH connector kit + crimp tool** | وصلات JST + كماشة تكريب | 1 | 60 | Cables cut to exact length, sensors unplug for repair. The biggest tidiness win. Dupont kit is the cheaper substitute |
| ☐ | **22 AWG stranded wire**, 3 colours | سلك ٢٢ مجدول | 3 | 15 | **Stranded, not solid.** Solid wire work-hardens and snaps from vibration |
| ☐ | **Heat-shrink assortment** | أنابيب حرارية | 1 | 15 | §5.1 forbids exposed conductor |
| ☐ | **Spiral cable wrap 6 mm** | لفافة أسلاك | 2 m | 10 | Bundles the loom |
| ☐ | **Pin headers, male + female** | هيدر ذكر وأنثى | few | 10 | |
| ☐ | **Spare HC-SR04** | حساس مسافة | 2 | 20 ea | They die. Same part as yours |
| ☐ | *optional* piezo buzzer 5 V | صافرة | 1 | 5 | In parallel with the LED. Makes the countdown audible to a judge |

**Do NOT buy:** any second microcontroller (ESP32, Nano, Pi) — §2.2,
instant disqualification, even fitted and unused. No external memory chip —
the Uno's built-in 1 kB EEPROM is ten times what we need. **No laser
distance sensors** — I modelled VL53L0X/VL53L1X and they measured *worse*
than your HC-SR04s on this maze, because a wide sonar cone averages a whole
square of wall and that is what a wall-follower wants.

### Why the line sensor is off the list

You asked whether removing it would help. It does — and not because it was
useless, but because it was **dangerous**.

Its only navigation job was a shortcut for noticing the run was over: four
black-to-white edges inside 350 ms means "I am crossing the striped finish
gate". A TCRT5000 is a comparator with a trim pot, and when it crosses a
strip of tape at an angle its output chatters around the threshold. Four
edges is easy to produce by accident. The robot would then declare itself
finished **in the middle of the maze** and stop — a whole map lost, to a
sensor that was not steering anything.

Measured with it removed: **24 runs, 24 complete, identical times to a tenth
of a second, every sector line still crossed.** The robot notices the finish
by driving into open space on all three sonars, which is what actually fired
on every run in this project anyway.

So: one less thing to buy, one less thing to solder, one less thing to
calibrate against a floor colour you have not seen yet, ~8 g saved, and D12
is now a free pin. The code is still in the firmware behind a switch if you
ever want it back.

Subtotal: **240–300 SAR**

---

## 2. SACO (ساكو)

### Tools — buy these once

| ✓ | Item | Arabic | SAR |
| --- | --- | --- | --- |
| ☐ | **Soldering iron 40–60 W + stand, solder, flux** | كاوي لحام + قصدير | 90 |
| ☐ | **Digital multimeter** | افوميتر | 60 |
| ☐ | Precision screwdriver set + PH1/PH2 | طقم مفكات دقيقة + مفك صليبة | 50 |
| ☐ | Needle-nose pliers, side cutters, wire strippers | زرادية، قصافة، مقشر أسلاك | 55 |
| ☐ | Desoldering braid | شفاط لحام | 10 |
| ☐ | Hot glue gun + sticks | مسدس شمع | 30 |
| ☐ | Craft knife, small files | كتر، مبارد | 25 |
| ☐ | Safety glasses | نظارة أمان | 15 |
| ☐ | Parts organiser box | علبة تنظيم | 25 |

### Fasteners — the light column matters here

| ✓ | Item | Arabic | Reliable vs light |
| --- | --- | --- | --- |
| ☐ | M3 screws 6/8/10/12/20 mm | مسامير M3 | Steel where it carries load |
| ☐ | **M3 NYLON standoffs 10–25 mm** | فواصل نايلون M3 | **Buy nylon, not brass.** Same job, about a third of the weight, and you need 8–12 of them. Free ~25 g |
| ☐ | **M3 nylon screws + nuts** | مسامير نايلون M3 | For mounting the sensor boards, which carry nothing. Another ~10 g |
| ☐ | M3 steel nuts, nylon lock nuts, washers | صواميل وورد M3 | Steel for the motor brackets only |
| ☐ | M2 screws + nuts | مسامير M2 | Sensor modules |
| ☐ | Blue thread-lock | مثبت مسامير | Vibration loosens everything on this robot |
| ☐ | Zip ties 100 mm + adhesive mounts | ربطات + قواعد لاصقة | |
| ☐ | Double-sided foam tape (3M VHB if stocked) | لاصق وجهين | Mounting the gyro flat and rigid |
| ☐ | Electrical tape | شريط عازل | |

### Practice track — do not skip this

| ✓ | Item | Arabic | Qty |
| --- | --- | --- | --- |
| ☐ | **Foam board 5 mm, ~50 × 70 cm** | فوم بورد | **14 sheets** |
| ☐ | White poster board / paper roll for the floor | كرتون أبيض | 4 |
| ☐ | **Black gaffer or electrical tape, 30 mm wide** | شريط لاصق أسود عريض | 3 rolls |
| ☐ | Masking tape | شريط ورقي | 2 |
| ☐ | Right-angle brackets, or use the hot glue | زوايا تثبيت | 20 |
| ☐ | Tape measure + long steel ruler | متر + مسطرة | 1 |

Cut the walls **19 cm tall** (7.5 in, as the spreadsheet says), stand them
**30.5 cm apart** (1 ft), and lay black tape **30 cm straight across the
passage** for the sector lines.

Subtotal: **~420 SAR**

---

## 3. Free weight savings — worth about 90 g

No money, real speed:

| Change | Saves |
| --- | --- |
| Nylon standoffs and screws instead of brass/steel where nothing structural hangs on them | ~35 g |
| 2S LiPo instead of 2 × 18650 (only if someone knows LiPo) | ~40 g |
| Leave the breadboard off the robot — §2.2 allows it, and it belongs in the box for inspection anyway | ~30 g |
| Cut every wire to length instead of coiling spare jumper leads | ~15 g |
| Green perfboard instead of the white breadboard | ~25 g |

On a ~600 g robot, 90 g is 15 %. It shows up as quicker starts out of every
one of the 8 turns on Map 3.

---

## 4. Speed, for the tie-break

`PWM_CRUISE` in `config.h` is the one number that trades time for safety.
Measured, 15 seeds per map, complete + full road coverage each time:

| `PWM_CRUISE` | Map 1 | Map 2 | Map 3 | Total | Complete | Wall contact, bad hardware |
| --- | --- | --- | --- | --- | --- | --- |
| 110 | 52 s | 58 s | 72 s | 182 s | 100 % | — |
| 140 | 41 s | 46 s | 60 s | 147 s | 100 % | — |
| 170 | 35 s | 40 s | 53 s | 128 s | 100 % | 100 episodes |
| **200 — shipped** | **32 s** | **36 s** | **48 s** | **116 s** | **100 %** | **none** |
| 230 | 29 s | 33 s | 45 s | 108 s | 100 % | none |

Two things changed here since the last version of this list, and both are
worth understanding before you tune anything on the day.

**The speed ceiling moved.** 170 used to be the limit because Map 2 started
failing above it. That was never really about speed — it was the two pivots
in the open crossing, and the route you drew deletes them. With those gone,
every speed on the table completes every run.

**Faster measured *cleaner*, which is not what you would guess.** At 170 the
robot logged 100 wall-contact episodes across 78 deliberately-degraded runs;
at 200 and 230 it logged none. The reason is that a slower run is a *longer*
run, and the gyro drifts with time, not with distance. Getting out of the
maze sooner means less accumulated error to fight.

**200 rather than 230** because steering is added to cruise and then clamped
at 255. At 200 the robot can still swing 135 counts of left-right
difference to save a bad corner; at 230 only 105. That reserve is worth more
than 8 seconds.

If the real track turns out slipperier than the model, drop to 170 — you
lose 12 seconds and every hard correction gets its full authority back.

If the real track turns out slipperier than the model, drop to 140 — you
lose 19 seconds and buy back a lot of margin.

---

## 5. Competition-day bag

| ✓ | Item |
| --- | --- |
| ☐ | Robot, assembled and tested |
| ☐ | Laptop + USB-B cable + charger |
| ☐ | **3 charged battery sets + charger** |
| ☐ | Spares: MPU-6050, HC-SR04 ×2, LM393, push button, 330 Ω resistors, jumper leads |
| ☐ | Soldering iron, solder, cutters, screwdrivers, multimeter |
| ☐ | M3 screws, nuts, nylon standoffs, zip ties |
| ☐ | Black tape + marker + tape measure |
| ☐ | **The kit box with every original part, including the breadboard** |
| ☐ | `docs/07_COMPETITION_DAY.md` and `docs/12_STARTING_THE_ROBOT.md`, printed |
