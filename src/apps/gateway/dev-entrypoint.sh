#!/bin/bash
set -e

FAKETTY=/dev/ttyUSBFAKE
GRBLSIM=/app/grbl_sim.exe

if [ ! -e "$GRBLSIM" ]; then
  echo "ERROR: GRBL simulator not found at $GRBLSIM"
  exit 1
fi

# Start socat + GRBL simulator to create virtual serial port in the background
socat -d -d PTY,raw,link="$FAKETTY",echo=0 EXEC:"'$GRBLSIM -n -s step.out -b block.out'",pty,raw,echo=0 &

# Wait for the virtual serial port to become available
for i in $(seq 1 10); do
  [ -e "$FAKETTY" ] && break
  sleep 1
done

if [ ! -e "$FAKETTY" ]; then
  echo "ERROR: Virtual serial port $FAKETTY did not appear after 10s."
  exit 1
fi

chmod a+rw "$FAKETTY"
echo "GRBL simulator running on $FAKETTY"

# Start the gateway (or whatever command was passed)
exec "$@"
