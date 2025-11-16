from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from pathlib import Path
import numpy as np

# --- Load graph ---
g = Graph()
BASE_DIR = Path(__file__).resolve().parent
ttl_file = BASE_DIR / "utils" / "combined_menu.ttl"
g.parse(ttl_file, format="ttl")

# Namespace
EX = Namespace("http://example.com/menu#")

def get_local_name(uri):
    if uri is None:
        return ""
    return str(uri).split("/")[-1].replace("_", " ")

def clean_category(uri):
    if not uri:
        return ""
    return uri.split("#")[-1]

def safe_float(lit):
    if lit is None:
        return 0.0

    value = str(lit).strip()

    # Handle <1 etc.
    if value.startswith("<"):
        return 1.0
    if value.startswith(">"):
        return float(value[1:]) if value[1:].isdigit() else 1.0

    try:
        return float(value)
    except ValueError:
        return 0.0

# Thresholds copied EXACTLY from your working test script
thresholds = {
    "HighSugar": {"solid": 10.0, "liquid": 5.0, "label": "High in Sugar"},
    "HighSaturatedFat": {"solid": 4.0, "liquid": 3.0, "label": "High in Saturated Fat"},
    "HighCalories": {"solid": 275.0, "liquid": 70.0, "label": "High in Calories"},
    "HighSodium": {"solid": 400.0, "liquid": 100.0, "label": "High in Sodium"},
}

def compute_seals(item):
    state = item.get("state", "Solid").lower()
    seals = []
    if item["sugars"] >= thresholds["HighSugar"][state]:
        seals.append(thresholds["HighSugar"]["label"])
    if item["fat"] >= thresholds["HighSaturatedFat"][state]:
        seals.append(thresholds["HighSaturatedFat"]["label"])
    if item["calories"] >= thresholds["HighCalories"][state]:
        seals.append(thresholds["HighCalories"]["label"])
    if item["sodium"] >= thresholds["HighSodium"][state]:
        seals.append(thresholds["HighSodium"]["label"])
    return seals

# --- SPARQL ---
query_all = prepareQuery("""
SELECT ?name ?company ?calories ?protein ?fat ?carbs ?sugars ?saturatedFat ?sodium ?category ?state
WHERE {
    ?s a ex:MenuItem ;
       ex:itemName ?name ;
       ex:company ?company ;
       ex:calories ?calories ;
       ex:protein ?protein ;
       ex:totalFat ?fat ;
       ex:carbs ?carbs ;
       ex:sugars ?sugars ;
       ex:saturatedFat ?saturatedFat ;
       ex:sodium ?sodium ;
       OPTIONAL { ?s ex:category ?category }
       OPTIONAL { ?s ex:state ?state }
}
ORDER BY ?name
""", initNs={"ex": EX})

# --- Build item list ---
def get_items_sparql():
    results = []

    for row in g.query(query_all):

        item = {
            "name": str(row.name),
            "company": get_local_name(row.company),
            "calories": safe_float(row.calories),
            "protein": safe_float(row.protein),
            "fat": safe_float(row.fat),
            "carbs": safe_float(row.carbs),
            "sugars": safe_float(row.sugars),
            "saturatedFat": safe_float(row.saturatedFat),
            "sodium": safe_float(row.sodium),
            "category": clean_category(row.category) if row.category else "",
            "state": clean_category(row.state).lower() if row.state else "solid",
        }

        item["seals"] = compute_seals(item)

        results.append(item)

    return results

# --- Recommender ---
def platos_similares(nombre, k=6):
    items = get_items_sparql()
    base = next((p for p in items if p["name"].lower() == nombre.lower()), None)
    if not base:
        return []

    X_base = np.array([base["calories"], base["protein"], base["fat"], base["carbs"]])

    sims = []
    for p in items:
        if p["name"] == base["name"]:
            continue
        X = np.array([p["calories"], p["protein"], p["fat"], p["carbs"]])
        dist = np.linalg.norm(X - X_base)
        sims.append((dist, p))

    sims.sort(key=lambda x: x[0])
    return [s[1] for s in sims[:k]]