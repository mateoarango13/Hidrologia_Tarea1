# Tarea 1 — Clasificación hidroclimática mensual del Río Maipo en El Manzano

**Curso:** Hidrología, Universidad Nacional de Colombia, Sede Medellín, semestre 202602. **Profesor:** Carlos David Hoyos.
**Cuenca:** Río Maipo en El Manzano, Chile central. Estación DGA `5710001` (CAMELS-CL), 4839 km².

## Integrantes
- Mateo Arango Cortés
- Bryan Alexander Salazar Castañeda
- Santiago Ortega Ruiz
- Tomás Gómez Zuleta

## Contenido del paquete

```text
├── README.md                    # Este archivo
├── requirements.txt             # Dependencias de Python y sus versiones (probadas en un entorno limpio)
├── AGENTS.md                    # Protocolo de uso de IA del equipo (evidencia de uso de IA)
├── BITACORA_AGENTES.md          # Registro de todas las sesiones con IA (evidencia de uso de IA)
│
├── documentos/
│   ├── informe_final_tarea1.pdf # INFORME FINAL: cinco secciones, referencias, Anexo A (trazabilidad)
│   │                            #   y Anexo B (figuras complementarias)
│   └── informe_final_tarea1.tex # Fuente LaTeX del informe
│
├── scripts/                     # Códigos numerados 01–25 y módulos comunes (rol_c_comun.py, p5_comun.py)
│
├── datos/                       # Datos de entrada efectivamente usados
│   ├── datos_mensuales_maipo.csv        # Serie maestra mensual 1980-01 a 2020-04 (todas las variables)
│   ├── datos_mensuales_procesados.csv   # Agregación mensual de CAMELS-CL con días válidos por mes (script 01)
│   ├── datos_satelitales_imerg_era5.csv # IMERG y ERA5-Land mensuales de la cuenca (script 02)
│   ├── camels_cl_5710001/               # Subconjunto diario CAMELS-CL: Q, P y Tmax/Tmin CR2MET, atributos y polígono
│   ├── campos_era5/                     # SST, PNM y Z500 mensuales ERA5 a 1°, 1979–2020, y costa de Natural Earth
│   ├── campos_ersst/                    # SST NOAA ERSST v5 a 2°, 1979–2020 (contraste del punto 5)
│   └── ASTGTM_003-20261004_142607/      # Cuatro teselas ASTER GDEM v3 (mapa topográfico e hipsometría)
│
├── figuras/                     # Productos del análisis: figuras PNG (>= 300 DPI), tablas tabla_*.csv,
│                                #   series procesadas y anomalías serie_*.csv
│
└── dashboard/                   # Dashboard interactivo usado en la exposición
    ├── dashboard_autocontenido.html     # ABRIR ESTE: un solo archivo, funciona sin internet
    └── index.html, css/, js/, vendor/   # Versión modular (mismo contenido)
```

## Dashboard

Abrir `dashboard/dashboard_autocontenido.html` con doble clic en cualquier navegador moderno (Chrome, Edge o Firefox). El archivo incluye los datos, Plotly, los íconos y las tipografías, así que **no necesita internet ni servidor**. Los únicos enlaces externos son los DOI de las referencias. El botón del informe abre `documentos/informe_final_tarea1.pdf`, por lo que conviene conservar la estructura de carpetas del paquete.

## Procedencia de los datos

| Variable | Columna / archivo | Fuente | Unidades |
|---|---|---|---|
| Caudal | `Caudal_m3s`, `Q_lamina_mm`; `camels_cl_5710001/q_m3s_day.csv` | CAMELS-CL (Alvarez-Garreton et al., 2018, doi:10.5194/hess-22-5817-2018), estación DGA 5710001 | m³/s; mm/mes |
| Precipitación de referencia | `P_local_mm`; `precip_cr2met_day.csv` | CR2MET, distribuida por CAMELS-CL | mm/mes |
| Temperatura (de la base) | `Temp_C`; `tmax_cr2met_day.csv`, `tmin_cr2met_day.csv` | CR2MET, distribuida por CAMELS-CL: media mensual de (Tmax+Tmin)/2 | °C |
| Precipitación satelital | `P_IMERG_mm`; `datos_satelitales_imerg_era5.csv` | NASA GPM IMERG Final mensual V06 (doi:10.5067/GPM/IMERG/3B-MONTH/06), vía Google Earth Engine | mm/mes |
| Temperatura de contraste | `Temp_ERA5L_C`; `datos_satelitales_imerg_era5.csv` | ECMWF ERA5-Land mensual, vía Google Earth Engine | °C |
| Campos climáticos | `campos_era5/*.nc` | ECMWF ERA5 mensual (Copernicus CDS), remuestreado a 1° | K, Pa, m²/s² |
| SST de contraste | `campos_ersst/*.nc` | NOAA ERSST v5 (doi:10.7289/V5T72FNM), NOAA PSL | °C |
| Topografía | `ASTGTM_003-*/*_dem.tif` | ASTER GDEM v3 (doi:10.5067/ASTER/ASTGTM.003), NASA Earthdata | m |
| Delimitación | `camels_cl_5710001/polygon/` | Polígono de la cuenca CAMELS-CL | — |

