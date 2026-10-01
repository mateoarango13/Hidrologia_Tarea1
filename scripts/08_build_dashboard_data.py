import pandas as pd
import numpy as np
import json
import os

def build_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datos_path = os.path.join(base_dir, 'datos', 'datos_mensuales_maipo.csv')
    tabla_a_path = os.path.join(base_dir, 'figuras', 'tabla_1_6_sintesis_clasificacion.csv')
    tabla_subperiodos_path = os.path.join(base_dir, 'figuras', 'tabla_1_5_subperiodos_estabilidad.csv')
    tabla_relaciones_path = os.path.join(base_dir, 'figuras', 'tabla_2_1_metricas_relaciones.csv')
    tabla_errores_grupo_path = os.path.join(base_dir, 'figuras', 'tabla_2_1_errores_por_grupo.csv')
    tabla_influyentes_path = os.path.join(base_dir, 'figuras', 'tabla_2_1_meses_influyentes.csv')
    tabla_rezagos_path = os.path.join(base_dir, 'figuras', 'tabla_2_2_correlaciones_rezagos.csv')
    tabla_metricas_bloque_path = os.path.join(base_dir, 'figuras', 'tabla_2_3_metricas_por_bloque.csv')
    tabla_pred_path = os.path.join(base_dir, 'figuras', 'tabla_2_3_predicciones_fuera_ajuste.csv')
    
    df = pd.read_csv(datos_path)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # 1. Integridad del registro y completitud dentro de la cobertura real de cada serie.
    record_start = df['date'].min()
    record_end = df['date'].max()
    expected_months = len(pd.date_range(record_start, record_end, freq='MS'))
    record_dates = pd.date_range(record_start, record_end, freq='MS')
    missing_record_dates = int(len(record_dates.difference(pd.DatetimeIndex(df['date'].drop_duplicates()))))
    quality_specs = [
        ('P_local_mm', 'Precipitación local', 'mm/mes', True),
        ('Caudal_m3s', 'Caudal medio Q / lámina R', 'm³/s · mm/mes', True),
        ('P_IMERG_mm', 'Precipitación satelital IMERG', 'mm/mes', False),
        ('Temp_C', 'Temperatura ERA5-Land', '°C', False)
    ]
    quality_series = []
    for column, label, unit, uses_full_record in quality_specs:
        valid_mask = df[column].notna()
        if column == 'Caudal_m3s':
            valid_mask &= df['Q_lamina_mm'].notna()
        valid_dates = df.loc[valid_mask, 'date']
        if uses_full_record:
            coverage_start, coverage_end = record_start, record_end
            expected = expected_months
            available = int(valid_mask.sum())
        elif len(valid_dates):
            coverage_start, coverage_end = valid_dates.min(), valid_dates.max()
            expected = len(pd.date_range(coverage_start, coverage_end, freq='MS'))
            in_coverage = df['date'].between(coverage_start, coverage_end)
            available = int((in_coverage & valid_mask).sum())
        else:
            coverage_start, coverage_end, expected, available = None, None, 0, 0
        missing = expected - available
        quality_series.append({
            'column': column,
            'label': label,
            'unit': unit,
            'coverageStart': coverage_start.strftime('%Y-%m') if coverage_start is not None else None,
            'coverageEnd': coverage_end.strftime('%Y-%m') if coverage_end is not None else None,
            'available': available,
            'expected': expected,
            'missing': missing,
            'completenessPct': round(100 * available / expected, 2) if expected else 0,
            'outsideCoverage': expected_months - expected,
            'usesFullRecord': uses_full_record
        })

    checked_columns = ['P_local_mm', 'P_IMERG_mm', 'Caudal_m3s', 'Q_lamina_mm']
    qualitySummary = {
        'recordStart': record_start.strftime('%Y-%m'),
        'recordEnd': record_end.strftime('%Y-%m'),
        'rows': int(len(df)),
        'expectedMonths': expected_months,
        'duplicateDates': int(df['date'].duplicated().sum()),
        'missingRecordDates': missing_record_dates,
        'negativeHydrologyValues': int(df[checked_columns].lt(0).sum().sum()),
        'series': quality_series
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
    
    # 4. Relaciones del Rol B; cada panel conserva sus pares válidos y fechas.
    season_map = {12:'Verano', 1:'Verano', 2:'Verano',
                  3:'Otoño', 4:'Otoño', 5:'Otoño',
                  6:'Invierno', 7:'Invierno', 8:'Invierno',
                  9:'Primavera', 10:'Primavera', 11:'Primavera'}
    relation_specs = {
        'precipitation': ('P_local_mm', 'P_IMERG_mm'),
        'localFlow': ('P_local_mm', 'Caudal_m3s'),
        'imergFlow': ('P_IMERG_mm', 'Caudal_m3s'),
        'localRunoff': ('P_local_mm', 'Q_lamina_mm'),
        'imergRunoff': ('P_IMERG_mm', 'Q_lamina_mm')
    }
    metrics_by_pair = {}
    if os.path.exists(tabla_relaciones_path):
        df_rel = pd.read_csv(tabla_relaciones_path)
        metrics_by_pair = {(row['x'], row['y']): row for row in df_rel.to_dict(orient='records')}

    scatter_pairs = {}
    for key, (x_column, y_column) in relation_specs.items():
        pair = df.dropna(subset=[x_column, y_column]).copy()
        pair['season'] = pair['month'].map(season_map)
        traces = []
        for season in ['Verano', 'Otoño', 'Invierno', 'Primavera']:
            season_data = pair[pair['season'] == season]
            traces.append({
                'name': season,
                'x': season_data[x_column].round(2).tolist(),
                'y': season_data[y_column].round(2).tolist(),
                'date': season_data['date'].dt.strftime('%Y-%m').tolist()
            })
        metric = metrics_by_pair.get((x_column, y_column), metrics_by_pair.get((y_column, x_column), {}))
        scatter_pairs[key] = {
            'xTitle': x_column,
            'yTitle': y_column,
            'traces': traces,
            'n': int(len(pair)),
            'periodStart': pair['date'].min().strftime('%Y-%m') if len(pair) else None,
            'periodEnd': pair['date'].max().strftime('%Y-%m') if len(pair) else None,
            'maxVal': round(float(max(pair[x_column].max(), pair[y_column].max())), 2) if len(pair) else 0,
            'pearson': metric.get('pearson_r'),
            'spearman': metric.get('spearman_rho'),
            'meanBias': metric.get('mean_bias_PI_minus_PL_mm_month'),
            'mae': metric.get('mae_mm_month'),
            'rmse': metric.get('rmse_mm_month'),
            'pbias': metric.get('pbias_PI_minus_PL_percent')
        }

    scatterImerg = {
        'traces': scatter_pairs['precipitation']['traces'],
        'maxVal': [scatter_pairs['precipitation']['maxVal']]
    }

    erroresGrupo = []
    if os.path.exists(tabla_errores_grupo_path):
        erroresGrupo = pd.read_csv(tabla_errores_grupo_path).to_dict(orient='records')

    mesesInfluyentes = []
    if os.path.exists(tabla_influyentes_path):
        mesesInfluyentes = pd.read_csv(tabla_influyentes_path).head(5).to_dict(orient='records')
    if mesesInfluyentes and scatter_pairs['precipitation']['rmse'] is not None:
        total_sse = scatter_pairs['precipitation']['rmse'] ** 2 * scatter_pairs['precipitation']['n']
        top_five_sse = sum(row['error_PI_minus_PL_mm_month'] ** 2 for row in mesesInfluyentes)
        mesesInfluyentesShare = round(100 * top_five_sse / total_sse, 2)
    else:
        mesesInfluyentesShare = None
    
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
        
    # 6. Rezagos exploratorios de anomalías; lluvia en t-k frente a caudal en t.
    rezagos = None
    if os.path.exists(tabla_rezagos_path):
        df_rez = pd.read_csv(tabla_rezagos_path)
        df_rez_q = df_rez[(df_rez['rain_variable'] == 'P_local_mm') & (df_rez['flow_variable'] == 'Caudal_m3s')].sort_values('lag_months')
        df_rez_imerg = df_rez[(df_rez['rain_variable'] == 'P_IMERG_mm') & (df_rez['flow_variable'] == 'Caudal_m3s')].sort_values('lag_months')
        rezagos = {
            'lags': df_rez_q['lag_months'].tolist(),
            'r_local': df_rez_q['pearson_r_anomalies'].round(4).tolist(),
            'rho_local': df_rez_q['spearman_rho_anomalies'].round(4).tolist(),
            'n_local': df_rez_q['n_valid_pairs'].tolist(),
            'r_imerg': df_rez_imerg['pearson_r_anomalies'].round(4).tolist() if len(df_rez_imerg) > 0 else [],
            'n_imerg': df_rez_imerg['n_valid_pairs'].tolist() if len(df_rez_imerg) > 0 else []
        }
    
    # 7. Métricas por bloque para comparar contra las líneas base del ajuste.
    metricasPorBloque = []
    if os.path.exists(tabla_metricas_bloque_path):
        metricasPorBloque = pd.read_csv(tabla_metricas_bloque_path).to_dict(orient='records')

    rezagosSeleccionados = []
    modelosLluviaSeleccionados = []
    seleccion_path = os.path.join(base_dir, 'figuras', 'tabla_2_3_seleccion_modelos_ajuste.csv')
    if os.path.exists(seleccion_path):
        df_sel = pd.read_csv(seleccion_path)
        selected = df_sel[(df_sel['task'] == 'estimar_caudal') &
                          (df_sel['selected_on_inner_tuning'].astype(str).str.lower() == 'true') &
                          df_sel['candidate_lag_months'].notna()]
        rezagosSeleccionados = selected[[
            'predictor', 'outer_fold', 'candidate_lag_months',
            'anomaly_model_intercept', 'anomaly_model_slope'
        ]].drop_duplicates().to_dict(orient='records')
        selected_rain = df_sel[(df_sel['task'] == 'estimar_precipitacion_local') &
                               (df_sel['candidate_model'] == 'seleccion_final_reajustada')]
        for row in selected_rain.to_dict(orient='records'):
            metric = next((item for item in metricasPorBloque
                           if item['task'] == 'estimar_precipitacion_local' and
                           item['outer_fold'] == row['outer_fold'] and
                           item['model'] == 'Corrección seleccionada en ajuste'), {})
            modelosLluviaSeleccionados.append({
                'outer_fold': row['outer_fold'],
                'model_variant': metric.get('model_variant'),
                'intercept': row['intercept'],
                'slope': row['slope'],
                'smearing_factor': None if pd.isna(row['smearing_factor']) else row['smearing_factor']
            })

    # 8. Predicciones externas y residuos de ambos modelos de caudal con rezago.
    validacionTemporal = None
    if os.path.exists(tabla_pred_path):
        df_pred = pd.read_csv(tabla_pred_path)
        df_pred_q = df_pred[(df_pred['task'] == 'estimar_caudal') &
                            (df_pred['model'].str.contains('anomal', case=False, na=False))].copy()
        if len(df_pred_q) > 0:
            df_pred_q['date'] = pd.to_datetime(df_pred_q['date'])
            observed = df_pred_q.drop_duplicates('date').set_index('date')['observed']
            local_rows = df_pred_q[df_pred_q['predictor'].str.contains('P_local', case=False, na=False)].set_index('date')
            imerg_rows = df_pred_q[df_pred_q['predictor'].str.contains('P_IMERG', case=False, na=False)].set_index('date')
            dates = sorted(df_pred_q['date'].unique())
            validacionTemporal = {
                'fechas': [date.strftime('%Y-%m-%d') for date in dates],
                'observado': [round(float(observed.get(date)), 2) for date in dates],
                'modeladoLocal': [round(float(local_rows.at[date, 'predicted']), 2) if date in local_rows.index else None for date in dates],
                'modeladoImerg': [round(float(imerg_rows.at[date, 'predicted']), 2) if date in imerg_rows.index else None for date in dates],
                'bloques': [df_pred_q.loc[df_pred_q['date'] == date, 'outer_fold'].iloc[0] for date in dates]
            }

            residuos = {}
            for predictor, key, label in [
                ('P_local', 'local', 'Precipitación local'),
                ('P_IMERG', 'imerg', 'IMERG')
            ]:
                subset = df_pred_q[df_pred_q['predictor'].str.contains(predictor, case=False, na=False)].copy()
                residuos[key] = {
                    'name': label,
                    'date': subset['date'].dt.strftime('%Y-%m-%d').tolist(),
                    'predicted': subset['predicted'].round(2).tolist(),
                    'residual': subset['residual_pred_minus_obs'].round(2).tolist(),
                    'month': subset['calendar_month'].tolist(),
                    'block': subset['outer_fold'].tolist()
                }
            validacionTemporal['residuals'] = residuos
            
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
        'qualitySummary': qualitySummary,
        'cicloAnual': cicloAnual,
        'histPrecip': histPrecip,
        'scatterImerg': scatterImerg,
        'scatterPairs': scatter_pairs,
        'erroresGrupo': erroresGrupo,
        'mesesInfluyentes': mesesInfluyentes,
        'mesesInfluyentesShare': mesesInfluyentesShare,
        'subperiodos': subperiodos,
        'rezagos': rezagos,
        'metricasPorBloque': metricasPorBloque,
        'rezagosSeleccionados': rezagosSeleccionados,
        'modelosLluviaSeleccionados': modelosLluviaSeleccionados,
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
