# python
from pathlib import Path
from rdflib import Graph, Literal
import re

BASE = Path(__file__).resolve().parent
files = [
    BASE / "nutritional_ontology.ttl",
    BASE / "combined_menu.ttl",
]

g = Graph()
for p in files:
    if p.exists():
        try:
            g.parse(p.as_posix(), format="turtle")
            print(f"Parsed: `{p}` ({len(g)} triples)")
        except Exception as e:
            print(f"Failed to parse `{p}`:", e)
    else:
        print(f"Missing: `{p}`")

print(f"{len(g)} triples in graph")

# write merged Turtle
merged_path = BASE / "merged.ttl"
g.serialize(destination=merged_path.as_posix(), format="turtle", encoding="utf-8")
print(f"Wrote merged TTL to `{merged_path}`\n")

# print a short Turtle preview
ttl = g.serialize(format="turtle")
if isinstance(ttl, bytes):
    ttl = ttl.decode("utf-8")
print("Turtle preview (first 1200 chars):\n")
print(ttl[:1200].replace("\n", "\\n"))
print("\n---\n")