#!/usr/bin/env python3
"""HomiSort - sort files into Jalali (Shamsi) date folders and find duplicates.

Usage:
  python homisort.py sort SRC DEST [--apply] [--copy]
  python homisort.py dupes SRC [--csv report.csv]
  python homisort.py test
"""
import argparse
import csv
import datetime as dt
import hashlib
import os
import shutil
import sys
import unittest

MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

_G_D_M = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


def gregorian_to_jalali(gy, gm, gd):
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + _G_D_M[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def file_date(path):
    """EXIF date if Pillow is available, else modification time."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            exif = im.getexif()
            raw = exif.get(36867) or exif.get(306)
            if not raw:
                raw = exif.get_ifd(0x8769).get(36867)
            if raw:
                return dt.datetime.strptime(str(raw)[:10], "%Y:%m:%d").date()
    except Exception:
        pass
    return dt.date.fromtimestamp(os.path.getmtime(path))


def target_dir(dest, d):
    jy, jm, _ = gregorian_to_jalali(d.year, d.month, d.day)
    return os.path.join(dest, str(jy), "%02d-%s" % (jm, MONTHS[jm - 1]))


def unique_path(path, taken):
    base, ext = os.path.splitext(path)
    cand, n = path, 0
    while os.path.exists(cand) or cand.lower() in taken:
        n += 1
        cand = "%s_%d%s" % (base, n, ext)
    return cand


def walk_files(src, skip=None):
    skip = os.path.abspath(skip) if skip else None
    for root, dirs, files in os.walk(src):
        if skip:
            dirs[:] = [d for d in dirs
                       if os.path.abspath(os.path.join(root, d)) != skip]
        for f in files:
            yield os.path.join(root, f)


def cmd_sort(a):
    src, dest = os.path.abspath(a.src), os.path.abspath(a.dest)
    if not os.path.isdir(src):
        sys.exit("پوشه مبدأ پیدا نشد: " + src)
    taken, count = set(), 0
    for p in sorted(walk_files(src, skip=dest)):
        folder = target_dir(dest, file_date(p))
        new = unique_path(os.path.join(folder, os.path.basename(p)), taken)
        taken.add(new.lower())
        print("%s -> %s" % (p, new))
        count += 1
        if a.apply:
            os.makedirs(folder, exist_ok=True)
            (shutil.copy2 if a.copy else shutil.move)(p, new)
    mode = ("کپی" if a.copy else "جابه‌جایی") if a.apply else "گزارش (dry-run)"
    print("%d فایل - حالت: %s" % (count, mode))
    if not a.apply:
        print("برای اجرای واقعی --apply را بزنید.")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_dupes(src):
    by_size = {}
    for p in walk_files(src):
        try:
            by_size.setdefault(os.path.getsize(p), []).append(p)
        except OSError:
            pass
    by_hash = {}
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for p in paths:
            try:
                by_hash.setdefault((size, sha256(p)), []).append(p)
            except OSError:
                pass
    return {k: v for k, v in by_hash.items() if len(v) > 1}


def cmd_dupes(a):
    groups = find_dupes(a.src)
    out = open(a.csv, "w", newline="", encoding="utf-8-sig") if a.csv \
        else sys.stdout
    w = csv.writer(out)
    w.writerow(["group", "sha256", "size", "path"])
    for i, ((size, h), paths) in enumerate(sorted(groups.items()), 1):
        for p in sorted(paths):
            w.writerow([i, h, size, p])
    if a.csv:
        out.close()
    print("%d گروه تکراری (هیچ فایلی حذف نشد)" % len(groups), file=sys.stderr)


class Tests(unittest.TestCase):
    def test_known_dates(self):
        cases = {(2024, 3, 20): (1403, 1, 1), (2023, 3, 21): (1402, 1, 1),
                 (2025, 3, 21): (1404, 1, 1), (2024, 3, 19): (1402, 12, 29),
                 (2024, 12, 31): (1403, 10, 11), (2000, 1, 1): (1378, 10, 11),
                 (2025, 1, 1): (1403, 10, 12)}
        for g, j in cases.items():
            self.assertEqual(gregorian_to_jalali(*g), j, g)

    def test_sort_and_dupes(self):
        sys.stdout.reconfigure(errors="replace")
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            src, dest = os.path.join(t, "s"), os.path.join(t, "d")
            os.makedirs(src)
            for name, data, day in [("a.txt", b"x", "2024-03-20"),
                                    ("b.txt", b"x", "2024-03-20"),
                                    ("c.txt", b"yy", "2024-04-25")]:
                p = os.path.join(src, name)
                with open(p, "wb") as f:
                    f.write(data)
                ts = dt.datetime.fromisoformat(day + "T12:00").timestamp()
                os.utime(p, (ts, ts))
            ns = argparse.Namespace
            cmd_sort(ns(src=src, dest=dest, apply=False, copy=False))
            self.assertFalse(os.path.exists(dest))
            cmd_sort(ns(src=src, dest=dest, apply=True, copy=True))
            self.assertEqual(len(os.listdir(src)), 3)
            f = os.path.join(dest, "1403", "01-فروردین")
            self.assertEqual(sorted(os.listdir(f)), ["a.txt", "b.txt"])
            self.assertTrue(os.path.exists(os.path.join(
                dest, "1403", "02-اردیبهشت", "c.txt")))
            # collision: existing file is never overwritten
            cmd_sort(ns(src=src, dest=dest, apply=True, copy=True))
            self.assertIn("a_1.txt", os.listdir(f))
            self.assertEqual(len(find_dupes(src)), 1)


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="HomiSort")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sort", help="sort files into Jalali folders")
    s.add_argument("src")
    s.add_argument("dest")
    s.add_argument("--apply", action="store_true", help="actually move/copy")
    s.add_argument("--copy", action="store_true", help="copy instead of move")
    d = sub.add_parser("dupes", help="report duplicate files (CSV)")
    d.add_argument("src")
    d.add_argument("--csv", help="output file (default: stdout)")
    sub.add_parser("test", help="run self-tests")
    a = ap.parse_args()
    if a.cmd == "sort":
        cmd_sort(a)
    elif a.cmd == "dupes":
        cmd_dupes(a)
    else:
        unittest.main(argv=[sys.argv[0]], verbosity=2)


if __name__ == "__main__":
    main()
