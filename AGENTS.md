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

---

## 2. REGLAS FUNDAMENTALES DEL PROYECTO HIDROLÓGICO

### A. Dataset Maestro Único: `datos/datos_mensuales_maipo.csv`
- Todos los análisis (gráficos, balances, correlaciones, modelos) **DEBEN** alimentarse de este archivo maestro.
- **Rango temporal consolidado:** Enero 1980 a Marzo 2020 (483 meses / > 40 años).
- **Regla estricta de longitud temporal:** La tarea exige al menos 25 años de registro. El registro local (precipitación observada y caudal) tiene 40 años completos. Los datos satelitales (GPM IMERG) inician en junio del 2000 (~20 años). **BAJO NINGUNA CIRCUNSTANCIA** se debe recortar la serie local de 40 años al periodo del satélite; se utiliza unión externa (*outer join*), rellenando con `NaN` los periodos donde el satélite aún no existía.

### B. Unidades Hidrológicas Estándar
- **Área de la cuenca:** $4837.4 \text{ km}^2$ ($4.8374 \times 10^9 \text{ m}^2$).
- **Precipitación local (CR2MET / Estaciones):** `precip_local_mm` en $\text{mm/mes}$.
- **Precipitación satelital (GPM IMERG V07):** `precip_sat_imerg_mm` en $\text{mm/mes}$.
- **Caudal medio mensual:**
  - En volumen/tiempo: `caudal_m3_s` en $\text{m}^3/\text{s}$.
  - En lámina equivalente: `caudal_mm` en $\text{mm/mes}$, calculado como:
    $$Q_{\text{mm}} = \frac{Q_{\text{m}^3/\text{s}} \times (\text{días del mes} \times 86400)}{4837.4 \times 10^6 \text{ m}^2} \times 1000$$
- **Temperatura ERA5-Land:** `temp_era5_c` en $^{\circ}\text{C}$.

### C. Estructura del Repositorio
- `datos/`: Únicamente datasets procesados livianos (el CSV maestro `datos_mensuales_maipo.csv`).
- `scripts/`: Scripts modulares y numerados (`01_...`, `02_...`, etc.) comentados y reproducibles.
- `figuras/`: Gráficas generadas en alta resolución (mínimo 300 DPI) listas para el informe.
- `documentos/`: Enunciado de la tarea, rúbricas y borradores del informe.
- `datos_pesados_ignorados/`: Archivos `.zip`, NetCDF o HDF5 crudos (IGNORADOS por `.gitignore`, no subir a GitHub).

---

## 3. PROTOCOLO OBLIGATORIO AL FINALIZAR UNA TAREA (HANDOVER)
Cuando el agente concluya una sesión de trabajo con su usuario:
1. **Registrar la entrada en `BITACORA_AGENTES.md`** siguiendo la plantilla establecida (fecha, integrante, agente usado, resumen de lo realizado, validaciones numéricas, figuras generadas y próximos pasos).
2. Recordar al usuario hacer **Commit y Push en GitHub Desktop** para que los demás compañeros y sus agentes reciban la actualización.
