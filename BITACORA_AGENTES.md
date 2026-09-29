# BITÁCORA DE COORDINACIÓN Y TRABAJO ENTRE AGENTES DE IA (HANDOVER LOG)
# Proyecto: Tarea 1 de Hidrología (UNAL) - Cuenca Río Maipo en El Manzano (5710001)

> **INSTRUCCIÓN PARA EL AGENTE QUE ABRE ESTE ARCHIVO:**  
> 1. Lee la **Última Entrada Registrada** para entender en qué punto quedó el proyecto.
> 2. Haz un breve **Peer Review** (revisión de pares) del código y figuras producidas antes de continuar.
> 3. Al terminar tu labor en esta sesión, **agrega una nueva entrada** al final de este archivo siguiendo la plantilla.

## AVISO PRIORITARIO: REGISTRO TEMPORAL DEL EQUIPO
- Existe `documentos/bitacora_datos_temporal/`, una carpeta temporal compartida para que los roles A, B, C y D registren datos, métodos, resultados verificables, limitaciones y su interpretación por separado.
- **Antes de entregar el trabajo final, se debe borrar la carpeta completa `documentos/bitacora_datos_temporal/` con todos sus archivos y confirmar que no esté incluida en el ZIP final.** No borrar por error los scripts, las figuras oficiales, el dataset maestro ni esta bitácora, que están fuera de esa carpeta.
- **Instrucción para cada IA que lea esta bitácora:** informar proactivamente al integrante con quien trabaja que existe esta carpeta temporal, explicar su propósito y recordarle que debe eliminarse completa antes de la entrega final. Esta comunicación debe hacerse cada vez que un integrante consulte la bitácora mediante una IA.
- Hasta la limpieza previa a la entrega, los registros son evidencia de trabajo y apoyo para redactar/sustentar; no reemplazan los datos fuente ni el informe final. Distinguir siempre resultados calculados, interpretación y preguntas pendientes.

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
- **Integrante Responsable:** Santiago Ortega — Rol B (Modelador)
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

### 7. Checklist Operativo — Santiago Ortega, Rol B (Modelador)
#### 7.1. Preparación y validación
- [x] Cargar el dataset maestro `datos/datos_mensuales_maipo.csv`.
- [x] Definir ventanas por análisis sin recortar las series locales para igualar la cobertura de IMERG.
- [x] Usar meses coincidentes y válidos; informar periodo, número de observaciones y tratamiento de faltantes para cada comparación, rezago y modelo.
- [x] Documentar las columnas, fuentes, unidades y transformaciones del dataset.

#### 7.2. Relaciones y diagramas de dispersión
- [x] Graficar IMERG frente a precipitación de referencia, con línea 1:1 y escalas comparables.
- [x] Graficar precipitación de referencia frente a caudal.
- [x] Graficar IMERG frente a caudal.
- [x] Definir ejes y unidades; para lluvia–caudal presentar `Q` y apoyar la comparación de láminas con `R` cuando sea pertinente.
- [x] Colorear por mes calendario o estación climática e indicar periodo y tamaño de muestra.
- [x] Interpretar dirección, forma, fuerza, dispersión, agrupamientos, valores influyentes y cambios de variabilidad con la magnitud mediante resúmenes por estación/intensidad y sensibilidad a extremos.
- [x] Para IMERG frente a precipitación de referencia calcular sesgo medio firmado `PI - PL` en unidades originales, MAE y RMSE; explicar el signo respecto a la referencia. Si se informa PBIAS, definir fórmula, denominador y convención de signo.
- [x] Calcular Pearson (`r`) y Spearman (`rho`) e interpretar sus diferencias. No presentar correlación como prueba de causalidad ni como evidencia suficiente de capacidad predictiva.

