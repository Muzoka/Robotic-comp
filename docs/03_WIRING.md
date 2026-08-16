# Wiring

Every pin on the Uno is spoken for. Do not improvise — `config.h` and the
firmware assume exactly this.

## Pin map

```
                 ARDUINO UNO R3
  ┌───────────────────────────────────────────────┐
  │ D0  RX   — leave alone (USB serial)           │
  │ D1  TX   — leave alone (USB serial)           │
  │ D2  ───── LEFT  wheel encoder  (LM393 OUT)    │  interrupt 0
  │ D3  ───── RIGHT wheel encoder  (LM393 OUT)    │  interrupt 1
  │ D4  ───── L298N IN1                           │
  │ D5  ───── L298N ENA   (PWM, RIGHT motor)      │
  │ D6  ───── L298N ENB   (PWM, LEFT  motor)      │
  │ D7  ───── L298N IN2                           │
  │ D8  ───── L298N IN3                           │
  │ D9  ───── HC-SR04 RIGHT  TRIG                 │
  │ D10 ───── HC-SR04 RIGHT  ECHO                 │
  │ D11 ───── L298N IN4                           │
  │ D12 ───── spare  (leave empty, handy test pt) │
  │ D13 ───── status LED (onboard) + buzzer       │
  │           + GO button to GND VIA 330 Ω        │  see below
  │ A0  ───── HC-SR04 FRONT  TRIG                 │
  │ A1  ───── HC-SR04 FRONT  ECHO                 │
  │ A2  ───── HC-SR04 LEFT   TRIG                 │
  │ A3  ───── HC-SR04 LEFT   ECHO                 │
  │ A4  ───── MPU-6050 SDA        do not reuse    │
  │ A5  ───── MPU-6050 SCL        do not reuse    │
  │ VIN ───── battery +                           │
  │ GND ───── common ground                       │
  └───────────────────────────────────────────────┘
```

## Power

```
   [ SWITCH ]
 ┌─────/ ─────┬──────────────► L298N  +12V
 │            │
BATT+         └──────────────► Arduino VIN
 │
BATT−  ──┬───────────────────► L298N  GND
         ├───────────────────► Arduino GND
         └───────────────────► sensor GND rail

 Arduino 5V ──────────────────► sensor 5V rail
                                 ├─ HC-SR04 ×3   VCC
                                 ├─ MPU-6050     VCC
                                 └─ LM393 ×2     VCC

 1000 µF across the battery at the L298N terminals
 100 nF soldered across each motor's own two terminals
```

Rules to obey or the robot misbehaves in ways that look like software bugs:

1. **One common ground.** Arduino GND, L298N GND, battery −, every sensor
   GND. If the sonar reads nonsense, this is the first thing to check.
2. **Never join the L298N 5 V output to the Arduino 5 V pin.** Leave the
   L298N 5V-EN jumper fitted so the driver powers its own logic, and stop
   there.
3. **Remove the ENA and ENB jumpers on the L298N.** With them fitted the
   enable pins are tied high, PWM does nothing and the robot has one speed:
   flat out.
4. Never power the motors from the USB port. It cannot supply the current
   and you may damage the port.
5. Sensors get 5 V from the Arduino, not from the L298N.

## L298N to motors

| L298N | Goes to | Controlled by |
| --- | --- | --- |
| OUT1, OUT2 | RIGHT motor | ENA (D5), IN1 (D4), IN2 (D7) |
| OUT3, OUT4 | LEFT motor | ENB (D6), IN3 (D8), IN4 (D11) |

If a wheel spins the wrong way, **do not rewire it** — set `MOTOR_L_SIGN` or
`MOTOR_R_SIGN` to `-1` in `config.h`. Swapping wires and swapping signs at
the same time is how you spend an afternoon confused.

## Sensor mounting

**Ultrasonics.** Front one dead ahead in the middle of the nose. Left and
right ones facing exactly 90° out, level, as far forward as you can without
poking past the tyres. Then measure where they actually ended up and put
those numbers in `config.h` (`US_F_X_MM`, `US_L_Y_MM` …). The code uses them.

Two things that will bite you:

- **Cross-talk.** Three sonars firing together hear each other's pings. The
  firmware fires them one at a time in the order front, left, front, right —
  never change that to "ping all three" to go faster.
- **Angled walls.** Ultrasound bounces off a wall like light off a mirror. Hit
  a wall at more than about 60° off square and the echo never comes back —
  the sensor reports "nothing there". The simulator models this, which is
  why the code treats a missing echo as "far" and only believes it after two
  consecutive misses. Mount the side sensors square to the wall.

**MPU-6050.** Flat, level, rigid, and as close to the middle of the robot as
you can. Double-sided foam tape then a zip tie over the top. If it can
wobble, it will report the wobble as turning. Keep it away from the motors
and away from the motor wires — twist those wires together to cancel their
field.

If you mount it upside down, set `GYRO_Z_SIGN = -1.0f` in `MazeRunner.ino`.

**GO button — D13, and the 330 Ω is not optional.** D13 already drives the
onboard status LED, so the pin spends most of its life as an *output*. A
plain button from D13 to ground would short that output straight to ground
every time you pressed it. The 330 Ω resistor sits in series with the button
and limits that to a few milliamps.

```
   D13 ──┬──── onboard LED (already on the board)
         │
         └──[ 330 Ω ]──[ GO button ]──── GND
```

The firmware flips D13 to an input with the pull-up on for 200 µs, reads it,
and flips it straight back to an output — so the LED keeps working and the
button still reads. It is only sampled before the run starts, so a knock
mid-run cannot restart anything. Full procedure in
`docs/12_STARTING_THE_ROBOT.md`.

**No floor sensor.** There is deliberately nothing under the nose any more —
see `docs/09_CHECKLIST.md`. D12 is free; it makes a convenient scope point.

**Encoders.** The LM393 slot sensor straddles the black slotted disc on the
inside of each wheel. Get the disc centred in the slot — if it rubs, it
brakes the wheel; if it is too far out, it misses counts.

## Inspection checklist (§11)

Go through this before you get in the queue.

- [ ] No exposed conductor anywhere. Heat-shrink every joint.
- [ ] Nothing on a breadboard. Everything soldered or in a locked connector.
- [ ] Every board bolted down with M3 screws and standoffs, not tape alone.
- [ ] Wires tied down; nothing can reach a wheel.
- [ ] No sharp edges. File any cut screw ends.
- [ ] Master switch reachable without touching anything else.
- [ ] Battery mechanically retained, not just plugged in.
- [ ] All original kit parts present and working (the breadboard is the one
      exception §2.2 allows you to leave off — bring it in the box anyway so
      you can show it).
- [ ] Nothing that could be mistaken for a radio. No second microcontroller,
      no Bluetooth module, no ESP anything, not even unused on the board.
- [ ] The robot starts on its own with nobody touching it (see
      `docs/07_COMPETITION_DAY.md`).
