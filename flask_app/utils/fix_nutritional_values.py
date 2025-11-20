#!/usr/bin/env python3
"""
merged_inline_fix_with_state.py

Fixes:
1) Convert ex:category "Sandwich" → ex:category ex:Sandwich
2) Convert numeric strings → numbers for numeric fields
3) Add ex:state ex:Solid or ex:Liquid based on category
4) Preserve formatting & triple order
5) Handles already converted ex:Category as well
"""

import re
import shutil
from pathlib import Path

INPUT = Path("combined_menu_original.ttl")
BACKUP = INPUT.with_suffix(".bak")
OUTPUT = Path("combined_menu_fixed.ttl")

# ---------------------------------------
# CATEGORY LIST
# ---------------------------------------
CATEGORIES = [
    "Bread", "Breakfast", "Cheese", "Condiment", "Dessert",
    "Drink", "Extra", "KidsMeal", "Pizza", "Protein",
    "Salad", "Sandwich", "Sauces", "Seasonings", "Snack",
    "Veggies", "Wrap"
]

# ---------------------------------------
# SOLID / LIQUID LOGIC
# ---------------------------------------
CATEGORY_TO_STATE = {
    "Drink": "Liquid"
}
DEFAULT_STATE = "Solid"

# ---------------------------------------
# REGEX PATTERNS
# ---------------------------------------
category_pattern = re.compile(
    r'(?P<prefix>\bex:category\s+)'  # the prefix
    r'(?:'  # either quoted or already ex:Category
    r'"(?P<cat1>' + "|".join(CATEGORIES) + r')"'
    r'|'
    r'(?P<cat2>ex:(?:' + "|".join(CATEGORIES) + r'))'
    r')'
    r'(?P<trail>\s*[;.,])'
)

NUMERIC_PREDICATES = [
    "calories", "totalFat", "saturatedFat", "transFat",
    "cholesterol", "sodium", "carbs", "fiber",
    "sugars", "protein"
]

numeric_pattern = re.compile(
    r'(?P<prefix>\bex:(?:' + "|".join(NUMERIC_PREDICATES) + r')\b\s+)'
    r'"(?P<number>[0-9]+(?:\.[0-9]+)?)"'
    r'(?P<trail>\s*[;.,])'
)

subject_end = re.compile(r'\.\s*$')

# ---------------------------------------
# HELPER
# ---------------------------------------
def infer_state_from_category(category):
    """Return Solid/Liquid based on category."""
    return CATEGORY_TO_STATE.get(category, DEFAULT_STATE)

# ---------------------------------------
# MAIN
# ---------------------------------------
def main():
    if not INPUT.exists():
        print(f"ERROR: file not found: {INPUT}")
        return

    shutil.copyfile(INPUT, BACKUP)
    print(f"Backup created at {BACKUP}")

    with INPUT.open("r", encoding="utf-8") as fin, OUTPUT.open("w", encoding="utf-8") as fout:
        subject_lines = []
        current_state = None

        for lineno, line in enumerate(fin, start=1):
            # Fix numeric literals (replace quotes with numbers)
            line = numeric_pattern.sub(lambda m: f"{m.group('prefix')}{m.group('number')}{m.group('trail')}", line)

            # Fix category (handles quoted and already ex:Category)
            def category_repl(m):
                nonlocal current_state
                cat = m.group("cat1") or m.group("cat2")  # pick whichever matched
                cat_name = cat.replace("ex:", "")  # remove ex: prefix for state inference
                current_state = infer_state_from_category(cat_name)
                return f"{m.group('prefix')}ex:{cat_name}{m.group('trail')}"

            line = category_pattern.sub(category_repl, line)

            # Collect lines for the current subject
            subject_lines.append(line)

            # If end of subject, inject state before final "."
            if subject_end.search(line):
                all_text = "".join(subject_lines).rstrip()
                if current_state:
                    # Replace last '.' with ';' for chaining
                    if all_text.endswith('.'):
                        all_text = all_text[:-1] + ' ;'
                    # Determine indentation (match last non-empty line)
                    last_nonempty = next((l for l in reversed(subject_lines) if l.strip()), "")
                    indent_match = re.match(r'(\s*)', last_nonempty)
                    indent = indent_match.group(1) if indent_match else '    '
                    # Append ex:state triple
                    all_text += f"\n{indent}ex:hasPhysicalState ex:{current_state} .\n"
                else:
                    all_text += "\n"
                fout.write(all_text)

                # Reset for next item
                subject_lines = []
                current_state = None

    print("\nDONE — Output saved to:", OUTPUT)
    print("To replace original: mv", OUTPUT, INPUT)

# ---------------------------------------
if __name__ == "__main__":
    main()