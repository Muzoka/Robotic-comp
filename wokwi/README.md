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
ultrasonics, the MPU-6050, the GO button and the encoders — and replaces
the six L298N control lines with six LEDs. That turns out to be genuinely
useful: you can watch the motor commands as light. Left turn, right turn,
forward, reverse, PWM brightness — all visible.

There is **no floor line sensor** in the diagram any more, because there is
no longer one on the robot. See `docs/09_CHECKLIST.md` — it was removed on
purpose, and the pin it used to occupy (D12) now carries the GO button.

---

## Setting it up — two files, two minutes

1. Go to **<https://wokwi.com>** and sign in (free).
2. **New Project → Arduino Uno.**
3. Click the **`diagram.json`** tab. Select everything, delete it, and paste
   **`wokwi/diagram.json`** from this repo.
4. Click the **`sketch.ino`** tab. Select everything, delete it, and paste
   **`wokwi/sketch.ino`** — note: `wokwi/sketch.ino`, *not* the one in
   `firmware/`.
5. Press the green **play** button.

That is it. Two tabs, two pastes, nothing to name.

`wokwi/sketch.ino` is the whole firmware squashed into one file — every line
of `config.h`, `nav_core.h`, `nav_core.cpp` and `MazeRunner.ino`, in
dependency order. It is **generated** by `tools/make_wokwi_sketch.py`, never
edited by hand, so it cannot drift from the real sources. Re-run that script
after changing any firmware file.

### If you get `fatal error: config.h: No such file or directory`

You pasted `firmware/MazeRunner/MazeRunner.ino` instead of
`wokwi/sketch.ino`. The firmware version is split across four files and says
`#include "config.h"` at the top; Wokwi cannot find that file because you
only gave it one. Paste `wokwi/sketch.ino` instead and it will build.

### The four-file way (only if you want to edit the firmware in Wokwi)

Wokwi's tab bar has `sketch.ino`, `diagram.json`, `Library Manager`, and a
small **▼** arrow at the end. That arrow — *not* a plus button — is the file
menu.

1. Paste `firmware/MazeRunner/MazeRunner.ino` into the `sketch.ino` tab.
2. **▼ → New File…**, name it exactly `config.h`, paste that file.
3. Repeat for `nav_core.h` and `nav_core.cpp`.

Names are case-sensitive and need their extensions. These are the same four
files you flash to the real Uno, unchanged.

---

## What to do once it runs

Open the **Serial Monitor** (bottom panel) and set it to 115200. You should
see:

```
# MazeRunner booting - hold still, calibrating gyro
# gyro OK
# ready. Press GO, or wave a hand in front of the nose.
t_ms,state,dF,dL,dR,head,tgt,encL,encR,pwmL,pwmR,sect
```

Now drive it by hand:

| Do this | Should happen |
| --- | --- |
| Press the **red GO button** (D12) | Serial prints `# GO pressed`, state goes `WAIT_START → COUNTDOWN`, D13 blinks for 3 s, then `DRIVE`. This is exactly how you will start it on the day |
| *or* click the **front HC-SR04** and drag its distance slider down to ~5 cm, then back up to 60 cm | Same thing, hands-free. The button and the hand-wave both work |
| Watch the LEDs after `DRIVE` | ENA and ENB light up, IN1 and IN3 on, IN2 and IN4 off — both motors forward |
| Drag the **front** sensor down to 15 cm | State goes to `CREEP`, then `TURN`. IN1/IN2 or IN3/IN4 swap — the robot is pivoting |
| Drag the **left** sensor up to 100 cm while the front stays clear | It should spot a left opening, `CREEP`, then turn left |
| Drag **front, left and right all above 60 cm** at once | Nothing should happen for a moment, then `DRIVE` continues straight — this is the straight-through-a-crossing rule, the one that gives Map 2 the route you drew |
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
