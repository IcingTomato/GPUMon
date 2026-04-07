#!/usr/bin/env python3
"""
GPU Data Collector - runs on server, no third-party dependencies.
Saves nvidia-smi dmon output to a standardized CSV file.

Usage:
    python3 gpu_collect.py                    # default 1s sampling
    python3 gpu_collect.py -i 2               # 2s sampling interval
    python3 gpu_collect.py -o gpu_data.csv    # specify output file
    python3 gpu_collect.py -d 3600            # run for 3600 seconds

Press Ctrl+C to stop.
"""

import argparse
import csv
import os
import signal
import subprocess
import sys
import time
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description="Collect nvidia-smi dmon data to CSV")
    p.add_argument("-i", "--interval", type=int, default=1,
                   help="Sampling interval in seconds (default: 1)")
    p.add_argument("-o", "--output", type=str, default="gpu_data.csv",
                   help="Output CSV file path (default: gpu_data.csv)")
    p.add_argument("-d", "--duration", type=int, default=0,
                   help="Duration in seconds, 0 for unlimited (default: 0)")
    return p.parse_args()


def get_gpu_uuid_map():
    """Query nvidia-smi for GPU index -> UUID mapping."""
    uuid_map = {}
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 2:
                    uuid_map[parts[0]] = parts[1]
    except Exception:
        pass
    return uuid_map


def main():
    args = parse_args()
    running = True

    def on_signal(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    uuid_map = get_gpu_uuid_map()
    if uuid_map:
        print(f"Detected {len(uuid_map)} GPU(s):")
        for idx, uuid in sorted(uuid_map.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]):
            print(f"  GPU {idx}: {uuid}")
        print()

    cmd = ["nvidia-smi", "dmon", "-s", "puc", "-d", str(args.interval)]
    print(f"Starting: {' '.join(cmd)}")
    print(f"Output:   {os.path.abspath(args.output)}")
    print(f"Press Ctrl+C to stop\n")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, bufsize=1)
    except FileNotFoundError:
        print("Error: nvidia-smi not found")
        sys.exit(1)

    columns = []
    header_parsed = False
    count = 0
    start = time.time()

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "gpu", "uuid", "pwr", "gtemp", "sm", "mem",
                          "enc", "dec", "mclk", "pclk"])

        try:
            for line in proc.stdout:
                if not running:
                    break

                line = line.strip()
                if not line:
                    continue

                if line.startswith("#"):
                    if not header_parsed and ("gpu" in line.lower() or "idx" in line.lower()):
                        columns = line.lstrip("# ").split()
                        columns = [c.lower() for c in columns]
                        header_parsed = True
                    continue

                if not header_parsed:
                    continue

                parts = line.split()
                if len(parts) != len(columns):
                    continue

                row = dict(zip(columns, parts))
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                gpu_idx = row.get("gpu", row.get("idx", "0"))
                uuid = uuid_map.get(gpu_idx, "N/A")

                writer.writerow([
                    now, gpu_idx, uuid,
                    row.get("pwr", "-"),
                    row.get("gtemp", "-"),
                    row.get("sm", "-"),
                    row.get("mem", "-"),
                    row.get("enc", "-"),
                    row.get("dec", "-"),
                    row.get("mclk", "-"),
                    row.get("pclk", "-"),
                ])
                f.flush()
                count += 1

                if count % 60 == 0:
                    print(f"[{now}] Collected {count} samples")

                if args.duration > 0 and time.time() - start >= args.duration:
                    print(f"Reached {args.duration}s duration limit, stopping.")
                    break
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print(f"\nDone. {count} samples -> {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
