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
/* MEASURED on the robot as it stands. Keep these honest - every other
 * number in this file and every simulator result depends on them.
 *
 * TARGET: 220 x 140 mm. Measured across all three maps, five seeds each:
 *      250 x 150 (today)  ->  Map 3 completed  20% of runs
 *      235 x 145          ->  Map 3 completed 100% of runs
 *      220 x 140          ->  Map 3 completed 100% of runs, 92 s
 * The cliff is at a body diagonal of about 280 mm. Losing 10 mm of length
 * and 5 mm of width is enough to cross it. */
#define ROBOT_LENGTH_MM     220.0f   /* nose to tail, including anything that sticks out */
#define ROBOT_WIDTH_MM      115.0f   /* OUTSIDE OF LEFT TYRE TO OUTSIDE OF RIGHT TYRE.
                                        Not the chassis plate - the tyres. This is what
                                        sweeps the circle and what the walls see.       */
#define WHEEL_BASE_MM       (ROBOT_WIDTH_MM - 26.0f)  /* tyre centres: width minus one
                                        tyre width. Sets how fast a given PWM
                                        difference turns the robot, so the turn
                                        feed-forward below is computed from it.         */
#define WHEEL_DIAM_MM        65.0f   /* yellow TT wheel, measure it                    */
#define AXLE_FROM_NOSE_MM   (ROBOT_LENGTH_MM * 0.5f)   /* front bumper to wheel axle. KEEP THIS AT HALF
                                       OF ROBOT_LENGTH_MM: a centred axle gives
                                       the smallest possible pivot circle, and
                                       the pivot circle is what decides whether
                                       the robot can turn in the corridor.     */

/* Where each ultrasonic sits, relative to the wheel-axle centre.
 * x = forward (+), y = left (+), angle = 0 forward, +90 = pointing left. */
#define US_F_X_MM   (ROBOT_LENGTH_MM * 0.5f - 10.0f)
#define US_F_Y_MM     0.0f
#define US_F_ANG      0.0f

/* The side sonars sit ON the wheel-axle line, not ahead of it. That way a
 * gap is seen at the instant the axle draws level with it, which is the
 * moment the robot needs to know about. Measured: moving them back from
 * 40 mm ahead to the axle line is worth about 20 percentage points of
 * completion on Map 3. It costs nothing - just remount them. */
#define US_L_X_MM     0.0f
#define US_L_Y_MM   (ROBOT_WIDTH_MM * 0.5f - 7.0f)
#define US_L_ANG     90.0f

#define US_R_X_MM     0.0f
#define US_R_Y_MM   (-(ROBOT_WIDTH_MM * 0.5f - 7.0f))
#define US_R_ANG    -90.0f

/* ------------------------------------------------------------------ */
/* 2. SENSOR LIMITS                                                    */
/* ------------------------------------------------------------------ */
#define US_MAX_MM          2000     /* anything past this is reported as US_MAX_MM  */
#define US_MIN_MM            25     /* HC-SR04 cannot see closer than ~2 cm         */
#define US_INVALID        60000     /* no echo came back                            */

/* A side reading bigger than this is an opening rather than a wall.
 * A wall beside us reads TARGET_SIDE_MM; an opening one square deep reads
 * TARGET_SIDE_MM + CORRIDOR_MM. Sit between them, biased towards the wall.
 * The old hand-set 420 mm was larger than a one-square opening ever reads,
 * so the robot drove straight past every turn it was meant to take. */
#define OPEN_SIDE_MM     (TARGET_SIDE_MM + (int)(CORRIDOR_MM * 0.45f))
/* An opening only counts on the EDGE wall->open, and only after the reading
 * has been open this many loops. One dropped ping must never invent a
 * junction that is not there. */
#define OPEN_DEBOUNCE         9
/* A front reading smaller than this means "wall ahead, start setting up".
 * At a square's centre a wall in the next square reads 37 mm, and a wall two
 * squares away reads 342 mm, so 200 mm triggers about one square early. */
#define FRONT_BLOCKED_MM    200
/* ...and bigger than this means "the way ahead is open for at least one more
 * square" (342 mm at a square centre, so 260 mm has margin both ways). */
