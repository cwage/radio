# RTL-SDR V4 Scan Results — Nashville, TN (East Nashville)

Date: 2026-03-20
Setup: RTL-SDR Blog V4, telescoping whip antenna (BNC), indoors, gain 40 dB

## Hardware

- **Dongle:** RTL-SDR Blog V4 (R828D tuner, 1PPM TCXO)
- **Antenna:** Telescoping whip via BNC-to-SMA adapter (from ConnectoRF universal kit)
- **Location:** Indoor, East Nashville 37206
- **Driver:** RTL-SDR Blog fork (built from source, https://github.com/rtlsdrblog/rtl-sdr-blog)
  - Stock Ubuntu `rtl-sdr 0.6.0` does NOT work with V4 — PLL never locks
  - Kernel DVB modules must be blacklisted (`/etc/modprobe.d/blacklist-rtlsdr.conf`)

## FM Broadcast (88–108 MHz)

Noise floor: ~-22 dB

| Freq (MHz) | Power (dB) | Above noise | Station |
|-----------|-----------|------------|---------|
| 105.9 | +10.4 | +32 | WQQK (R&B/Hip-hop) |
| 103.3 | +8.9 | +31 | WKDF (Country) |
| 97.9 | +5.4 | +27 | WRMX |
| 106.7 | +3.8 | +25 | WRVW (The River) |
| 107.5 | +0.4 | +22 | WAMB/WWTN |
| 95.5 | -2.5 | +19 | WSM-FM |
| 96.3 | -3.5 | +18 | WRQQ |
| 93.0 | -3.9 | +18 | Lightning 100 |

## VHF (108–174 MHz)

Noise floor: ~-27 dB

| Freq (MHz) | Power (dB) | Above noise | Likely ID |
|-----------|-----------|------------|-----------|
| 162.55 | -4.9 | +22 | **NOAA Weather Radio** (WXL58 Nashville) |
| 121.2 | -13.1 | +14 | Aircraft emergency/guard frequency |
| 123.3 | -13.3 | +14 | Air traffic control (Nashville approach) |
| 167–173 | -10 to -13 | +14–17 | Business/government VHF (Nashville city services, utilities) |

## Pager / NOAA (148–165 MHz)

Noise floor: ~-25 dB

| Freq (MHz) | Power (dB) | Above noise | Likely ID |
|-----------|-----------|------------|-----------|
| 162.55 | -2.3 | +22 | NOAA Weather Radio |
| 164.98 | -6.3 | +18 | Pager frequency |

## UHF (400–512 MHz)

Noise floor: ~-14 dB

| Freq (MHz) | Power (dB) | Above noise | Likely ID |
|-----------|-----------|------------|-----------|
| 480.0 | +8.1 | +22 | UHF TV broadcast |
| 500.3 | +7.1 | +21 | UHF TV / trunked radio |
| 502–503 | +1–2 | +15–16 | Signal cluster — TV station or trunked system |
| 506.3 | +3.8 | +18 | UHF TV broadcast |

## ISM 433 MHz Band

No strong signals found indoors. Weather stations and IoT sensors are low-power; need outdoor antenna.

## Notes

- NOAA Weather Radio (162.55 MHz) is the strongest non-FM signal, easily receivable indoors
- Aircraft frequencies (121.2, 123.3 MHz) detectable even with whip indoors — Nashville airspace is busy
- The whip antenna is not ideal for any of these bands but still picks up plenty indoors
- The V-dipole antenna (137 MHz, arriving soon) will be tuned for NOAA satellite passes but should also improve weather radio and VHF reception
- FM broadcast stations are extremely strong in Nashville — picking up 10+ stations indoors with a whip

## Useful Commands

```bash
# Scan a frequency range
rtl_power -f 88M:108M:25k -g 40 -i 5 output.csv

# Listen to NOAA weather radio
rtl_fm -f 162.55M -M fm -s 12000 -g 40 - | aplay -r 12000 -f S16_LE -c 1

# Listen to FM broadcast
rtl_fm -f 105.9M -M wbfm -s 200000 -r 48000 -g 40 - | aplay -r 48000 -f S16_LE -c 1

# Record 10 seconds of audio to file
timeout 10 rtl_fm -f 162.55M -M fm -s 12000 -g 40 output.raw
```

## Project Ideas

- [ ] NOAA/Meteor weather satellite imagery (waiting on V-dipole antenna)
- [ ] Automated NOAA weather radio monitoring + Whisper transcription
- [ ] FT8 passive decoding + propagation dashboard (dad's ham freq on 40m)
- [ ] Numbers station hunter (HF, needs long wire antenna out window)
- [ ] 433 MHz ISM band sensor snooping with `rtl_433` (needs outdoor antenna)
- [ ] Meteor scatter detection on FM band
