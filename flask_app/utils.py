from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
import numpy as np

# --- Cargar grafo RDF ---
g = Graph()
g.parse("utils/combined_menu.ttl", format="ttl")
EX = Namespace("http://example.com/menu#")

# --- Consulta SPARQL para obtener todos los platos ---
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

def get_items_sparql():
    """Devuelve todos los platos como lista de diccionarios."""
    results = []
    for row in g.query(query_all):
        results.append({
            "name": str(row.name),
            "company": str(row.company),
            "calories": float(row.calories),
            "protein": float(row.protein),
            "fat": float(row.fat),
            "carbs": float(row.carbs),
            "category": str(row.category) if row.category else ""
        })
    return results

#Recomendador en base a distancia euclidiana
def platos_similares(nombre, k=6):
    items = get_items_sparql()
    base = next((p for p in items if p["name"].lower() == nombre.lower()), None)
    if not base:
        return []
    
    # Vector de nutrientes
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