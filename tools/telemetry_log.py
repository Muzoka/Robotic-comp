#!/usr/bin/env python3
"""
telemetry_log.py - record what the real robot did, so you can compare it
against what the simulator said it would do.

    pip install pyserial
    python3 tools/telemetry_log.py --port /dev/ttyUSB0 --out run01.csv
    python3 tools/telemetry_log.py --port COM3 --out run01.csv        (Windows)

The firmware prints one CSV line every 100 ms with exactly the same columns
the simulator writes to sim/runs/<map>.csv, so you can put the two side by
side. When they disagree, the difference tells you which number in
sim/robot.py is wrong - fix that, and from then on the simulator predicts
your actual robot instead of a generic one.

Press Ctrl-C to stop.
"""

import argparse
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial is not installed.  pip install pyserial")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--out", default="run.csv")
    ap.add_argument("--go", action="store_true",
                    help="send 'g' to start the run as soon as we connect")
    a = ap.parse_args()

    ser = serial.Serial(a.port, a.baud, timeout=1)
    time.sleep(2.0)                      # the Uno resets when the port opens
    if a.go:
        ser.write(b"g")

    n = 0
    print("logging to %s - Ctrl-C to stop" % a.out)
    with open(a.out, "w", encoding="utf-8") as fh:
        try:
            while True:
                line = ser.readline().decode("utf-8", "replace").strip()
                if not line:
                    continue
                if line.startswith("#"):
                    print(line)
                    continue
                fh.write(line + "\n")
                fh.flush()
                n += 1
                if n % 10 == 0:
                    print("\r%d rows   %s" % (n, line[:70]), end="")
        except KeyboardInterrupt:
            pass
    print("\n%d rows written to %s" % (n, a.out))


if __name__ == "__main__":
    main()
