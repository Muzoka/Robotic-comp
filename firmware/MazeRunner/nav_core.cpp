/*
 * nav_core.cpp - navigation brain, shared by the Arduino and the simulator.
 * Plain C++ only. No Arduino API. No dynamic memory.
 */
#include "nav_core.h"
#include "config.h"
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#define DEG2RAD (float)(M_PI / 180.0)
#define RAD2DEG (float)(180.0 / M_PI)

/* ------------------------------------------------------------------ */
/* small helpers                                                       */
/* ------------------------------------------------------------------ */
static float wrap180(float a)
{
    while (a > 180.0f)  a -= 360.0f;
    while (a < -180.0f) a += 360.0f;
    return a;
}

static int16_t clamp16(float v, int16_t lo, int16_t hi)
{
    if (v < (float)lo) return lo;
    if (v > (float)hi) return hi;
    return (int16_t)v;
}

/* A TT motor does nothing below PWM_MIN. Push small commands up to the
 * threshold so the PD loop keeps authority instead of silently dying. */
static int16_t deadband(int16_t v)
{
    if (v == 0) return 0;
    if (v > 0 && v < PWM_MIN)  return PWM_MIN;
    if (v < 0 && v > -PWM_MIN) return -PWM_MIN;
    return v;
}

/* direction index: 0 = +X (the way we faced at the start), 1 = +Y (left),
 * 2 = -X, 3 = -Y. */
static uint8_t dir_of_heading(float h)
{
    int d = (int)floorf((wrap180(h) + 45.0f) / 90.0f);
    d &= 3;
    return (uint8_t)d;
}

/* ------------------------------------------------------------------ */
/* Tremaux junction memory - 4 bytes per junction, lives in SRAM and is  */
/* mirrored into the Uno's built-in 1 kB EEPROM by the .ino.            */
/* ------------------------------------------------------------------ */
/* 4 bytes each. Position is stored in units of 50 mm, which covers a 6 m
 * maze in a signed byte and is finer than we can navigate anyway. */
typedef struct {
    int8_t  qx, qy;      /* position / 50 mm                              */
    uint8_t marks;       /* 2 bits per direction, value 0..2              */
    uint8_t used;
} Junction;
#define JUNC_UNIT_MM   50.0f
#define JUNC_MATCH_MM 260.0f

typedef struct {
    /* configuration */
    uint8_t mode;
    int8_t  hand;              /* +1 left-hand rule, -1 right-hand rule   */

    /* state machine */
    uint8_t state;
    uint32_t t_ms;             /* time since nav_reset                    */
    uint32_t state_t_ms;       /* time in current state                   */
    uint32_t run_t_ms;         /* time since the run actually started     */

    /* odometry */
    int32_t prev_tl, prev_tr;
    uint8_t odom_primed;
    float   gyro_bias;         /* dps, re-estimated every time we stop     */
    float   bias_acc;
    uint16_t bias_n;
    uint32_t still_ms;
    float   x_mm, y_mm;        /* position, start pose = (0,0)            */
    float   heading;           /* degrees, continuous                     */
    float   heading_ref;       /* gyro reading that corresponds to 0 deg  */
    float   dist_total_mm;
    float   dist_since_decision_mm;
    float   dist_open_mm;      /* how far we have driven fully in the open */
    float   last_d_mm;         /* |distance| covered in the last tick      */

    /* driving */
    float   target_deg;        /* heading we want to hold, multiple of 90 */
    float   prev_side_err;
    float   creep_target_mm;
    float   backup_start_mm;

    /* turning */
    float   turn_from_deg;
    uint32_t turn_ok_ms;
    uint8_t  turn_retries;
    uint8_t  resume_turn;      /* back up, then finish the turn we started */
    int16_t  last_cmd_mag;

    /* decision snapshot, captured the instant we spot a junction */
    uint8_t snap_left, snap_front, snap_right;
    uint8_t open_cnt_l, open_cnt_r;   /* debounce integrators              */
    uint8_t open_l, open_r;           /* debounced "there is a gap" flags  */
    uint8_t creep_by_front;           /* aligning on a wall, not on odometry */

    /* stuck detector */
    int32_t stuck_tl, stuck_tr;
    uint32_t stuck_ms;
    uint8_t  stuck_escapes;

    /* floor line sensor */
    uint8_t  line_prev;
    uint16_t sectors;
    uint32_t last_edge_ms;
    uint8_t  edge_burst;

    /* memory */
    Junction junc[MAX_JUNCTIONS];
    uint8_t  njunc;
    uint8_t  last_dir;

    /* misc */
    uint8_t  first_decision_done;
    uint8_t  start_armed;
    uint32_t arm_ms;
    uint8_t  done;
} Nav;

