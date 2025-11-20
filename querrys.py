import requests
import random

# Tolerancias sugeridas para cada nutriente
TOLERANCES = {
    "calories": 50,       # ±50 kcal
    "totalfat": 3,        # ±3 g
    "fatsaturated": 2,    # ±2 g
    "fattrans": 0.5,      # ±0.5 g
    "cholesterol": 20,    # ±20 mg
    "sodium": 100,        # ±100 mg
    "carbs": 10,          # ±10 g
    "fiber": 2,           # ±2 g
    "sugar": 2,           # ±2 g
    "protein": 5          # ±5 g
}

ENDPOINT = "https://wikifcd.wikibase.cloud/query/sparql"

def get_similar_foods(reference_values, limit=100, sample_size=6, lang="en"):
    """
    Devuelve alimentos similares a un alimento de referencia según ventanas ± tolerancia
    y trae automáticamente los labels en inglés para los resultados aleatorios.
    """
    param_map = {
        "calories": "calories",
        "totalfat": "totalfat",
        "fatsaturated": "fatsaturated",
        "fattrans": "fattrans",
        "cholesterol": "cholesterol",
        "sodium": "sodium",
        "carbs": "carbs",
        "fiber": "fiber",
        "sugar": "sugar",
        "protein": "protein"
    }

    # Construir filtros SPARQL
    filters = []
    for key, var in param_map.items():
        if key in reference_values:
            val = reference_values[key]
            tol = TOLERANCES.get(key, 0)
            filters.append(f"FILTER(?{var} >= {val - tol} && ?{var} <= {val + tol})")
    filter_block = "\n  ".join(filters)

    # Consulta SPARQL principal (sin labels)
    query = f"""
    PREFIX wb: <https://wikifcd.wikibase.cloud/entity/>
    PREFIX p: <https://wikifcd.wikibase.cloud/prop/>
    PREFIX ps: <https://wikifcd.wikibase.cloud/prop/statement/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT 
      ?food 
      ?sodium 
      ?sugar
      ?calories
      ?fatsaturated
      ?totalfat
      ?cholesterol
      ?fattrans
      ?protein
      ?fiber
      ?carbs
    WHERE {{
      ?food p:P18 ?stmtSodium. ?stmtSodium ps:P18 ?sodium.
      ?food p:P104 ?stmtSugar. ?stmtSugar ps:P104 ?sugar.
      ?food p:P6 ?stmtCalories. ?stmtCalories ps:P6 ?calories.
      ?food p:P86 ?stmtFatSaturated. ?stmtFatSaturated ps:P86 ?fatsaturated.
      ?food p:P8 ?stmtTotalFat. ?stmtTotalFat ps:P8 ?totalfat.
      ?food p:P99 ?stmtCholesterol. ?stmtCholesterol ps:P99 ?cholesterol.
      ?food p:P271 ?stmtFatTrans. ?stmtFatTrans ps:P271 ?fattrans.
      ?food p:P7 ?stmtProtein. ?stmtProtein ps:P7 ?protein.
      ?food p:P11 ?stmtFiber. ?stmtFiber ps:P11 ?fiber.
      ?food p:P89 ?stmtCarbs. ?stmtCarbs ps:P89 ?carbs.

      {filter_block}
    }}
    LIMIT {limit}
    """

    headers = {"Accept": "application/sparql-results+json"}
    response = requests.get(ENDPOINT, params={"query": query}, headers=headers)
    data = response.json()

    if "results" not in data or "bindings" not in data["results"] or len(data["results"]["bindings"]) == 0:
        return []

    results_list = data["results"]["bindings"]

    # Selección aleatoria de 20 resultados
    sample = random.sample(results_list, min(sample_size, len(results_list)))

    # Obtener los QIDs de los resultados
    qids = [r["food"]["value"].split("/")[-1] for r in sample]
    values_clause = " ".join(f"wb:{qid}" for qid in qids)

    # Consulta SPARQL para labels de los 20 elementos usando rdfs:label
    label_query = f"""
    PREFIX wb: <https://wikifcd.wikibase.cloud/entity/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?food ?foodLabel WHERE {{
      VALUES ?food {{ {values_clause} }}
      ?food rdfs:label ?foodLabel .
      FILTER(LANG(?foodLabel) = "{lang}")
    }}
    """
    label_resp = requests.get(ENDPOINT, params={"query": label_query}, headers=headers).json()
    labels_map = {item["food"]["value"]: item["foodLabel"]["value"]
                  for item in label_resp.get("results", {}).get("bindings", [])}

    # Formatear resultados con valores numéricos y label
    formatted = []
    for r in sample:
        row = {k: float(v["value"]) if k != "food" else v["value"] for k, v in r.items()}
        row["foodLabel"] = labels_map.get(r["food"]["value"], r["food"]["value"].split("/")[-1])
        formatted.append(row)

    return formatted


