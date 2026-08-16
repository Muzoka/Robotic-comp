/*
 * config.h - ALL tunable numbers live here.
 * This file is shared byte-for-byte between the Arduino firmware and the
 * desktop simulator, so a value tuned in simulation is the value that flies.
 *
 * Units: millimetres (mm), degrees (deg), milliseconds (ms).
 */
#ifndef CONFIG_H
#define CONFIG_H

/* ------------------------------------------------------------------ */
/* 1. ROBOT GEOMETRY - MEASURE YOUR REAL ROBOT AND PUT THE NUMBERS HERE */
/* ------------------------------------------------------------------ */
#define ROBOT_LENGTH_MM     250.0f   /* nose to tail, including any sensor sticking out */
#define ROBOT_WIDTH_MM      150.0f   /* outside of left tyre to outside of right tyre  */
#define WHEEL_BASE_MM       128.0f   /* centre of left tyre to centre of right tyre    */
#define WHEEL_DIAM_MM        65.0f   /* yellow TT wheel, measure it                    */
#define AXLE_FROM_NOSE_MM   125.0f   /* front bumper to wheel axle. KEEP THIS AT HALF
                                       OF ROBOT_LENGTH_MM: a centred axle gives
                                       the smallest possible pivot circle, and
                                       the pivot circle is what decides whether
                                       the robot can turn in the corridor.     */

/* Where each ultrasonic sits, relative to the wheel-axle centre.
 * x = forward (+), y = left (+), angle = 0 forward, +90 = pointing left. */
#define US_F_X_MM   115.0f
#define US_F_Y_MM     0.0f
#define US_F_ANG      0.0f

#define US_L_X_MM    40.0f
#define US_L_Y_MM    68.0f
#define US_L_ANG     90.0f

#define US_R_X_MM    40.0f
#define US_R_Y_MM   -68.0f
#define US_R_ANG    -90.0f

/* ------------------------------------------------------------------ */
/* 2. SENSOR LIMITS                                                    */
/* ------------------------------------------------------------------ */
#define US_MAX_MM          2000     /* anything past this is reported as US_MAX_MM  */
#define US_MIN_MM            25     /* HC-SR04 cannot see closer than ~2 cm         */
#define US_INVALID        60000     /* no echo came back                            */

/* A side reading bigger than this means "there is an opening on that side". */
#define OPEN_SIDE_MM        420
/* An opening only counts on the EDGE wall->open, and only after the reading
 * has been open this many loops. One dropped ping must never invent a
 * junction that is not there. */
#define OPEN_DEBOUNCE         9
/* A front reading smaller than this means "wall ahead, start setting up". */
#define FRONT_BLOCKED_MM    200
/* Creep forward until the front sensor reads this, THEN pivot. The number
 * puts the wheel axle in the middle of the junction square:
 *      CORRIDOR_MM / 2 - US_F_X_MM  =  150 - 95  =  55
 * Get this wrong and the robot pivots off-centre and clips the corner. */
#define FRONT_PIVOT_MM       40
/* Closer than this: reverse before doing anything else. */
#define FRONT_TOOCLOSE_MM    40

/* ------------------------------------------------------------------ */
/* 3. MAZE ASSUMPTIONS                                                 */
/* ------------------------------------------------------------------ */
#define CORRIDOR_MM         300     /* rulebook says 200..400 mm                    */
#define CELL_MM             300     /* one "step" of the maze grid                  */
#define TARGET_SIDE_MM       90     /* how far we try to stay off a wall we follow  */

/* ------------------------------------------------------------------ */
/* 4. SPEEDS  (PWM counts, 0..255)                                     */
/* ------------------------------------------------------------------ */
#define PWM_MIN              55     /* below this a TT motor just buzzes            */
#define PWM_MAX             255
#define PWM_CRUISE          150     /* straight-line speed                          */
#define PWM_SLOW             95     /* creeping / approaching a wall                */
#define PWM_TURN            110     /* pivot speed                                  */
#define PWM_BACK             95     /* reversing                                    */