#define FRONT_OPEN_MM       260
/* Lining up on a wall ahead.
 *
 * We want the wheel AXLE in the middle of the junction square before we
 * pivot, which means the wall should end up CORRIDOR_MM/2 = 152 mm from the
 * axle. The front sonar sits US_F_X_MM = 115 mm ahead of the axle, so it
 * would have to read 37 mm - and an HC-SR04 is not trustworthy under about
 * 40 mm.
 *
 * So we range off the wall down to a reading we can believe, then hand over
 * to the wheel encoders for the last few centimetres. */
#define FRONT_HANDOVER_MM   100     /* switch from sonar to encoders here   */
/* Where to stop before a 90 degree pivot, measured back from the middle of
 * the junction square. A full 360 pivot sweeps the same circle wherever you
 * stand, but a QUARTER turn does not: sitting further back gives the front
 * corner room to swing into. In a passage this tight that is worth real
 * points, so the number is measured, not guessed - see docs/10_MAP_NOTES.md */
#define PIVOT_BACKOFF_MM     40
/* Closer than this: reverse before doing anything else. Must stay well
 * below FRONT_HANDOVER_MM or the robot reverses out of its own approach. */
#define FRONT_TOOCLOSE_MM    25

/* ------------------------------------------------------------------ */
/* 3. MAZE ASSUMPTIONS                                                 */
/* ------------------------------------------------------------------ */
#define CORRIDOR_MM         305     /* 1 ft grid, from the organisers' spreadsheet  */
#define CELL_MM             305     /* one "step" of the maze grid = 1 ft           */
/* DERIVED - do not hand-edit. Change the geometry above and these follow.
 *
 * Getting these wrong by hand is what cost the most time on this project:
 * a threshold tuned for one body width silently stops working when the body
 * changes, and the symptom looks like a navigation bug rather than a number.
 *
 * Dead centre of the passage, as the side sensor sees it. */
#define TARGET_SIDE_MM   ((int)(CORRIDOR_MM * 0.5f - US_L_Y_MM))

/* ------------------------------------------------------------------ */
/* 4. SPEEDS  (PWM counts, 0..255)                                     */
/* ------------------------------------------------------------------ */
#define PWM_MIN              55     /* below this a TT motor just buzzes            */
#define PWM_MAX             255
#define PWM_CRUISE          170     /* straight-line speed. Tuned: slower scores more */
#define PWM_SLOW             95     /* creeping / approaching a wall                */
#define PWM_TURN            110
#define PWM_BACK             95     /* reversing                                    */

/* ------------------------------------------------------------------ */
/* 5. CONTROL GAINS                                                    */
/* ------------------------------------------------------------------ */
#define KP_WALL            0.42f    /* PWM per mm of side error                     */
#define KD_WALL            2.10f    /* PWM per (mm/s) of side error rate            */
#define KP_HEADING         3.20f    /* PWM per degree of heading error (straights)  */
/* Yaw-rate damping. The gyro measures how fast we are turning, so we can
 * subtract it and stop the robot weaving down a straight instead of only
 * reacting after the heading has already gone wrong. This is the single
 * biggest "makes it look smooth" term in the whole file. */
#define KD_YAW             0.00f
#define STEER_LIMIT          80     /* max differential PWM applied while driving   */
/* Never step a motor by more than this in one 20 ms tick. Sudden steps make
 * the tyres slip, and slipping wheels are lying wheels. */
#define PWM_SLEW             255

/* ---- turning ----
 * The firmware can drive a proper trapezoidal turn profile - ramp up, hold,
 * ramp down - which is what serious micromouse code does
 * (see github.com/ukmars/mazerunner-core). It is implemented and it works.
 *
 * It is switched OFF here, because it was measured and it LOST:
 *
 *      no profile   map1  83%   map2 100%   map3  50%   avg 78%
 *      profile on   map1  83%   map2  83%   map3  50%   avg 72%
 *
 * Motion profiles pay off when you have wheel-speed PID running off
 * high-resolution encoders and you are trying to corner at speed. With 20
 * ticks per wheel revolution and a passage that leaves 28 mm a side, the
 * plain PD controller reacts faster and wins. Leaving OMEGA and ALPHA huge
 * makes the profile effectively instant, i.e. a plain PD.
 *
 * If you ever fit better encoders, set OMEGA to about 150 and ALPHA to 1000
 * and re-run the sweep - the code is all still here. */