#### 7.3. Rezagos y anomalías
- [x] Calcular exploratoriamente asociaciones de anomalías para precipitación en `t-k` frente a caudal en `t`, con rezagos de 0 a 12 meses.
- [x] Seleccionar rezagos candidatos mediante ajuste/validación interna temporal y evaluarlos fuera de muestra; interpretar el mecanismo solo como hipótesis, no como causalidad.
- [x] No usar precipitación futura para predecir caudal pasado; los rezagos se definieron como lluvia previa frente a caudal actual.
- [x] Comparar exploratoriamente relaciones originales con anomalías mensuales, retirando la climatología del mes calendario según la guía.
- [x] Apoyar al grupo calculando anomalías `a = X - media mensual` y estandarizadas `z = (X - media mensual) / desviación estándar mensual` para las variables acordadas.
- [x] Usar un periodo de referencia fijo común (2000-06 a 2020-03); reportar años válidos por mes y revisar desviaciones estándar nulas, pequeñas o calculadas con pocos datos.
- [x] Para anomalías usadas en modelos con evaluación temporal, calcular la climatología solo con el bloque de ajuste y aplicarla sin recalcularla al bloque de evaluación.

#### 7.4. Modelos candidatos
- [x] Evaluar precipitación de referencia estimada a partir de IMERG.
- [x] Evaluar caudal estimado a partir de precipitación de referencia o IMERG.
- [x] Usar regresión lineal como referencia y comparar alternativas razonables solo si la evidencia justifica transformaciones, relaciones no lineales sencillas o rezagos.
- [x] No forzar un modelo si los datos no respaldan capacidad explicativa suficiente.
- [x] Documentar ecuación, variables, unidades, parámetros, supuestos, rango de aplicación y tratamiento de ceros o transformaciones.
- [x] Justificar el modelo seleccionado frente a alternativas y discutir plausibilidad física. Aclarar que una relación lluvia–caudal no reemplaza el balance hídrico ni garantiza conservación de masa.

#### 7.5. Evaluación temporal fuera del ajuste
- [x] Separar ajuste y evaluación mediante bloques temporales o años completos; justificar la partición y no mezclar aleatoriamente meses dependientes.
- [x] Seleccionar modelos, rezagos, transformaciones y climatologías para modelar exclusivamente con los datos de ajuste.
- [x] En el periodo de evaluación calcular sesgo, MAE y RMSE.
- [x] Comparar precipitación estimada con IMERG sin corrección y caudal estimado con la climatología mensual del caudal; calcular ambas referencias usando solo el ajuste.
- [ ] Examinar residuos frente al tiempo, valor estimado y mes calendario; revisar estacionalidad residual, predicciones físicamente implausibles y estabilidad entre periodos. (Se generaron diagnósticos temporales, mensuales y anuales, pero solo hay una partición externa; falta evaluar estabilidad con bloques independientes adicionales.)
- [x] Concluir si la relación es aprovechable, para qué condiciones funciona y si mejora frente a la referencia. Un resultado negativo bien sustentado también es válido.

#### 7.6. Interpretación, incertidumbre y fuentes
- [x] Interpretar resultados con mecanismos pertinentes a la cuenca y los datos; considerar orografía, nieve, almacenamiento o regulación solo cuando exista evidencia.
- [x] Distinguir asociación, explicación física y predicción; discutir incertidumbres, limitaciones y explicaciones alternativas.
- [x] Revisar posibles fuentes compartidas: IMERG Final incorpora pluviómetros y la precipitación de referencia podría incluir información satelital. (La existencia de estaciones compartidas concretas sigue sin confirmarse.)
- [x] Respaldar afirmaciones metodológicas y físicas con literatura revisada por pares o documentación técnica oficial; registrar referencias y DOI o enlace verificable.
- [x] Vincular las conclusiones con resultados reproducibles, no solo con inspección visual.

#### 7.7. Entregables y aporte al equipo
- [x] Producir el análisis reproducible del rol B desde el dataset maestro.
- [x] Guardar figuras y tablas legibles, con unidades, periodos y tamaños de muestra, en `figuras/` o en la ubicación acordada por el equipo.
- [x] Entregar métricas, decisiones metodológicas, interpretación, limitaciones y referencias para integrar el informe y preparar la defensa oral.
- [x] Registrar estado, archivos, validaciones, hallazgos y próximos pasos en la bitácora.

