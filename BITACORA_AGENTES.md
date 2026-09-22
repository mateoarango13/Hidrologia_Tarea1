# BITÁCORA DE COORDINACIÓN Y TRABAJO ENTRE AGENTES DE IA (HANDOVER LOG)
# Proyecto: Tarea 1 de Hidrología (UNAL) - Cuenca Río Maipo en El Manzano (5710001)

> **INSTRUCCIÓN PARA EL AGENTE QUE ABRE ESTE ARCHIVO:**  
> 1. Lee la **Última Entrada Registrada** para entender en qué punto quedó el proyecto.
> 2. Haz un breve **Peer Review** (revisión de pares) del código y figuras producidas antes de continuar.
> 3. Al terminar tu labor en esta sesión, **agrega una nueva entrada** al final de este archivo siguiendo la plantilla.

---

## ÍNDICE DE SESIONES Y AVANCE DEL PROYECTO
- **Fase 1:** Preparación de Datos, Descargas Satelitales y Consolidación del Dataset Maestro $\rightarrow$ `[COMPLETADA ✅]`
- **Fase 2:** Análisis Comparativo de Precipitación (Local vs Satélite IMERG) $\rightarrow$ `[PENDIENTE / EN CURSO ⏳]`
- **Fase 3:** Estimación de Evapotranspiración Potencial y Real (Hargreaves / Thornthwaite / Balance) $\rightarrow$ `[PENDIENTE ⏳]`
- **Fase 4:** Balance Hídrico de Cuenca, Análisis de Almacenamiento e Informe Final $\rightarrow$ `[PENDIENTE ⏳]`

---

## ENTRADA #1: FASE 1 — PREPARACIÓN, SATÉLITE Y DATASET MAESTRO
- **Fecha:** 2026-09-20 / 2026-09-22
- **Integrante Responsable:** Mateo Arango
- **Agente de IA utilizado:** Antigravity (Google DeepMind)
- **Estado de la Fase:** COMPLETADA AL 100% ✅

### 1. Resumen de lo Realizado
1. **Datos Locales (CAMELS-CL):**
   - Se procesaron las series históricas de la cuenca 5710001 (*Río Maipo en El Manzano*).
   - Se convirtieron los caudales de $\text{m}^3/\text{s}$ a lámina mensual ($\text{mm/mes}$) usando el área oficial de la cuenca ($4837.4 \text{ km}^2$) y los días exactos de cada mes.
   - Control de calidad: 0% datos faltantes en precipitación local (CR2MET) y < 2% en caudales observados (cumple sobradamente el criterio del < 10%).
2. **Descarga Satelital (Google Earth Engine):**
   - Se configuró la autenticación con Earth Engine (Proyecto: `hidrologia2026-2`).
   - Se extrajo la serie de precipitación satelital **GPM IMERG V07 (Monthly)** (`NASA/GPM_L3/IMERG_MONTHLY_V07`) agregada espacialmente sobre el polígono de la cuenca (2000 a 2020).
   - Se extrajo la temperatura media mensual de reanálisis **ERA5-Land** (`ECMWF/ERA5_LAND/MONTHLY_AGGR`) convertida de Kelvin a Celsius.
3. **Consolidación en Dataset Maestro:**
   - Se generó el archivo `datos/datos_mensuales_maipo.csv` (1980-01 a 2020-03, 483 meses / > 40 años).
   - Se preservaron los 40 años de datos locales mediante unión externa (*outer join*), garantizando el cumplimiento estricto del requisito de $\ge 25$ años.
4. **Infraestructura y Git:**
   - Se configuró `.gitignore` para blindar el repositorio de archivos pesados (`.zip`, `.nc`).
   - Se estructuró el repositorio (`datos/`, `scripts/`, `figuras/`, `documentos/`) y se sincronizó con GitHub y GitHub Desktop.

### 2. Archivos Clave Producidos
- `datos/datos_mensuales_maipo.csv`: Dataset maestro consolidado.
- `scripts/01_preparar_datos.py`: Procesamiento de datos locales CAMELS-CL.
- `scripts/02_descargar_satelite.py`: Script de descarga satelital en Earth Engine.
- `scripts/03_integrar_datos.py`: Fusión de fuentes en el dataset maestro.
- `figuras/grafica_1_1_series.png`: Gráfica de series de tiempo completas.

### 3. Tarea Inmediata para el Siguiente Agente / Integrante
- **Objetivo:** Ejecutar la **Fase 2 (Punto 2 de la Tarea)**.
- **Acciones específicas:**
  1. Crear el script `scripts/04_analisis_precipitacion.py`.
  2. Leer `datos/datos_mensuales_maipo.csv` y filtrar el periodo común (junio 2000 a marzo 2020).
  3. Generar gráfico de dispersión (*Scatter plot*) con línea 1:1 entre `precip_local_mm` y `precip_sat_imerg_mm`.
  4. Generar histogramas / curvas de densidad comparativas.
  5. Calcular métricas estadísticas: Coeficiente de Pearson ($r$), Spearman ($\rho$), Sesgo porcentual (PBIAS), RMSE y MAE. Guardar las figuras en `figuras/`.
  6. Documentar hallazgos físicos (subestimación orográfica de IMERG en alta montaña andina).

---

## PLANTILLA PARA NUEVAS ENTRADAS (COPIAR Y PEGAR ABAJO)

```markdown
## ENTRADA #[Número]: FASE [Número] — [Título de la Tarea]
- **Fecha:** AAAA-MM-DD
- **Integrante Responsable:** [Nombre del compañero]
- **Agente de IA utilizado:** [Nombre de la IA: Claude Code, Cursor, Copilot, ChatGPT, Antigravity, etc.]
- **Estado de la Fase:** [EN CURSO / COMPLETADA]

### 1. Revisión de Pares (Peer Review del trabajo previo)
- [Breve nota confirmando que se revisó lo anterior y si se detectó algún error o ajuste necesario].

### 2. Resumen de lo Realizado en esta Sesión
- [Detalle claro de los scripts creados, fórmulas aplicadas o análisis realizados].

### 3. Archivos Modificados o Generados
- `scripts/...`: [Descripción]
- `figuras/...`: [Descripción]
- `datos/...`: [Descripción]

### 4. Conclusiones y Métricas Relevantes
- [Resultados numéricos clave obtenidos, ej: r = 0.85, PBIAS = -12%, etc.]

### 5. Próximos Pasos para el Siguiente Integrante / Agente
- [Qué debe hacer el siguiente compañero y qué archivo debe tomar como base].
```
