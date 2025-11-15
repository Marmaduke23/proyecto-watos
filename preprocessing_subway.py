import pandas as pd
import re

# Leer el archivo CSV original
df = pd.read_csv("exported_data.csv")

# Limpiar los nombres de columnas por si tienen saltos de línea o espacios
df.columns = df.columns.str.replace('\n', ' ').str.strip()

# Renombrar 'Unnamed: 0' a 'Item' si existe
if 'Unnamed: 0' in df.columns:
    df = df.rename(columns={'Unnamed: 0': 'Item'})

# Agregar columna 'Company' con valor 'Subway'
df['Company'] = 'Subway'

# Eliminar columnas no deseadas si existen
df = df.drop(columns=[
    "Vitamin A % DV", "Vitamin C % DV", 
    "Calcium % DV", "Iron % DV", "Serving Size (g)"
], errors='ignore')


def limpiar_marcas(texto):
    """
    Elimina símbolos de marca registrada y caracteres especiales de un texto.

    Esta función limpia cadenas de texto que puedan contener símbolos de 
    copyright, marcas registradas u otros caracteres no deseados, dejando 
    el texto listo para análisis de datos.

    Parámetros
    ----------
    texto : str
        Cadena de texto que se desea limpiar. Si no es una cadena, se devuelve tal cual.

    Retorna
    -------
    str
        Cadena de texto sin símbolos de marca y con espacios múltiples reemplazados 
        por un solo espacio.

    Ejemplos
    --------
    >>> limpiar_marcas("Coca-Cola®")
    'Coca-Cola'

    >>> limpiar_marcas("Pizza™  Hut")
    'Pizza Hut'
    """
    if isinstance(texto, str):
        # Eliminar símbolos comunes de marca registrada y otros caracteres especiales
        texto = re.sub(r'[®™℠©]', '', texto)
        # Eliminar dobles espacios resultantes
        texto = re.sub(r'\s{2,}', ' ', texto)
        return texto.strip()
    return texto

# Aplicar limpieza a todas las columnas de texto del DataFrame
df = df.applymap(limpiar_marcas)

# Renombrar columnas específicas para consistencia
df = df.rename(columns={
    "Carbohydrates (g)": "Carbs (g)",
    "Dietary Fiber (g)": "Fiber (g)"
})

# Guardar el resultado en un nuevo archivo CSV
df.to_csv("exported_data_clean.csv", index=False, encoding='utf-8-sig')
