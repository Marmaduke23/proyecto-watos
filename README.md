# Proyecto: Menú de Comida Rápida

## Descripción
Este proyecto procesa bases de datos de menús de comida rápida de varias cadenas, limpia, combina los datos y genera un grafo RDF para análisis semántico. Basado en Flask, lo que permite a los usuarios consultar información nutricional de los ítems del menú. 

Adicionalmente, se ha desarrollado una ontología personalizada para representar mejor los datos nutricionales y poder asignar sellos de valor nutricional a los resultados SPARQL, en base a la ley chilena 20.606.

## Instalación

1. Clona este repositorio: https://github.com/Marmaduke23/proyecto-watos.git

2. Instala las dependencias necesarias:

   ```bash
   pip install -r requirements.txt
   ```
3. Arranca la aplicación ejecutando:
   
   ```bash
   python3 flask_app/app.py
   ```

## Preparación para RDF

Esta parte procesa menús de comida rápida de múltiples cadenas, limpia y combina los datos, y genera un grafo RDF listo para análisis semántico.

---

Archivos CSV originales:

FastFoodNutritionMenuV3.csv

exported_data.csv (Subway)

### Limpieza de CSV
#### Limpieza general (preprocessing_others.py)
Esta etapa:

Elimina símbolos de marca registrada (®, ™, ℠, ©) de todos los campos de texto.

Quita columnas innecesarias (Weight Watchers Pnts, Calories from Fat).

Guarda un CSV limpio: FastFoodNutritionMenuV3_clean.csv.

Ejecución:

```bash
python3 preprocessing_others.py
```
#### Limpieza específica para Subway (preprocessing_subway.py)
Esta etapa:

Limpia símbolos de marca registrada.

Añade columna Company = 'Subway'.

Quita columnas innecesarias de vitaminas y tamaño de porción.

Renombra columnas específicas:

Carbohydrates (g) → Carbs (g)

Dietary Fiber (g) → Fiber (g)

Guarda CSV limpio: exported_data_clean.csv.

Ejecución:

```bash
python3 preprocessing_subway.py
```
#### Combinación de CSV (merged.py)
Esta etapa:

Antes de la mezcla se añade una columna llamada "Category" que indica el tipo de plato, esta fue agregada manualmente mediante asistencia de IA.

Combina los CSV limpios (FastFoodNutritionMenuV3_clean.csv y exported_data_clean.csv).

Normaliza nombres de columnas.

Rellena valores nulos con 0 en columnas numéricas solo para filas donde la categoría sea drink.

Guarda el CSV combinado: combined_menu.csv.

Ejecución:

```bash
python3 merged.py
```
### Preparación para RDF
#### Limpieza de nombres y columnas (rename.py)
Esta etapa:

Limpia nombres de compañías para que sean compatibles con RDF/URI (por ejemplo, McDonald's → McDonalds).

Renombra columnas numéricas para que sean URI-friendly.

CSV listo para RDF: combined_menu_renamed.csv.

Ejecución:

```bash
python3 rename.py
```
#### Ajuste final de columnas (fixed.py)

Esta etapa:

Renombra columnas numéricas para mayor consistencia.

CSV final para RDF: combined_menu_fixed.csv.

Ejecución:

```bash
python3 fixed.py
```
### Generación de RDF (menu_mapping.sparql)
Esta etapa:

Cada fila se convierte en un ex:MenuItem.

Las compañías se mapean a IRIs de DBpedia conocidas:

Nombre CSV	IRI DBpedia
McDonalds	http://dbpedia.org/resource/McDonald's

Burger_King	http://dbpedia.org/resource/Burger_King

Pizza_Hut	http://dbpedia.org/resource/Pizza_Hut

KFC	http://dbpedia.org/resource/KFC

Taco_Bell	http://dbpedia.org/resource/Taco_Bell

Wendys	http://dbpedia.org/resource/The_Wendy's_Company

Subway	http://dbpedia.org/resource/Subway_(restaurant)

Los ítems desconocidos se asignan a <http://example.com/menu#UnknownCompany>.

Ejecución:
Asumiendo que está en el directorio donde se encuentra tarql.

```bash
\tarql-1.2\bin\tarql.bat C:\tarql-1.2\bin\menu_mapping.sparql C:\PROYECTO-WATOS\combined_menu_fixed.csv > C:\PROYECTO-WATOS\combined_menu.ttl
```
Lo anterior exporta un RDF en Turtle.

## Post-procesamiento RDF

### Reparación semántica de combined_menu.ttl (fix_nutritional_values.py)

Algunos cambios fueron hechos para mejorar el diseño semántico de nuestros datos, incluyendo:

1) Se arregló ex:category "Sandwich" → ex:category ex:Sandwich
2) Transformación de strings numéricos a floats
3) Añadir ex:state ex:Solid o ex:Liquid según la categoría específica de cada item
4) Preservación de formato y tripletes

Exporta un nuevo archivo `combined_menu_fixed.ttl`.

Ejecución:

```bash
python3 fix_nutritional_values.py
```

### Nueva ontología (nutritional_ontology.ttl)

Luego de analizar los datos y sus relaciones, se creó una ontología personalizada `nutritional_ontology.ttl` para representar mejor la información contenida.

En ella se definen:

1) Clases: MenuItem, Brand, Category, NutritionalSeal y PhysicalState
2) Propiedades de objeto: company, itemName, category, hasPhysicalState, etc.
3) Propiedades de datos: HighSugar, HighSaturatedFat, HighCalories, HighSodium, thresholdSolid, thresholdLiquid, perAmount, etc.

### Unión de datos y ontología (merge_ttl.py)

Posterormente, se unieron los datos con la ontología para crear un .ttl final completo con un grafo coherente. Exportando el resultado final a `merged.ttl`.

Ejecución:

```bash
python3 merge_ttl.py
```

### Diagrama de flujo del proceso

```mermaid
flowchart TD
    A[FastFoodNutritionMenuV3.csv] --> B[preprocessing_others.py]
    C[exported_data.csv] --> D[preprocessing_subway.py]
    B --> E[FastFoodNutritionMenuV3_clean.csv]
    D --> F[exported_data_clean.csv]
    E & F --> G[merged.py]
    G --> H[combined_menu.csv]
    H --> I[rename.py]
    I --> J[combined_menu_renamed.csv]
    J --> K[fixed.py]
    K --> L[combined_menu_fixed.csv]
    L --> M[menu_mapping.sparql]
    M --> N[fix_nutritional_values.py]
    N --> O[combined_menu_fixed.ttl]
    O & P[nutritional_ontology.ttl] --> Q[merge_ttl.py]
    Q --> R[merged.ttl]
    R --> S[RDF Graph]
```
