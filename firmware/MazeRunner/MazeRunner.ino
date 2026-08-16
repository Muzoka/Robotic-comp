/* =====================================================================
 * MazeRunner - Robotics Navigation Challenge
 * Arduino Uno R3 + L298N + 3x HC-SR04 + MPU-6050 + 2x slot encoders
 *
 * This file is ONLY hardware: pins, timers, I2C, PWM.
 * All the thinking happens in nav_core.cpp, which is also compiled into
 * the desktop simulator. Do not put navigation logic in here.
 *
 * Board:  Arduino Uno    Port: whatever the CH340 shows up as
 * Libraries needed: none (Wire and EEPROM ship with the IDE)
 * ===================================================================== */

#include <Wire.h>
#include <EEPROM.h>
#include "config.h"
#include "nav_core.h"

/* ===================================================================== */
/* Ultrasonics - serviced one at a time, front twice as often as the sides */
/* ===================================================================== */
struct Sonar { uint8_t trig, echo; uint16_t mm; uint8_t fails; };
static Sonar sonarF = { PIN_TRIG_F, PIN_ECHO_F, US_MAX_MM, 0 };
static Sonar sonarL = { PIN_TRIG_L, PIN_ECHO_L, US_MAX_MM, 0 };
static Sonar sonarR = { PIN_TRIG_R, PIN_ECHO_R, US_MAX_MM, 0 };

/* 2 m of air, there and back, at 343 m/s = 11.7 ms. 13 ms is a safe cap. */
static const unsigned long ECHO_TIMEOUT_US = 13000UL;

static void sonarPing(Sonar &s)
{
  digitalWrite(s.trig, LOW);  delayMicroseconds(3);
  digitalWrite(s.trig, HIGH); delayMicroseconds(10);
  digitalWrite(s.trig, LOW);

  unsigned long us = pulseIn(s.echo, HIGH, ECHO_TIMEOUT_US);
  if (us == 0) {
    /* No echo. Either nothing is there, or the wall is at a bad angle and
     * the ping bounced away. Both mean "far" as far as we care. Two
     * misses in a row before we believe it, so one bad ping cannot make
     * the robot think a wall vanished. */
    if (s.fails < 3) s.fails++;
    if (s.fails >= 2) s.mm = US_MAX_MM;
    return;
  }
  s.fails = 0;

  uint16_t mm = (uint16_t)(us * 343UL / 2000UL);   /* us -> mm */
  if (mm < US_MIN_MM) mm = US_MIN_MM;
  if (mm > US_MAX_MM) mm = US_MAX_MM;

  /* median-of-3 on the fly: cheap, kills the classic single-sample spike */
  static uint16_t h[3][3]; static uint8_t hi[3];
  uint8_t k = (&s == &sonarF) ? 0 : (&s == &sonarL) ? 1 : 2;
  h[k][hi[k]] = mm; hi[k] = (hi[k] + 1) % 3;
  uint16_t a = h[k][0], b = h[k][1], c = h[k][2];
  uint16_t med = (a > b) ? ((b > c) ? b : ((a > c) ? c : a))
                         : ((a > c) ? a : ((b > c) ? c : b));
  s.mm = med;
}

/* ===================================================================== */
/* Wheel encoders - single channel, so direction comes from the command   */
/* ===================================================================== */
volatile int32_t encL = 0, encR = 0;
volatile int8_t  dirL = 1, dirR = 1;

static void isrL() { encL += dirL; }
static void isrR() { encR += dirR; }

/* ===================================================================== */
/* MPU-6050 - raw I2C, no library, so nothing can fail to install         */
/* ===================================================================== */
static const uint8_t MPU = 0x68;
static float gyroBiasZ = 0.0f;
static float headingDeg = 0.0f;
static float gyroRateDps = 0.0f;
static bool  gyroOK = false;

/* Set to -1 if you bolt the MPU on upside down. */
static const float GYRO_Z_SIGN = +1.0f;

static void mpuWrite(uint8_t reg, uint8_t val)
{
  Wire.beginTransmission(MPU); Wire.write(reg); Wire.write(val); Wire.endTransmission();
}

static int16_t mpuReadGyroZ()
{
  Wire.beginTransmission(MPU); Wire.write(0x47); Wire.endTransmission(false);
  Wire.requestFrom((int)MPU, 2);
  if (Wire.available() < 2) return 0;
  int16_t hi = Wire.read(), lo = Wire.read();
  return (int16_t)((hi << 8) | lo);
}