**Criterio de completitud mensual (aplicado en todo el análisis):** acumulado de precipitación solo con el 100 % de los días válidos; medias de caudal y temperatura con al menos el 80 % de los días. Resultado: precipitación y temperatura con 484 de 484 meses; caudal con 463 (14 meses sin datos y 7 con datos parciales excluidos). Los faltantes nunca se rellenan con ceros; la única interpolación es la de la anomalía del caudal para el análisis espectral, documentada en el informe.

Los datos de IMERG analizados (2000-06 a 2020-03) están en `datos_satelitales_imerg_era5.csv` y en la columna `P_IMERG_mm` del CSV maestro. Fuera de ese intervalo la columna queda en `NaN`, porque el periodo local no se recorta.

## Requisitos

Python 3.13 (probado; también sirve >= 3.10) con las librerías de `requirements.txt`. Se recomienda un entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
```

`statsmodels 0.14.5` requiere `pandas` 2.x (no es compatible con pandas 3). `cdsapi`, `earthengine-api` y `geopandas` solo hacen falta para **volver a descargar** datos, que ya vienen incluidos. No se entregan credenciales de acceso.

## Orden de ejecución

Todos los scripts se ejecutan desde la raíz del paquete (`python scripts/<nombre>.py`), usan rutas relativas al paquete y escriben sus productos en `figuras/`.

1. **Datos (ya entregados):** `01_preparar_datos.py` → `03_integrar_datos.py` reconstruyen el CSV maestro a partir de CAMELS-CL y del archivo satelital. `02_descargar_satelite.py` (Earth Engine) y `15_p5_1_descargar_campos_era5.py` (Copernicus CDS) solo hacen falta para volver a descargar, y requieren credenciales.
2. **Punto 1:** `22_p1_0_topografia_cuenca.py`, `23_p1_5_isoterma_cero.py`, `07_rol_a_explorador.py`, `20_p1_4_auditoria_diaria.py`.
3. **Punto 2:** `04_analisis_precipitacion.py`, `05_anomalias_rezagos.py`, `06_modelos_validacion_temporal.py`.
4. **Punto 3:** `09_p3_2_anomalias.py`, `10_p3_3_escalas_temporales.py`, `11_p3_4_metodos_tendencia.py`, `12_p3_5_incertidumbre_robustez.py`, `21_p3_1_temperatura_cr2met.py`, `25_p3_6_balance_anual.py`.
5. **Punto 4:** `13_p4_1_preparacion_espectral.py`, `14_p4_2_espectros_interpretacion.py`.
6. **Punto 5:** `16_p5_1_campos_climaticos.py`, `17_p5_2_mapas_correlacion.py`, `18_p5_3_robustez.py`, `19_p5_4_interpretacion.py`, `24_p5_3_contraste_ersst.py`.
7. **Dashboard (al final):** `08_build_dashboard_data.py`.
8. **Informe:** desde `documentos/`, ejecutar `pdflatex informe_final_tarea1.tex` dos veces. Las figuras se leen de `../figuras/`.

El análisis completo tarda unos 6 minutos. El Anexo A del informe relaciona cada script con sus figuras, tablas y la sección donde se usan.

## Repositorio de trabajo y armado del ZIP

Este repositorio contiene, además del paquete de entrega, material de trabajo que **no** va en el ZIP:
- `documentos/anexos/`: borradores por punto (`.tex/.pdf`) de versiones anteriores; sus cifras pueden no coincidir con el informe final.
- `documentos/presentacion/`: guiones de la exposición.
- `documentos/material_interno/`: enunciado, plan de trabajo, notas, `README_entrega.md` (README del paquete) y `armar_entrega.py`.

Para generar la carpeta y el ZIP de entrega, desde la raíz del repositorio:

```bash
python documentos/material_interno/armar_entrega.py
```

El script copia a `entrega_final/Tarea1_Hidrologia_RioMaipo_5710001/` solo lo que exige la guía, usa `README_entrega.md` como README del paquete y genera el `.zip` a su lado. Deja fuera el material de trabajo, los archivos auxiliares de LaTeX, `__pycache__`, los `*_num.tif` de ASTER (metadatos de calidad que no se usan), `.git/` y `.vscode/`. `entrega_final/` está en `.gitignore`.