static Nav g;

/* ------------------------------------------------------------------ */
/* Find the junction we are standing in.
 *
 * Matching is by proximity, not by an exact cell index, because after a
 * few metres the encoders have drifted and an exact match would file the
 * same corner twice and the memory would be worthless.
 *
 * The useful side effect: when we DO recognise a junction, we trust the
 * position we recorded the first time and snap the odometry back onto it.
 * That is loop closure, and it stops drift accumulating lap after lap. */
static Junction *junction_at(float x, float y, uint8_t create)
{
    Junction *best = 0;
    float best_d2 = JUNC_MATCH_MM * JUNC_MATCH_MM;

    for (uint8_t i = 0; i < g.njunc; i++) {
        if (!g.junc[i].used) continue;
        float dx = (float)g.junc[i].qx * JUNC_UNIT_MM - x;
        float dy = (float)g.junc[i].qy * JUNC_UNIT_MM - y;
        float d2 = dx * dx + dy * dy;
        if (d2 < best_d2) { best_d2 = d2; best = &g.junc[i]; }
    }
    if (best) {
        if (create) {
            g.x_mm = (float)best->qx * JUNC_UNIT_MM;
            g.y_mm = (float)best->qy * JUNC_UNIT_MM;
        }
        return best;
    }
    if (!create || g.njunc >= MAX_JUNCTIONS) return 0;
    Junction *j = &g.junc[g.njunc++];
    j->qx = (int8_t)lroundf(x / JUNC_UNIT_MM);
    j->qy = (int8_t)lroundf(y / JUNC_UNIT_MM);
    j->marks = 0; j->used = 1;
    return j;
}

static uint8_t mark_get(const Junction *j, uint8_t dir)
{
    return (uint8_t)((j->marks >> (dir * 2)) & 0x3);
}

static void mark_inc(Junction *j, uint8_t dir)
{
    uint8_t v = mark_get(j, dir);
    if (v < 2) v++;
    j->marks = (uint8_t)((j->marks & ~(0x3 << (dir * 2))) | (v << (dir * 2)));
}

/* ------------------------------------------------------------------ */
NAV_API void nav_reset(uint8_t mode, int8_t hand)
{
    memset(&g, 0, sizeof(g));
    g.mode  = mode;
    g.hand  = (hand >= 0) ? +1 : -1;
    g.state = ST_BOOT;
    g.target_deg = 0.0f;
}

/* ------------------------------------------------------------------ */
static void odom_update(const NavIn *in)
{
    if (!g.odom_primed) {
        g.prev_tl = in->ticks_left;
        g.prev_tr = in->ticks_right;
        g.heading_ref = in->heading_deg;
        g.odom_primed = 1;
        return;
    }

    float dl = (float)(in->ticks_left  - g.prev_tl) * ENC_MM_PER_TICK;
    float dr = (float)(in->ticks_right - g.prev_tr) * ENC_MM_PER_TICK;
    g.prev_tl = in->ticks_left;
    g.prev_tr = in->ticks_right;

    float d = 0.5f * (dl + dr);

    /* Pivoting in place must not move the position estimate. The two wheels
     * are never perfectly matched, so (dl+dr)/2 comes out a few millimetres
     * short of zero on every single turn, and forty turns later the robot
     * thinks it is a quarter of a metre from where it is. Detect the pivot
     * and throw the translation away. */
    {
        float adl = dl < 0 ? -dl : dl;
        float adr = dr < 0 ? -dr : dr;
        float ad  = d  < 0 ? -d  : d;
        if (ad < 0.35f * (adl + adr)) d = 0.0f;
    }

#if HAS_GYRO
    /* Integrate the gyro here rather than in the hardware layer, so the
     * drift handling is part of the code the simulator tests.
     *
     * Two things keep an MPU-6050 honest over a four minute run:
     *   - re-measure the zero-rate bias every time we are standing still,
     *     which happens for a moment before every single pivot;
     *   - a deadband, so the noise floor cannot random-walk the heading
     *     while we drive down a straight.
     * Without both, the bias alone is worth 15-20 degrees per run, and a
     * robot 20 degrees out of square wedges itself in the first corner. */
    if (g.last_cmd_mag == 0) {
        g.still_ms += in->dt_ms;
        if (g.still_ms > 150) {              /* let the chassis stop ringing */
            g.bias_acc += in->gyro_rate_dps;
            g.bias_n++;
        }
    } else {
        if (g.bias_n > 4) {
            float est = g.bias_acc / (float)g.bias_n;
            g.gyro_bias += 0.5f * (est - g.gyro_bias);
        }
        g.bias_acc = 0.0f; g.bias_n = 0; g.still_ms = 0;
    }

    float rate = in->gyro_rate_dps - g.gyro_bias;
    if (rate > -0.40f && rate < 0.40f) rate = 0.0f;
    g.heading = wrap180(g.heading + rate * (in->dt_ms / 1000.0f));
#else
    g.heading = wrap180(g.heading + (dr - dl) / WHEEL_BASE_MM * RAD2DEG);
#endif

    float hr = g.heading * DEG2RAD;
    g.x_mm += d * cosf(hr);
    g.y_mm += d * sinf(hr);

    if (d < 0) d = -d;
    g.last_d_mm                = d;
    g.dist_total_mm           += d;
    g.dist_since_decision_mm  += d;
}

