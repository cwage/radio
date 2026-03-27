#!/usr/bin/env python3
"""
GQRX Tuning Logger — polls GQRX's remote control interface, logs state,
and identifies likely stations based on frequency/time/mode.

Requires: GQRX running with remote control enabled (Tools > Remote control)
Default: localhost:7356
"""

import argparse
import json
import socket
import sys
import time
from datetime import datetime, timezone

HOST = "127.0.0.1"
PORT = 7356

# Known stations: (freq_hz, name, type, notes)
# AM broadcast stations receivable in Nashville area
AM_STATIONS = [
    (540000, "WCSV Crossville TN", "AM", "Religious"),
    (570000, "WMAM Marinette WI", "AM", ""),
    (580000, "WFBR unknown", "AM", ""),
    (620000, "WZON Bangor ME", "AM", "Sports"),
    (630000, "WFBR unknown", "AM", ""),
    (640000, "WGA Atlanta", "AM", "News/Talk"),
    (650000, "WSM Nashville", "AM", "Country/Opry, 50kW clear channel"),
    (680000, "WPTF Raleigh NC", "AM", "News/Talk"),
    (700000, "WLW Cincinnati", "AM", "News/Talk, 50kW clear channel"),
    (720000, "WGN Chicago", "AM", "News/Talk, 50kW clear channel"),
    (750000, "WSB Atlanta", "AM", "News/Talk, 50kW"),
    (770000, "WABC New York", "AM", "Talk, 50kW"),
    (780000, "WBBM Chicago", "AM", "News, 50kW"),
    (800000, "WVLK Lexington KY", "AM", "Talk"),
    (810000, "WGY Schenectady NY", "AM", "Talk, 50kW"),
    (840000, "WHAS Louisville", "AM", "News/Talk, 50kW"),
    (850000, "WKNR Cleveland", "AM", "Sports"),
    (870000, "WWL New Orleans", "AM", "News/Talk, 50kW clear channel"),
    (880000, "WCBS New York", "AM", "News, 50kW"),
    (890000, "WLS Chicago", "AM", "Talk, 50kW"),
    (900000, "WLAC Nashville (historical)", "AM", ""),
    (910000, "WRNZ Lexington KY", "AM", ""),
    (920000, "WONE Dayton OH", "AM", ""),
    (940000, "WINZ Miami", "AM", "News"),
    (950000, "WROL Boston", "AM", "Religious"),
    (960000, "WSBT South Bend IN", "AM", ""),
    (970000, "WFLA Tampa", "AM", "News/Talk"),
    (980000, "WYFN Nashville area", "AM", "Religious"),
    (1010000, "WINS New York", "AM", "News, 50kW"),
    (1020000, "KDKA Pittsburgh", "AM", "News, 50kW"),
    (1030000, "WBZ Boston", "AM", "News, 50kW"),
    (1050000, "WFBG Altoona PA", "AM", ""),
    (1060000, "WQMG Greensboro NC", "AM", ""),
    (1070000, "WDIA Memphis", "AM", ""),
    (1080000, "WTIC Hartford", "AM", "News/Talk, 50kW"),
    (1090000, "KAAY Little Rock", "AM", "Talk"),
    (1100000, "WTAM Cleveland", "AM", "Sports, 50kW"),
    (1120000, "KMOX St Louis", "AM", "News/Talk, 50kW"),
    (1140000, "WRVA Richmond", "AM", "News/Talk, 50kW"),
    (1160000, "WVOL Nashville", "AM", "Urban/Gospel"),
    (1200000, "WCHB Detroit", "AM", "Talk"),
    (1210000, "WPHT Philadelphia", "AM", "Talk, 50kW"),
    (1240000, "WNAH Nashville", "AM", ""),
    (1260000, "WCHB Detroit", "AM", ""),
    (1300000, "WJZM Clarksville TN", "AM", ""),
    (1340000, "WKDA Nashville", "AM", ""),
    (1360000, "WSAI Cincinnati", "AM", ""),
    (1380000, "WKGN Knoxville", "AM", ""),
    (1400000, "WKDA Nashville area", "AM", ""),
    (1410000, "WRMH Nashville area", "AM", ""),
    (1430000, "WOI Ames IA", "AM", ""),
    (1470000, "WVOL Nashville area", "AM", ""),
    (1490000, "WJMW Nashville area", "AM", ""),
    (1510000, "WLAC Nashville", "AM", "News/Talk"),
    (1520000, "WKDA Nashville area", "AM", ""),
    (1560000, "WQAK Nashville area", "AM", ""),
    (1600000, "WNQM Nashville", "AM", "Religious"),
    (1640000, "WKND Hartford", "AM", ""),
    (1650000, "WHKT Norfolk VA", "AM", ""),
]