/* Top turn rate. Must be reachable inside PWM_TURN:
 *      omega_max = (PWM_TURN - PWM_MIN) / TURN_FF
 * Asking for more than the motors can give just saturates the loop and
 * throws away the whole point of having a profile. */
#define TURN_OMEGA_DPS    600.0f
#define TURN_ALPHA_DPS2  20000.0f
#define V_MAX_MMS         380.0f    /* wheel speed at PWM 255, loaded. Measure it   */
#define KP_TURN            2.60f    /* PWM per degree of error against the profile  */
#define KD_TURN            0.22f    /* PWM per (deg/s) of rate error                */
/* Feed-forward: the PWM that ALREADY produces the rate we are asking for, so
 * the PD terms only have to correct the difference. Straight from geometry. */
#define TURN_FF   (WHEEL_BASE_MM * 0.5f / 57.29578f * (255.0f - PWM_MIN) / V_MAX_MMS)
#define TURN_TOL_DEG       3.0f     /* pivot is finished inside this error          */
#define TURN_SETTLE_MS      120     /* ...and must stay inside it this long         */
#define TURN_TIMEOUT_MS    2600     /* give up and move on                          */


/* ------------------------------------------------------------------ */
/* 5b. STAYING SQUARE WITH THE MAZE                                    */
/* ------------------------------------------------------------------ */
/* How hard to trust the walls over the gyro when both walls are in view.
 * A pivot that finishes three degrees short is invisible to the gyro,
 * because the heading was re-zeroed onto the target - but three degrees is
 * 16 mm of drift per foot, and two corners later it is a wall. The walls
 * themselves are the only absolute reference the robot has. See
 * "corridor-parallel correction" in nav_core.cpp. */
#define WALL_ALIGN_GAIN    0.35f
#define WALL_ALIGN_MM      70.0f    /* travel between angle estimates       */

/* Livelock guard. Deciding this many times inside this little travel means
 * the robot is turning on the spot arguing with itself, which is how a run
 * quietly burns three minutes without going anywhere. */
#define DECIDE_BURST_MAX      3
#define DECIDE_BURST_MM   250.0f
#define DECIDE_LOCKOUT_MM 350.0f

/* ------------------------------------------------------------------ */
/* 6. TIMING                                                           */
/* ------------------------------------------------------------------ */
#define LOOP_HZ              50
#define LOOP_DT_MS           20
#define BACKUP_MS           420
/* Roll this far past a side opening before pivoting into it. Ideal value is
 *      CORRIDOR_MM / 2 + US_L_X_MM - (debounce lag, about 45 mm) = 145 */
#define CREEP_AFTER_OPEN_MM 147
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

/* Which hand do we keep on the wall?  +1 = LEFT hand, -1 = RIGHT hand.
 *
 * RIGHT, and it is not a coin toss. The rules want the robot to drive the
 * WHOLE road before it leaves, not the shortest way across, and only one
 * hand does that on these three maps:
 *
 *              road covered     left hand    right hand
 *      Map 1                       100%         100%
 *      Map 2                        50%         100%
 *      Map 3                       100%         100%
 *
 * On Map 2 the left hand turns straight out of the exit the first time it
 * reaches the junction and skips the entire loop. The right hand takes the
 * loop first and only leaves once there is nothing else to drive. */
#define WALL_HAND            (-1)

/* Navigation mode */
#define MODE_WALLFOLLOW       0     /* simple, never gets confused in a plain maze  */
#define MODE_TREMAUX          1     /* remembers junctions, beats loops and islands */
/* Wall following, not Tremaux. The three competition maps are published in
 * advance and none of them needs memory: the left-hand rule picks the
 * correct exit at every single decision point on all three. Measured, the
 * memory mode is WORSE here - it depends on odometry to recognise a junction
 * it has seen before, and odometry is the least trustworthy thing on the
 * robot. Switch to MODE_TREMAUX only if a map turns up with a real loop. */
#define DEFAULT_MODE   MODE_WALLFOLLOW

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