/* Count black floor marks. Each sector line gives one black->white edge.
 * A start/finish gate is painted as stripes, so it gives a fast burst of
 * edges - that is how we know we are out. */
static void line_update(const NavIn *in)
{
#if HAS_LINE_SENSOR
    if (in->line_black != g.line_prev) {
        if (g.line_prev == 1) {          /* leaving black = crossed a mark */
            g.sectors++;
        }
        if (g.t_ms - g.last_edge_ms < 350) {
            if (g.edge_burst < 255) g.edge_burst++;
        } else {
            g.edge_burst = 0;
        }
        g.last_edge_ms = g.t_ms;
        g.line_prev = in->line_black;
    }
#else
    (void)in;
#endif
}

/* ------------------------------------------------------------------ */
/* straight-line steering: centre in the corridor, hug one wall if only  */
/* one is there, and always let the gyro veto long-term drift.           */
/* ------------------------------------------------------------------ */
static float steer_command(const NavIn *in, float dt_s)
{
    uint8_t have_l = (in->dist_left_mm  < OPEN_SIDE_MM);
    uint8_t have_r = (in->dist_right_mm < OPEN_SIDE_MM);

    /* Sign convention, and it matters: side_err > 0 means "we are too far
     * to the LEFT and need to move right". All three cases below have to
     * agree on that, and the steering term is then subtracted. */
    float side_err = 0.0f;
    uint8_t side_valid = 1;

    if (have_l && have_r) {
        side_err = (float)in->dist_right_mm - (float)in->dist_left_mm;
        side_err *= 0.5f;
    } else if (have_l) {
        side_err = (float)TARGET_SIDE_MM - (float)in->dist_left_mm;
    } else if (have_r) {
        side_err = (float)in->dist_right_mm - (float)TARGET_SIDE_MM;
    } else {
        side_valid = 0;
    }

    float steer = 0.0f;
    if (side_valid) {
        float derr = (side_err - g.prev_side_err) / (dt_s > 0.0f ? dt_s : 0.02f);
        /* clamp the derivative: a sonar dropout must not slam the wheels */
        if (derr >  600.0f) derr =  600.0f;
        if (derr < -600.0f) derr = -600.0f;
        steer = -(KP_WALL * side_err + KD_WALL * (derr * 0.001f));
        g.prev_side_err = side_err;
    } else {
        g.prev_side_err = 0.0f;
    }

    /* Heading hold. With walls present it is a gentle trim; with no walls
     * it is the only thing keeping us straight. */
    float herr = wrap180(g.target_deg - g.heading);
    float hterm = KP_HEADING * herr;
    steer += side_valid ? (hterm * 0.35f) : hterm;

    if (steer >  (float)STEER_LIMIT) steer =  (float)STEER_LIMIT;
    if (steer < -(float)STEER_LIMIT) steer = -(float)STEER_LIMIT;
    return steer;
}

