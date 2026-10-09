# INSTRUCCIONES PARA AGENTES DE INTELIGENCIA ARTIFICIAL (AGENTS.md)
# Proyecto: Tarea 1 - Hidrología (UNAL) - Análisis Hidroclimático de Cuenca
# Cuenca Asignada: Río Maipo en El Manzano (Código CAMELS-CL: 5710001)

Este documento es una directriz de contexto y protocolo obligatorio para **cualquier agente de Inteligencia Artificial** (Antigravity, Claude Code, Cursor, Copilot, ChatGPT, Gemini, etc.) que abra este repositorio en el computador de cualquier integrante del equipo.

---

## 1. PROTOCOLO OBLIGATORIO DE INICIO PARA EL AGENTE
Antes de responder al usuario o escribir cualquier línea de código, el agente debe:
1. **Leer este archivo (`AGENTS.md`)** para entender las reglas y restricciones del proyecto.
2. **Leer `BITACORA_AGENTES.md`** en la raíz del repositorio para:
   - Conocer la última fase completada y qué agente/compañero la realizó.
   - **Hacer una revisión cruzada (Peer Review):** Validar brevemente la coherencia del trabajo anterior antes de construir sobre él.
   - Identificar cuál es la tarea inmediata pendiente según la hoja de ruta.
  - La carpeta temporal `documentos/bitacora_datos_temporal/` ya fue eliminada (2026-10-07) al organizar la entrega final; no volver a crearla.

---

## 2. REGLAS FUNDAMENTALES DEL PROYECTO HIDROLÓGICO

### A. Dataset Maestro Único: `datos/datos_mensuales_maipo.csv`
- Todos los análisis (gráficos, balances, correlaciones, modelos) **DEBEN** alimentarse de este archivo maestro.
- **Rango temporal del CSV:** Enero 1980 a Abril 2020 (484 filas mensuales). Lo construye `scripts/03_integrar_datos.py` desde `datos/datos_mensuales_procesados.csv` (script 01) y `datos/datos_satelitales_imerg_era5.csv` (script 02). **Criterio de completitud (desde 2026-10-07):** acumulado de P solo con el 100 % de los días; medias de Q y T con >= 80 % de los días. Resultado: P 484/484, T 484/484, Q 463/484 (14 meses sin datos y 7 parciales excluidos), IMERG y ERA5-Land 238 meses (2000-06 a 2020-03). No describir todas las filas como meses con observación válida.
- **Regla estricta de longitud temporal:** La tarea exige al menos 25 años de registro. Conservar todo el periodo local disponible y no recortarlo a la cobertura satelital, que inicia en junio de 2000; usar unión externa (*outer join*) y conservar `NaN` donde una fuente no existe.

### B. Unidades Hidrológicas Estándar
- **Área de la cuenca:** $4839.047 \text{ km}^2$ (atributo `area_km2` de CAMELS-CL; el script 01 la lee del archivo de atributos). Es la única área usada en scripts, figuras, informe y dashboard (antes se usaba 4837.4 en algunos lugares; ya se unificó).
- **Precipitación local (referencia CR2MET/observacional según la procedencia del proyecto):** `P_local_mm` en $\text{mm/mes}$. Confirmar los metadatos de la fuente antes de afirmar estaciones concretas o independencia respecto de otros productos.
- **Precipitación satelital:** `P_IMERG_mm` en $\text{mm/mes}$. `scripts/02_descargar_satelite.py` selecciona `NASA/GPM_L3/IMERG_MONTHLY_V06` (IMERG Final mensual V06; DOI de producto `10.5067/GPM/IMERG/3B-MONTH/06`). La versión que originó el CSV debe confirmarse; no etiquetar sus valores como V07 hasta reconciliar la procedencia. DOI de V07: `10.5067/GPM/IMERG/3B-MONTH/07`.
- **Caudal medio mensual:**
  - En volumen/tiempo: `Caudal_m3s` en $\text{m}^3/\text{s}$.
  - En lámina equivalente: `Q_lamina_mm` en $\text{mm/mes}$, calculado como:
    $$Q_{\text{mm}} = \frac{Q_{\text{m}^3/\text{s}} \times (\text{días del mes} \times 86400)}{4839.047 \times 10^6 \text{ m}^2} \times 1000$$
