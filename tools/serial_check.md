# Bench tests — one thing at a time

Do these in order, before you flash the real firmware. Each is a throwaway
sketch. Debugging three subsystems at once is how a week disappears.

Put the robot **on a block so the wheels spin free** for anything involving
motors.

---

## 1. Motors

```cpp
#define ENA 5
#define IN1 4
#define IN2 7
#define ENB 6
#define IN3 8
#define IN4 11

void setup() {
  int p[] = {ENA, IN1, IN2, ENB, IN3, IN4};
  for (int i = 0; i < 6; i++) pinMode(p[i], OUTPUT);
}

void drive(bool leftFwd, bool rightFwd, int pwm) {
  digitalWrite(IN3, leftFwd);  digitalWrite(IN4, !leftFwd);  analogWrite(ENB, pwm);
  digitalWrite(IN1, rightFwd); digitalWrite(IN2, !rightFwd); analogWrite(ENA, pwm);
}

void loop() {
  drive(true,  true,  150); delay(1500);   // both forward
  drive(false, false, 150); delay(1500);   // both back
  drive(true,  false, 150); delay(1500);   // spin left
  drive(false, true,  150); delay(1500);   // spin right
  analogWrite(ENA, 0); analogWrite(ENB, 0); delay(1500);
}
```

**Pass:** all four motions correct, and the wheels stop completely in the
pause.

If a wheel goes the wrong way, do **not** swap the wires — set `MOTOR_L_SIGN`
or `MOTOR_R_SIGN` to `-1` in `config.h`. If you swap wires *and* signs you
will spend an afternoon confused.

Also note the lowest PWM at which the wheel actually turns — that is
`PWM_MIN`. It is usually 50–70.

---

## 2. Encoders

```cpp
volatile long cl = 0, cr = 0;
void isrL() { cl++; }
void isrR() { cr++; }

void setup() {
  Serial.begin(115200);
  pinMode(2, INPUT); pinMode(3, INPUT);
  attachInterrupt(digitalPinToInterrupt(2), isrL, RISING);
  attachInterrupt(digitalPinToInterrupt(3), isrR, RISING);
}
void loop() {
  Serial.print(cl); Serial.print('\t'); Serial.println(cr);
  delay(200);
}
```

**Pass:** turn each wheel exactly one revolution by hand — the count goes up
by 20 (or whatever `ENC_TICKS_PER_REV` is for your discs; count the slots).
If it jumps by 2–3 per slot you have contact bounce: check the disc is
centred in the sensor slot and not rubbing.

---

## 3. Ultrasonics

```cpp
struct S { uint8_t t, e; const char *n; };
S s[3] = { {A0, A1, "F"}, {A2, A3, "L"}, {9, 10, "R"} };

long ping(S &x) {
  digitalWrite(x.t, LOW);  delayMicroseconds(3);
  digitalWrite(x.t, HIGH); delayMicroseconds(10);
  digitalWrite(x.t, LOW);
  long us = pulseIn(x.e, HIGH, 13000);
  return us ? us * 343L / 2000L : -1;          // mm, -1 = no echo
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 3; i++) { pinMode(s[i].t, OUTPUT); pinMode(s[i].e, INPUT); }
}
void loop() {
  for (int i = 0; i < 3; i++) {
    Serial.print(s[i].n); Serial.print('='); Serial.print(ping(s[i]));
    Serial.print("  ");
    delay(60);                    // one at a time, or they hear each other
  }
  Serial.println();
}
```

**Pass:** hold a flat book at 50, 100, 300 and 1000 mm and check each sensor
against a ruler. Within ~10 mm is fine.

Then check the failure you actually care about: **hold the book at 45° to the
sensor.** It should return −1 (no echo). That is normal physics, not a broken
sensor, and it is why the firmware treats a missing echo as "far".

Remove the `delay(60)` and watch the readings go mad — that is cross-talk,
and it is why the firmware never fires two sonars at once.

---

## 4. Gyro (MPU-6050)

```cpp
#include <Wire.h>
const uint8_t MPU = 0x68;
float bias = 0, heading = 0;
unsigned long last;

int16_t gz() {
  Wire.beginTransmission(MPU); Wire.write(0x47); Wire.endTransmission(false);
  Wire.requestFrom((int)MPU, 2);
  int16_t h = Wire.read(), l = Wire.read();
  return (h << 8) | l;
}

void setup() {
  Serial.begin(115200); Wire.begin();
  Wire.beginTransmission(MPU); Wire.write(0x6B); Wire.write(0x01); Wire.endTransmission();
  delay(50);
  Wire.beginTransmission(MPU); Wire.write(0x1B); Wire.write(0x08); Wire.endTransmission();
  Serial.println("hold still...");
  long sum = 0;
  for (int i = 0; i < 800; i++) { sum += gz(); delay(3); }
  bias = sum / 800.0;
  Serial.print("bias "); Serial.println(bias);
  last = millis();
}

void loop() {
  unsigned long now = millis();
  float dt = (now - last) / 1000.0; last = now;
  float dps = (gz() - bias) / 65.5;
  if (dps > -0.4 && dps < 0.4) dps = 0;
  heading += dps * dt;
  Serial.println(heading, 1);
  delay(20);
}
```

**Pass, three checks:**

1. Sitting still for 60 seconds, the heading stays within ±2°. More than that
   and the module is loose or the bias calibration was done while it moved.
2. Turn the robot 90° by hand against a square. It should read 90 ± 3°.
3. Turn it 90° the *other* way. It should read −90. If the sign is backwards,
   set `GYRO_Z_SIGN = -1.0f` in `MazeRunner.ino`.

If nothing prints at all, the module is not answering on I2C — check SDA on
A4, SCL on A5, and that it has 5 V and GND.

---

## 5. Line sensor

```cpp
void setup() { Serial.begin(115200); pinMode(12, INPUT); }
void loop() { Serial.println(digitalRead(12)); delay(50); }
```

**Pass:** clean `1` over white floor, clean `0` over black tape, changing
right at the edge. Adjust the trimmer on the module until it does. Set the
height at 5–10 mm and do not change it afterwards.

---

## 6. Everything together

Now flash `firmware/MazeRunner/MazeRunner.ino`, keep the robot on the block,
open the Serial Monitor at **115200**, and watch:

```
# MazeRunner booting - hold still, calibrating gyro
# gyro OK
# ready. Wave a hand in front of the nose to arm.
t_ms,state,dF,dL,dR,head,tgt,encL,encR,pwmL,pwmR,sect
1240,WAIT_START,1850,1200,1300,0.0,0.0,0,0,0,0,0
```

Wave a hand in front of the nose and take it away. The state should go
`WAIT_START → COUNTDOWN` (LED blinking) `→ DRIVE`, and the wheels should
spin. Put a book in front of the nose and it should go to `CREEP` and then
`TURN`.

If that all works on the block, put it on the practice track.