/* ------------------------------------------------------------------ */
/* choose where to go at a junction                                     */
/* ------------------------------------------------------------------ */
/* returns a turn in units of 90 deg: +1 left, 0 straight, -1 right, 2 = U */
static int8_t choose_turn(void)
{
    uint8_t openL = g.snap_left;
    uint8_t openF = g.snap_front;
    uint8_t openR = g.snap_right;

    if (g.mode == MODE_WALLFOLLOW) {
        if (g.hand > 0) {                       /* left-hand rule */
            if (openL) return +1;
            if (openF) return  0;
            if (openR) return -1;
            return 2;
        } else {                                /* right-hand rule */
            if (openR) return -1;
            if (openF) return  0;
            if (openL) return +1;
            return 2;
        }
    }

    /* ---- Tremaux: prefer the passage we have used least ---- */
    uint8_t here = dir_of_heading(g.heading);
    Junction *j = junction_at(g.x_mm, g.y_mm, 1);
    if (!j) {                       /* memory full: fall back to the hand rule */
        if (g.hand > 0) { if (openL) return +1; if (openF) return 0; if (openR) return -1; }
        else            { if (openR) return -1; if (openF) return 0; if (openL) return +1; }
        return 2;
    }

    /* mark the passage we arrived through */
    mark_inc(j, (uint8_t)((here + 2) & 3));

    /* At the very first junction, the passage behind us is the start gate.
     * Burn it to "fully used" so the robot will only ever go back out of
     * its own start line if literally everything else has been tried. A
     * wall follower that laps the outer ring and calmly drives back out of
     * the front door is the single most common way to score nothing. */
    if (!g.first_decision_done) {
        g.first_decision_done = 1;
        mark_inc(j, (uint8_t)((here + 2) & 3));
        mark_inc(j, (uint8_t)((here + 2) & 3));
    }

    /* candidates, in hand-rule preference order so ties break the way a
     * plain wall follower would - that keeps the path short and tidy */
    int8_t  order[4];
    uint8_t opn[4];
    if (g.hand > 0) {
        order[0] = +1; opn[0] = openL;
        order[1] =  0; opn[1] = openF;
        order[2] = -1; opn[2] = openR;
    } else {
        order[0] = -1; opn[0] = openR;
        order[1] =  0; opn[1] = openF;
        order[2] = +1; opn[2] = openL;
    }
    order[3] = 2; opn[3] = 1;       /* turning round is always possible */

    int8_t  best = 2;
    uint8_t best_marks = 99;
    for (uint8_t i = 0; i < 4; i++) {
        if (!opn[i]) continue;
        uint8_t d;
        if (order[i] == 2) d = (uint8_t)((here + 2) & 3);
        else               d = (uint8_t)((here + (int)order[i] + 4) & 3);
        uint8_t m = mark_get(j, d);
        if (m < best_marks) { best_marks = m; best = order[i]; }
    }

    uint8_t chosen = (best == 2) ? (uint8_t)((here + 2) & 3)
                                 : (uint8_t)((here + (int)best + 4) & 3);
    mark_inc(j, chosen);
    return best;
}

/* ------------------------------------------------------------------ */
static void enter_turn(int8_t quarters)
{
    g.turn_from_deg = g.heading;
    if (quarters == 2) g.target_deg = wrap180(g.target_deg + 180.0f);
    else               g.target_deg = wrap180(g.target_deg + 90.0f * (float)quarters);
    g.state = ST_TURN;
    g.state_t_ms = 0;
    g.turn_ok_ms = 0;
    g.prev_side_err = 0.0f;
}

static void snapshot(const NavIn *in)
{
    g.snap_left  = g.open_l;
    g.snap_right = g.open_r;
    g.snap_front = (in->dist_front_mm > (uint16_t)(FRONT_BLOCKED_MM + 150)) ? 1 : 0;
}

/* Debounce the side readings into steady "there is a gap here" flags, and
 * report the rising edge. Level-triggering would fire the instant the robot
 * rolls out of the start gate into open floor, before it has seen a single
 * wall - which is exactly the failure that eats a run in the first second. */
