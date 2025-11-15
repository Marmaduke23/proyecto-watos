import pandas as pd

"""
Renombra columnas numéricas de un CSV combinado de menús de comida rápida.

Este script:
1. Carga un CSV original con nombres de columnas que incluyen espacios y paréntesis.
2. Renombra las columnas numéricas para que sean más limpias y consistentes.
3. Guarda el CSV resultante con las columnas renombradas.

Parámetros
----------
input_csv : str
    Ruta del archivo CSV original que se desea renombrar.
output_csv : str
    Ruta del archivo CSV donde se guardará el CSV corregido.

Ejemplos
--------
>>> input_csv = "combined_menu.csv"
>>> output_csv = "combined_menu_fixed.csv"
>>> # Ejecutar el script renombrará las columnas y guardará el nuevo CSV
"""

# Ruta del CSV original
input_csv = "combined_menu_renamed.csv"
# Ruta del CSV renombrado
output_csv = "combined_menu_fixed.csv"

# Leer el CSV original
df = pd.read_csv(input_csv)

# Diccionario con los cambios de nombre de columnas
rename_columns = {
    "Total Fat (g)": "TotalFat",
    "Saturated Fat (g)": "SaturatedFat",
    "Trans Fat (g)": "TransFat",
    "Cholesterol (mg)": "Cholesterol",
    "Sodium (mg)": "Sodium",
    "Carbs (g)": "Carbs",
    "Fiber (g)": "Fiber",
    "Sugars (g)": "Sugars",
    "Protein (g)": "Protein"
}

# Renombrar las columnas
df.rename(columns=rename_columns, inplace=True)

# Guardar el CSV corregido
df.to_csv(output_csv, index=False)

print(f"CSV renombrado generado: {output_csv}")