---

## ENTRADA #4: ROL B — ASIGNACIÓN Y DISEÑO DEL ANÁLISIS
- **Fecha:** 2026-09-28
- **Integrante Responsable:** Santiago Ortega
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** EN CURSO — pasos 1, 2.1 y cálculo exploratorio de anomalías/rezagos completados; selección validada de rezagos y modelos pendientes

### 1. Revisión de Pares
- Se revisó la checklist de la entrada #3 contra el punto 2, la sección 3.2 de anomalías y la rúbrica de la guía `documentos/tarea_1_202602.pdf`.
- La checklist ampliada quedó asignada a Santiago Ortega y se incorporó en la sección 7 de la entrada #3. Los criterios grupales se identifican como aportes, no como entregables individuales del rol B.

### 2. Resumen de lo Realizado
- Se completó la preparación y diseño inicial del análisis del rol B leyendo el CSV maestro y contabilizando cobertura, faltantes y pares válidos sin imputar datos.
- Se definió trabajar por pares completos válidos en cada análisis y mantener las series locales completas, sin recortarlas al periodo de IMERG.
- Se mapearon las columnas del CSV: `date` (fecha mensual), `P_local_mm` (precipitación de referencia, mm/mes), `P_IMERG_mm` (IMERG, mm/mes), `Caudal_m3s` (caudal, m3/s), `Q_lamina_mm` (lámina equivalente, mm/mes) y `Temp_C` (temperatura, °C).
- Se creó `scripts/04_analisis_precipitacion.py`, que genera los tres diagramas de dispersión del punto 2.1, dos paneles complementarios con `Q_lamina_mm`, y una tabla reproducible de métricas.
- Los puntos se colorean por mes calendario; cada panel informa sus ejes, unidades, ventana y cantidad de pares. IMERG frente a precipitación de referencia incluye la línea 1:1 con escalas comparables.
- Se añadieron diagnósticos descriptivos de error por estación/intensidad, meses influyentes y sensibilidad a extremos, sin excluirlos del resultado principal.
- Se creó `scripts/05_anomalias_rezagos.py` para calcular anomalías y anomalías estandarizadas de las cinco variables con una referencia fija común y explorar rezagos de precipitación previa a caudal actual.

