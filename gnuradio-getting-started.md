# GNU Radio Getting Started Guide

RTL-SDR Blog V4 on Ubuntu 22.04

## What is GNU Radio?

GNU Radio is a visual signal processing toolkit. You build "flowgraphs" — chains of signal processing blocks — either in a GUI (GNU Radio Companion / GRC) or in Python. Think of it like a modular synth but for radio: source → filter → demodulate → decode → output.

## Installation

```bash
# GNU Radio + RTL-SDR source block
sudo apt install gnuradio gr-osmosdr

# Verify
gnuradio-companion --version
```

Note: We already have the RTL-SDR Blog fork drivers installed (`/usr/local/lib/librtlsdr.so`). The `gr-osmosdr` block talks to librtlsdr, so it should pick up the Blog fork automatically. If it doesn't, you may need to rebuild gr-osmosdr against the blog fork's librtlsdr.

Launch the GUI with:
```bash
gnuradio-companion
```

## Core Concepts

- **Source** — where samples come from (RTL-SDR, file, signal generator)
- **Sink** — where samples go (audio output, file, GUI display)
- **Sample rate** — how many samples per second the SDR captures (RTL-SDR max ~2.4 MS/s)
- **Complex samples (I/Q)** — radio signals have two components (in-phase and quadrature); this is how SDRs represent RF digitally
- **Flowgraph** — a chain of blocks connected together: source → processing → sink

## Project 1: FM Radio Receiver

The "hello world" of GNU Radio. Demodulate a broadcast FM station.

**Flowgraph:**
```
RTL-SDR Source (freq=105.9M, rate=2M, gain=40)
  → Low Pass Filter (cutoff=100k, transition=10k)
  → WBFM Receive (audio_rate=48k, quad_rate=480k)
  → Rational Resampler (interpolation=48, decimation=480)
  → Audio Sink (rate=48k)
```

Add a `QT GUI Frequency Sink` and `QT GUI Waterfall Sink` off the source to see the spectrum.

**What you learn:** Basic flowgraph construction, sample rates, filtering, FM demodulation.

## Project 2: NOAA Weather Radio Decoder

Narrowband FM (NFM) demodulation — same idea as FM broadcast but narrower bandwidth.

**Flowgraph:**
```
RTL-SDR Source (freq=162.55M, rate=1M, gain=40)
  → Low Pass Filter (cutoff=8k, transition=2k)
  → NBFM Receive (audio_rate=48k, quad_rate=96k)
  → Audio Sink (rate=48k)
```

**What you learn:** Difference between wideband FM (broadcast) and narrowband FM (two-way radio, weather). Same demod technique, different filter widths.

## Project 3: Aircraft Transponder (ADS-B on 1090 MHz)

This one is more about demonstrating digital signal processing. ADS-B is a pulsed binary protocol.

Note: Dedicated tools (`dump1090`) do this much better, but building it in GNU Radio teaches you how digital signals work.

**Flowgraph (simplified):**
```
RTL-SDR Source (freq=1090M, rate=2M, gain=49.6)
  → Complex to Mag (convert I/Q to amplitude)
  → Threshold (detect pulses above noise)
  → Custom Python block (parse ADS-B frames)
```

**What you learn:** Digital signal detection, pulse amplitude modulation, binary protocol decoding.

## Project 4: Decode POCSAG Pagers (~152-158 MHz)

Pagers use FSK (frequency shift keying) — one of the simplest digital modulations. POCSAG is the protocol. Hospitals, restaurants, and some emergency services still use them, completely unencrypted.

**Flowgraph:**
```
RTL-SDR Source (freq=152.48M, rate=1M, gain=40)
  → Low Pass Filter (cutoff=15k)
  → NBFM Receive
  → Audio Sink → pipe to multimon-ng for POCSAG decode
```

Or skip GNU Radio and use `multimon-ng` directly:
```bash
rtl_fm -f 152.48M -M fm -s 22050 -g 40 - | multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -
```

You'll need to find active pager frequencies in Nashville — scan around 152-158 MHz for FSK signals (they look like two alternating tones on the waterfall).

**What you learn:** FSK demodulation, digital protocol decoding, real-world unencrypted data.

## Project 5: 433 MHz ISM Band Sensor Decoding

Wireless weather stations, tire pressure sensors, doorbell buttons, soil sensors all transmit on 433.92 MHz using OOK (on-off keying) or simple FSK.

**The easy way (no GNU Radio needed):**
```bash
sudo apt install rtl-433
# or build from https://github.com/merbanan/rtl_433

rtl_433 -g 40
```

This auto-detects and decodes hundreds of device protocols. Run it and see what your neighbors' weather stations are reporting.

**The GNU Radio way:**
```
RTL-SDR Source (freq=433.92M, rate=1M, gain=40)
  → Complex to Mag
  → Binary Slicer
  → Custom decoder block
```

**What you learn:** OOK modulation, protocol reverse engineering. `rtl_433` is more practical but GNU Radio teaches you what's happening under the hood.

## Project 6: FM Stereo Decoder (deep dive)

Broadcast FM is more complex than it seems. The signal contains:
- Mono audio (0-15 kHz)
- 19 kHz pilot tone
- Stereo difference signal modulated around 38 kHz
- RDS digital data at 57 kHz (station name, song info)

Build a flowgraph that separates all of these. The RDS decode is particularly satisfying — extracting station names and radio text from a subcarrier buried in the FM signal.

**What you learn:** Subcarrier demodulation, pilot tone detection, multiplexing, PSK (phase shift keying for RDS).

## Useful Resources

- GNU Radio wiki tutorials: https://wiki.gnuradio.org/index.php/Tutorials
- RTL-SDR FM Receiver tutorial: https://wiki.gnuradio.org/index.php?title=RTL-SDR_FM_Receiver
- GRC flowgraph examples ship with GNU Radio (usually in `/usr/share/gnuradio/examples/`)

## Tips

- Start with Project 1 (FM radio) — if that works, everything else is variations on the same theme
- The GUI (GRC) generates Python code — look at it to understand what's happening
- Sample rate mismatches are the #1 source of errors; every block in the chain must agree on rates
- The RTL-SDR source block in GNU Radio is called "osmocom Source" (from gr-osmosdr)
- Set the device string to `rtl=0` in the osmocom source block
- Always close GQRX before using GNU Radio (only one app can use the dongle at a time)
