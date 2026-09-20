import pandas as pd
import matplotlib.pyplot as plt
import os

# Definir rutas a los archivos
directorio_cuenca = 'camels_cl_5710001'
archivo_caudal = os.path.join(directorio_cuenca, 'q_m3s_day.csv')
# Usaremos CR2MET como la lluvia local (es la mejor referencia grillada en Chile)
archivo_lluvia = os.path.join(directorio_cuenca, 'precip_cr2met_day.csv')
archivo_temp = os.path.join(directorio_cuenca, 'tmax_cr2met_day.csv') # Podemos promediar tmax y tmin luego

print("Cargando datos...")
# Cargar datos diarios
# Usamos usecols para leer solo la fecha y el valor, y evitamos las columnas de año/mes/día
df_q = pd.read_csv(archivo_caudal, usecols=['date', '5710001'], index_col='date', parse_dates=True)
df_p = pd.read_csv(archivo_lluvia, usecols=['date', '5710001'], index_col='date', parse_dates=True)

# Renombrar la columna para mayor claridad
df_q.columns = ['Caudal_m3s']
df_p.columns = ['Precipitacion_mm']

# Unir ambos dataframes por fecha
df = pd.merge(df_p, df_q, left_index=True, right_index=True, how='outer')

# Definir un periodo de análisis común (ej: 1980 a 2020, 40 años)
fecha_inicio = '1980-01-01'
fecha_fin = '2020-04-01'
df_periodo = df.loc[fecha_inicio:fecha_fin]

print(f"\n--- Análisis del Periodo Común ({fecha_inicio} a {fecha_fin}) ---")
# Evaluar porcentaje de datos faltantes (Requisito: máximo 10% faltante)
faltantes = df_periodo.isna().mean() * 100
print("Porcentaje de datos faltantes por variable:")
print(faltantes.round(2).astype(str) + " %")

if faltantes.max() > 10:
    print("¡ALERTA! Hay más del 10% de datos faltantes en este periodo.")
else:
    print("¡Cumple el requisito de la tarea (< 10% de faltantes)!")

# Convertir a escala mensual (Punto 1.1 de la tarea)
# Precipitación: Suma mensual (Pm)
# Caudal: Promedio mensual (Qm)
print("\nConvirtiendo a escala mensual...")
df_mensual = pd.DataFrame()
df_mensual['Pm_mm'] = df_periodo['Precipitacion_mm'].resample('ME').sum(min_count=20) 
df_mensual['Qm_m3s'] = df_periodo['Caudal_m3s'].resample('ME').mean()

# Convertir caudal a lámina (mm/mes)
# Formula: Rm = (86.4 / A) * sum(Qd) -> que es igual a (86.4 * nm / A) * Qm
# Área de la cuenca 5710001 es 4839.047 km2
area_km2 = 4839.047
# Días en cada mes
dias_mes = df_mensual.index.days_in_month
df_mensual['Rm_mm'] = (86.4 * dias_mes / area_km2) * df_mensual['Qm_m3s']

# Guardar los datos mensuales procesados
df_mensual.to_csv('datos_mensuales_procesados.csv')
print("Datos mensuales guardados en 'datos_mensuales_procesados.csv'")

# Graficar la serie mensual
plt.figure(figsize=(12, 6))
plt.plot(df_mensual.index, df_mensual['Pm_mm'], label='Precipitación (mm/mes)', color='blue', alpha=0.7)
plt.plot(df_mensual.index, df_mensual['Rm_mm'], label='Caudal a lámina (mm/mes)', color='red', alpha=0.8)
plt.title('Series Mensuales de Precipitación y Caudal - Río Maipo')
plt.ylabel('mm / mes')
plt.legend()
plt.tight_layout()
plt.savefig('grafica_1_1_series.png')
print("Gráfica guardada como 'grafica_1_1_series.png'")
# plt.show()
