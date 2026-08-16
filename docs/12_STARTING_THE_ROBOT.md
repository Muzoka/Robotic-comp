# Starting the robot

You put the robot on the track, then tell it to go, without touching it once
it is running. Here is exactly how, and why it is built this way.

---

## The short version

```
1.  Put the robot in the start pocket, pointing down the first passage.
2.  Flip the MASTER SWITCH on.        LED blinks fast  = calibrating, keep off it
3.  Wait until the fast blink stops.  LED steady on    = ready, waiting for you
4.  Hold your hand about 5 cm in front of its nose, then take it away.
5.  LED blinks a 3-second countdown.  Step back.
6.  It goes. Do not touch it (SS3.4).
```

Nothing is pressed, nothing is nudged, no laptop, no radio.

---

## Why a hand in front of the nose, and not a button

A push button seems simpler, and it is — until you use one. The passage is
**304.8 mm** wide and the robot is **115 mm** wide, so it has about **95 mm**
of room either side when driving and **28 mm** when it turns. Pressing a
button on the robot moves it a few millimetres and twists it a degree or two.
That is a meaningful fraction of the margin, given away for free, on every
single run.

The robot already has an ultrasonic sensor pointing forward. Holding a hand
in front of it and taking it away is a signal it can read perfectly, and your
hand never touches the robot.

It is also unambiguous for the judges (§11 D, "Autonomous Start Procedure"):
you can stand back with both hands visible and show that nothing on the robot
was touched between placing it and it moving.

## What each light means

| LED (pin D13) | Meaning |
| --- | --- |
| Fast blink, ~2–3 s after switch-on | Calibrating the gyro. **Keep completely still.** |
| Steady on | Ready. Waiting for your hand. |
| Blinking, 3 seconds | Countdown. Step back now. |
| Off, robot moving | Running. |
| Fast blink, robot stopped | Finished. |

Add a small buzzer in parallel with the LED if you want the countdown audible
— it makes the start much clearer to a judge across the table.

## Choosing which wall to follow, at the start line

The length of the hold also picks the strategy, so you can change it at the
start line without a laptop:

| Gesture | Rule used | Countdown blink |
| --- | --- | --- |
| **Quick tap** (under 1.5 s) | **RIGHT-hand rule** — the default, use this | fast |
| Long hold (over 1.5 s) | Left-hand rule — fallback only | slow |

**Use the quick tap.** The right-hand rule is what drives the whole road on
all three maps; the left-hand rule skips half of Map 2. The long hold is
there in case you meet a map where the right hand loops forever.

Watch the countdown blink and check it matches what you wanted. If it does
not, switch off and start again — you have not lost anything.

## The gyro calibration, and why you must not touch it

For the first couple of seconds after switch-on the robot measures how much
its gyro drifts when it is not moving. If it is moving during that
measurement, the number is wrong and the robot will slowly curve for the rest
of the run.

Two things follow:

- **Place it first, switch on second.** Do not switch it on in your hand and
  then carry it to the track.
- If you did switch on while carrying it, it will still recover: the firmware
  re-measures the drift every time the robot stands still, including during
  the 3-second countdown. But the clean way costs nothing.

## The switch itself

One **master rocker or toggle switch, rated 3 A, in the battery + line**,
before everything else. That is the only switch you need. Put it somewhere
you can reach without leaning over the robot — the back edge is ideal — and
mount it so it cannot be knocked by a wall.

An inline **3 A fuse** next to it is 5 SAR of insurance against a shorted
motor lead.

## If you would rather have a physical GO button

You can, but it costs you the floor sensor. D12 is the only free pin, and the
TCRT5000 is using it to count sector lines and spot the striped finish gate.

If you decide the button is worth more:

1. Wire a push button between **D12** and **GND**.
2. In `MazeRunner.ino`, change `HAS_LINE_SENSOR` to `0` in `config.h`, and
   replace the line-sensor read with:
   ```cpp
   pinMode(PIN_LINE, INPUT_PULLUP);            // in setup()
   startPressed = (digitalRead(PIN_LINE) == LOW);   // in loop()
   ```
3. Mount the button on the **back** of the robot, on a stiff bracket, so
   pressing it pushes the robot into the start wall rather than sideways.

I would not do it. The hand gesture works, costs no pins, and does not move
the robot.

## What NOT to do

- **No radio, Bluetooth, IR remote or phone app.** §3.1 and §10 — instant
  disqualification, even if the module is fitted and unused.
- **Do not start it by plugging in the USB cable.** It works, but a judge
  watching a laptop cable go into the robot at the start line is a
  conversation you do not want, and the cable moves the robot.
- **Do not press RESET to start.** It reboots the gyro calibration while your
  finger is on the robot, which is the worst of both worlds.

## Between runs

- **Fresh battery every run**, not every third run.
- Wipe the tyres — dust changes how the turns come out.
- Put it down and let it sit still through the calibration blink.
- Check the side sensors are still square. They get knocked.
