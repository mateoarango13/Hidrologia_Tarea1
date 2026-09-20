import pandas as pd

print("Iniciando la integración de datos (Fase 1)...")

try:
    # 1. Cargar datos locales (procesados por Integrante 3 en 01_preparar_datos.py)
    df_local = pd.read_csv('datos_mensuales_procesados.csv', index_col=0, parse_dates=True)
    print("Datos locales cargados correctamente.")
except FileNotFoundError:
    print("ERROR: No se encontró 'datos_mensuales_procesados.csv'. Asegúrate de ejecutar 01_preparar_datos.py primero.")
    exit()

try:
    # 2. Cargar datos satelitales (procesados por Integrante 1 y 2 en 02_descargar_satelite.py)
    df_satelite = pd.read_csv('datos_satelitales_imerg_era5.csv', index_col=0, parse_dates=True)
    print("Datos satelitales cargados correctamente.")
except FileNotFoundError:
    print("ERROR: No se encontró 'datos_satelitales_imerg_era5.csv'. Asegúrate de ejecutar 02_descargar_satelite.py primero.")
    exit()

# Alinear las fechas al primer día del mes para que el inner join coincida exactamente
df_local.index = df_local.index.to_period('M').to_timestamp()
df_satelite.index = df_satelite.index.to_period('M').to_timestamp()

# 3. Unir (Merge) ambos dataframes usando la fecha como índice
print("\nIntegrando bases de datos...")
# Usamos un OUTER JOIN. La tarea prohíbe explícitamente que la menor duración de IMERG (20 años)
# recorte los registros locales largos (40 años). Por lo tanto, mantendremos todas las fechas.
df_maestro = pd.merge(df_local, df_satelite, left_index=True, right_index=True, how='outer')

# Renombrar columnas para estandarizar la nomenclatura final
# Pm_mm: Precipitación local (CR2MET)
# Qm_m3s: Caudal en m3/s
# Rm_mm: Caudal en lámina (mm/mes)
# PI_mm: Precipitación IMERG
# Temp_C: Temperatura ERA5-Land
df_maestro = df_maestro.rename(columns={
    'Pm_mm': 'P_local_mm',
    'Rm_mm': 'Q_lamina_mm',
    'PI_mm': 'P_IMERG_mm'
})

# Reordenar las columnas para mayor legibilidad
columnas_ordenadas = ['P_local_mm', 'P_IMERG_mm', 'Caudal_m3s', 'Q_lamina_mm', 'Temp_C']
# Manejar si Caudal_m3s no existe por el script 1, usar Qm_m3s
if 'Qm_m3s' in df_maestro.columns:
    df_maestro = df_maestro.rename(columns={'Qm_m3s': 'Caudal_m3s'})

df_maestro = df_maestro[columnas_ordenadas]

# 4. Exportar el CSV maestro
nombre_archivo_final = 'datos_mensuales_maipo.csv'
df_maestro.to_csv(nombre_archivo_final)

print(f"\n¡ÉXITO TOTAL! El archivo maestro '{nombre_archivo_final}' ha sido creado.")
print(f"Periodo de datos integrados: desde {df_maestro.index.min().strftime('%Y-%m')} hasta {df_maestro.index.max().strftime('%Y-%m')}.")
print(f"Número de meses comunes: {len(df_maestro)} meses.")
print("\n¡LA FASE 1 ESTÁ LISTA! Suban este archivo al repositorio de GitHub y comiencen la Fase 2 de forma paralela.")
