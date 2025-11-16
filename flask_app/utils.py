from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from pathlib import Path
import numpy as np

# --- Load graph ---
g = Graph()
BASE_DIR = Path(__file__).resolve().parent
ttl_file = BASE_DIR / "utils" / "combined_menu.ttl"
g.parse(ttl_file, format="ttl")

# Namespace FIXED — now matches your TTL exactly
EX = Namespace("http://example.com/menu#")

# Helper for URI → local name
def get_local_name(uri):
    if uri is None:
        return ""
    last = str(uri).split("/")[-1]
    return last.replace("_", " ")

# SPARQL ALL ITEMS
query_all = prepareQuery("""
    SELECT ?name ?company ?calories ?protein ?fat ?carbs ?category
    WHERE {
        ?s a ex:MenuItem ;
           ex:itemName ?name ;
           ex:company ?company ;
           ex:calories ?calories ;
           ex:protein ?protein ;
           ex:totalFat ?fat ;
           ex:carbs ?carbs ;
           OPTIONAL { ?s ex:category ?category }
    }
""", initNs={"ex": EX})

# --- Consulta SPARQL para obtener todos los platos ---
def get_items_sparql():
    results = []
    for row in g.query(query_all):
        results.append({
            "name": str(row.name),
            "company": get_local_name(row.company),
            "calories": float(row.calories),
            "protein": float(row.protein),
            "fat": float(row.fat),
            "carbs": float(row.carbs),
            "category": get_local_name(row.category)
        })
    return results

# Recommender
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