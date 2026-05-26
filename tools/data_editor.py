"""
Tiny CSV data editor.
Run from project root with: python tools/data_editor.py
"""

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def choose(options, prompt="Chon"):
    for i, option in enumerate(options, 1):
        print(f"[{i}] {option}")
    while True:
        raw = input(f"{prompt}: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("So khong hop le.")


def main():
    os.chdir(ROOT)
    files = sorted(DATA.rglob("*.csv"))
    idx = choose([str(p.relative_to(ROOT)) for p in files], "File")
    path = files[idx]
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []
    if not rows:
        print("File rong.")
        return
    row_idx = choose([
        " | ".join(f"{k}={v}" for k, v in row.items())
        for row in rows
    ], "Dong")
    field_idx = choose(fields, "Field")
    field = fields[field_idx]
    print(f"Gia tri cu: {rows[row_idx][field]}")
    rows[row_idx][field] = input("Gia tri moi: ")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print("Da ghi file.")


if __name__ == "__main__":
    main()
