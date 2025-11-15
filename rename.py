import pandas as pd
import re

"""
Prepara un CSV combinado de menús de comida rápida para uso en RDF. 

Este script:
1. Carga el CSV combinado original.
2. Renombra columnas numéricas para que sean URI-friendly (sin espacios ni paréntesis).
3. Limpia los nombres de empresas para que sean válidos en RDF (URI-friendly).
4. Guarda el CSV resultante listo para procesos de RDF.
"""

# Leer el CSV combinado original
df = pd.read_csv("combined_menu.csv")

# Renombrar columnas numéricas para que sean URI-friendly
df = df.rename(columns={
    "Total Fat (g)": "Total_Fat_g",
    "Saturated Fat (g)": "Saturated_Fat_g",
    "Trans Fat (g)": "Trans_Fat_g",
    "Cholesterol (mg)": "Cholesterol_mg",
    "Sodium (mg)": "Sodium_mg",
    "Carbs (g)": "Carbs_g",
    "Fiber (g)": "Fiber_g",
    "Sugars (g)": "Sugars_g",
    "Protein (g)": "Protein_g"
})

def clean_company_name_for_rdf(s):
    """
    Limpia el nombre de una empresa para que sea compatible con RDF/URI.

    Se eliminan caracteres especiales, apóstrofes, comillas, se reemplazan
    ciertos símbolos problemáticos por 'and', se normalizan espacios y se
    eliminan caracteres no alfanuméricos o guión bajo.

    Parámetros
    ----------
    s : str
        Nombre de la empresa a limpiar.

    Retorna
    -------
    str
        Nombre de empresa limpio y compatible con RDF/URI.
    
    Ejemplos
    --------
    >>> clean_company_name_for_rdf("McDonald's")
    'McDonalds'

    >>> clean_company_name_for_rdf("A&B \"Company\"")
    'AandB_Company'
    """
    if pd.isna(s):
        return s
    # Eliminar apóstrofes tipográficos y normales
    s = re.sub(r"[’']", "", s)
    # Reemplazar otros caracteres problemáticos (&, ") por 'and'
    s = re.sub(r"[&\"]", "and", s)
    # Normalizar espacios y otros separadores a guión bajo
    s = re.sub(r"\s+", "_", s)
    # Eliminar caracteres que no sean alfanuméricos o guión bajo
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.strip()

# Aplicar limpieza a la columna Company
df['Company'] = df['Company'].apply(clean_company_name_for_rdf)

# Revisar nombres únicos de empresas
print(df['Company'].unique())

# Guardar CSV renombrado y limpio para RDF
df.to_csv("combined_menu_renamed.csv", index=False, encoding="utf-8")
