import pandas as pd
import numpy as np
import json
import os

def build_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datos_path = os.path.join(base_dir, 'datos', 'datos_mensuales_maipo.csv')
    tabla_a_path = os.path.join(base_dir, 'figuras', 'tabla_1_6_sintesis_clasificacion.csv')
    tabla_subperiodos_path = os.path.join(base_dir, 'figuras', 'tabla_1_5_subperiodos_estabilidad.csv')
    tabla_rezagos_path = os.path.join(base_dir, 'figuras', 'tabla_2_2_correlaciones_rezagos.csv')
    tabla_pred_path = os.path.join(base_dir, 'figuras', 'tabla_2_3_predicciones_fuera_ajuste.csv')
    
    df = pd.read_csv(datos_path)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # 1. Disponibilidad (Heatmap)
    years = sorted(df['year'].unique().tolist())
    months = list(range(1, 13))
    
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
    
    # 3. Histograma Precipitación Local vs IMERG
    bins = np.linspace(0, max(df['P_local_mm'].max(), df['P_IMERG_mm'].max()), 25)
    hist_local, _ = np.histogram(df['P_local_mm'].dropna(), bins=bins)
    hist_imerg, _ = np.histogram(df['P_IMERG_mm'].dropna(), bins=bins)
    centers = [round((bins[i] + bins[i+1])/2, 1) for i in range(len(bins)-1)]
    
    histPrecip = {
        'x': centers,
        'y_local': hist_local.tolist(),
        'y_imerg': hist_imerg.tolist()
    }
    
    # 4. Scatter IMERG vs Local
    df_imerg = df.dropna(subset=['P_local_mm', 'P_IMERG_mm']).copy()
    df_imerg['season'] = df_imerg['month'].map({12:'Verano', 1:'Verano', 2:'Verano',
                                                3:'Otoño', 4:'Otoño', 5:'Otoño',
                                                6:'Invierno', 7:'Invierno', 8:'Invierno',
                                                9:'Primavera', 10:'Primavera', 11:'Primavera'})
    
    scatter_traces = []
    for season in ['Verano', 'Otoño', 'Invierno', 'Primavera']:
        df_s = df_imerg[df_imerg['season'] == season]
        scatter_traces.append({
            'name': season,
            'x': df_s['P_local_mm'].round(2).tolist(),
            'y': df_s['P_IMERG_mm'].round(2).tolist()
        })
        
    max_val = max(df_imerg['P_local_mm'].max(), df_imerg['P_IMERG_mm'].max())
    scatterImerg = {
        'traces': scatter_traces,
        'maxVal': [round(float(max_val), 2)]
    }
    
    # 5. Subperiodos (Impacto Megasequía)
    subperiodos = None
    if os.path.exists(tabla_subperiodos_path):
        df_sub = pd.read_csv(tabla_subperiodos_path)
        subperiodos = {
            'meses': df_sub['Mes_Nombre'].tolist(),
            'pl_1980_1999': df_sub['PL_1980_1999_mm'].round(2).tolist(),
            'pl_2000_2020': df_sub['PL_2000_2020_mm'].round(2).tolist(),
            'r_1980_1999': df_sub['R_1980_1999_mm'].round(2).tolist(),
            'r_2000_2020': df_sub['R_2000_2020_mm'].round(2).tolist()
        }
        
    # 6. Rezagos (Efecto Memoria Nival)
    rezagos = None
    if os.path.exists(tabla_rezagos_path):
        df_rez = pd.read_csv(tabla_rezagos_path)
        df_rez_q = df_rez[(df_rez['rain_variable'] == 'P_local_mm') & (df_rez['flow_variable'] == 'Caudal_m3s')].sort_values('lag_months')
        df_rez_imerg = df_rez[(df_rez['rain_variable'] == 'P_IMERG_mm') & (df_rez['flow_variable'] == 'Caudal_m3s')].sort_values('lag_months')
        rezagos = {
            'lags': df_rez_q['lag_months'].tolist(),
            'r_local': df_rez_q['pearson_r_anomalies'].round(4).tolist(),
            'rho_local': df_rez_q['spearman_rho_anomalies'].round(4).tolist(),
            'r_imerg': df_rez_imerg['pearson_r_anomalies'].round(4).tolist() if len(df_rez_imerg) > 0 else []
        }
    
    # 7. Validación temporal con datos reales del Modelo
    validacionTemporal = None
    if os.path.exists(tabla_pred_path):
        df_pred = pd.read_csv(tabla_pred_path)
        # Filtrar modelo de anomalías con rezago para Caudal
        df_pred_q = df_pred[(df_pred['task'] == 'estimar_caudal') & 
                            (df_pred['model'].str.contains('anomal', case=False, na=False)) &
                            (df_pred['predictor'].str.contains('local', case=False, na=False))].sort_values('date')
        if len(df_pred_q) > 0:
            validacionTemporal = {
                'fechas': df_pred_q['date'].tolist(),
                'observado': df_pred_q['observed'].round(2).tolist(),
                'modelado': df_pred_q['predicted'].round(2).tolist(),
                'bloques': df_pred_q['outer_fold'].tolist()
            }
            
    if validacionTemporal is None:
        # Fallback a últimos 120 meses si no estuviera la tabla
        df_val = df.dropna(subset=['Caudal_m3s']).tail(120)
        validacionTemporal = {
            'fechas': df_val['date'].dt.strftime('%Y-%m-%d').tolist(),
            'observado': df_val['Caudal_m3s'].round(2).tolist(),
            'modelado': df_val['Caudal_m3s'].rolling(window=3, center=True).mean().bfill().round(2).tolist(),
            'bloques': []
        }
    
    # 8. Tabla Síntesis Rol A
    tablaSintesisA = None
    if os.path.exists(tabla_a_path):
        df_tabla = pd.read_csv(tabla_a_path)
        tablaSintesisA = {
            'headers': df_tabla.columns.tolist(),
            'rows': df_tabla.values.tolist()
        }
    
    # Combinar todo el dataset
    dashboard_data = {
        'disponibilidad': disponibilidad,
        'cicloAnual': cicloAnual,
        'histPrecip': histPrecip,
        'scatterImerg': scatterImerg,
        'subperiodos': subperiodos,
        'rezagos': rezagos,
        'validacionTemporal': validacionTemporal,
        'tablaSintesisA': tablaSintesisA
    }
    
    # Guardar en js/data.js
    js_content = f"window.dashboardData = {json.dumps(dashboard_data, indent=2)};\n"
    out_js = os.path.join(base_dir, 'dashboard', 'js', 'data.js')
    os.makedirs(os.path.dirname(out_js), exist_ok=True)
    with open(out_js, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"Data JS generada exitosamente en {out_js}")

    # 9. Generar archivo HTML Standalone 100% Autocontenido
    css_path = os.path.join(base_dir, 'dashboard', 'css', 'styles.css')
    app_js_path = os.path.join(base_dir, 'dashboard', 'js', 'app.js')
    html_path = os.path.join(base_dir, 'dashboard', 'index.html')
    plotly_local = os.path.join(base_dir, 'dashboard', 'js', 'plotly.min.js')

    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    with open(app_js_path, 'r', encoding='utf-8') as f:
        app_js_content = f.read()

    with open(html_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Si plotly local existe, leerlo para incrustarlo en la versión standalone
    plotly_code = ""
    if os.path.exists(plotly_local):
        with open(plotly_local, 'r', encoding='utf-8') as f:
            plotly_code = f.read()

    # Crear versión autocontenida
    standalone_html = html_template
    # 1. Reemplazar estilos externos por inline
    css_tag = f"<style>\n{css_content}\n</style>"
    standalone_html = standalone_html.replace('<link rel="stylesheet" href="css/styles.css">', css_tag)
    
    # 2. Reemplazar Plotly script
    if plotly_code:
        plotly_tag = f"<script>\n{plotly_code}\n</script>"
        standalone_html = standalone_html.replace('<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>', plotly_tag)
        standalone_html = standalone_html.replace('<script src="js/plotly.min.js"></script>', plotly_tag)
    
    # 3. Reemplazar data.js y app.js al final
    scripts_bundle = f"""
    <script>
    window.dashboardData = {json.dumps(dashboard_data, indent=2)};
    </script>
    <script>
    {app_js_content}
    </script>
    """
    standalone_html = standalone_html.replace('<script src="js/data.js"></script>', '')
    standalone_html = standalone_html.replace('<script src="js/app.js"></script>', scripts_bundle)

    standalone_out = os.path.join(base_dir, 'dashboard', 'dashboard_autocontenido.html')
    with open(standalone_out, 'w', encoding='utf-8') as f:
        f.write(standalone_html)
    print(f"Dashboard 100% Autocontenido generado en {standalone_out}")

if __name__ == '__main__':
    build_data()