static void openings_update(const NavIn *in)
{
    uint8_t raw_l = (in->dist_left_mm  > OPEN_SIDE_MM);
    uint8_t raw_r = (in->dist_right_mm > OPEN_SIDE_MM);

    if (raw_l) { if (g.open_cnt_l < 12) g.open_cnt_l++; }
    else       { if (g.open_cnt_l > 0)  g.open_cnt_l--; }
    if (raw_r) { if (g.open_cnt_r < 12) g.open_cnt_r++; }
    else       { if (g.open_cnt_r > 0)  g.open_cnt_r--; }

    if (g.open_cnt_l >= OPEN_DEBOUNCE) g.open_l = 1;
    else if (g.open_cnt_l <= 3)        g.open_l = 0;
    if (g.open_cnt_r >= OPEN_DEBOUNCE) g.open_r = 1;
    else if (g.open_cnt_r <= 3)        g.open_r = 0;
}

/* An opening seen on the way in stays remembered, because by the time the
 * axle reaches the junction the side sensor may already be past the gap. */
static void snapshot_merge(const NavIn *in)
{
    if (g.open_l) g.snap_left  = 1;
    if (g.open_r) g.snap_right = 1;
    g.snap_front = (in->dist_front_mm > (uint16_t)(FRONT_BLOCKED_MM + 150)) ? 1 : 0;
}