static bool mpuBegin()
{
  Wire.begin();
  Wire.setClock(400000);
  Wire.beginTransmission(MPU);
  if (Wire.endTransmission() != 0) return false;

  mpuWrite(0x6B, 0x01);   /* wake, clock from gyro X                       */
  delay(50);
  mpuWrite(0x1A, 0x03);   /* DLPF 44 Hz - kills motor vibration            */
  mpuWrite(0x1B, 0x08);   /* gyro full scale +/-500 dps -> 65.5 LSB/dps    */
  mpuWrite(0x19, 0x04);   /* sample rate 200 Hz                            */
  delay(50);

  /* Bias calibration. THE ROBOT MUST BE COMPLETELY STILL FOR THIS. */
  long sum = 0;
  const int N = 800;
  for (int i = 0; i < N; i++) { sum += mpuReadGyroZ(); delay(3); }
  gyroBiasZ = (float)sum / (float)N;
  return true;
}

/* Report the rate only. nav_core does the integrating, the deadband and
 * the re-biasing, because that is the part that has to be tested in the
 * simulator - and the simulator cannot run this file. headingDeg below is
 * for the serial log and for your eyes, nothing steers by it. */
static void gyroUpdate(float dt_s)
{
  if (!gyroOK) return;
  float raw = (float)mpuReadGyroZ() - gyroBiasZ;
  gyroRateDps = GYRO_Z_SIGN * raw / 65.5f;
  headingDeg += gyroRateDps * dt_s;
}

/* ===================================================================== */
/* L298N                                                                  */
/* ===================================================================== */
static void motorsBegin()
{
  pinMode(PIN_ENA, OUTPUT); pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN1, OUTPUT); pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT); pinMode(PIN_IN4, OUTPUT);
  analogWrite(PIN_ENA, 0);  analogWrite(PIN_ENB, 0);
}

static void motorsWrite(int16_t l, int16_t r)
{
  l *= MOTOR_L_SIGN;
  r *= MOTOR_R_SIGN;

  dirL = (l >= 0) ? 1 : -1;
  dirR = (r >= 0) ? 1 : -1;

  /* LEFT motor -> ENB / IN3,IN4 */
  digitalWrite(PIN_IN3, l >= 0 ? HIGH : LOW);
  digitalWrite(PIN_IN4, l >= 0 ? LOW  : HIGH);
  analogWrite(PIN_ENB, (uint8_t)constrain(abs(l), 0, 255));

  /* RIGHT motor -> ENA / IN1,IN2 */
  digitalWrite(PIN_IN1, r >= 0 ? HIGH : LOW);
  digitalWrite(PIN_IN2, r >= 0 ? LOW  : HIGH);
  analogWrite(PIN_ENA, (uint8_t)constrain(abs(r), 0, 255));
}

/* ===================================================================== */
/* EEPROM - the Uno already has 1024 bytes on board. No memory module,    */
/* no extra chip, nothing to buy. This is where the junction map lives    */
/* so a stopped-and-restarted run does not start from zero knowledge.     */
/* ===================================================================== */
static void memorySave()
{
  uint8_t buf[MAX_JUNCTIONS * 4];
  uint32_t n = nav_export_memory(buf, sizeof(buf));
  int a = EEPROM_BASE;
  EEPROM.update(a++, (uint8_t)(EEPROM_MAGIC >> 8));
  EEPROM.update(a++, (uint8_t)(EEPROM_MAGIC & 0xFF));
  EEPROM.update(a++, (uint8_t)(n >> 8));
  EEPROM.update(a++, (uint8_t)(n & 0xFF));
  for (uint32_t i = 0; i < n && a < 1000; i++) EEPROM.update(a++, buf[i]);
}

static void memoryLoad()
{
  int a = EEPROM_BASE;
  uint16_t magic = ((uint16_t)EEPROM.read(a) << 8) | EEPROM.read(a + 1);
  if (magic != EEPROM_MAGIC) return;
  uint16_t n = ((uint16_t)EEPROM.read(a + 2) << 8) | EEPROM.read(a + 3);
  if (n == 0 || n > MAX_JUNCTIONS * 4) return;
  static uint8_t buf[MAX_JUNCTIONS * 4];
  for (uint16_t i = 0; i < n; i++) buf[i] = EEPROM.read(a + 4 + i);
  nav_import_memory(buf, n);
}

