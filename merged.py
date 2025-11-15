import pandas as pd

"""
Combina dos archivos CSV de menús de comida rápida y normaliza los valores numéricos
para la categoría 'drink'.

Este script:
1. Carga dos CSV limpios.
2. Normaliza los nombres de columnas para evitar duplicados.
3. Asegura que las columnas estén en el mismo orden.
4. Combina ambos DataFrames en uno solo.
5. Rellena valores nulos con 0 en las columnas numéricas solo para la categoría 'drink'.
6. Guarda el DataFrame resultante en un nuevo CSV.
"""

# --- Leer los CSV limpios ---
df1 = pd.read_csv("FastFoodNutritionMenuV3_clean.csv")
df2 = pd.read_csv("exported_data_clean.csv")

# --- Normalizar nombres de columnas ---
# Eliminar espacios al inicio/final y caracteres invisibles
df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# --- Asegurar que df2 tenga las mismas columnas y en el mismo orden que df1 ---
df2 = df2[df1.columns]

# --- Unir los DataFrames verticalmente ---
df_combined = pd.concat([df1, df2], ignore_index=True)

# --- Columnas numéricas que pueden contener valores nulos ---
cols_numericas = [
    'Calories', 'Total Fat (g)', 'Saturated Fat (g)', 'Trans Fat (g)',
    'Cholesterol (mg)', 'Sodium (mg)', 'Carbs (g)', 'Fiber (g)',
    'Sugars (g)', 'Protein (g)'
]

# --- Rellenar valores nulos con 0 solo para filas donde la categoría sea 'drink' ---
df_combined.loc[df_combined['Category'].str.lower() == 'drink', cols_numericas] = \
    df_combined.loc[df_combined['Category'].str.lower() == 'drink', cols_numericas].fillna(0)

# --- Guardar el DataFrame combinado en un nuevo archivo CSV ---
df_combined.to_csv("combined_menu.csv", index=False, encoding='utf-8-sig')