/* ------------------------------------------------------------------ */
NAV_API void nav_step(const NavIn *in, NavOut *out)
{
    float dt_s = (in->dt_ms > 0) ? (in->dt_ms / 1000.0f) : 0.02f;
    g.t_ms       += in->dt_ms;
    g.state_t_ms += in->dt_ms;

    odom_update(in);
    line_update(in);

    uint8_t was_open_l = g.open_l, was_open_r = g.open_r;
    openings_update(in);
    uint8_t edge_l = (g.open_l && !was_open_l);
    uint8_t edge_r = (g.open_r && !was_open_r);

    /* --- wedged? --- Motors commanded, wheels not turning: something is
     * jammed against a wall. This has to be watched in every moving state,
     * not just while driving straight - a robot that jams mid-pivot is the
     * classic way to lose a run. */
    uint8_t moving = (g.state == ST_DRIVE || g.state == ST_CREEP ||
                      g.state == ST_BACKUP || g.state == ST_TURN);
    if (moving && g.last_cmd_mag >= PWM_MIN) {
        if (in->ticks_left == g.stuck_tl && in->ticks_right == g.stuck_tr) {
            g.stuck_ms += in->dt_ms;
        } else {
            g.stuck_ms = 0;
            g.stuck_tl = in->ticks_left;
            g.stuck_tr = in->ticks_right;
        }
    } else {
        g.stuck_ms = 0;
        g.stuck_tl = in->ticks_left;
        g.stuck_tr = in->ticks_right;
    }
    if (g.stuck_ms > STUCK_WINDOW_MS) {
        g.stuck_ms = 0;
        g.stuck_escapes++;
        g.resume_turn = 0;
        g.backup_start_mm = g.dist_total_mm;
        g.state = ST_STUCK_RECOVER;
        g.state_t_ms = 0;
    }

    int16_t base = 0;
    float   steer = 0.0f;

    switch (g.state) {

    /* ---------------------------------------------------------- */
    case ST_BOOT:
        g.state = ST_WAIT_START;
        g.state_t_ms = 0;
        break;

    /* Autonomous start: hold a hand ~5 cm in front of the nose, then take
     * it away. No radio, no laptop, nothing to touch.
     *
     * The length of the hold also picks which wall we follow, so you can
     * change strategy at the start line after looking at the map without
     * opening a laptop:
     *      quick tap  (< 1.5 s)  -> LEFT-hand rule
     *      long hold  (> 1.5 s)  -> RIGHT-hand rule
     * The countdown then blinks slow for left, fast for right. */
    case ST_WAIT_START:
        if (in->dist_front_mm < 80) {
            g.start_armed = 1;
            g.arm_ms += in->dt_ms;
        } else if (g.start_armed && in->dist_front_mm > 200) {
            g.hand = (g.arm_ms >= 1500) ? -1 : +1;
            g.state = ST_COUNTDOWN; g.state_t_ms = 0;
        }
        if (in->start_signal) { g.state = ST_COUNTDOWN; g.state_t_ms = 0; }
        break;

    case ST_COUNTDOWN:
        /* three seconds of blinking so the judges can see it is autonomous */
        if (g.state_t_ms >= 3000) {
            /* zero everything here: this pose is the origin of the run */
            g.heading = 0.0f;
            g.target_deg = 0.0f;
            g.x_mm = g.y_mm = 0.0f;
            g.dist_total_mm = g.dist_since_decision_mm = 0.0f;

            /* The way we came in is the start gate, not the finish. Burn it
             * into the memory as "already used twice" so the robot never
             * turns round and drives back out of its own start line - which
             * is exactly how a wrong-handed wall follower loses a run. */
            g.state = ST_DRIVE; g.state_t_ms = 0;
        }
        break;

    /* ---------------------------------------------------------- */
    case ST_DRIVE: {
        g.run_t_ms += in->dt_ms;

        /* --- are we out of the maze? ---
         * Open on every side AND well away from where we started, so
         * reversing back out of the start gate is never mistaken for a
         * finish. */
        float from_origin = sqrtf(g.x_mm * g.x_mm + g.y_mm * g.y_mm);
        uint8_t wide_open = (in->dist_front_mm > 700 &&
                             in->dist_left_mm  > 700 &&
                             in->dist_right_mm > 700 &&
                             from_origin > 800.0f);
        if (wide_open && g.dist_total_mm > 600.0f) {
            g.dist_open_mm += g.last_d_mm;
            if (g.dist_open_mm > 450.0f) { g.state = ST_FINISH; g.state_t_ms = 0; break; }
        } else {
            g.dist_open_mm = 0.0f;
        }
        /* a burst of stripes under the nose is the finish gate */
        if (g.edge_burst >= 4 && from_origin > 800.0f) {
            g.state = ST_FINISH; g.state_t_ms = 0; break;
        }
        if (g.run_t_ms > RUN_TIMEOUT_MS) { g.state = ST_FINISH; g.state_t_ms = 0; break; }

        /* --- junction? ---
         * Two ways to notice one: a wall appears ahead, or a side wall
         * that was there a moment ago is suddenly not. Either way we do
         * NOT pivot here - we creep until the wheel axle is in the middle
         * of the junction square, and pivot from there. */
        if (in->dist_front_mm < FRONT_TOOCLOSE_MM) {
            snapshot(in);
            g.backup_start_mm = g.dist_total_mm;
            g.state = ST_BACKUP; g.state_t_ms = 0;
            break;
        }

        if (in->dist_front_mm < FRONT_BLOCKED_MM) {
            snapshot(in);
            g.creep_by_front = 1;
            g.creep_target_mm = g.dist_total_mm + 600.0f;   /* safety stop */
            g.state = ST_CREEP; g.state_t_ms = 0;
            break;
        }

        if ((edge_l || edge_r) && g.dist_since_decision_mm > (float)CELL_MM * 0.5f) {
            snapshot(in);
            if (edge_l) g.snap_left = 1;
            if (edge_r) g.snap_right = 1;
            g.creep_by_front = 0;
            g.creep_target_mm = g.dist_total_mm + (float)CREEP_AFTER_OPEN_MM;
            g.state = ST_CREEP; g.state_t_ms = 0;
            break;
        }

        /* --- normal driving --- */
        base  = PWM_CRUISE;
        if (in->dist_front_mm < 320) base = PWM_SLOW;   /* ease into corners */
        steer = steer_command(in, dt_s);
        break;
    }

    /* ---------------------------------------------------------- */
    /* Line the wheel axle up with the middle of the junction, then decide.
     * If a wall is ahead we range off it, which is far more accurate than
     * dead reckoning; otherwise we count millimetres off the encoders. */
    case ST_CREEP: {
        base  = PWM_SLOW;
        steer = steer_command(in, dt_s);

        if (in->dist_front_mm < FRONT_TOOCLOSE_MM) {
            g.backup_start_mm = g.dist_total_mm;
            g.state = ST_BACKUP; g.state_t_ms = 0;
            break;
        }
        /* keep watching the sides while we roll in - a gap can open up
         * during the creep itself */
        if (edge_l) g.snap_left = 1;
        if (edge_r) g.snap_right = 1;

        /* Sonar gets us close, encoders finish the job. Once the wall is
         * near enough to measure accurately, work out exactly how much
         * further the axle has to travel and count it off the wheels. */
        if (g.creep_by_front && in->dist_front_mm <= FRONT_HANDOVER_MM) {
            float remain = (float)in->dist_front_mm + US_F_X_MM
                         - ((float)CORRIDOR_MM * 0.5f + (float)PIVOT_BACKOFF_MM);
            if (remain < 0.0f) remain = 0.0f;
            g.creep_target_mm = g.dist_total_mm + remain;
            g.creep_by_front = 0;
        }

        if ((!g.creep_by_front && g.dist_total_mm >= g.creep_target_mm)
                || g.state_t_ms > 2500) {
            snapshot_merge(in);
            int8_t q = choose_turn();
            g.dist_since_decision_mm = 0.0f;
            g.creep_by_front = 0;
            if (q == 0) { g.state = ST_DRIVE; g.state_t_ms = 0; }
            else        { enter_turn(q); }
        }
        break;
    }

    /* ---------------------------------------------------------- */
    case ST_BACKUP:
        base = -PWM_BACK;
        steer = 0.0f;
        if ((g.dist_total_mm - g.backup_start_mm) > 90.0f || g.state_t_ms > BACKUP_MS) {
            if (g.resume_turn) {
                /* we were mid-pivot and ran out of room; try again with
                 * some space behind us */
                g.resume_turn = 0;
                g.state = ST_TURN; g.state_t_ms = 0; g.turn_ok_ms = 0;
                break;
            }
            snapshot_merge(in);
            int8_t q = choose_turn();
            g.dist_since_decision_mm = 0.0f;
            if (q == 0) { g.state = ST_DRIVE; g.state_t_ms = 0; }
            else        { enter_turn(q); }
        }
        break;

    /* ---------------------------------------------------------- */
    case ST_TURN: {
        if (g.state_t_ms < TURN_SETTLE_IN_MS) {
            /* stand still for a moment: pivoting while still rolling
             * forward is what puts a corner of the chassis into a wall */
            out->pwm_left = 0; out->pwm_right = 0;
            g.last_cmd_mag = 0;
            out->state = g.state; out->done = 0; out->led = 1;
            out->sectors_seen = g.sectors;
            out->dbg_target_deg = g.target_deg; out->dbg_steer = 0.0f;
            return;
        }
        float err = wrap180(g.target_deg - g.heading);
        float ae  = err < 0 ? -err : err;
        int16_t t;
        if (ae < TURN_TOL_DEG) {
            /* Inside tolerance: command nothing. The motor deadband would
             * otherwise force 55 PWM here, the robot would hunt across the
             * target forever, the settle window would never be met and the
             * turn would time out a few degrees short - which is exactly how
             * a robot ends up crabbing into the next wall. */
            t = 0;
        } else {
            float cmd = KP_TURN * err - KD_TURN * in->gyro_rate_dps;
            t = clamp16(cmd, -PWM_TURN, PWM_TURN);
            t = deadband(t);
        }
        g.last_cmd_mag = (t < 0) ? (int16_t)(-t) : t;
        out->pwm_left  = (int16_t)(-t);
        out->pwm_right = (int16_t)(+t);

        if (ae < TURN_TOL_DEG) {
            g.turn_ok_ms += in->dt_ms;
        } else {
            g.turn_ok_ms = 0;
        }
        if (g.state_t_ms > TURN_TIMEOUT_MS && g.turn_ok_ms < TURN_SETTLE_MS) {
            /* Out of time and still not pointing the right way: almost
             * always a corner of the body touching a wall. Reverse a little
             * and finish the same turn rather than setting off at an angle. */
            if (g.turn_retries < 2) {
                g.turn_retries++;
                g.resume_turn = 1;
                g.backup_start_mm = g.dist_total_mm;
                g.state = ST_BACKUP; g.state_t_ms = 0;
            } else {
                g.turn_retries = 0;
                g.target_deg = 90.0f * lroundf(g.heading / 90.0f);
                g.prev_side_err = 0.0f;
                g.dist_since_decision_mm = 0.0f;
                g.state = ST_DRIVE; g.state_t_ms = 0;
            }
        } else if (g.turn_ok_ms >= TURN_SETTLE_MS) {
            /* snap the target to the nearest quarter turn so gyro drift can
             * never accumulate from one corner to the next */
            g.turn_retries = 0;
            g.target_deg = 90.0f * lroundf(g.target_deg / 90.0f);
            /* We have just finished lining up with a corridor, so this is
             * the most trustworthy heading we will ever have. Call it exact
             * and the gyro's error stops accumulating from corner to
             * corner - it only ever has to survive one turn. */
            g.heading = g.target_deg;
            g.prev_side_err = 0.0f;
            g.dist_since_decision_mm = 0.0f;
            g.open_cnt_l = g.open_cnt_r = 0;
            g.open_l = g.open_r = 0;
            g.snap_left = g.snap_right = 0;
            g.state = ST_DRIVE; g.state_t_ms = 0;
        }
        out->state = g.state;
        out->done  = 0;
        out->led   = 1;
        out->sectors_seen = g.sectors;
        out->dbg_target_deg = g.target_deg;
        out->dbg_steer = 0.0f;
        return;                     /* turn writes its own PWM, skip the mixer */
    }

    /* ---------------------------------------------------------- */
    case ST_STUCK_RECOVER:
        base = -PWM_BACK;
        steer = (g.stuck_escapes & 1) ? 45.0f : -45.0f;
        if (g.state_t_ms > 600) {
            g.stuck_tl = in->ticks_left;
            g.stuck_tr = in->ticks_right;
            g.dist_since_decision_mm = 0.0f;
            g.state = ST_DRIVE; g.state_t_ms = 0;
        }
        break;

    /* ---------------------------------------------------------- */
    case ST_FINISH:
    default:
        base = 0; steer = 0.0f;
        g.done = 1;
        break;
    }

    /* ------------- mix and clamp ------------- */
    float l = (float)base - steer;
    float r = (float)base + steer;
    int16_t li = clamp16(l, -PWM_MAX, PWM_MAX);
    int16_t ri = clamp16(r, -PWM_MAX, PWM_MAX);
    if (base != 0) { li = deadband(li); ri = deadband(ri); }
    else           { li = 0; ri = 0; }

    g.last_cmd_mag = (int16_t)((li < 0 ? -li : li) > (ri < 0 ? -ri : ri)
                               ? (li < 0 ? -li : li) : (ri < 0 ? -ri : ri));
    out->pwm_left  = li;
    out->pwm_right = ri;
    out->state     = g.state;
    out->done      = g.done;
    /* countdown blink: slow = left-hand rule, fast = right-hand rule */
    uint16_t blink = (g.hand > 0) ? 400 : 130;
    out->led       = (g.state == ST_COUNTDOWN) ? (uint8_t)((g.state_t_ms / blink) & 1)
                                               : (uint8_t)(g.state == ST_FINISH);
    out->sectors_seen   = g.sectors;
    out->dbg_target_deg = g.target_deg;
    out->dbg_steer      = steer;
}

