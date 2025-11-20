from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from rdflib.namespace import SKOS, RDF, XSD
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)

# --- Load graph ---
g = Graph()
BASE_DIR = Path(__file__).resolve().parent
ttl_file = BASE_DIR / "utils" / "merged.ttl"
g.parse(ttl_file, format="ttl")

# Namespace
EX = Namespace("http://example.com/menu#")
g.bind("ex", EX)
g.bind("skos", SKOS)
g.bind("xsd", XSD)

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

# --- SPARQL ---
query_all = prepareQuery("""
PREFIX ex: <http://example.com/menu#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT
    ?item ?name ?company ?calories ?protein ?fat ?carbs
    ?sugars ?saturatedFat ?sodium ?category ?state ?sealLabel
WHERE {

    ### CORE PRODUCT DATA ###
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

    # Normalize state to plain string "solid"|"liquid"
    BIND(
        IF(?stateRaw = ex:Liquid, "liquid",
            IF(?stateRaw = ex:Solid, "solid", "solid")
        ) AS ?state
    )

    ###########################
    ### NUTRITIONAL SEALS #####
    ###########################

    # SUGAR SEAL — compare numeric values, cast item value to decimal
    OPTIONAL {
        ?sealSugar a ex:HighSugar ;
                   skos:prefLabel ?sealSugarLabel ;
                   ex:thresholdLiquid ?sugarLiquid ;
                   ex:thresholdSolid ?sugarSolid .
        FILTER(
            (?state = "solid"  && xsd:float(?sugars) >= xsd:float(?sugarSolid)) ||
            (?state = "liquid" && xsd:float(?sugars) >= xsd:float(?sugarLiquid))
        )
        BIND(?sealSugarLabel AS ?sealLabel)
    }

    # SATURATED FAT SEAL
    OPTIONAL {
        ?sealSF a ex:HighSaturatedFat ;
                skos:prefLabel ?sealSFLabel ;
                ex:thresholdLiquid ?sfLiquid ;
                ex:thresholdSolid ?sfSolid .
        FILTER(
            (?state = "solid"  && xsd:float(?saturatedFat) >= xsd:float(?sfSolid)) ||
            (?state = "liquid" && xsd:float(?saturatedFat) >= xsd:float(?sfLiquid))
        )
        BIND(?sealSFLabel AS ?sealLabel)
    }

    # CALORIES SEAL
    OPTIONAL {
        ?sealCal a ex:HighCalories ;
                 skos:prefLabel ?sealCalLabel ;
                 ex:thresholdLiquid ?calLiquid ;
                 ex:thresholdSolid ?calSolid .
        FILTER(
            (?state = "solid"  && xsd:float(?calories) >= xsd:float(?calSolid)) ||
            (?state = "liquid" && xsd:float(?calories) >= xsd:float(?calLiquid))
        )
        BIND(?sealCalLabel AS ?sealLabel)
    }

    # SODIUM SEAL
    OPTIONAL {
        ?sealNa a ex:HighSodium ;
                skos:prefLabel ?sealNaLabel ;
                ex:thresholdLiquid ?naLiquid ;
                ex:thresholdSolid ?naSolid .
        FILTER(
            (?state = "solid"  && xsd:float(?sodium) >= xsd:float(?naSolid)) ||
            (?state = "liquid" && xsd:float(?sodium) >= xsd:float(?naLiquid))
        )
        BIND(?sealNaLabel AS ?sealLabel)
    }
}
""", initNs={"ex": EX, "skos": SKOS, "xsd": XSD})

# --- Build item list ---
def get_items_sparql():
    """
    Run the SPARQL that calculates seals and return a list of item dicts
    with accumulated seals.
    """
    items_map = {}

    for row in g.query(query_all):

        item_uri = str(row.item)
        name = str(row.name)

        # Initialize item entry if new
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
                # ensure state is a clean string (fallback to "solid")
                "state": str(row.state) if row.state else "solid",
                "seals": []
            }

        # Append seal label when present (don't overwrite)
        if row.sealLabel:
            seal_label = str(row.sealLabel)
            if seal_label not in items_map[item_uri]["seals"]:
                items_map[item_uri]["seals"].append(seal_label)

    # Convert to list for use in the app
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