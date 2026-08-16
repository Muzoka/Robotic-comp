"""
cfg.py - read firmware/MazeRunner/config.h so the simulator and the robot
never disagree about a number. Change config.h, both change.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_H = os.path.join(_HERE, "..", "firmware", "MazeRunner", "config.h")

_NUM = re.compile(
    r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+\(?\s*([+-]?[0-9]*\.?[0-9]+)[fFuUlL]*\s*\)?\s*(?:/\*.*)?$"
)


def load(path=CONFIG_H):
    out = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            m = _NUM.match(line.split("//")[0])
            if m:
                name, val = m.group(1), m.group(2)
                out[name] = float(val) if ("." in val) else int(val)
    return out


CFG = load()


def get(name, default=None):
    v = CFG.get(name, default)
    if v is None:
        raise KeyError("%s is not defined in config.h" % name)
    return v