### 3. Validaciones y Resultados del Paso 1
- El CSV tiene **484 filas mensuales**, de 1980-01 a 2020-04; la secuencia es continua y no hay fechas duplicadas.
- Precipitación de referencia: 483 valores válidos; falta 2020-04 (1/484; 0.21%).
- IMERG: 238 valores válidos de 2000-06 a 2020-03 (246/484 vacíos fuera de esa cobertura).
- Caudal y lámina equivalente: 470 valores válidos cada uno; 14/484 vacíos (2.89%).
- Temperatura: 238 valores válidos de 2000-06 a 2020-03.
- Pares válidos para el diseño: precipitación de referencia–IMERG, **238** (2000-06 a 2020-03); precipitación de referencia–caudal, **469** (1980-01 a 2020-03); IMERG–caudal, **230** (2000-06 a 2020-03). Los conteos son iguales al usar `Q_lamina_mm` en lugar de `Caudal_m3s`.
- En precipitación IMERG frente a referencia: Pearson `r = 0.8875`, Spearman `rho = 0.8245`, sesgo medio `PI - PL = -5.503 mm/mes`, MAE `= 27.344 mm/mes`, RMSE `= 48.656 mm/mes` y PBIAS `= -8.764%`, calculado como `100 * sum(PI - PL) / sum(PL)`. El sesgo agregado es negativo con esta convención; no implica que todos los meses estén subestimados.
- Correlaciones de series mensuales originales: precipitación local–caudal `r = -0.2009`, `rho = -0.3931`; IMERG–caudal `r = -0.2772`, `rho = -0.4234`. Son asociaciones contemporáneas que conservan el ciclo anual; no se interpretan todavía como relación hidrológica independiente. La diferencia Pearson–Spearman muestra que la asociación monotónica medida por rangos es más negativa, pero debe reevaluarse con anomalías mensuales y rezagos.
- La climatología de precipitación local y caudal muestra máximos mensuales distintos: precipitación en junio (179.01 mm/mes) y caudal en diciembre (210.71 m3/s); los mínimos son marzo (10.85 mm/mes) y agosto (64.81 m3/s), respectivamente. La correlación entre las 12 medias climatológicas es `r = -0.7676` (solo descripción del ciclo anual, no una prueba inferencial). Esto es consistente con el signo negativo contemporáneo en series originales y con un posible desfase estacional asociado al almacenamiento y deshielo, que debe contrastarse con bibliografía regional.
- Al restar a cada mes su propia media climatológica calculada con los mismos pares válidos del periodo analizado, la asociación contemporánea pasa a ser débilmente positiva: precipitación local–caudal `r = 0.1648`, `rho = 0.1426` (469 pares); IMERG–caudal `r = 0.1789`, `rho = 0.2325` (230 pares). Para anomalías con lluvia en `t-k` frente a caudal en `t`, los rezagos exploratorios de 5 y 6 meses alcanzan para precipitación local `r = 0.3827` y `0.4553`, y para IMERG `r = 0.4095` y `0.3924`, respectivamente. Estas asociaciones no demuestran causalidad ni desempeño predictivo: las climatologías se estimaron sobre el periodo completo, los rezagos se exploraron en la misma muestra y la autocorrelación debe considerarse. No son resultados de validación fuera de muestra.
- La distribución del error IMERG–referencia refuerza que el sesgo medio no representa cada mes: IMERG es menor en 103 pares y mayor en 135, mientras el sesgo medio es `-5.503 mm/mes` pero la mediana del error es `+3.856 mm/mes`. Los cinco mayores errores absolutos aportan 52.35% de la suma de errores cuadrados; se deben revisar como meses influyentes, no excluir sin justificación.
- El desglose de error por estación austral muestra sesgo medio de `+6.85 mm/mes` en verano y entre `-8.28` y `-11.33 mm/mes` en otoño, invierno y primavera. La relación IMERG–referencia es más dispersa en invierno (RMSE `76.72 mm/mes`) que en verano (`14.20 mm/mes`), con distinta amplitud de lluvia entre estaciones.
- Por cuartiles de precipitación local, IMERG sobreestima en los tres cuartiles inferiores (sesgos de `+14.00`, `+9.97` y `+6.43 mm/mes`) y subestima en el superior (`-51.94 mm/mes`). MAE/RMSE suben en el cuartil más lluvioso (MAE `58.75`, RMSE `88.52 mm/mes`), consistente con mayor dispersión absoluta del error en eventos intensos; la conclusión se limita a estos pares mensuales y no atribuye una causa física.
- Los mayores errores absolutos son 2000-06 (`-334.60 mm`), 2008-05 (`-233.52 mm`), 2005-06 (`-217.22 mm`), 2006-07 (`-208.93 mm`) y 2005-08 (`-193.99 mm`). Deben verificarse contra la procedencia de ambas fuentes. Como sensibilidad descriptiva, al excluir solo los cinco meses extremos Pearson cambia de `0.8875` a `0.8829`, mientras RMSE cae de `48.66` a `33.94 mm/mes`; los cinco meses se conservan en todos los resultados principales.
- La descripción de dirección, agrupamiento por mes/estación, dispersión por intensidad y meses influyentes del punto 2.1 queda completada. No se atribuyen los errores a orografía, nieve u otra causa sin validar fuentes y bibliografía; tampoco se excluyen extremos.
- Referencia fija para anomalías: junio de 2000 a marzo de 2020, ventana común más amplia entre productos satelitales y series locales disponibles. Se mantuvieron todas las fechas locales en la serie de anomalías; para cada mes, `P_local_mm`, `P_IMERG_mm` y `Temp_C` tienen 19–20 años válidos; `Caudal_m3s` y `Q_lamina_mm`, 18–20. No hubo meses con desviación estándar mensual nula en estas variables. La desviación estándar usada para `z` es muestral (`ddof=1`).
- Para comparación lluvia previa–caudal actual, lag 0: precipitación local `r = 0.1569`, `rho = 0.1754` (`n=469`); IMERG `r = 0.1783`, `rho = 0.2368` (`n=230`). A lag 7 meses, local `r = 0.4773`, `rho = 0.2953` (`n=463`); IMERG `r = 0.4222`, `rho = 0.3549` (`n=224`). El sentido está fijado como precipitación en `t-k` frente a caudal en `t`; nunca se usó lluvia futura.
- El máximo exploratorio de Pearson para lluvia previa–caudal actual aparece en torno a 7 meses con esta referencia fija; un cálculo exploratorio anterior con una climatología diferente tuvo máximos distintos. Esta sensibilidad y el barrido de 13 rezagos refuerzan que no se debe presentar todavía un rezago físico identificado ni habilidad predictiva: autocorrelación, múltiples rezagos examinados y climatología calculada sobre todo el periodo requieren validación por bloques temporales.
- Se detectó una discrepancia documental: `AGENTS.md` y entradas anteriores describen 483 meses hasta 2020-03, precipitación local sin faltantes y menos de 2% de faltantes en caudal. El CSV actual contiene 484 filas hasta 2020-04, un faltante en precipitación local y 2.89% de faltantes en caudal. No se modificó el CSV ni `AGENTS.md`; se debe reconciliar esta diferencia antes de citar esas cifras como validación oficial.

