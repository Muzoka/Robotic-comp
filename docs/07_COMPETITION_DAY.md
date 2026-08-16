# Competition day

Print this. Take it with you.

---

## The bag

- [ ] Robot, assembled and working
- [ ] Laptop + USB cable + charger
- [ ] Charged batteries ×3 sets, plus the charger
- [ ] Spare MPU-6050, spare HC-SR04, spare jumper leads
- [ ] Soldering iron, solder, side cutters, screwdrivers, multimeter
- [ ] M3 screws, nuts, standoffs, zip ties
- [ ] Black tape and a marker (for re-marking anything)
- [ ] Tape measure (to measure the real maze)
- [ ] This printout, and `docs/03_WIRING.md`
- [ ] The kit box with **every original part**, including the breadboard, to
      show the inspector (§11 A)

---

## On arrival — before you queue for inspection

1. **Measure the maze.** Passage width, wall height, overall size. Write it
   down.
2. **Photograph each map from directly above** if you are allowed. You will
   trace them.
3. **Trace each map into `sim/maps/`.** Fifteen minutes each. Then:
   ```bash
   cd sim
   python3 run.py --map maps/real_map1.txt --compare
   ```
   That tells you, per map, whether the left- or right-hand rule works and
   roughly how many sector points to expect. This is the whole reason the
   simulator exists — use it.
4. If the passage is narrower than you were told, re-run
   `python3 tools/geometry_check.py --corridor <actual>` and find out
   immediately whether the robot can turn at all.

---

## Technical inspection (§11)

Have these ready to say:

| They check | You say / show |
| --- | --- |
| Kit completeness | Here is the box with every original part |
| No replacements | Original Arduino Uno, original L298N, original motors, original chassis |
| Nothing disabled | All present and working |
| Breadboard | §2.2 permits removing it. Here it is in the box; we soldered instead for reliability |
| Add-ons | 3 ultrasonics (§2.2 explicitly allows 3), one gyro, two wheel encoders, one GO button. All sensors — no extra microcontroller anywhere |
| Battery | 7.4 V (or 9 V). Under the 12 V per-supply and 20 V total limits |
| Safety | No exposed conductor, no sharp edges, everything bolted, master switch here |
| Autonomy | No radio of any kind. It starts on its own — watch |

Then demonstrate the start. That is the strongest thing you can show.

---

## Starting the robot — no laptop

```
1.  Switch on. It calibrates the gyro — KEEP IT COMPLETELY STILL for ~3 s.
2.  Place it in the Start Zone, pointing down the first corridor.
3.  Watch it for ten seconds without touching it. It must NOT move.
4.  Press the GO button on the back. Step back.
5.  The LED blinks a 3-second countdown.
6.  It goes. Do not touch it again (§3.4).
```

Step 3 is not padding. The firmware once had a fault that made it start its
own run about three seconds after power-on, and the only symptom was the
robot driving off while somebody was still placing it. It is fixed and
tested, but ten seconds of watching costs nothing.

**Backup start, if the button or its wire fails:** hold a hand about 5 cm in
front of the nose for a second, then take it away. Same countdown, same run.
Nothing to plug in. Worth practising once so you are not learning it at the
table.

The hand-wave also picks which wall the robot follows — a quick tap for
left, a longer hold for right, and the countdown blinks slow or fast to tell
you which it chose. **This no longer matters:** since the straight-first
rule went in, left and right drive the identical route on all three maps.
Do not spend attention on it.

---

## Between runs

- **Swap the battery.** Every run, not every third run. A tired battery is
  the most common cause of a bad second attempt.
- **Wipe the wheels.** Dust on the tyres makes turns inconsistent.
- **Check the sensors are still square.** They get knocked.
- Put it down flat and still for the gyro calibration. Do not hold it in your
  hand while it boots.

---

## What to do when it goes wrong

| It does this | Cause | Fix at the table |
| --- | --- | --- |
| Curves into a wall on a straight | Gyro not calibrated (it moved during boot) | Power cycle, keep it still |
| Turns short or long | Gyro mounted loose, or upside down | Tighten it; check `GYRO_Z_SIGN` |
| Stops dead, motors humming | Battery flat, or wedged | New battery |
| Spins in place | Both side sensors reading "open" — a sensor came loose | Check the 5 V and GND on the side sonars |
| Drives back out of the start gate | It reached a dead end and came all the way back | Different hand rule next attempt |
| Ignores a turn | Side sensor not seeing the wall — mounted too far back or crooked | Re-square the sensor |
| Resets mid-run | Motor surge browning out the Arduino | Check the 1000 µF capacitor is fitted |

Nothing above needs a code change. Do not edit code between runs unless you
have a genuine, understood reason — and if you do, run it in the simulator
first, even at the venue. It takes 30 seconds.

---

## Strategy reminders

- **Points, not speed.** §6.1: one point per sector line all three wheels
  fully cross. Time is only a tie-breaker (§6.3). Never trade reliability for
  speed.
- **Attempts.** §3.3 gives 2–3 attempts only if you did *not* complete the
  map. Completing slowly is better than failing quickly.
- **Finishing is not required to score.** A robot that keeps moving and keeps
  crossing lines beats one that solves two maps and jams on the third.
- **Do not touch the robot during a run** (§3.4, §6.2). If it is stuck, let
  the judge stop it. Touching it costs you the run.
- **Appeals** must be filed within 10 minutes (§7.3).