- **Temperatura (desde 2026-10-07):** `Temp_C` es la temperatura de la base: media mensual de (Tmax+Tmin)/2 CR2MET de CAMELS-CL, 1980-2020, en $^{\circ}\text{C}$ (la guía pide usar la temperatura de la base). `Temp_ERA5L_C` es ERA5-Land (2000-06 a 2020-03) y se usa solo como contraste; nunca unir las dos series. ERA5-Land es 5.6 °C más fría en promedio.

### C. Estructura del Repositorio
- `datos/`: CSV maestro `datos_mensuales_maipo.csv`, sus dos insumos (`datos_mensuales_procesados.csv` y `datos_satelitales_imerg_era5.csv`) y los subconjuntos de datos de entrada listados abajo.
- `scripts/`: Scripts modulares y numerados (`01_...`, `02_...`, etc.) comentados y reproducibles.
- `figuras/`: Gráficas generadas en alta resolución (mínimo 300 DPI) listas para el informe.
- `documentos/`: `informe_final_tarea1.tex/.pdf` (informe entregable) en la raíz de la carpeta; `anexos/` (documentos detallados de los puntos 1–5); `presentacion/` (guiones de la exposición); `material_interno/` (enunciado, plan de trabajo y notas internas; NO va en el ZIP).
- `dashboard/`: dashboard interactivo de apoyo a la exposición (lo regenera `scripts/08_build_dashboard_data.py`).
- La estructura de entrega y el armado del ZIP están descritos en `README.md`; dependencias en `requirements.txt`.
- `datos_pesados_ignorados/`: Archivos `.zip`, NetCDF o HDF5 crudos (IGNORADOS por `.gitignore`, no subir a GitHub).
- **Excepción acordada (2026-10-07):** `datos/campos_era5/` contiene los campos ERA5 mensuales globales a 1° del punto 5 (SST, presión al nivel del mar y geopotencial 500 hPa, 1979–2020). Sí se versionan en GitHub (cada archivo < 100 MB) para que todo el equipo use los mismos datos; se generan con `scripts/15_p5_1_descargar_campos_era5.py`.
- **Excepción (2026-10-07):** `datos/camels_cl_5710001/` contiene el subconjunto diario CAMELS-CL efectivamente usado (caudal, precipitación y Tmax/Tmin CR2MET, atributos y polígono, ~1.5 MB). La guía exige entregar los datos de entrada en el ZIP; lo usan `scripts/20_p1_4_auditoria_diaria.py` y `scripts/21_p3_1_temperatura_cr2met.py`.
- **Excepción (2026-10-07):** `datos/ASTGTM_003-20261004_142607/` contiene las cuatro teselas ASTER GDEM v3 (30 m; S34–S35, W070–W071; ~128 MB, cada archivo < 31 MB) descargadas de NASA Earthdata. Las usa `scripts/22_p1_0_topografia_cuenca.py` para el mapa topográfico y la curva hipsométrica. Solo se leen los `*_dem.tif`; los `*_num.tif` son metadatos de calidad del producto.
- **Excepción (2026-10-07):** `datos/campos_ersst/` contiene el subconjunto de NOAA ERSST v5 (2°, 1979–2020, ~15 MB) que genera `scripts/24_p5_3_contraste_ersst.py` para contrastar el producto de SST del punto 5.

---

## 3. PROTOCOLO OBLIGATORIO AL FINALIZAR UNA TAREA (HANDOVER)
Cuando el agente concluya una sesión de trabajo con su usuario:
1. **Registrar la entrada en `BITACORA_AGENTES.md`** siguiendo la plantilla establecida (fecha, integrante, agente usado, resumen de lo realizado, validaciones numéricas, figuras generadas y próximos pasos).
2. Recordar al usuario hacer **Commit y Push en GitHub Desktop** para que los demás compañeros y sus agentes reciban la actualización.
