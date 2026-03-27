#!/usr/bin/env python3
"""
HF Scanner — scan a frequency range, find strong signals, record audio,
and transcribe with Whisper.

Requires: rtl_power, rtl_fm, sox, whisper
"""

import argparse
import csv
import io
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def scan_range(start_hz, stop_hz, bin_size=10000, offset=125000000, gain=40, integration_time="10s"):
    """Run rtl_power to scan a frequency range. Returns list of (freq_hz, power_db) tuples."""
    tuned_start = start_hz + offset
    tuned_stop = stop_hz + offset

    print(f"Scanning {start_hz/1e6:.3f} - {stop_hz/1e6:.3f} MHz "
          f"(tuning {tuned_start/1e6:.3f} - {tuned_stop/1e6:.3f} MHz with offset)...")

    cmd = [
        "rtl_power",
        "-f", f"{int(tuned_start)}:{int(tuned_stop)}:{int(bin_size)}",
        "-g", str(gain),
        "-i", integration_time,
        "-1",  # single sweep then exit
        "-",   # output to stdout
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"rtl_power error: {result.stderr}", file=sys.stderr)
        return []

    samples = []
    for line in result.stdout.strip().split("\n"):
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) < 7:
            continue
        # CSV format: date, time, hz_low, hz_high, hz_step, num_samples, db1, db2, ...
        hz_low = float(parts[2].strip())
        hz_step = float(parts[4].strip())
        db_values = [float(x.strip()) for x in parts[6:] if x.strip()]
        for i, db in enumerate(db_values):
            freq = hz_low + (i * hz_step)
            real_freq = freq - offset
            samples.append((real_freq, db))

    print(f"  Got {len(samples)} frequency bins")
    return samples


def find_peaks(samples, threshold_db=10, min_spacing_hz=20000):
    """Find frequencies with signal above noise floor + threshold.
    Groups nearby peaks and picks the strongest in each group."""
    if not samples:
        return []

    powers = [s[1] for s in samples]
    noise_floor = sorted(powers)[len(powers) // 4]  # 25th percentile as noise floor estimate
    print(f"  Noise floor estimate: {noise_floor:.1f} dB")
    print(f"  Detection threshold: {noise_floor + threshold_db:.1f} dB")

    # Find all bins above threshold
    candidates = [(freq, db) for freq, db in samples if db > noise_floor + threshold_db]
    if not candidates:
        print("  No signals found above threshold")
        return []

    # Sort by power descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Group nearby frequencies, keep strongest
    peaks = []
    for freq, db in candidates:
        too_close = False
        for peak_freq, _ in peaks:
            if abs(freq - peak_freq) < min_spacing_hz:
                too_close = True
                break
        if not too_close:
            peaks.append((freq, db))

    peaks.sort(key=lambda x: x[0])  # sort by frequency
    print(f"  Found {len(peaks)} signals above threshold")
    for freq, db in peaks:
        print(f"    {freq/1e3:.0f} kHz  ({db:.1f} dB, +{db - noise_floor:.1f} above noise)")
    return peaks


def record_signal(freq_hz, duration_secs, output_wav, offset=125000000, gain=40):
    """Record AM audio from a frequency using rtl_fm + sox."""
    tuned_freq = int(freq_hz + offset)
    raw_file = output_wav + ".raw"

    print(f"  Recording {freq_hz/1e3:.0f} kHz for {duration_secs}s...")

    # rtl_fm outputs raw signed 16-bit samples
    cmd = [
        "rtl_fm",
        "-f", str(tuned_freq),
        "-M", "am",
        "-s", "48000",
        "-g", str(gain),
        "-l", "0",
        raw_file,
    ]

    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    try:
        time.sleep(duration_secs)
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)

    if not os.path.exists(raw_file):
        print(f"  ERROR: No audio recorded for {freq_hz/1e3:.0f} kHz")
        return False

    # Convert raw to WAV with sox
    sox_cmd = [
        "sox",
        "-r", "48000",
        "-e", "signed-integer",
        "-b", "16",
        "-c", "1",
        "-t", "raw",
        raw_file,
        output_wav,
    ]
    subprocess.run(sox_cmd, capture_output=True)
    os.remove(raw_file)

    if os.path.exists(output_wav):
        size_kb = os.path.getsize(output_wav) / 1024
        print(f"  Saved {output_wav} ({size_kb:.0f} KB)")
        return True
    return False


