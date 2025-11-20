import requests
import random
from rdflib import Graph, Literal, Namespace, URIRef, XSD, RDF, SKOS

# ---------- CONFIG ----------
ENDPOINT = "https://wikifcd.wikibase.cloud/query/sparql"

TOLERANCES = {
    "calories": 50, "totalfat": 3, "fatsaturated": 2, "fattrans": 0.5,
    "cholesterol": 20, "sodium": 100, "carbs": 10, "fiber": 2,
    "sugar": 2, "protein": 5
}

NUTRITIONAL_SEALS = [
    {"seal": "HighCalories", "nutrient": "calories", "thresholdSolid": 275.0, "unit": "kcal"},
    {"seal": "HighSaturatedFat", "nutrient": "fatsaturated", "thresholdSolid": 4.0, "unit": "g"},
    {"seal": "HighSodium", "nutrient": "sodium", "thresholdSolid": 400.0, "unit": "mg"},
    {"seal": "HighSugar", "nutrient": "sugar", "thresholdSolid": 10.0, "unit": "g"},
]

# ---------- FUNCION PRINCIPAL ----------
def fetch_foods_with_ttl_and_json(reference_values, limit=100, sample_size=6, lang="en", ttl_file="foods.ttl"):
    # --- SPARQL dinámico para el rango de nutrientes ---
    param_map = {
        "calories": "calories", "totalfat": "totalfat", "fatsaturated": "fatsaturated",
        "fattrans": "fattrans", "cholesterol": "cholesterol", "sodium": "sodium",
        "carbs": "carbs", "fiber": "fiber", "sugar": "sugar", "protein": "protein"
    }

    filters = []
    for key, var in param_map.items():
        if key in reference_values:
            val = reference_values[key]
            tol = TOLERANCES.get(key, 0)
            filters.append(f"FILTER(?{var} >= {val - tol} && ?{var} <= {val + tol})")
    filter_block = "\n  ".join(filters)

    query = f"""
    PREFIX wb: <https://wikifcd.wikibase.cloud/entity/>
    PREFIX p: <https://wikifcd.wikibase.cloud/prop/>
    PREFIX ps: <https://wikifcd.wikibase.cloud/prop/statement/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?food ?sodium ?sugar ?calories ?fatsaturated ?totalfat ?cholesterol ?fattrans ?protein ?fiber ?carbs
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
    resp = requests.get(ENDPOINT, params={"query": query}, headers=headers)
    data = resp.json()
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return [], []

    # Sample aleatorio
    sample = random.sample(bindings, min(sample_size, len(bindings)))

    # Obtener labels
    qids = [r["food"]["value"].split("/")[-1] for r in sample]
    values_clause = " ".join(f"wb:{qid}" for qid in qids)
    label_query = f"""
    PREFIX wb: <https://wikifcd.wikibase.cloud/entity/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?food ?foodLabel WHERE {{
        VALUES ?food {{ {values_clause} }}
        ?food rdfs:label ?foodLabel .
        FILTER(LANG(?foodLabel)="{lang}")
    }}
    """
    label_resp = requests.get(ENDPOINT, params={"query": label_query}, headers=headers).json()
    labels_map = {item["food"]["value"]: item["foodLabel"]["value"]
                  for item in label_resp.get("results", {}).get("bindings", [])}

    # --- Construir RDF y JSON ---
    g = Graph()
    EX = Namespace("http://example.com/menu#")
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", Namespace("http://www.w3.org/2000/01/rdf-schema#"))
    g.bind("skos", SKOS)
    g.bind("xsd", XSD)

    json_list = []

    for idx, r in enumerate(sample, 1):
        row = {k: float(v["value"]) if k != "food" else v["value"] for k, v in r.items()}
        row["foodLabel"] = labels_map.get(r["food"]["value"], r["food"]["value"].split("/")[-1])
        item_uri = EX[f"item/{idx}"]
        g.add((item_uri, RDF.type, EX.MenuItem))

        # Propiedades básicas
        for prop, val in [("itemName", row["foodLabel"]), ("calories", row["calories"]), ("carbs", row["carbs"]),
                          ("fiber", row["fiber"]), ("protein", row["protein"]), ("totalFat", row["totalfat"]),
                          ("saturatedFat", row["fatsaturated"]), ("transFat", row["fattrans"]),
                          ("cholesterol", row["cholesterol"]), ("sodium", row["sodium"]), ("sugars", row["sugar"])]:
            g.add((item_uri, getattr(EX, prop), Literal(val, datatype=XSD.float if isinstance(val, float) else XSD.string)))

        g.add((item_uri, EX.category, EX.Sandwich))
        g.add((item_uri, EX.hasPhysicalState, EX.Solid))
        g.add((item_uri, EX.company, URIRef("http://dbpedia.org/resource/FOOD_LION")))
        g.add((item_uri, EX.wikiLink, URIRef(row["food"])))

        # Sellos
        seals_json = []
        for seal in NUTRITIONAL_SEALS:
            val = row.get(seal["nutrient"], 0)
            if val >= seal["thresholdSolid"]:
                seal_uri = EX[seal["seal"]]
                g.add((item_uri, EX.hasNutritionalSeal, seal_uri))
                seals_json.append(seal["seal"])

        # JSON
        json_list.append({
            "name": row["foodLabel"],
            "calories": row["calories"],
            "protein": row["protein"],
            "totalFat": row["totalfat"],
            "sodium": row["sodium"],
            "wikibase": row["food"],
            "nutritionalSeals": seals_json,
            "carbs": row["carbs"],
            "sugars": row["sugar"],
            "saturatedFat": row["fatsaturated"],
        })

    print(json_list)

    g.serialize(ttl_file, format="turtle")
    return json_list, ttl_file