# ----------------------------
# EJEMPLO DE USO
# ----------------------------
reference_hamburger = {
    "calories": 250,
    "totalfat": 9,
    "fatsaturated": 3.5,
    "fattrans": 0.5,
    "cholesterol": 25,
    "sodium": 520,
    "carbs": 31,
    "fiber": 2,
    "sugar": 6,
    "protein": 12
}

similar_foods = get_similar_foods(reference_hamburger)

from rdflib import Graph, Literal, Namespace, URIRef, XSD, RDF, SKOS

# Umbrales segun ontología
NUTRITIONAL_SEALS = [
    {"seal": "HighCalories", "nutrient": "calories", "thresholdSolid": 275.0, "unit": "kcal"},
    {"seal": "HighSaturatedFat", "nutrient": "fatsaturated", "thresholdSolid": 4.0, "unit": "g"},
    {"seal": "HighSodium", "nutrient": "sodium", "thresholdSolid": 400.0, "unit": "mg"},
    {"seal": "HighSugar", "nutrient": "sugar", "thresholdSolid": 10.0, "unit": "g"},
]

def export_foods_to_ttl_with_ontology(food_list, ttl_file="foods_with_ontology.ttl"):
    g = Graph()
    EX = Namespace("http://example.com/menu#")
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", Namespace("http://www.w3.org/2000/01/rdf-schema#"))
    g.bind("skos", SKOS)
    g.bind("xsd", XSD)

    for idx, food_data in enumerate(food_list, 1):
        item_uri = EX[f"item/{idx}"]
        g.add((item_uri, RDF.type, EX.MenuItem))

        # Propiedades básicas
        g.add((item_uri, EX.itemName, Literal(food_data.get("foodLabel", f"Item {idx}"), datatype=XSD.string)))
        g.add((item_uri, EX.calories, Literal(food_data.get("calories", 0), datatype=XSD.float)))
        g.add((item_uri, EX.carbs, Literal(food_data.get("carbs", 0), datatype=XSD.float)))
        g.add((item_uri, EX.fiber, Literal(food_data.get("fiber", 0), datatype=XSD.float)))
        g.add((item_uri, EX.protein, Literal(food_data.get("protein", 0), datatype=XSD.float)))
        g.add((item_uri, EX.totalFat, Literal(food_data.get("totalfat", 0), datatype=XSD.float)))
        g.add((item_uri, EX.saturatedFat, Literal(food_data.get("fatsaturated", 0), datatype=XSD.float)))
        g.add((item_uri, EX.transFat, Literal(food_data.get("fattrans", 0), datatype=XSD.float)))
        g.add((item_uri, EX.cholesterol, Literal(food_data.get("cholesterol", 0), datatype=XSD.float)))
        g.add((item_uri, EX.sodium, Literal(food_data.get("sodium", 0), datatype=XSD.float)))
        g.add((item_uri, EX.sugars, Literal(food_data.get("sugar", 0), datatype=XSD.float)))

        # Categoría y estado físico por defecto
        g.add((item_uri, EX.category, EX.Sandwich))
        g.add((item_uri, EX.hasPhysicalState, EX.Solid))
        g.add((item_uri, EX.company, URIRef("http://dbpedia.org/resource/FOOD_LION")))

        # Enlace al Wikibase
        if "food" in food_data:
            g.add((item_uri, EX.wikiLink, URIRef(food_data["food"])))

        # --- Agregar sellos nutricionales ---
        for seal in NUTRITIONAL_SEALS:
            value = food_data.get(seal["nutrient"], 0)
            if value >= seal["thresholdSolid"]:
                seal_uri = EX[seal["seal"]]
                g.add((item_uri, EX.hasNutritionalSeal, seal_uri))

    # Guardar TTL
    g.serialize(ttl_file, format="turtle")

export_foods_to_ttl_with_ontology(similar_foods)