/*
 * nav_core.h - the robot's brain.
 *
 * THIS FILE CONTAINS NO ARDUINO CODE AT ALL.
 * It is plain C++ with only <stdint.h>, which means the exact same source
 * is compiled twice:
 *
 *   1. into MazeRunner.ino, which runs on the Arduino Uno
 *   2. into libnavcore.so, which the Python simulator drives
 *
 * So whatever behaviour you see in the simulator is, literally, the
 * behaviour of the firmware. Tune in sim, flash, drive.
 */
#ifndef NAV_CORE_H
#define NAV_CORE_H

#include <stdint.h>

#ifdef _WIN32
#define NAV_API extern "C" __declspec(dllexport)
#else
#define NAV_API extern "C"
#endif

/* ---------------- what the brain is told, every 20 ms ---------------- */
struct NavIn {
    uint16_t dist_front_mm;   /* US_MAX_MM when nothing is in range        */
    uint16_t dist_left_mm;
    uint16_t dist_right_mm;
    float    heading_deg;     /* continuous, CCW positive, 0 = start pose  */
    float    gyro_rate_dps;   /* yaw rate, CCW positive                    */
    int32_t  ticks_left;      /* cumulative, signed                        */
    int32_t  ticks_right;
    uint8_t  line_black;      /* 1 = floor sensor is over a black mark     */
    uint8_t  start_signal;    /* 1 = judge said go                         */
    uint16_t dt_ms;
};

/* ---------------- what the brain answers ---------------- */
struct NavOut {
    int16_t pwm_left;         /* -255 .. +255                              */
    int16_t pwm_right;
    uint8_t state;            /* NavState                                  */
    uint8_t done;             /* 1 = finished, stop the run                */
    uint8_t led;              /* 1 = light/beep                            */
    uint16_t sectors_seen;    /* black marks counted by the floor sensor    */
    float   dbg_target_deg;
    float   dbg_steer;
};

typedef enum {
    ST_BOOT = 0,
    ST_WAIT_START,
    ST_COUNTDOWN,
    ST_DRIVE,
    ST_CREEP,          /* rolling forward so the axle reaches the junction */
    ST_BACKUP,
    ST_TURN,
    ST_STUCK_RECOVER,
    ST_FINISH,
    ST_NUM_STATES
} NavState;

/* ---------------- API ---------------- */
NAV_API void        nav_reset(uint8_t mode, int8_t hand);
NAV_API void        nav_step(const NavIn *in, NavOut *out);
NAV_API const char *nav_state_name(uint8_t s);

/* Introspection, used by the simulator's telemetry log and by the
 * Arduino's serial debug output. */
NAV_API int32_t     nav_odom_x_mm(void);
NAV_API int32_t     nav_odom_y_mm(void);
NAV_API int32_t     nav_junction_count(void);
NAV_API uint32_t    nav_memory_bytes(void);

/* Tremaux memory, exposed so the .ino can mirror it into the Uno's
 * built-in 1 kB EEPROM (no external memory chip is needed). */
NAV_API uint32_t    nav_export_memory(uint8_t *buf, uint32_t buf_len);
NAV_API void        nav_import_memory(const uint8_t *buf, uint32_t buf_len);

#endif /* NAV_CORE_H */