def transcribe(wav_path, model="base", language=None):
    """Run Whisper on a WAV file, return transcription text."""
    output_dir = os.path.dirname(wav_path)
    cmd = [
        "whisper",
        wav_path,
        "--model", model,
        "--output_format", "txt",
        "--output_dir", output_dir,
    ]
    if language:
        cmd.extend(["--language", language])

    print(f"  Transcribing {os.path.basename(wav_path)}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    txt_path = wav_path.rsplit(".", 1)[0] + ".txt"
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            text = f.read().strip()
        if text:
            print(f"  Transcript: {text[:120]}{'...' if len(text) > 120 else ''}")
        else:
            print(f"  (empty transcript)")
        return text

    print(f"  Whisper error: {result.stderr[:200] if result.stderr else 'unknown'}")
    return None


def main():
    parser = argparse.ArgumentParser(description="Scan HF frequencies, record, and transcribe")
    parser.add_argument("--start", type=float, default=530000,
                        help="Start frequency in Hz (default: 530000 = 530 kHz)")
    parser.add_argument("--stop", type=float, default=1700000,
                        help="Stop frequency in Hz (default: 1700000 = 1700 kHz)")
    parser.add_argument("--offset", type=float, default=125000000,
                        help="Upconverter offset in Hz (default: 125000000)")
    parser.add_argument("--threshold", type=float, default=10,
                        help="dB above noise floor to detect a signal (default: 10)")
    parser.add_argument("--duration", type=int, default=30,
                        help="Seconds of audio to record per station (default: 30)")
    parser.add_argument("--gain", type=int, default=40,
                        help="RTL-SDR gain (default: 40)")
    parser.add_argument("--output", type=str, default="./scans",
                        help="Output directory (default: ./scans)")
    parser.add_argument("--model", type=str, default="base",
                        help="Whisper model (default: base)")
    parser.add_argument("--language", type=str, default=None,
                        help="Language hint for Whisper (default: auto-detect)")
    parser.add_argument("--scan-only", action="store_true",
                        help="Only scan, don't record or transcribe")
    parser.add_argument("--skip-scan", type=str, default=None,
                        help="Skip scan, use comma-separated frequencies in Hz to record")
    parser.add_argument("--no-transcribe", action="store_true",
                        help="Record but don't transcribe")
    parser.add_argument("--bin-size", type=int, default=10000,
                        help="Frequency bin size for scanning in Hz (default: 10000)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scan_dir = output_dir / timestamp
    scan_dir.mkdir(parents=True, exist_ok=True)

    print(f"HF Scanner")
    print(f"  Range: {args.start/1e3:.0f} - {args.stop/1e3:.0f} kHz")
    print(f"  Upconverter offset: {args.offset/1e6:.0f} MHz")
    print(f"  Output: {scan_dir}")
    print()

    # Step 1: Scan or use provided frequencies
    if args.skip_scan:
        freqs = [float(f.strip()) for f in args.skip_scan.split(",")]
        peaks = [(f, 0) for f in freqs]
        print(f"Using provided frequencies: {[f'{f/1e3:.0f} kHz' for f in freqs]}")
    else:
        print("=== Step 1: Scanning for signals ===")
        samples = scan_range(args.start, args.stop, bin_size=args.bin_size,
                             offset=args.offset, gain=args.gain)
        peaks = find_peaks(samples, threshold_db=args.threshold)

        # Save scan results
        scan_csv = scan_dir / "scan_results.csv"
        with open(scan_csv, "w") as f:
            f.write("frequency_hz,frequency_khz,power_db\n")
            for freq, db in samples:
                f.write(f"{freq:.0f},{freq/1e3:.1f},{db:.1f}\n")
        print(f"  Scan data saved to {scan_csv}")

        if not peaks:
            print("\nNo signals detected. Try lowering --threshold.")
            return

    if args.scan_only:
        print("\nScan complete (--scan-only mode)")
        return

    # Step 2: Record each signal
    print(f"\n=== Step 2: Recording {len(peaks)} signals ({args.duration}s each) ===")
    recorded = []
    for i, (freq, db) in enumerate(peaks):
        label = f"{freq/1e3:.0f}kHz"
        wav_path = str(scan_dir / f"{label}.wav")
        print(f"\n[{i+1}/{len(peaks)}] {label}")
        if record_signal(freq, args.duration, wav_path, offset=args.offset, gain=args.gain):
            recorded.append((freq, wav_path))
        # small delay between recordings to let the tuner settle
        if i < len(peaks) - 1:
            time.sleep(1)

    if not recorded:
        print("\nNo audio recorded.")
        return

    if args.no_transcribe:
        print(f"\nDone. {len(recorded)} recordings saved to {scan_dir}")
        return

    # Step 3: Transcribe
    print(f"\n=== Step 3: Transcribing {len(recorded)} recordings ===")
    results = []
    for i, (freq, wav_path) in enumerate(recorded):
        print(f"\n[{i+1}/{len(recorded)}] {freq/1e3:.0f} kHz")
        text = transcribe(wav_path, model=args.model, language=args.language)
        results.append((freq, wav_path, text))

    # Summary
    print(f"\n{'='*60}")
    print(f"SCAN SUMMARY — {timestamp}")
    print(f"{'='*60}")
    for freq, wav_path, text in results:
        print(f"\n{freq/1e3:.0f} kHz:")
        if text:
            print(f"  {text[:200]}")
        else:
            print(f"  (no transcription)")
    print(f"\nFiles saved to {scan_dir}")


if __name__ == "__main__":
    main()
