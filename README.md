# HomiSort

**فارسی** | [English](#english)

مرتب‌سازی عکس و فایل در پوشه‌های تاریخ شمسی و پیدا کردن فایل‌های تکراری. فقط کتابخانه‌ی استاندارد پایتون؛ Pillow اختیاری است (برای تاریخ EXIF، وگرنه تاریخ تغییر فایل).

```
python homisort.py sort مبدأ مقصد                  # فقط گزارش (dry-run)
python homisort.py sort مبدأ مقصد --apply          # جابه‌جایی واقعی
python homisort.py sort مبدأ مقصد --apply --copy   # کپی به‌جای جابه‌جایی
python homisort.py dupes مبدأ --csv report.csv     # گزارش تکراری‌ها
python homisort.py test                            # تست‌ها
```

خروجی: `مقصد/1403/01-فروردین/فایل.jpg`

ایمنی: پیش‌فرض dry-run است، هیچ فایلی حذف نمی‌شود، روی فایل موجود بازنویسی نمی‌شود (نام تکراری ← `_1`، `_2`، ...). دستور `dupes` فقط گزارش CSV می‌دهد (اول با اندازه، سپس SHA256).

## English

Sort photos and files into Jalali (Persian) date folders and find duplicates. Pure Python standard library; Pillow is optional (EXIF date, otherwise file modification time).

```
python homisort.py sort SRC DEST                 # report only (dry-run)
python homisort.py sort SRC DEST --apply         # really move
python homisort.py sort SRC DEST --apply --copy  # copy instead of move
python homisort.py dupes SRC --csv report.csv    # duplicate report
python homisort.py test                          # run tests
```

Output: `DEST/1403/01-فروردین/file.jpg` (Persian month names, ASCII digits).

Safety: dry-run by default, nothing is ever deleted, existing files are never overwritten (name clash → `_1`, `_2`, ...). `dupes` only writes a CSV report (grouped by size first, then SHA256).

## License

See [LICENSE](LICENSE).
