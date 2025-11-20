from rdflib import Graph, Namespace
from rdflib.namespace import SKOS, XSD
from rdflib.plugins.sparql import prepareQuery
from pathlib import Path
import logging
import numpy as np
logger = logging.getLogger(__name__)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
ORIGINAL_FILE = BASE_DIR / "utils/merged.ttl"
CACHE_FILE = BASE_DIR / "utils/menu_with_seals.ttl"

# --- Namespaces ---
EX = Namespace("http://example.com/menu#")

# --- Helper functions ---
def get_local_name(uri):
    return str(uri).split("/")[-1].replace("_", " ") if uri else ""

def clean_category(uri):
    return uri.split("#")[-1] if uri else ""

def safe_float(lit):
    if lit is None:
        return 0.0
    value = str(lit).strip()
    if value.startswith("<"):
        return 1.0
    if value.startswith(">"):
        try:
            return float(value[1:])
        except:
            return 1.0
    try:
        return float(value)
    except:
        return 0.0

# --- Load graph with cache ---
g = Graph()
g.bind("ex", EX)
g.bind("skos", SKOS)
g.bind("xsd", XSD)

if CACHE_FILE.exists():
    logger.info(f"Cargando grafo desde cache: {CACHE_FILE}")
    g.parse(CACHE_FILE, format="ttl")
else:
    logger.info("Cache no encontrada. Cargando grafo original y calculando sellos...")
    g.parse(ORIGINAL_FILE, format="ttl")

    # --- SPARQL dinámico para calcular sellos ---
    query_all = """
    PREFIX ex: <http://example.com/menu#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?item ?seal ?sealLabel ?nutrient ?thresholdSolid ?thresholdLiquid ?state ?calories ?sugars ?saturatedFat ?sodium
    WHERE {
        ?item a ex:MenuItem ;
              ex:hasPhysicalState ?stateRaw ;
              ex:calories ?calories ;
              ex:sugars ?sugars ;
              ex:saturatedFat ?saturatedFat ;
              ex:sodium ?sodium .

        ?seal a ex:NutritionalSeal ;
              skos:prefLabel ?sealLabel ;
              ex:nutrient ?nutrient ;
              ex:thresholdSolid ?thresholdSolid ;
              ex:thresholdLiquid ?thresholdLiquid .

        BIND(IF(?stateRaw = ex:Liquid, "liquid", "solid") AS ?state)

        BIND(
            IF(?nutrient = "calories", ?calories,
            IF(?nutrient = "sugars", ?sugars,
            IF(?nutrient = "saturatedFat", ?saturatedFat,
            IF(?nutrient = "sodium", ?sodium, 0)))) AS ?nutrientValue
        )

        FILTER(
            (?state = "solid"  && xsd:float(?nutrientValue) >= xsd:float(?thresholdSolid)) ||
            (?state = "liquid" && xsd:float(?nutrientValue) >= xsd:float(?thresholdLiquid))
        )
    }
    """
    prepared_query = prepareQuery(query_all, initNs={"ex": EX, "skos": SKOS, "xsd": XSD})

    # --- Agregar triples hasNutritionalSeal ---
    for row in g.query(prepared_query):
        g.add((row.item, EX.hasNutritionalSeal, row.seal))

    # --- Guardar cache ---
    g.serialize(destination=CACHE_FILE, format="ttl")
    logger.info(f"Grafo con sellos guardado en cache: {CACHE_FILE}")



# --- Función para obtener items con sellos ---
def get_items_sparql():
    items_map = {}

    query = """
    PREFIX ex: <http://example.com/menu#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?item ?name ?company ?calories ?protein ?fat ?carbs ?sugars ?saturatedFat ?sodium ?category ?state ?seal ?sealLabel
    WHERE {
        ?item a ex:MenuItem ;
              ex:itemName ?name ;
              ex:company ?company ;
              ex:calories ?calories ;
              ex:protein ?protein ;
              ex:totalFat ?fat ;
              ex:carbs ?carbs ;
              ex:sugars ?sugars ;
              ex:saturatedFat ?saturatedFat ;
              ex:sodium ?sodium .

        OPTIONAL { ?item ex:category ?category }
        OPTIONAL { ?item ex:hasPhysicalState ?stateRaw }

        BIND(IF(?stateRaw = ex:Liquid, "liquid", "solid") AS ?state)

        OPTIONAL {
            ?item ex:hasNutritionalSeal ?seal .
            ?seal skos:prefLabel ?sealLabel .
        }
    }
    """
    prepared_query = prepareQuery(query, initNs={"ex": EX, "skos": SKOS})

    for row in g.query(prepared_query):
        item_uri = str(row.item)
        name = str(row.name)

        if item_uri not in items_map:
            items_map[item_uri] = {
                "uri": item_uri,
                "name": name,
                "company": get_local_name(row.company),
                "calories": safe_float(row.calories),
                "protein": safe_float(row.protein),
                "fat": safe_float(row.fat),
                "carbs": safe_float(row.carbs),
                "sugars": safe_float(row.sugars),
                "saturatedFat": safe_float(row.saturatedFat),
                "sodium": safe_float(row.sodium),
                "category": clean_category(row.category) if row.category else "",
                "state": str(row.state) if row.state else "solid",
                "seals": []
            }

        if row.sealLabel:
            seal_label = str(row.sealLabel)
            if seal_label not in items_map[item_uri]["seals"]:
                items_map[item_uri]["seals"].append(seal_label)

    return list(items_map.values())


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