### 4. Archivos Modificados o Generados
- `BITACORA_AGENTES.md`: checklist aprobada asignada a Santiago Ortega y registro del paso 1.
- `documentos/checklist_modelador_propuesta.md`: copia de revisión aprobada; la versión oficial está en esta bitácora.
- `scripts/04_analisis_precipitacion.py`: análisis de pares mensuales y generación de dispersogramas/métricas.
- `figuras/figura_2_1_relaciones_scatter.png`: tres relaciones requeridas y dos apoyos con lámina, resolución de 300 DPI.
- `figuras/tabla_2_1_metricas_relaciones.csv`: tamaños de muestra, ventanas, correlaciones y métricas de concordancia entre productos.
- `figuras/tabla_2_1_errores_por_grupo.csv`: concordancia de precipitación por estación austral y cuartil de intensidad local.
- `figuras/tabla_2_1_meses_influyentes.csv`: diez meses con mayores errores absolutos, conservados en el análisis.
- `figuras/tabla_2_1_sensibilidad_extremos.csv`: sensibilidad descriptiva de r, sesgo, MAE y RMSE al excluir extremos únicamente como diagnóstico.
- `scripts/05_anomalias_rezagos.py`: climatología de referencia, anomalías estandarizadas y análisis de rezagos 0–12.
- `figuras/tabla_2_2_climatologia_referencia.csv`: media, mediana, desviación estándar y años válidos por mes.
- `figuras/serie_2_2_anomalias_estandarizadas.csv`: anomalías y valores z de la serie mensual completa disponible.
- `figuras/tabla_2_2_correlaciones_rezagos.csv` y `figuras/figura_2_2_correlaciones_rezagos.png`: correlaciones exploratorias y resumen gráfico por rezago.
- `datos/datos_mensuales_maipo.csv`: solo lectura; no modificado.

### 5. Próximos Pasos
- Justificar con bibliografía regional los rezagos candidatos, considerando que el pico exploratorio cambió al cambiar el periodo de referencia.
- Evaluar candidatos de rezago con bloques temporales; calcular climatología, selección de rezago y modelos solo en el ajuste, considerar autocorrelación y comparar contra la climatología mensual del caudal calculada solo en el ajuste.
- Verificar las fechas de mayor discrepancia contra la procedencia y metadatos de las fuentes antes de proponer correcciones o explicaciones físicas.
- Mantener explícitos los periodos y tamaños de muestra definidos aquí; tratar faltantes con casos válidos por análisis, sin rellenarlos.
- Reconciliar con el equipo la diferencia entre los metadatos/handoffs previos y la cobertura/missingness observada en el CSV.