# Shortwave / HF stations active evenings UTC targeting North America
HF_STATIONS = [
    (3330000, "CHU Canada", "Time Signal", "24/7"),
    (5000000, "WWV Fort Collins CO", "Time Signal", "24/7"),
    (5935000, "WWCR Nashville", "Shortwave", "100kW, local"),
    (5950000, "WRMI Okeechobee FL", "Shortwave", ""),
    (5985000, "WRMI Okeechobee FL", "Shortwave", ""),
    (6000000, "Radio Havana Cuba", "Shortwave", "English to N.America"),
    (6070000, "CFRX Toronto", "Shortwave", "Relay of CFRB 1010"),
    (7490000, "WBCQ Monticello ME", "Shortwave", ""),
    (7780000, "WRMI Okeechobee FL", "Shortwave", ""),
    (7850000, "CHU Canada", "Time Signal", "24/7"),
    (9395000, "WRMI Okeechobee FL", "Shortwave", ""),
    (9455000, "WRMI Okeechobee FL", "Shortwave", ""),
    (9955000, "WRMI Okeechobee FL", "Shortwave", ""),
    (10000000, "WWV Fort Collins CO", "Time Signal", "24/7"),
    (11580000, "WRMI Okeechobee FL", "Shortwave", ""),
    (11860000, "Radio Marti", "Shortwave", "US govt, Spanish to Cuba, from Greenville NC"),
    (11930000, "Radio Marti", "Shortwave", "Spanish"),
    (14670000, "CHU Canada", "Time Signal", "24/7"),
    (15000000, "WWV Fort Collins CO", "Time Signal", "24/7"),
]

ALL_STATIONS = AM_STATIONS + HF_STATIONS


def gqrx_cmd(cmd, host=HOST, port=PORT):
    """Send a command to GQRX and return the response."""
    with socket.create_connection((host, port), timeout=2) as s:
        s.sendall((cmd + "\n").encode())
        data = s.recv(4096).decode(errors="replace").strip()
    return data


def find_station(freq_hz, tolerance_hz=15000):
    """Find the closest known station within tolerance."""
    best = None
    best_dist = tolerance_hz + 1
    for station_freq, name, stype, notes in ALL_STATIONS:
        dist = abs(freq_hz - station_freq)
        if dist < best_dist:
            best_dist = dist
            best = (station_freq, name, stype, notes, dist)
    if best and best[4] <= tolerance_hz:
        return best
    return None


def format_freq(hz):
    """Format frequency for display."""
    if hz >= 1000000:
        return f"{hz/1e6:.3f} MHz"
    else:
        return f"{hz/1e3:.0f} kHz"


def main():
    parser = argparse.ArgumentParser(description="Log GQRX tuning and identify stations")
    parser.add_argument("--host", default=HOST, help="GQRX host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=PORT, help="GQRX port (default: 7356)")
    parser.add_argument("--interval", type=float, default=2, help="Poll interval in seconds (default: 2)")
    parser.add_argument("--log", type=str, default="gqrx_tune_log.jsonl", help="Log file (default: gqrx_tune_log.jsonl)")
    parser.add_argument("--offset", type=float, default=0,
                        help="Display offset in Hz (0 = use freq as-is, set to -125000000 if GQRX LNB LO is not set)")
    parser.add_argument("--quiet", action="store_true", help="Only print when station changes")
    args = parser.parse_args()

    print(f"GQRX Station Logger")
    print(f"  Connecting to {args.host}:{args.port}")
    print(f"  Logging to {args.log}")
    print(f"  Poll interval: {args.interval}s")
    print(f"  Press Ctrl+C to stop")
    print()

    last_station = None
    last_freq = None

    while True:
        try:
            freq_raw = gqrx_cmd("f", args.host, args.port)
            mode = gqrx_cmd("m", args.host, args.port)
            strength = gqrx_cmd("l STRENGTH", args.host, args.port)

            freq_hz = int(freq_raw) + int(args.offset)
            strength_db = float(strength)
            now = datetime.now(timezone.utc)

            match = find_station(freq_hz)

            row = {
                "ts": now.isoformat(),
                "freq_hz": freq_hz,
                "freq_display": format_freq(freq_hz),
                "mode": mode,
                "strength_dbfs": strength_db,
            }

            if match:
                station_freq, name, stype, notes, dist = match
                row["station"] = name
                row["station_type"] = stype
                row["station_freq_hz"] = station_freq
                row["station_notes"] = notes
                row["offset_hz"] = dist
                station_str = f"{name} ({format_freq(station_freq)})"
                if notes:
                    station_str += f" — {notes}"
            else:
                station_str = "Unknown"

            with open(args.log, "a") as f:
                f.write(json.dumps(row) + "\n")

            # Print to terminal
            changed = (match and last_station != (match[0], match[1])) or \
                      (not match and last_freq != freq_hz)

            if not args.quiet or changed:
                sig_bar = "█" * max(0, int((strength_db + 60) / 3)) if strength_db > -60 else ""
                ts_local = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts_local}] {format_freq(freq_hz):>12s}  {mode:>4s}  {strength_db:>6.1f} dB  {sig_bar:16s}  {station_str}")

            if match:
                last_station = (match[0], match[1])
            else:
                last_station = None
            last_freq = freq_hz

        except ConnectionRefusedError:
            print("Cannot connect to GQRX — is remote control enabled? (Tools > Remote control)")
            time.sleep(5)
        except socket.timeout:
            print("Connection timeout — GQRX not responding")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
