"""
cfg.py - read firmware/MazeRunner/config.h so the simulator and the robot
never disagree about a number. Change config.h, both change.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_H = os.path.join(_HERE, "..", "firmware", "MazeRunner", "config.h")

_DEF = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$")
_SAFE = re.compile(r"^[A-Za-z0-9_+\-*/(). ]+$")


def _clean(expr):
    """Strip C comments, float/int suffixes and casts so Python can eval it."""
    expr = re.sub(r"/\*.*?\*/", "", expr, flags=re.S)
    expr = expr.split("/*")[0]          # a comment that runs on to the next line
    expr = expr.split("//")[0]
    expr = expr.replace("(int)", "").replace("(float)", "")
    expr = re.sub(r"(\d)[fFuU]\b", r"\1", expr)
    expr = re.sub(r"(\d)[lL]+\b", r"\1", expr)
    return expr.strip()


def load(path=CONFIG_H):
    """Read config.h. Values may be plain numbers or expressions built from
    values defined earlier in the file - the geometry-derived thresholds are
    written that way on purpose, so changing the robot's size cannot leave a
    stale threshold behind."""
    defs = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            m = _DEF.match(raw)
            if not m:
                continue
            expr = _clean(m.group(2))
            if expr and _SAFE.match(expr):
                defs.append((m.group(1), expr))

    # C macros expand where they are used, not where they are written, so a
    # definition may refer to one that appears later in the file. Keep
    # sweeping until nothing new resolves.
    out = {}
    for _ in range(6):
        progress = False
        for name, expr in defs:
            if name in out:
                continue
            try:
                v = eval(expr, {"__builtins__": {}}, dict(out))   # noqa: S307
            except Exception:
                continue
            if isinstance(v, (int, float)):
                out[name] = v
                progress = True
        if not progress:
            break
    return out


CFG = load()


def get(name, default=None):
    v = CFG.get(name, default)
    if v is None:
        raise KeyError("%s is not defined in config.h" % name)
    return v
