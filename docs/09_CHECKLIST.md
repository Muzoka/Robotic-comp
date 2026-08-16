# Every item, with alternatives

Tick as you go. **Have** = already yours (invoice or photos). **Buy** = not
yet. **Alt** = what to get instead if the shop does not have it.

---

## A. The kit — must be on the robot, cannot be replaced (§2.2)

| ✓ | Item | Have | Note |
| --- | --- | --- | --- |
| ☐ | Arduino Uno R3 (CH340 DIP) | ✔ | The only microcontroller allowed |
| ☐ | L298N motor driver module | ✔ | Remove the ENA/ENB jumpers |
| ☐ | 2WD chassis plate | ✔ | Cannot be cut or replaced |
| ☐ | 2 × TT gear motor + bracket + screws | ✔ | Cannot be modified |
| ☐ | 2 × yellow wheel + tyre | ✔ | |
| ☐ | 1 × castor wheel (front, free-turning) | ✔ | Counts as the third wheel for scoring |
| ☐ | 2 × slotted encoder disc (black) | ✔ | In the kit bag; they pair with the LM393 sensors |
| ☐ | Breadboard EIC-101 | ✔ | The one part §2.2 lets you leave off. Bring it in the box anyway |
| ☐ | Jumper wires | ✔ | Fine for the bench, not for the run |
| ☐ | Battery holder | ✔ | Being upgraded — section C |

## B. Sensors — all legal add-ons (§2.2 "use of multiple sensors")

| ✓ | Item | Have | Buy | Alternative if unavailable |
| --- | --- | --- | --- | --- |
| ☐ | HC-SR04 ultrasonic × 3 | ✔ 3 | +1 spare | **HC-SR04P** or **RCWL-1601** — same pinout, work on 3–5 V. **US-100** also fits but must be in pin mode, not serial |
| ☐ | MPU-6050 / GY-521 gyro | | **2** | **MPU-9250 / MPU-6500 / GY-521 clone** — all speak the same I2C registers. **Avoid** BNO055 (expensive, different protocol) and any compass-only module (HMC5883L/QMC5883 — the motors will fool it) |
| ☐ | LM393 slot speed sensor × 2 | | **2–4** | Sold as "encoder module", "speed sensor", "H206", "photo-interrupter". Any 3-pin (VCC/GND/DO) slot type works |
| ☐ | TCRT5000 line sensor × 2 | | **2** | Any 3-pin IR reflectance module with a trimmer: "line follower sensor", "IR obstacle sensor". A 4-channel line array also works — use one channel |
| ☐ | Acrylic ultrasonic bracket | ✔ 1 | +2 | Or make them from the M3 standoffs and a scrap of the green board |

## C. Power

| ✓ | Item | Buy | Alternative |
| --- | --- | --- | --- |
| ☐ | 2 × 18650 Li-ion cell (protected, 2600 mAh+) | ✔ | **6 × AA alkaline** in a 6-cell holder = 9 V. Simplest, works, but you will get through a lot of batteries |
| ☐ | 2-cell 18650 holder, series, with leads | ✔ | |
| ☐ | 18650 charger (2-bay) | ✔ | |
| ☐ | **or** a 7.4 V 2S LiPo 1500 mAh + balance charger | | Lighter and stronger again, but needs care and a fireproof bag. Only if someone on the team already knows LiPos |
| ☐ | Rocker or toggle switch, ≥ 3 A × 2 | ✔ | Any switch rated 3 A. SACO sells these in the electrical aisle |
| ☐ | Inline fuse holder + 3 A fuse | ✔ | Cheap insurance against a shorted motor lead |
| ☐ | 1000 µF 16 V electrolytic × 2 | ✔ | 470 µF works. 25 V rating is also fine |
| ☐ | 100 nF ceramic × 10 | ✔ | Marked "104" |

**Why not 4 × AA:** the L298N drops about 2 V internally. From 6 V (sagging
to ~5 V under load) the motors see barely 3 V — slow, weak, and the dip when
both motors start can reset the Arduino mid-run. 7.4 V puts ~5.4 V at the
motors, which is what they are rated for. Rule check: §2.2 allows 12 V per
supply and 20 V total, so 7.4 V or 9 V is comfortably legal.

## D. Wiring and cable management — your question

You do not need much, but these four things turn a bird's nest into
something that passes inspection (§5.1, §11 C):

| ✓ | Item | Arabic | Why |
| --- | --- | --- | --- |
| ☐ | **JST-XH 2.54 mm connector kit** + crimp tool | وصلات JST + كماشة تكريب | Make your own cables to exact length. Sensors unplug for repair. This is the single biggest tidiness win |
| ☐ | **Dupont connector kit** (if no JST) | وصلات ديبونت | Same idea, cheaper, slightly less secure |
| ☐ | **Spiral cable wrap, 6 mm** | لفافة أسلاك حلزونية | Bundles several wires into one tidy sleeve. Sold by the metre |
| ☐ | **Heat-shrink assortment** | أنابيب حرارية | Every solder joint. §5.1 forbids exposed conductor |
| ☐ | **Small zip ties (100 mm) + adhesive tie mounts** | ربطات + قواعد لاصقة | Anchor the loom to the chassis |
| ☐ | **22 AWG stranded wire**, red / black / 3 colours | سلك ٢٢ مجدول | Stranded, not solid — solid wire work-hardens and snaps from vibration |
| ☐ | Cable/spiral wrap or braided sleeve 4 mm | | For the motor leads specifically |

