import pandas as pd
import numpy as np
import json
import os

def build_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datos_path = os.path.join(base_dir, 'datos', 'datos_mensuales_maipo.csv')
    tabla_a_path = os.path.join(base_dir, 'figuras', 'tabla_1_6_sintesis_clasificacion.csv')
    
    df = pd.read_csv(datos_path)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # 1. Disponibilidad (Heatmap)
    years = sorted(df['year'].unique().tolist())
    months = list(range(1, 13))
    
    # Creamos matriz de disponibilidad (usamos P_local como proxy)
    z_matrix = []
    for m in months:
        row = []
        for y in years:
            val = df[(df['year'] == y) & (df['month'] == m)]['P_local_mm'].notna().sum()
            row.append(1 if val > 0 else 0)
        z_matrix.append(row)
        
    disponibilidad = {
        'x': years,
        'y': ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
        'z': z_matrix
    }
    
    # 2. Ciclo Anual (Periodo Común 2000-06 a 2020-03)
    df_comun = df[(df['date'] >= '2000-06-01') & (df['date'] <= '2020-03-31')].copy()
    ciclo = df_comun.groupby('month')[['P_local_mm', 'Caudal_m3s']].mean().reset_index()
    
    cicloAnual = {
        'meses': ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
        'precip': ciclo['P_local_mm'].round(2).tolist(),
        'caudal': ciclo['Caudal_m3s'].round(2).tolist()
    }
    
    # 3. Histograma
    hist, bins = np.histogram(df['P_local_mm'].dropna(), bins=20)
    histPrecip = {
        'x': [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)],
        'y': hist.tolist()
    }
    
    # 4. Scatter IMERG
    df_imerg = df.dropna(subset=['P_local_mm', 'P_IMERG_mm']).copy()
    # Estaciones
    df_imerg['season'] = df_imerg['month'].map({12:'Verano', 1:'Verano', 2:'Verano',
                                                3:'Otoño', 4:'Otoño', 5:'Otoño',
                                                6:'Invierno', 7:'Invierno', 8:'Invierno',
                                                9:'Primavera', 10:'Primavera', 11:'Primavera'})
    
    scatter_traces = []
    for season in ['Verano', 'Otoño', 'Invierno', 'Primavera']:
        df_s = df_imerg[df_imerg['season'] == season]
        scatter_traces.append({
            'name': season,
            'x': df_s['P_local_mm'].tolist(),
            'y': df_s['P_IMERG_mm'].tolist()
        })
        
    max_val = max(df_imerg['P_local_mm'].max(), df_imerg['P_IMERG_mm'].max())
    
    scatterImerg = {
        'traces': scatter_traces,
        'maxVal': [max_val]
    }
    
    # 5. Validación temporal dummy (Serie de caudal)
    # Mostramos la serie de caudal real vs una media móvil simple como "modelo" para ilustrar la interactividad.
    df_val = df.dropna(subset=['Caudal_m3s']).tail(120) # Ultimos 10 años
    
    validacionTemporal = {
        'fechas': df_val['date'].dt.strftime('%Y-%m-%d').tolist(),
        'observado': df_val['Caudal_m3s'].tolist(),
        'modelado': df_val['Caudal_m3s'].rolling(window=3, center=True).mean().bfill().tolist()
    }
    
    # 6. Tabla Síntesis Rol A
    tablaSintesisA = None
    if os.path.exists(tabla_a_path):
        df_tabla = pd.read_csv(tabla_a_path)
        tablaSintesisA = {
            'headers': df_tabla.columns.tolist(),
            'rows': df_tabla.values.tolist()
        }
    
    # Combinar todo
    dashboard_data = {
        'disponibilidad': disponibilidad,
        'cicloAnual': cicloAnual,
        'histPrecip': histPrecip,
        'scatterImerg': scatterImerg,
        'validacionTemporal': validacionTemporal,
        'tablaSintesisA': tablaSintesisA
    }
    
    # Escribir JS
    js_content = f"window.dashboardData = {json.dumps(dashboard_data, indent=2)};\n"
    out_path = os.path.join(base_dir, 'dashboard', 'js', 'data.js')
    
    # Asegurar directorio
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Data JS generada exitosamente en {out_path}")

if __name__ == '__main__':
    build_data()
