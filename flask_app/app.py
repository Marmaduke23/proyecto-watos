from flask import Flask,render_template,jsonify, request
from utils import get_items_sparql, platos_similares, map_item_to_json

app = Flask(__name__)


@app.route("/")
def index():
    items = get_items_sparql()
    query = request.args.get("q", "").strip().lower()

    # Filtrar los ítems por nombre
    if query:
        filtered = [p for p in items if query in p["name"].lower()]
    else:
        filtered = items

    # Si hay coincidencias, calcular platos similares al primero
    if filtered:
        recommendations = platos_similares(filtered[0]["name"], k=6)
    else:
        recommendations = []

    return render_template(
        "index.html",
        title="Index",
        items=filtered,
        recommendations=recommendations
    )

@app.route("/platos")
def listar_platos():
    items = get_items_sparql()
    return jsonify(items)

@app.route("/recomendar")
def recomendar():
    nombre = request.args.get("nombre")
    if not nombre:
        return jsonify({"error": "Falta el parámetro 'nombre'"}), 400
    
    similares = platos_similares(nombre)
    return jsonify({
        "plato_base": nombre,
        "recomendaciones": similares
    })

@app.route("/recomendar_wiki")
def recomendar_wiki():
    # Supongamos que ya tienes una función que devuelve los platos desde el TTL
    from querys import fetch_foods_with_ttl_and_json  
    nombre = request.args.get("nombre")
    items = get_items_sparql()
    base_item = next((p for p in items if p["name"].lower() == nombre.lower()), None)
    if not base_item:
        return jsonify({"error": "Plato no encontrado"}), 404

    plato_base = map_item_to_json(base_item)
    
    recomendaciones = fetch_foods_with_ttl_and_json(plato_base)[0]
    print(recomendaciones)

    return jsonify({"recomendaciones": recomendaciones})


if __name__ == "__main__":
    app.run(debug=True)