---

## ENTRADA #5: CREACIÓN DE REGISTRO TEMPORAL OBJETIVO POR ROLES
- **Fecha:** 2026-09-28
- **Integrante Responsable:** Equipo; rol B inicial documentado por Santiago Ortega
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** EN CURSO

### 1. Revisión de Pares
- Se verificó el protocolo de agentes, la bitácora vigente y la asignación A–D descrita en `documentos/plan_trabajo_equipo.pdf`.
- Los resultados existentes del rol B están separados entre métricas reproducibles, resultados exploratorios e interpretación por validar; no se convierten en afirmaciones causales.

### 2. Resumen de lo Realizado
- Se creó `documentos/bitacora_datos_temporal/` con instrucciones comunes, una sección/archivo independiente para cada rol A–D y un registro inicial de los resultados del rol B.
- Se añadió a este handoff un aviso prioritario que exige borrar toda la carpeta temporal antes de preparar la entrega final e instruye explícitamente a cada IA que lea la bitácora a comunicar ese requisito al integrante.
- Se actualizó `AGENTS.md` para dirigir a los agentes al aviso de limpieza cuando lean este handoff.

### 3. Archivos Clave
- `documentos/bitacora_datos_temporal/00_INSTRUCCIONES.md`: formato común, reglas de trazabilidad y protocolo de limpieza.
- `documentos/bitacora_datos_temporal/rol_a_explorador.md`
- `documentos/bitacora_datos_temporal/rol_b_modelador.md`
- `documentos/bitacora_datos_temporal/rol_c_tendencias_y_fourier.md`
- `documentos/bitacora_datos_temporal/rol_d_climatologia_global.md`

### 4. Validación y Próximos Pasos
- Se conservaron los nombres A–D del plan de equipo. Solo el registro del rol B se prellenó con resultados existentes del CSV maestro; los otros roles quedan vacíos para que sus responsables registren su propia evidencia.
- Los integrantes deben añadir resultados con unidades, periodo, n, datos faltantes, método, archivos reproducibles, límites e interpretación separada. No completar campos con valores supuestos.
- Antes de la entrega, borrar íntegramente `documentos/bitacora_datos_temporal/` y comprobar que no aparezca en el paquete final.

---

## ENTRADA #6: FUENTES CIENTÍFICAS PARA SUSTENTAR EL ROL B
- **Fecha:** 2026-09-28
- **Integrante Responsable:** Santiago Ortega — Rol B
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** EN CURSO

### 1. Resumen de la búsqueda
- Se revisaron registros DOI de Crossref y resúmenes editoriales para literatura sobre nieve/deshielo y precipitación orográfica en Chile central/Andes, evaluación de IMERG por intensidad/terreno/densidad de pluviómetros y evaluación hidrológica con métricas complementarias.
- Se creó `documentos/bitacora_datos_temporal/referencias_sustento_rol_b.md` con nueve referencias, DOI, hallazgos, límites geográficos/versionales y ejemplos de redacción para el informe.
- Se enlazó la bibliografía con el registro temporal `rol_b_modelador.md`.

### 2. Conclusión metodológica
- Literatura sobre nieve en Andes centrales y precipitación orográfica de Chile central hace plausible explorar almacenamiento/deshielo para interpretar el desfase de la climatología, pero no demuestra que el rezago exploratorio de siete meses sea causal.
- Estudios externos de IMERG describen dependencias del error por intensidad, densidad de referencia y ambiente. Son contexto metodológico, no validación directa del IMERG V07 de Maipo.
- La evaluación directa IMERG–Chile montañoso de Rojas et al. (2021, DOI `10.1016/j.atmosres.2021.105454`) es IMERG V06, campañas de invierno cerca de 36°S; no valida el agregado mensual areal de Maipo. El script del proyecto usa `NASA/GPM_L3/IMERG_MONTHLY_V06`, mientras documentos anteriores decían V07; confirmar la exportación del CSV.
- No afirmar que la subestimación local está demostrada como orográfica ni que nieve/deshielo causa el lag exploratorio de siete meses.

