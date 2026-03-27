#!/bin/bash
# Serve the web UI
cd /opt/dump1090/public_html
python3 -m http.server 8080 --bind 0.0.0.0 &

# Start dump1090, writing JSON for the web UI
cd /opt/dump1090
exec ./dump1090 --net --quiet \
    --write-json /run/dump1090-fa \
    --write-json-every 1 \
    --lat 36.1811 --lon -86.7335 \
    "$@"