**How to actually keep them short**, which matters more than what you buy:

1. Mount the sensor board (green perfboard) in the **middle** of the chassis,
   not at one end. Every wire then runs at most half the robot's length.
2. Cut each wire **after** the parts are bolted down, not before. Route it,
   mark it, then cut and crimp.
3. **Twist the two motor wires together** along their whole length. A twisted
   pair cancels most of the magnetic noise that upsets the gyro and the
   ultrasonics. Free, and it works.
4. Run power wires down one side of the chassis and signal wires down the
   other. Where they must cross, cross at 90°.
5. Leave a **small service loop** at each sensor — about 30 mm — so you can
   unplug and re-seat without straining the joint.

## E. Tools (SACO)

| ✓ | Item | Arabic | Alternative |
| --- | --- | --- | --- |
| ☐ | Soldering iron 40–60 W + stand | كاوي لحام | A cheap 30 W pencil iron works but is slow. Temperature-controlled is much nicer |
| ☐ | Solder (60/40 or lead-free) + flux | قصدير + معجون | |
| ☐ | Desoldering braid or pump | شفاط لحام | |
| ☐ | **Digital multimeter** | افوميتر | Anything with continuity beep and DC volts. Do not skip |
| ☐ | Precision screwdriver set | طقم مفكات دقيقة | |
| ☐ | PH1 + PH2 screwdrivers | مفك صليبة | |
| ☐ | Needle-nose pliers | زرادية دقيقة | |
| ☐ | Side / flush cutters | قصافة | |
| ☐ | Wire strippers | مقشر أسلاك | Cutters + care will do at a pinch |
| ☐ | Hot glue gun + sticks | مسدس شمع | Strain relief only, never structural |
| ☐ | Craft knife, small files | كتر، مبارد | |
| ☐ | Safety glasses | نظارة أمان | |
| ☐ | Parts organiser box | علبة تنظيم | You will lose the M3 nuts otherwise |
| ☐ | Digital caliper *(optional)* | قدمة | For measuring the robot accurately |

## F. Fasteners (SACO)

| ✓ | Item | Arabic |
| --- | --- | --- |
| ☐ | M3 screws, 6 / 8 / 10 / 12 / 20 mm | مسامير M3 |
| ☐ | M3 nuts + M3 nylon lock nuts | صواميل M3 + صواميل نايلون |
| ☐ | M3 washers | ورد M3 |
| ☐ | M3 nylon standoffs 10–25 mm, M/F | فواصل نايلون M3 |
| ☐ | M2 screws + nuts (sensor modules) | مسامير M2 |
| ☐ | Blue thread-lock | مثبت مسامير |
| ☐ | Double-sided foam tape (3M VHB if available) | لاصق وجهين |
| ☐ | Electrical tape | شريط عازل |

## G. Practice track (SACO) — do not skip this

| ✓ | Item | Arabic | Qty |
| --- | --- | --- | --- |
| ☐ | Foam board 5 mm, ~50 × 70 cm | فوم بورد | 14 sheets |
| ☐ | White poster board or a white paper roll | كرتون أبيض | for the floor |
| ☐ | Black gaffer / electrical tape, 30 mm wide | شريط لاصق أسود عريض | 3 rolls |
| ☐ | Masking tape | شريط ورقي | 2 rolls |
| ☐ | Right-angle brackets or hot glue | زوايا تثبيت | |
| ☐ | Tape measure + long steel ruler | متر + مسطرة | |

Cut the walls **12 cm tall**, stand them at **30 cm apart**, and lay black
tape **30 cm long straight across the passage** for the sector lines — the
same as the real maps.

## H. Competition-day bag

| ✓ | Item |
| --- | --- |
| ☐ | Robot, assembled and tested |
| ☐ | Laptop + USB-B cable + charger |
| ☐ | 3 sets of charged batteries + charger |
| ☐ | Spare: MPU-6050, HC-SR04, LM393, TCRT5000, jumper leads |
| ☐ | Soldering iron, solder, cutters, screwdrivers, multimeter |
| ☐ | M3 screws, nuts, standoffs, zip ties |
| ☐ | Black tape + marker |
| ☐ | Tape measure (to check the maze against your maps) |
| ☐ | The kit box with every original part, including the breadboard |
| ☐ | `docs/07_COMPETITION_DAY.md` printed |
| ☐ | `docs/03_WIRING.md` printed |