/* ------------------------------------------------------------------ */
/* 5. CONTROL GAINS                                                    */
/* ------------------------------------------------------------------ */
#define KP_WALL            0.42f    /* PWM per mm of side error                     */
#define KD_WALL            2.10f    /* PWM per (mm/s) of side error rate            */
#define KP_HEADING         3.20f    /* PWM per degree of heading error (straights)  */
#define STEER_LIMIT          80     /* max differential PWM applied while driving   */

#define KP_TURN            2.60f    /* PWM per degree, during a pivot               */
#define KD_TURN            0.22f    /* PWM per (deg/s), during a pivot              */
#define TURN_TOL_DEG       3.0f     /* pivot is finished inside this error          */
#define TURN_SETTLE_MS      120     /* ...and must stay inside it this long         */
#define TURN_TIMEOUT_MS    2600     /* give up and move on                          */

/* ------------------------------------------------------------------ */
/* 6. TIMING                                                           */
/* ------------------------------------------------------------------ */
#define LOOP_HZ              50
#define LOOP_DT_MS           20
#define BACKUP_MS           420
/* Roll this far past a side opening before pivoting into it. Ideal value is
 *      CORRIDOR_MM / 2 + US_L_X_MM - (debounce lag, about 45 mm) = 145 */
#define CREEP_AFTER_OPEN_MM 145
#define TURN_SETTLE_IN_MS   260     /* stop dead before pivoting; also the
                                       window used to re-measure gyro bias  */
#define STUCK_WINDOW_MS     900     /* no encoder movement this long = stuck         */
#define RUN_TIMEOUT_MS   240000UL   /* 4 minutes then stop, whatever happens         */

/* ------------------------------------------------------------------ */
/* 7. ODOMETRY                                                         */
/* ------------------------------------------------------------------ */
#define ENC_TICKS_PER_REV    20     /* slots in the black encoder disc              */
#define ENC_MM_PER_TICK    (3.14159265f * WHEEL_DIAM_MM / (float)ENC_TICKS_PER_REV)

/* ------------------------------------------------------------------ */
/* 8. FEATURE SWITCHES                                                 */
/* ------------------------------------------------------------------ */
#define HAS_GYRO              1     /* MPU-6050 fitted                              */
#define HAS_ENCODERS          1     /* LM393 slot sensors fitted                    */
#define HAS_LINE_SENSOR       1     /* TCRT5000 looking at the floor                */

/* Which hand do we keep on the wall?  +1 = LEFT hand, -1 = RIGHT hand. */
#define WALL_HAND            (+1)

/* Navigation mode */
#define MODE_WALLFOLLOW       0     /* simple, never gets confused in a plain maze  */
#define MODE_TREMAUX          1     /* remembers junctions, beats loops and islands */
#define DEFAULT_MODE   MODE_TREMAUX

/* Tremaux memory */
#define MAX_JUNCTIONS        48     /* 48 * 5 bytes = 240 bytes of SRAM             */
#define EEPROM_MAGIC       0x4D5A   /* 'MZ'                                          */
#define EEPROM_BASE           0

/* ------------------------------------------------------------------ */
/* 9. ARDUINO PIN MAP  (Uno R3)                                        */
/* ------------------------------------------------------------------ */
#define PIN_ENC_L      2   /* INT0 - left  wheel slot sensor          */
#define PIN_ENC_R      3   /* INT1 - right wheel slot sensor          */
#define PIN_IN1        4   /* L298N                                    */
#define PIN_ENA        5   /* L298N, PWM, RIGHT motor                  */
#define PIN_ENB        6   /* L298N, PWM, LEFT  motor                  */
#define PIN_IN2        7
#define PIN_IN3        8
#define PIN_TRIG_R     9
#define PIN_ECHO_R    10
#define PIN_IN4       11
#define PIN_LINE      12   /* TCRT5000 digital out (LOW = black line)  */
#define PIN_LED       13   /* onboard LED + optional buzzer            */
#define PIN_TRIG_F   A0
#define PIN_ECHO_F   A1
#define PIN_TRIG_L   A2
#define PIN_ECHO_L   A3
/*      A4 = SDA, A5 = SCL  -> MPU-6050, do not use for anything else  */

/* Motor polarity: flip to -1 if a wheel spins backwards after wiring. */
#define MOTOR_L_SIGN  (+1)
#define MOTOR_R_SIGN  (+1)

#endif /* CONFIG_H */
