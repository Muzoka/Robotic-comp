"""
navcore.py - loads the REAL firmware brain (nav_core.cpp) as a shared
library and drives it with simulated sensor readings.

Nothing here re-implements the robot's logic. If the simulator turns left,
it is because the code that will be flashed onto the Uno decided to turn
left.
"""

import ctypes
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_FW = os.path.join(_HERE, "..", "firmware", "MazeRunner")
_LIB = os.path.join(_HERE, "libnavcore.so")
if sys.platform == "win32":
    _LIB = os.path.join(_HERE, "navcore.dll")
elif sys.platform == "darwin":
    _LIB = os.path.join(_HERE, "libnavcore.dylib")


class NavIn(ctypes.Structure):
    _fields_ = [
        ("dist_front_mm", ctypes.c_uint16),
        ("dist_left_mm", ctypes.c_uint16),
        ("dist_right_mm", ctypes.c_uint16),
        ("heading_deg", ctypes.c_float),
        ("gyro_rate_dps", ctypes.c_float),
        ("ticks_left", ctypes.c_int32),
        ("ticks_right", ctypes.c_int32),
        ("line_black", ctypes.c_uint8),
        ("start_signal", ctypes.c_uint8),
        ("dt_ms", ctypes.c_uint16),
    ]


class NavOut(ctypes.Structure):
    _fields_ = [
        ("pwm_left", ctypes.c_int16),
        ("pwm_right", ctypes.c_int16),
        ("state", ctypes.c_uint8),
        ("done", ctypes.c_uint8),
        ("led", ctypes.c_uint8),
        ("sectors_seen", ctypes.c_uint16),
        ("dbg_target_deg", ctypes.c_float),
        ("dbg_steer", ctypes.c_float),
    ]


def build(force=False):
    """Compile nav_core.cpp into a shared library."""
    src = os.path.join(_FW, "nav_core.cpp")
    if not force and os.path.exists(_LIB) and \
            os.path.getmtime(_LIB) > max(os.path.getmtime(src),
                                         os.path.getmtime(os.path.join(_FW, "config.h"))):
        return _LIB

    cxx = os.environ.get("CXX", "g++")
    cmd = [cxx, "-O2", "-fPIC", "-shared", "-std=c++11",
           "-Wall", "-Wextra", "-Wno-unused-parameter",
           "-I", _FW, src, "-o", _LIB, "-lm"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise RuntimeError("could not build nav_core - is g++ installed?")
    if r.stderr.strip():
        sys.stderr.write(r.stderr)
    return _LIB


class NavCore:
    def __init__(self, mode=1, hand=1, rebuild=False):
        build(force=rebuild)
        self.lib = ctypes.CDLL(_LIB)
        self.lib.nav_reset.argtypes = [ctypes.c_uint8, ctypes.c_int8]
        self.lib.nav_step.argtypes = [ctypes.POINTER(NavIn), ctypes.POINTER(NavOut)]
        self.lib.nav_state_name.restype = ctypes.c_char_p
        self.lib.nav_odom_x_mm.restype = ctypes.c_int32
        self.lib.nav_odom_y_mm.restype = ctypes.c_int32
        self.lib.nav_junction_count.restype = ctypes.c_int32
        self.lib.nav_memory_bytes.restype = ctypes.c_uint32
        self.inp = NavIn()
        self.out = NavOut()
        self.reset(mode, hand)

    def reset(self, mode=1, hand=1):
        self.lib.nav_reset(ctypes.c_uint8(mode), ctypes.c_int8(hand))

    def step(self, front, left, right, heading, rate, tl, tr, line, start, dt_ms):
        i = self.inp
        i.dist_front_mm = int(front)
        i.dist_left_mm = int(left)
        i.dist_right_mm = int(right)
        i.heading_deg = float(heading)
        i.gyro_rate_dps = float(rate)
        i.ticks_left = int(tl)
        i.ticks_right = int(tr)
        i.line_black = int(line)
        i.start_signal = int(start)
        i.dt_ms = int(dt_ms)
        self.lib.nav_step(ctypes.byref(i), ctypes.byref(self.out))
        return self.out

    def state_name(self, s):
        return self.lib.nav_state_name(ctypes.c_uint8(s)).decode()

    @property
    def odom(self):
        return (self.lib.nav_odom_x_mm(), self.lib.nav_odom_y_mm())

    @property
    def junctions(self):
        return self.lib.nav_junction_count()

    @property
    def memory_bytes(self):
        return self.lib.nav_memory_bytes()