/* ------------------------------------------------------------------ */
NAV_API const char *nav_state_name(uint8_t s)
{
    switch (s) {
    case ST_BOOT:          return "BOOT";
    case ST_WAIT_START:    return "WAIT_START";
    case ST_COUNTDOWN:     return "COUNTDOWN";
    case ST_DRIVE:         return "DRIVE";
    case ST_CREEP:         return "CREEP";
    case ST_BACKUP:        return "BACKUP";
    case ST_TURN:          return "TURN";
    case ST_STUCK_RECOVER: return "STUCK";
    case ST_FINISH:        return "FINISH";
    default:               return "?";
    }
}

NAV_API int32_t  nav_odom_x_mm(void)     { return (int32_t)g.x_mm; }
NAV_API int32_t  nav_odom_y_mm(void)     { return (int32_t)g.y_mm; }
NAV_API int32_t  nav_junction_count(void){ return (int32_t)g.njunc; }
NAV_API uint32_t nav_memory_bytes(void)  { return (uint32_t)(g.njunc * sizeof(Junction)); }

NAV_API uint32_t nav_export_memory(uint8_t *buf, uint32_t buf_len)
{
    uint32_t need = (uint32_t)(g.njunc * sizeof(Junction));
    if (buf_len < need) return 0;
    memcpy(buf, g.junc, need);
    return need;
}

NAV_API void nav_import_memory(const uint8_t *buf, uint32_t buf_len)
{
    uint32_t n = buf_len / sizeof(Junction);
    if (n > MAX_JUNCTIONS) n = MAX_JUNCTIONS;
    memcpy(g.junc, buf, n * sizeof(Junction));
    g.njunc = (uint8_t)n;
}