### 3. Próximos pasos
- Citar las fuentes solo para las afirmaciones que expresamente respaldan y conservar sus límites al redactar.
- Continuar el rol B con evaluación temporal de anomalías/rezagos en bloques completos.
- Recordatorio: la carpeta temporal completa debe eliminarse antes de la entrega final.

---

## ENTRADA #7: ROL B — SUSTENTO BIBLIOGRÁFICO Y EVALUACIÓN TEMPORAL
- **Fecha:** 2026-09-28
- **Integrante Responsable:** Santiago Ortega — Rol B
- **Agente de IA utilizado:** GitHub Copilot
- **Estado de la Fase:** Evaluación temporal de primera partición completada; estabilidad entre particiones y procedencia IMERG pendientes

### 1. Revisión de pares y correcciones
- Se contrastó la entrada #6 y su bibliografía ampliada. La versión anterior decía que no había evidencia IMERG directa en Chile y que la comparación del proyecto era V07; la revisión identificó estudios directos chilenos y confirmó que `scripts/02_descargar_satelite.py` usa `NASA/GPM_L3/IMERG_MONTHLY_V06`.
- Se auditó el rango realmente medido en las salidas: los tests nominales podían extenderse a 2020-04, pero los pares válidos terminan en 2020-03. Se corrigió `scripts/06_modelos_validacion_temporal.py` para imprimir fechas y n reales de cada bloque de evaluación.
- Se actualizaron las instrucciones vigentes de `AGENTS.md` con los nombres reales del CSV, la cobertura auditada y la advertencia V06/V07. Las entradas históricas #1 y #6 se conservan como registro de lo afirmado en su momento; esta entrada documenta la rectificación.

### 2. Sustento bibliográfico
- Se amplió `documentos/bitacora_datos_temporal/referencias_sustento_rol_b.md` a 22 artículos revisados por pares más dos fichas oficiales de producto/datos; el documento relaciona evidencia con cada apartado 7.1–7.7 y separa datos calculados, método, mecanismos regionales y validación directa.
- Rojas et al. (2021, DOI `10.1016/j.atmosres.2021.105454`) estudia IMERG V06 con CCOPE/ChOMPS, campañas de invierno 2015–2016 cerca de 36°S; identifica error dependiente de elevación/régimen microfísico. Es contexto regional directo, no validación del promedio mensual de Maipo.
- Soto-Alvarez et al. (2020, DOI `10.1016/j.jsames.2020.102870`) evalúa 3IMERG y TMPA con 143 estaciones chilenas (2014–2018); la versión de 3IMERG no queda precisada en el resumen revisado. da Silva et al. (2023, DOI `10.3390/rs15030573`) evalúa IMERG Early, no Final. Zambrano-Bigiarini et al. (2017, DOI `10.5194/hess-21-1295-2017`) evalúa gradientes chilenos, pero sus productos no incluyen IMERG.
- Para memoria nival/glaciar y lluvia–caudal se incluyeron Masiokas et al. (2006, DOI `10.1175/JCLI3969.1`), Alvarez-Garreton et al. (2021, DOI `10.5194/hess-25-429-2021`) y Ayala et al. (2020, DOI `10.5194/tc-14-2005-2020`). Para métricas, autocorrelación y evaluación bloqueada: Hossain & Huffman (2008, DOI `10.1175/2007JHM925.1`), Gupta et al. (2009, DOI `10.1016/j.jhydrol.2009.08.003`), Pyper & Peterman (1998, DOI `10.1139/f98-104`), Klemeš (1986, DOI `10.1080/02626668609491024`) y Roberts et al. (2017, DOI `10.1111/ecog.02881`). Los alcances y límites están desarrollados en el dossier enlazado.

