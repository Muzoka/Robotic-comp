# Wokwi — and an honest note about what it can and cannot do for you

## Read this first

You asked for a `diagram.json` you can drop into Wokwi so it "builds and
wires everything, and I copy it physically". Here is the straight answer:

**Wokwi cannot draw your robot's real wiring, because Wokwi has no L298N
motor driver, no TT gear motors and no wheels in its parts library.** Any
diagram.json is therefore a diagram of *part* of the robot. Nobody can give
you a Wokwi file that you copy 1:1 onto the chassis — not because it wasn't
made properly, but because the simulator does not contain those parts.

So you get two things instead, and together they do the whole job:

| For | Use | File |
| --- | --- | --- |
| **Testing the firmware** — pins right, gyro talking, sonar timing, state machine behaving | Wokwi | `wokwi/diagram.json` + the four source files |
| **Copying the wiring physically** | The wiring drawing | `docs/wiring_diagram.svg` and `docs/03_WIRING.md` |

The Wokwi diagram wires up everything Wokwi *does* have — the Uno, all three
ultrasonics, the MPU-6050, the floor sensor and the encoders — and replaces
the six L298N control lines with six LEDs. That turns out to be genuinely
useful: you can watch the motor commands as light. Left turn, right turn,
forward, reverse, PWM brightness — all visible.

---

## Setting it up (5 minutes)

1. Go to **<https://wokwi.com>** and sign in (free).
2. **New Project → Arduino Uno.**
3. Click the **`diagram.json`** tab. Select everything, delete it, and paste
   the contents of `wokwi/diagram.json` from this repo.
4. Click the **`sketch.ino`** tab and paste
   `firmware/MazeRunner/MazeRunner.ino`.
5. Add three more files with the **+** button next to the tabs, named exactly:
   - `config.h`
   - `nav_core.h`
   - `nav_core.cpp`

   Paste the matching file from `firmware/MazeRunner/` into each.
6. Press the green **play** button.

That is the same four files you will flash onto the real Uno. No changes.

---

## What to do once it runs

Open the **Serial Monitor** (bottom panel) and set it to 115200. You should
see:

```
# MazeRunner booting - hold still, calibrating gyro
# gyro OK
# ready. Wave a hand in front of the nose to arm.
t_ms,state,dF,dL,dR,head,tgt,encL,encR,pwmL,pwmR,sect
```

Now drive it by hand:

| Do this | Should happen |
| --- | --- |
| Click the **front HC-SR04** and drag its distance slider down to ~5 cm, then back up to 60 cm | State goes `WAIT_START → COUNTDOWN`, D13 blinks, then `DRIVE` |
| Watch the LEDs after `DRIVE` | ENA and ENB light up, IN1 and IN3 on, IN2 and IN4 off — both motors forward |
| Drag the **front** sensor down to 15 cm | State goes to `CREEP`, then `TURN`. IN1/IN2 or IN3/IN4 swap — the robot is pivoting |
| Drag the **left** sensor up to 100 cm while the front stays clear | It should spot a left opening, `CREEP`, then turn left |
| Hold the **black button** (D12) | The `sect` column at the end of the telemetry line goes up by one when you release — that is a sector line being counted |
| Tap the **blue / green buttons** | `encL` / `encR` count up — these stand in for the wheel encoders |

If all of that works in Wokwi, your firmware is correct and the pin map is
correct. What is left is purely mechanical: wiring, mounting and tuning.

### One thing Wokwi cannot do

There are no wheels, so the robot never actually moves. That means:

- The **encoder counts do not go up on their own**, so the "I am jammed"
  watchdog will fire after about a second of driving and put the robot into
  `STUCK`. **This is correct behaviour, not a bug** — from the firmware's
  point of view the motors are running and the wheels are not turning.
  Tap the blue and green buttons to keep it happy, or just ignore it.
- It cannot tell you whether the robot navigates a maze. That is what
  `sim/run.py` in this repo is for.

---

## Sanity checks worth doing here before you build

- **Memory.** After compiling, Wokwi prints the sketch size. You want RAM
  usage comfortably under 2048 bytes. Anything over ~1600 bytes and the Uno
  starts behaving strangely in ways that look like sensor faults.
- **Loop timing.** The telemetry timestamps should step by about 100 ms. If
  they are much slower, an ultrasonic is timing out every loop.
- **Gyro address.** If it prints `# gyro NOT FOUND`, the MPU-6050 is on
  address 0x69 instead of 0x68 — that happens when the AD0 pin is tied high.
  On the real module, leave AD0 unconnected.
