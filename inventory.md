# Radio Equipment Inventory

## SDR

- **RTL-SDR Blog V4** (R828D tuner, 1PPM TCXO, SMA female port)
  - Freq range: ~500 kHz – 1.7 GHz
  - Drivers: RTL-SDR Blog fork built from source at `~/git/third/rtl-sdr-blog`
  - Udev rules: `/etc/udev/rules.d/20-rtlsdr.rules`
  - Kernel blacklist: `/etc/modprobe.d/blacklist-rtlsdr.conf`

## Antennas

- **Telescoping whip antenna** (BNC male connector)
  - General purpose VHF/UHF, currently primary antenna
- **MLA-30+ Active Magnetic Loop** (0.5–30 MHz, 10m feeder cable included) — arrived 2026-03-26
  - Built-in low noise amplifier, USB bias tee power injector (micro USB, 5V DC only — no data)
  - Two SMA connectors on bias tee: "Active Loop ANT" (to antenna) and "TO RECEIVER" (to SDR)
  - Note: use battery power (USB battery pack) over wall charger to avoid switching noise injection
  - Primary use: HF receive — ham (20m/14.238 MHz), shortwave, AM
- **V-Dipole Antenna DIY Kit** (137 MHz, telescopic, SMA, 6m cable) — arrived 2026-03-26
  - For NOAA/Meteor weather satellite APT/LRPT reception
  - Mount horizontally, V at ~120°, arms ~53.4 cm each, aimed skyward
  - No tracking needed — omnidirectional upward pattern
- **WiFi AP antenna** (SMA, 2.4/5 GHz) — too high frequency for VHF, not useful
- **Misc speaker wire** — for improvised long wire HF antenna

## Adapters

- **ConnectoRF Universal RF Adapter Kit** — case with universal couplers + typed end pieces:
  - SMA male/female
  - BNC male/female
  - N male/female
  - TNC male/female
  - UHF male/female
  - Mini-UHF male/female
  - Universal couplers (barrels)

## Cables

- **Coax cable** (mini-UHF male on both ends) — for running antenna to window
  - Confirmed working with mini-UHF jack from adapter kit

## On Order

(none currently)

## Upconverters

- **Nooelec Ham It Up v1.3** — HF upconverter, working
  - Converts 0.5–30 MHz → 125 MHz passband for RTL-SDR
  - Confirmed receiving shortwave/AM broadcast with speaker wire antenna

## Binding Post Adapters

- **BNC binding post adapters** (2-pack) — screw-down terminals for bare wire antennas
  - BNC to dongle via adapter kit (BNC → coupler → SMA)
  - Used for: HF long wire antenna (speaker wire out window to fence)

## Other

- **Baofeng UV-5R** handheld radio (SMA female port — backwards from convention)
  - Rubber duck antenna is SMA male
- **Coax crimping tool + connectors** — somewhere
- **Old discone antenna** — missing/lost, was used for previous SDR work (Radio Cuba Libre)

## Software

- GQRX (AppImage at `~/packages`)
- rtl-sdr CLI tools (`rtl_test`, `rtl_fm`, `rtl_power`, `rtl_biast`) — `/usr/local/bin/`
- GNU Radio — `sudo apt install gnuradio gr-osmosdr`

## Current Working Setup

```
[Whip (BNC male)] → [BNC jack + coupler + SMA plug] → [RTL-SDR V4 (SMA female)] → USB → PC
```

### With coax cable (for window run)

```
[Whip (BNC male)] → [BNC jack + coupler + mini-UHF jack] → [coax cable] → [mini-UHF jack + coupler + SMA plug] → [RTL-SDR V4]
```

### Future: HF long wire

```
[Speaker wire in tree] → [BNC binding post] → [BNC jack + coupler + SMA plug] → [RTL-SDR V4]
```
