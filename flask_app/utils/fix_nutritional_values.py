#!/usr/bin/env python3
"""
merged_inline_fix.py

Fix 1: Convert ex:category "Sandwich" → ex:category ex:Sandwich
Fix 2: Convert numeric strings → numbers for all float/number predicates.

All while preserving original formatting and triple order.
"""

import re
import shutil
from pathlib import Path

INPUT = Path("combined_menu.ttl")
BACKUP = INPUT.with_suffix(INPUT.suffix + ".bak")
OUTPUT = Path("combined_menu_fixed_2.ttl")

# -----------------------------
# 1) CATEGORY FIX CONFIG
# -----------------------------
CATEGORIES = [
    "Bread", "Breakfast", "Cheese", "Condiment", "Dessert",
    "Drink", "Extra", "KidsMeal", "Pizza", "Protein",
    "Salad", "Sandwich", "Sauces", "Seasonings", "Snack",
    "Veggies", "Wrap"
]

# Regex: ex:category "Sandwich"
category_pattern = re.compile(
    r'(?P<prefix>\bex:category\s+)"(?P<cat>' + "|".join(CATEGORIES) + r')"(?P<trail>\s*[;.,])'
)

# -----------------------------
# 2) NUMERIC FIX CONFIG
# -----------------------------
NUMERIC_PREDICATES = [
    "calories", "totalFat", "saturatedFat", "transFat",
    "cholesterol", "sodium", "carbs", "fiber",
    "sugars", "protein"
]

numeric_pattern = re.compile(
    r'(?P<prefix>\bex:(?:' + "|".join(NUMERIC_PREDICATES) + r')\b\s+)'    # ex:calories
    r'"(?P<number>[0-9]+(?:\.[0-9]+)?)"'                                  # "250" or "12.0"
    r'(?P<trail>\s*[;.,])'
)

# -----------------------------
# PER-LINE REPLACEMENT
# -----------------------------
def fix_line(line: str, lineno: int):

    # 1) Fix category value
    line_new = category_pattern.sub(
        lambda m: (
            print(f"[line {lineno}] CATEGORY: {m.group('cat')} → ex:{m.group('cat')}"),
            f"{m.group('prefix')}ex:{m.group('cat')}{m.group('trail')}"
        )[1],
        line,
        count=1
    )

    # 2) Fix numeric literal
    line_new2 = numeric_pattern.sub(
        lambda m: (
            print(f"[line {lineno}] NUMERIC: {m.group('number')} (string) → {m.group('number')}"),
            f"{m.group('prefix')}{m.group('number')}{m.group('trail')}"
        )[1],
        line_new,
        count=1
    )

    return line_new2

# -----------------------------
# MAIN
# -----------------------------
def main():
    if not INPUT.exists():
        print(f"ERROR: Input file not found: {INPUT}")
        return

    shutil.copyfile(INPUT, BACKUP)
    print(f"Backup created: {BACKUP}")

    with INPUT.open("r", encoding="utf-8") as fin, OUTPUT.open("w", encoding="utf-8") as fout:
        for i, line in enumerate(fin, start=1):
            fout.write(fix_line(line, i))

    print(f"\nFix completed.")
    print(f"Output written to: {OUTPUT}")
    print(f"To overwrite the original: mv {OUTPUT} {INPUT}")


if __name__ == "__main__":
    main()