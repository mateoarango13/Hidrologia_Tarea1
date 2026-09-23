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

## ENTRADA #2: CONTEXTO BASE DEL REPOSITORIO Y PREPARACIÓN DEL ENTORNO
- **Fecha:** 2026-09-22
- **Integrante Responsable:** Usuario / equipo de trabajo
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** COMPLETADA

### 1. Revisión de Pares (Peer Review del trabajo previo)
- Se revisó la bitácora anterior y la estructura del repositorio. La Fase 1 está consolidada y no presenta contradicción con la regla del dataset maestro ni con la longitud mínima de registro requerida.
- Se confirma que la fuente oficial de verdad es `datos/datos_mensuales_maipo.csv` y que no debe cortarse la serie local para ajustar el periodo satelital.
- El único ajuste operativo observado es que el entorno actual no tiene Git disponible en el PATH, por lo que la sincronización debe hacerse desde GitHub Desktop o con instalación local de Git.

### 2. Resumen de lo Realizado en esta Sesión
- Se contextualizó el proyecto con base en `AGENTS.md`, `README.md` y la bitácora previa.
- Se validó la estructura del repo: `datos/`, `scripts/` y `documentos/` están organizados según la planificación de la tarea.
- Se revisaron los scripts de preparación y consolidación: `01_preparar_datos.py`, `02_descargar_satelite.py` y `03_integrar_datos.py`.
- Se dejó una guía de trabajo colaborativo y un formato de handoff legible por IA para futuras entregas del equipo.

### 3. Archivos Modificados o Generados
- `README.md`: actualización del flujo de trabajo, handoff IA y requisitos del entorno.
- `BITACORA_AGENTES.md`: incorporación de la entrada de contexto base y del protocolo del siguiente traspaso.
- `documentos/handoff_template.yaml`: plantilla estructurada para entregas IA-readable.

### 4. Conclusiones y Métricas Relevantes
- Periodo base: 1980-01 a 2020-03.
- Número de meses: 483.
- Duración total: > 40 años.
- Faltantes locales: < 2% en caudal y 0% en precipitación local; cumple el criterio del < 10% exigido.
- La serie local no fue recortada al periodo satelital; se mantiene la unión externa como establece la consigna del proyecto.

### 5. Próximos Pasos para el Siguiente Integrante / Agente
- Continuar con la Fase 2: análisis comparativo de precipitación local vs IMERG.
- Basarse en `datos/datos_mensuales_maipo.csv` como único input.
- Generar `scripts/04_analisis_precipitacion.py` y exportar los resultados a `figuras/`.
- Registrar la nueva entrega siguiendo el template estructurado en `documentos/handoff_template.yaml`.

### 6. Handoff IA-Readable
```yaml
project:
  name: "Tarea 1 - Hidrología"
  basin: "Río Maipo en El Manzano"
  camels_code: "5710001"
  area_km2: 4837.4
  dataset_master: "datos/datos_mensuales_maipo.csv"
  source_of_truth: "base local + satelite + reanalisis"
  temporal_window: "1980-01 to 2020-03"
  months: 483

status:
  phase_1: "completed"
  phase_2: "pending"
  phase_3: "pending"
  phase_4: "pending"

validation:
  local_precip_missing_pct: 0
  discharge_missing_pct: "< 2%"
  max_missing_allowed_pct: 10
  temporal_requirement_met: true
  outer_join_required: true

artifacts:
  scripts:
    - "scripts/01_preparar_datos.py"
    - "scripts/02_descargar_satelite.py"
    - "scripts/03_integrar_datos.py"
  data:
    - "datos/datos_mensuales_maipo.csv"
  figures:
    - "figuras/grafica_1_1_series.png"

constraints:
  - "No recortar la serie local 1980-2020 al periodo satelital 2000-2020"
  - "Usar un outer join para conservar todos los registros"
  - "Todos los análisis deben leerse desde el CSV maestro"

next_actions:
  - "Crear scripts/04_analisis_precipitacion.py"
  - "Comparar P_local_mm vs P_IMERG_mm en periodo común"
  - "Calcular r, rho, PBIAS, RMSE, MAE"
  - "Guardar figuras en figuras/"
  - "Actualizar BITACORA_AGENTES.md con nuevo handoff"
```

---

## ENTRADA #3: ASIGNACIÓN DEL ROL MODELADOR Y EXIGENCIA DE RIGOR RUBRICA
- **Fecha:** 2026-09-22
- **Integrante Responsable:** Equipo / estudiante asignado al rol modelador
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** EN CURSO

### 1. Revisión de Pares (Peer Review del trabajo previo)
- Se revisaron la guía oficial, el plan del equipo y el dataset maestro. El repositorio está listo para avanzar a la Fase 2, y la secuencia del trabajo respeta la lógica del proyecto.
- La única condición crítica es que el análisis no debe limitarse a un cálculo superficial: la rúbrica exige rigor estadístico, interpretación física y trazabilidad entre datos, métodos y resultados.
- El rol de Fourier ya fue asignado a otro compañero, por lo que el rol de Modelador se convierte en la parte analítica de comparación entre precipitación local y satelital, y de relaciones hidrometeorológicas de la cuenca.

### 2. Resumen de lo Realizado en esta Sesión
- Se validó que el plan del equipo cubre la estructura requerida por la tarea.
- Se confirmó que el foco del rol modelador debe ser la comparación cuantitativa entre variables, la relación lluvia-caudal y la evaluación de consistencia entre productos.
- Se dejó constancia de que la ejecución debe cumplir con la rúbrica del docente, no solo con una versión mínima funcional.