### 3. Evaluación retrospectiva fuera del ajuste
- Script reproducible: `scripts/06_modelos_validacion_temporal.py`; ejecutado sin errores el 2026-09-28 con Python 3.13. La prueba es cronológica y usa una sola partición externa; no es validación cruzada ni una afirmación de estabilidad a largo plazo.
- Precipitación local desde IMERG: ajuste final 2000-06 a 2015-12, selección interna 2013-01 a 2015-12 y test válido 2016-01 a 2020-03 (`n=51`). IMERG sin corrección: sesgo `-0.982 mm/mes`, MAE `18.840`, RMSE `32.578`. Regresión lineal seleccionada en ajuste: sesgo `+0.640`, MAE `20.853`, RMSE `30.739 mm/mes`. Mejora RMSE, pero empeora MAE; no afirmar mejora uniforme.
- Caudal desde precipitación local: ajuste 1980-01 a 2011-12; tuning 2008-01 a 2011-12; test válido 2012-01 a 2020-03 (`n=91`). Climatología mensual Q: sesgo `+47.722 m3/s`, MAE `48.652`, RMSE `61.004`. Lineal Q~P(t): `+47.490`, `54.349`, `59.710`. Modelo de anomalía con rezago seleccionado `k=6`: `+40.661`, `41.915`, `51.434 m3/s`. El rezago mejora MAE/RMSE frente a ambos; persiste sesgo positivo.
- Caudal desde IMERG: ajuste 2000-06 a 2015-12; tuning 2012-01 a 2015-12; test válido 2016-01 a 2020-03 (`n=51`). Climatología mensual Q: sesgo `+40.484 m3/s`, MAE `42.415`, RMSE `55.102`. Lineal Q~P(t): `+36.166`, `47.051`, `51.994`. Modelo de anomalía con rezago seleccionado `k=8`: `+26.396`, `35.192`, `49.120 m3/s`. Mejora MAE/RMSE en esta partición; persiste sesgo positivo.
- Ningún modelo produjo predicciones negativas. El máximo predicho por el modelo IMERG–Q con lag 8 fue `302.766 m3/s`; debe revisarse como pico alto frente al test, no descartarse sin análisis. La incertidumbre de parámetros y la variabilidad entre periodos no se cuantificaron.
- Selección interna y ecuaciones reproducibles están en `figuras/tabla_2_3_seleccion_modelos_ajuste.csv`; resultados completos, desgloses anuales/mensuales/estacionales y predicciones están en `figuras/tabla_2_3_*.csv`. Figuras: `figuras/figura_2_3_validacion_modelos.png` y `figuras/figura_2_4_residuos_en_tiempo.png` (300 DPI).

### 4. Interpretación y límites
- Los resultados apoyan utilidad predictiva preliminar del modelo de anomalías con rezago para Q en estos bloques concretos; la partición única y sus errores no demuestran generalización a otros periodos.
- La asociación compatible con nieve, aguas subterráneas o glaciares sigue siendo hipótesis, no atribución causal del lag. P–Q empírico no sustituye el balance hídrico ni representa por sí solo almacenamiento, ET o regulación.
- IMERG Final usa información de pluviómetros; la posible dependencia con CR2MET es un riesgo metodológico, pero no se confirmó qué estaciones concretas comparten. Tampoco se confirmó aún la versión que originó el CSV.

### 5. Próximos pasos
- Confirmar la procedencia exacta del valor `P_IMERG_mm` del CSV (V06/V07, corrida y banda/unidades de exportación) y reconciliar con cualquier fuente original guardada por el equipo.
- Auditar si estaciones CR2MET y GPCC se solapan; hasta entonces, evitar afirmaciones de independencia o solapamiento efectivo.
- Para evaluar estabilidad, añadir evaluación de origen rodante o bloques externos adicionales; revisar el pico predicho de 302.8 m3/s y residuos por mes/estación.
- Antes de entrega, eliminar completa `documentos/bitacora_datos_temporal/` y excluirla del ZIP.

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