static void memoryClear()
{
  EEPROM.update(EEPROM_BASE, 0); EEPROM.update(EEPROM_BASE + 1, 0);
}

/* ===================================================================== */
/* main                                                                   */
/* ===================================================================== */
static NavIn  nin;
static NavOut nout;
static unsigned long lastLoop = 0;
static uint8_t  sonarSlot = 0;
static bool     startPressed = false;
static bool     saved = false;

void setup()
{
  Serial.begin(115200);

  pinMode(sonarF.trig, OUTPUT); pinMode(sonarF.echo, INPUT);
  pinMode(sonarL.trig, OUTPUT); pinMode(sonarL.echo, INPUT);
  pinMode(sonarR.trig, OUTPUT); pinMode(sonarR.echo, INPUT);
  pinMode(PIN_LINE, INPUT);
  pinMode(PIN_LED, OUTPUT);

  motorsBegin();
  motorsWrite(0, 0);

#if HAS_ENCODERS
  pinMode(PIN_ENC_L, INPUT); pinMode(PIN_ENC_R, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_L), isrL, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_R), isrR, RISING);
#endif

  Serial.println(F("# MazeRunner booting - hold still, calibrating gyro"));
#if HAS_GYRO
  gyroOK = mpuBegin();
  Serial.print(F("# gyro ")); Serial.println(gyroOK ? F("OK") : F("NOT FOUND"));
#endif

  nav_reset(DEFAULT_MODE, WALL_HAND);
  /* Uncomment the next line only if you want run 2 to remember run 1.
   * For a fresh map, leave it commented so the robot starts clean. */
  /* memoryLoad(); */

  Serial.println(F("# ready. Wave a hand in front of the nose to arm."));
  Serial.println(F("t_ms,state,dF,dL,dR,head,tgt,encL,encR,pwmL,pwmR,sect"));
  lastLoop = millis();
}

void loop()
{
  unsigned long now = millis();
  unsigned long dt = now - lastLoop;
  if (dt < LOOP_DT_MS) return;
  lastLoop = now;

  /* --- sensors --- front, left, front, right --- */
  switch (sonarSlot) {
    case 0: case 2: sonarPing(sonarF); break;
    case 1:         sonarPing(sonarL); break;
    case 3:         sonarPing(sonarR); break;
  }
  sonarSlot = (sonarSlot + 1) & 3;

  gyroUpdate(dt / 1000.0f);

  /* Serial 'g' also starts a run, handy on the bench. */
  if (Serial.available()) { if (Serial.read() == 'g') startPressed = true; }

  noInterrupts();
  int32_t tl = encL, tr = encR;
  interrupts();

  nin.dist_front_mm = sonarF.mm;
  nin.dist_left_mm  = sonarL.mm;
  nin.dist_right_mm = sonarR.mm;
  nin.heading_deg   = headingDeg;
  nin.gyro_rate_dps = gyroRateDps;
  nin.ticks_left    = tl;
  nin.ticks_right   = tr;
#if HAS_LINE_SENSOR
  nin.line_black    = (digitalRead(PIN_LINE) == LOW) ? 1 : 0;
#else
  nin.line_black    = 0;
#endif
  nin.start_signal  = startPressed ? 1 : 0;
  nin.dt_ms         = (uint16_t)dt;

  nav_step(&nin, &nout);

  motorsWrite(nout.pwm_left, nout.pwm_right);
  digitalWrite(PIN_LED, nout.led ? HIGH : LOW);

  if (nout.done && !saved) { memorySave(); saved = true; }

  /* telemetry, every 100 ms, CSV - tools/telemetry_plot.py eats this */
  static unsigned long lastLog = 0;
  if (now - lastLog >= 100) {
    lastLog = now;
    Serial.print(now);              Serial.print(',');
    Serial.print(nav_state_name(nout.state)); Serial.print(',');
    Serial.print(nin.dist_front_mm); Serial.print(',');
    Serial.print(nin.dist_left_mm);  Serial.print(',');
    Serial.print(nin.dist_right_mm); Serial.print(',');
    Serial.print(headingDeg, 1);     Serial.print(',');
    Serial.print(nout.dbg_target_deg, 1); Serial.print(',');
    Serial.print(tl);                Serial.print(',');
    Serial.print(tr);                Serial.print(',');
    Serial.print(nout.pwm_left);     Serial.print(',');
    Serial.print(nout.pwm_right);    Serial.print(',');
    Serial.println(nout.sectors_seen);
  }
}
