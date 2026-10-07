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
  - Leer el aviso prioritario sobre `documentos/bitacora_datos_temporal/` y comunicar al integrante que consulta el repositorio su propósito y que toda esa carpeta debe eliminarse antes de la entrega final.

---

## 2. REGLAS FUNDAMENTALES DEL PROYECTO HIDROLÓGICO

### A. Dataset Maestro Único: `datos/datos_mensuales_maipo.csv`
- Todos los análisis (gráficos, balances, correlaciones, modelos) **DEBEN** alimentarse de este archivo maestro.
- **Rango temporal del CSV auditado:** Enero 1980 a Abril 2020 (484 filas mensuales). La precipitación local tiene un faltante en 2020-04 y el caudal tiene 14 faltantes; no describir todas las filas como meses con observación válida.
- **Regla estricta de longitud temporal:** La tarea exige al menos 25 años de registro. Conservar todo el periodo local disponible y no recortarlo a la cobertura satelital, que inicia en junio de 2000; usar unión externa (*outer join*) y conservar `NaN` donde una fuente no existe.

### B. Unidades Hidrológicas Estándar
- **Área de la cuenca:** $4837.4 \text{ km}^2$ ($4.8374 \times 10^9 \text{ m}^2$).
- **Precipitación local (referencia CR2MET/observacional según la procedencia del proyecto):** `P_local_mm` en $\text{mm/mes}$. Confirmar los metadatos de la fuente antes de afirmar estaciones concretas o independencia respecto de otros productos.
- **Precipitación satelital:** `P_IMERG_mm` en $\text{mm/mes}$. `scripts/02_descargar_satelite.py` selecciona `NASA/GPM_L3/IMERG_MONTHLY_V06` (IMERG Final mensual V06; DOI de producto `10.5067/GPM/IMERG/3B-MONTH/06`). La versión que originó el CSV debe confirmarse; no etiquetar sus valores como V07 hasta reconciliar la procedencia. DOI de V07: `10.5067/GPM/IMERG/3B-MONTH/07`.
- **Caudal medio mensual:**
  - En volumen/tiempo: `Caudal_m3s` en $\text{m}^3/\text{s}$.
  - En lámina equivalente: `Q_lamina_mm` en $\text{mm/mes}$, calculado como:
    $$Q_{\text{mm}} = \frac{Q_{\text{m}^3/\text{s}} \times (\text{días del mes} \times 86400)}{4837.4 \times 10^6 \text{ m}^2} \times 1000$$
- **Temperatura ERA5-Land:** `Temp_C` en $^{\circ}\text{C}$.

### C. Estructura del Repositorio
- `datos/`: Únicamente datasets procesados livianos (el CSV maestro `datos_mensuales_maipo.csv`).
- `scripts/`: Scripts modulares y numerados (`01_...`, `02_...`, etc.) comentados y reproducibles.
- `figuras/`: Gráficas generadas en alta resolución (mínimo 300 DPI) listas para el informe.
- `documentos/`: Enunciado de la tarea, rúbricas y borradores del informe.
- `datos_pesados_ignorados/`: Archivos `.zip`, NetCDF o HDF5 crudos (IGNORADOS por `.gitignore`, no subir a GitHub).
- **Excepción acordada (2026-10-07):** `datos/campos_era5/` contiene los campos ERA5 mensuales globales a 1° del punto 5 (SST, presión al nivel del mar y geopotencial 500 hPa, 1979–2020). Sí se versionan en GitHub (cada archivo < 100 MB) para que todo el equipo use los mismos datos; se generan con `scripts/15_p5_1_descargar_campos_era5.py`.
- **Excepción (2026-10-07):** `datos/camels_cl_5710001/` contiene el subconjunto diario CAMELS-CL efectivamente usado (caudal, precipitación y Tmax/Tmin CR2MET, atributos y polígono, ~1.5 MB). La guía exige entregar los datos de entrada en el ZIP; lo usan `scripts/20_p1_4_auditoria_diaria.py` y `scripts/21_p3_1_temperatura_cr2met.py`.
- **Excepción (2026-10-07):** `datos/ASTGTM_003-20261004_142607/` contiene las cuatro teselas ASTER GDEM v3 (30 m; S34–S35, W070–W071; ~128 MB, cada archivo < 31 MB) descargadas de NASA Earthdata. Las usa `scripts/22_p1_0_topografia_cuenca.py` para el mapa topográfico y la curva hipsométrica. Solo se leen los `*_dem.tif`; los `*_num.tif` son metadatos de calidad del producto.

---

## 3. PROTOCOLO OBLIGATORIO AL FINALIZAR UNA TAREA (HANDOVER)
Cuando el agente concluya una sesión de trabajo con su usuario:
1. **Registrar la entrada en `BITACORA_AGENTES.md`** siguiendo la plantilla establecida (fecha, integrante, agente usado, resumen de lo realizado, validaciones numéricas, figuras generadas y próximos pasos).
2. Recordar al usuario hacer **Commit y Push en GitHub Desktop** para que los demás compañeros y sus agentes reciban la actualización.
