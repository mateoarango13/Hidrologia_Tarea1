# pyrefly: ignore [missing-import]
import ee
import pandas as pd
import geopandas as gpd
import json
import os

# --- INSTRUCCIONES ---
# 1. Abre tu terminal e instala las librerías necesarias ejecutando:
#    pip install earthengine-api geopandas
# 2. Autentícate en Google Earth Engine ejecutando en tu terminal:
#    earthengine authenticate
# 3. Luego ejecuta este script.

print("Inicializando Earth Engine...")
try:
    ee.Initialize(project='hidrologia2026-2')
except Exception as e:
    print("\n¡ERROR DE AUTENTICACIÓN O PROYECTO!")
    print("Por favor, ejecuta el siguiente comando en tu consola para iniciar sesión:")
    print("py -m earthengine authenticate")
    print("Y sigue las instrucciones en el navegador para elegir un 'Cloud Project'.")
    exit()

# 1. Cargar el polígono de la cuenca desde el shapefile descargado
ruta_shp = 'camels_cl_5710001/polygon/polygon.shp'
print(f"Cargando polígono de la cuenca desde {ruta_shp}...")
cuenca_gdf = gpd.read_file(ruta_shp)

# Convertir el shapefile a un formato que Earth Engine entienda (GeoJSON a ee.Geometry)
json_geometry = json.loads(cuenca_gdf.to_json())['features'][0]['geometry']
cuenca_ee = ee.Geometry(json_geometry)

# Definir el periodo de análisis (IMERG empezó en junio del 2000)
# Usaremos desde el 2000-06-01 hasta 2020-04-01 para coincidir con el caudal
fecha_inicio = '2000-06-01'
fecha_fin = '2020-04-01'

print(f"Extrayendo datos desde {fecha_inicio} hasta {fecha_fin}...")

# 2. Obtener Precipitación IMERG (Modalidad Final, Mensual, V06)
# Producto: NASA/GPM_L3/IMERG_MONTHLY_V06
print("Procesando IMERG...")
imerg_col = ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V06") \
              .filterDate(fecha_inicio, fecha_fin) \
              .select('precipitation') # Unidad original: mm/hr

# Función para extraer el promedio de la cuenca mes a mes
def extraer_promedio_imerg(image):
    # IMERG mensual viene en tasa de mm/hr. Para pasarlo a mm/mes, hay que multiplicar por las horas del mes.
    # Earth Engine no tiene una función directa de "días del mes" fácil en imágenes, así que extraeremos 
    # la tasa y la multiplicaremos luego en pandas.
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=cuenca_ee,
        scale=10000, # Escala aproximada de IMERG (10 km)
        maxPixels=1e9
    )
    # Retornar una feature (fila) con el valor y la fecha
    return ee.Feature(None, {
        'date': image.date().format('YYYY-MM-dd'),
        'precip_mm_hr': mean_dict.get('precipitation')
    })

imerg_datos = imerg_col.map(extraer_promedio_imerg).getInfo()

# 3. Obtener Temperatura de ERA5-Land Mensual
# Producto: ECMWF/ERA5_LAND/MONTHLY_AGGR
print("Procesando Temperatura ERA5-Land...")
era5_col = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
             .filterDate(fecha_inicio, fecha_fin) \
             .select('temperature_2m') # Unidad original: Kelvin

def extraer_promedio_temp(image):
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=cuenca_ee,
        scale=11132, # Escala de ERA5-Land (~11 km)
        maxPixels=1e9
    )
    return ee.Feature(None, {
        'date': image.date().format('YYYY-MM-dd'),
        'temp_kelvin': mean_dict.get('temperature_2m')
    })

temp_datos = era5_col.map(extraer_promedio_temp).getInfo()

# 4. Consolidar los resultados en un DataFrame de Pandas
print("\nConsolidando datos en un archivo CSV...")

# Extraer listas de diccionarios
lista_imerg = [f['properties'] for f in imerg_datos['features']]
lista_temp = [f['properties'] for f in temp_datos['features']]

df_imerg = pd.DataFrame(lista_imerg).set_index('date')
df_temp = pd.DataFrame(lista_temp).set_index('date')

df_satelite = pd.merge(df_imerg, df_temp, left_index=True, right_index=True, how='outer')
df_satelite.index = pd.to_datetime(df_satelite.index)

# Conversiones de unidades (Puntos exigidos por la tarea)
# IMERG: de mm/hr a mm/mes
horas_por_mes = df_satelite.index.days_in_month * 24
df_satelite['PI_mm'] = df_satelite['precip_mm_hr'] * horas_por_mes

# Temperatura: de Kelvin a Celsius (T[°C] = T[K] - 273.15)
df_satelite['Temp_C'] = df_satelite['temp_kelvin'] - 273.15

# Filtrar columnas útiles
df_satelite = df_satelite[['PI_mm', 'Temp_C']]

df_satelite.to_csv('datos_satelitales_imerg_era5.csv')
print("\n¡ÉXITO! Los datos satelitales han sido descargados y guardados en 'datos_satelitales_imerg_era5.csv'")
print("El Integrante 4 ahora puede unir este archivo con el de los datos locales.")
