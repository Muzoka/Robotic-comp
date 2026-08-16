#!/bin/bash
# check_wokwi_sketch.sh - compile wokwi/sketch.ino the way ARDUINO does.
#
# This exists because of a bug that shipped. The first version of this check
# compiled the generated file as plain C++ and passed, and the Wokwi build
# then failed with
#
#     error: 'Junction' does not name a type; did you mean 'union'?
#
# Plain C++ cannot catch that, because the failure is caused by something
# g++ never does: the Arduino IDE scans the .ino, generates a prototype for
# every function it finds, and inserts them all NEAR THE TOP - above the
# lines where the types are defined. A prototype that mentions a type
# declared further down then fails to compile.
#
# So this script emulates that. It extracts every function signature, emits
# the prototypes at the top exactly as Arduino would, and compiles the
# result. Compiling without them is a DIFFERENT test, not a weaker one - it
# passes on files Arduino rejects.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKETCH="$ROOT/wokwi/sketch.ino"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

[ -f "$SKETCH" ] || { echo "missing $SKETCH - run tools/make_wokwi_sketch.py"; exit 1; }

# ---- minimal Arduino core, enough to compile against ----
cat > "$WORK/Arduino.h" <<'EOF'
#pragma once
#include <stdint.h>
#include <math.h>
#include <string.h>
#include <stddef.h>
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define RISING 3
#define A0 14
#define A1 15
#define A2 16
#define A3 17
#define A4 18
#define A5 19
#define F(x) (x)
#define constrain(x,lo,hi) ((x)<(lo)?(lo):((x)>(hi)?(hi):(x)))
#define abs(x) ((x)>0?(x):-(x))
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
typedef uint8_t byte;
void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
int  digitalRead(uint8_t);
void analogWrite(uint8_t, int);
unsigned long millis(void);
unsigned long micros(void);
void delay(unsigned long);
void delayMicroseconds(unsigned int);
unsigned long pulseIn(uint8_t, uint8_t, unsigned long);
uint8_t digitalPinToInterrupt(uint8_t);
void attachInterrupt(uint8_t, void (*)(void), int);
void noInterrupts(void);
void interrupts(void);
struct SerialC {
  void begin(long);
  int  available();
  int  read();
  void print(const char*); void print(char); void print(int); void print(long);
  void print(unsigned long); void print(unsigned int);
  void print(float,int=2); void print(double,int=2);
  void println(const char*); void println(int); void println(long);
  void println(unsigned int); void println(unsigned long);
};
extern SerialC Serial;
EOF

cat > "$WORK/Wire.h" <<'EOF'
#pragma once
#include <stdint.h>
#include <stddef.h>
struct TwoWire {
  void begin(); void beginTransmission(uint8_t); size_t write(uint8_t);
  uint8_t endTransmission(uint8_t v=1); uint8_t requestFrom(uint8_t,uint8_t);
  int available(); int read(); void setClock(uint32_t);
};
extern TwoWire Wire;
EOF

cat > "$WORK/EEPROM.h" <<'EOF'
#pragma once
#include <stdint.h>
struct EEPROMC {
  uint8_t read(int); void write(int,uint8_t); void update(int,uint8_t);
  template<class T> T &get(int, T &t){ return t; }
  template<class T> const T &put(int, const T &t){ return t; }
};
extern EEPROMC EEPROM;
EOF

# ---- Pass 1: plain compile (catches ordinary errors) ----
{ echo '#include "Arduino.h"'; cat "$SKETCH"; } > "$WORK/plain.cpp"
if ! g++ -std=gnu++11 -fsyntax-only -Wall -I"$WORK" "$WORK/plain.cpp"; then
  echo "FAIL: sketch does not compile even without generated prototypes"
  exit 1
fi
echo "pass 1 OK  - compiles as plain C++"

# ---- Pass 2: with Arduino-style prototypes hoisted to the top ----
# Emulates arduino-builder's PrototypesAdder: every function definition at
# column 0 gets a prototype, and they all go above the body.
python3 - "$SKETCH" "$WORK/proto.cpp" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

# A function definition starting at column 0: "<type> name(args)\n{"
pat = re.compile(
    r'^((?:static\s+|inline\s+|NAV_API\s+)*'      # storage / api macro
    r'(?:const\s+)?[A-Za-z_]\w*(?:\s*\*)*\s+\**'  # return type
    r'([A-Za-z_]\w*)\s*'                          # name
    r'\([^;{)]*\))\s*\n\{', re.M)

protos, seen = [], set()
for m in pat.finditer(text):
    sig, name = m.group(1).strip(), m.group(2)
    if name in ("if", "for", "while", "switch", "return", "sizeof"):
        continue
    if name in seen:
        continue
    seen.add(name)
    protos.append(sig + ";")

# arduino-builder's PrototypesAdder inserts the whole block immediately
# before the FIRST function definition in the file. Anything declared above
# that point (macros, the types out of nav_core.h) is visible to the
# prototypes; anything below it - Junction, Nav, Sonar - is not, unless
# make_wokwi_sketch.py forward-declared it at the top.
first = pat.search(text)
if not first:
    sys.exit("no function definitions found - the regex needs a look at")
insert_at = text[:first.start()].count("\n")

lines = text.splitlines()
out = lines[:insert_at]
out += ["", "/* ---- prototypes as the Arduino IDE would generate them ---- */"]
out += protos
out += [""] + lines[insert_at:]
open(dst, "w", encoding="utf-8").write(
    '#include "Arduino.h"\n' + "\n".join(out) + "\n")
print("   generated %d prototypes, inserted before the first function "
      "(line %d)" % (len(protos), insert_at + 1))
PY

if ! g++ -std=gnu++11 -fsyntax-only -Wall -I"$WORK" "$WORK/proto.cpp"; then
  echo
  echo "FAIL: compiles as plain C++ but NOT the way Arduino builds it."
  echo "This is the exact failure Wokwi reports. Usually it means a type is"
  echo "used in a function signature but defined further down the file, and"
  echo "is not forward-declared at the top by make_wokwi_sketch.py."
  exit 1
fi
echo "pass 2 OK  - compiles with Arduino-style hoisted prototypes"
echo
echo "wokwi/sketch.ino is good to paste."