### 3. Archivos Clave de Trabajo
- `datos/datos_mensuales_maipo.csv`: fuente única de verdad para todos los análisis.
- `scripts/04_analisis_precipitacion.py`: script que debe producir los análisis estadísticos del rol modelador.
- `figuras/`: destino de gráficos y métricas para la entrega.

### 4. Requerimientos Rigurosos para Cumplir la Rúbrica
- El análisis debe usar el período común de registros y distinguirlo del período completo.
- Debe documentarse explícitamente la diferencia entre precipitación local y precipitación IMERG.
- Deben generarse y reportarse métricas: Pearson, Spearman, PBIAS, RMSE y MAE.
- Deben incluirse gráficos de dispersión con línea 1:1, histogramas o curvas de densidad y comparación visual de series.
- La interpretación debe incluir una discusión física: sesgo sistemático, escala espacial, orografía, ajuste del producto satelital y plausibilidad hidrológica.
- No basta con correr código; debe existir una interpretación metodológica y una conclusión defendible.
- Toda afirmación teórica o metodológica debe estar sustentada en literatura científica confiable. No se aceptan generalidades, intuiciones o fuentes no revisadas por pares.
- Se priorizarán artículos científicos, reportes técnicos oficiales, documentación de NASA/NOAA/ECMWF y documentos con DOI o referencia formal verificable.
- Si se afirma que un modelo es viable o que una relación es apropiada, debe justificarse con evidencia empírica y literatura pertinente, no con el mero criterio visual del gráfico.
- Se debe evitar la referencia a fuentes no académicas como Wikipedia, foros, blogs o contenido no revisado por pares.

### 5. Conclusiones y Métricas Relevantes
- El punto de entrada del rol modelador no es solo “calcular correlaciones”; es validar la calidad y la consistencia del producto satelital frente a la referencia local.
- La comparación debe dejar evidencia suficiente para sostener si IMERG subestima, sobreestima o reproduce la variabilidad de la lluvia de la cuenca.
- La inferencia debe ser sólida, con métricas y explicaciones físicas, no subjetiva.

### 6. Próximos Pasos para el Siguiente Integrante / Agente
- Crear el script `scripts/04_analisis_precipitacion.py`.
- Usar `datos/datos_mensuales_maipo.csv` como único insumo.
- Trabajar con el período común (junio 2000 a marzo 2020) y dejar explícito el tratamiento del resto del registro.
- Generar figuras reproducibles y guardarlas en `figuras/`.
- Registrar la nueva entrega en la bitácora con métricas, hallazgos y limitaciones.

### 7. Checklist Operativo del Rol Modelador (Punto 2)
#### 7.1. Preparación y validación
- [ ] Cargar el dataset maestro `datos/datos_mensuales_maipo.csv`.
- [ ] Definir el período común de análisis y documentarlo explícitamente.
- [ ] Confirmar que la comparación es entre meses coincidentes y válidos.
- [ ] Registrar la cantidad de pares y la ventana temporal.

#### 7.2. Diagramas de dispersión
- [ ] Graficar IMERG vs precipitación local con línea 1:1.
- [ ] Graficar precipitación local vs caudal.
- [ ] Graficar IMERG vs caudal.
- [ ] Colorear por mes calendario o estación climática.
- [ ] Describir dirección, forma, dispersión y valores influyentes.

#### 7.3. Métricas estadísticas
- [ ] Calcular Pearson (`r`).
- [ ] Calcular Spearman (`rho`).
- [ ] Calcular sesgo medio (PBIAS o equivalente).
- [ ] Calcular MAE.
- [ ] Calcular RMSE.
- [ ] Interpretar las diferencias entre correlación y concordancia.

#### 7.4. Relación lluvia–caudal y rezagos
- [ ] Evaluar si la lluvia de meses anteriores ayuda a explicar el caudal.
- [ ] Definir el sentido del rezago y justificarlo físicamente.
- [ ] Explorar si la relación cambia al retirar la climatología anual.
- [ ] Comparar variables originales con anomalías mensuales.

#### 7.5. Modelación
- [ ] Evaluar regresión lineal como referencia.
- [ ] Justificar si existe una relación aprovechable para predicción.
- [ ] Considerar transformaciones o relaciones no lineales solo si hay evidencia.
- [ ] Documentar ecuación, variables, unidades, parámetros y supuestos.
- [ ] Explicar por qué el modelo propuesto es razonable y cuáles son sus limitaciones.

#### 7.6. Evaluación fuera del ajuste
- [ ] Separar datos de ajuste y validación por bloques temporales o años completos.
- [ ] Evaluar error fuera del ajuste con MAE y RMSE.
- [ ] Revisar residuos frente al tiempo, al valor estimado y al mes calendario.
- [ ] Comparar contra una referencia simple (p. ej., IMERG sin corrección o climatología mensual del caudal).
- [ ] Concluir si la relación es útil, débil o no aplicable.

#### 7.7. Sustentación científica
- [ ] Cada afirmación metodológica debe tener base en literatura revisada por pares.
- [ ] Cada conclusión debe estar respaldada por evidencia empírica y no por intuición visual.
- [ ] Documentar DOI o referencia oficial de las fuentes consultadas.
- [ ] No usar material no académico como fuente principal.

#### 7.8. Entregables mínimos del rol
- [ ] Script reproducible: `scripts/04_analisis_precipitacion.py`
- [ ] Figuras guardadas en `figuras/`
- [ ] Resumen de métricas y hallazgos físicos
- [ ] Registro actualizado en la bitácora con estado de avance y próximos pasos

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
