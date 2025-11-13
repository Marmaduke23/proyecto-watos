from rdflib import Graph, Namespace

# Cargar grafo
g = Graph()
g.parse("utils/combined_menu.ttl", format="ttl")
EX = Namespace("http://example.com/menu#")

# Función de conversión segura
def to_float(lit):
    try:
        return float(lit)
    except (ValueError, TypeError):
        return None

# Recorrer sujetos y propiedades nutricionales
for s in g.subjects(None, None):
    for prop in ["calories", "protein", "totalFat", "carbs"]:
        val = g.value(s, getattr(EX, prop))
        if val is not None and to_float(val) is None:
            nombre = g.value(s, EX.itemName)
            print(f"Error en {prop} para {nombre} ({s}): {val}")
