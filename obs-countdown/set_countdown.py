#!/usr/bin/env python3
"""
set_countdown.py — Write the countdown target file consumed by obs_countdown.py

Usage:
  # Count down to a specific date/time
  python set_countdown.py target "2026-04-18 20:00:00"

  # Count down from a duration starting NOW
  python set_countdown.py duration 1:30:00

  # Print current target without changing it
  python set_countdown.py read
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

DEFAULT_FILE = "countdown.txt"


def write_target(dt: datetime, path: str):
    with open(path, "w") as fh:
        fh.write(f"TARGET: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"Countdown set → {dt.strftime('%Y-%m-%d %H:%M:%S')}  (file: {path})")


def parse_duration(s: str) -> timedelta:
    parts = s.strip().split(":")
    if len(parts) == 3:
        h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
    elif len(parts) == 2:
        h, m, sec = 0, int(parts[0]), int(parts[1])
    else:
        raise ValueError(f"Cannot parse duration '{s}'. Use H:MM:SS or MM:SS.")
    return timedelta(hours=h, minutes=m, seconds=sec)


def cmd_target(args):
    try:
        dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        sys.exit("Date must be in format: YYYY-MM-DD HH:MM:SS")
    write_target(dt, args.file)


def cmd_duration(args):
    try:
        delta = parse_duration(args.duration)
    except ValueError as e:
        sys.exit(str(e))
    write_target(datetime.now() + delta, args.file)


def cmd_read(args):
    path = args.file
    if not os.path.isfile(path):
        sys.exit(f"File not found: {path}")
    with open(path) as fh:
        content = fh.read().strip()
    print(content)
    # Also show remaining time
    for line in content.splitlines():
        if line.upper().startswith("TARGET:"):
            val = line.split(":", 1)[1].strip()
            try:
                target = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                delta = target - datetime.now()
                total = int(delta.total_seconds())
                if total <= 0:
                    print("Status: countdown finished")
                else:
                    d, r = divmod(total, 86400)
                    h, r = divmod(r, 3600)
                    m, s = divmod(r, 60)
                    parts = []
                    if d:
                        parts.append(f"{d}d")
                    parts += [f"{h:02d}h", f"{m:02d}m", f"{s:02d}s"]
                    print(f"Remaining: {' '.join(parts)}")
            except ValueError:
                pass


def main():
    p = argparse.ArgumentParser(description="Write/read obs_countdown target file")
    p.add_argument("--file", "-f", default=DEFAULT_FILE,
                   help=f"Path to countdown file (default: {DEFAULT_FILE})")
    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("target", help="Set countdown to a specific datetime")
    t.add_argument("datetime", help="Target datetime, e.g. '2026-04-18 20:00:00'")
    t.set_defaults(func=cmd_target)

    d = sub.add_parser("duration", help="Set countdown from a duration starting now")
    d.add_argument("duration", help="Duration, e.g. 1:30:00 or 45:00")
    d.set_defaults(func=cmd_duration)

    r = sub.add_parser("read", help="Show current countdown file and remaining time")
    r.set_defaults(func=cmd_read)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
