# Checklist Rol B, Modelador (copia aprobada)

**Estado:** aprobada por Santiago Ortega el 2026-09-28 e incorporada en `BITACORA_AGENTES.md`, entrada #3, sección 7. Esta copia se conserva como registro de revisión; la bitácora es la fuente oficial.

**Alcance:** cubrir el punto 2 de la guía, el apoyo del rol B con anomalías estandarizadas y los aportes de modelación que sustentan la rúbrica. La integración completa de los cinco puntos, el ZIP final y la coordinación de la exposición son responsabilidades del equipo.

## 1. Datos y diseño del análisis

- [ ] Leer `datos/datos_mensuales_maipo.csv`, fuente maestra única, y mantener la resolución mensual.
- [ ] No recortar las series locales para igualar la cobertura más corta de IMERG.
- [ ] Para cada comparación, rezago y modelo, usar meses coincidentes y válidos e informar periodo, número de observaciones y tratamiento de faltantes.
- [ ] Documentar variables, fuentes, unidades y cualquier transformación. Distinguir precipitación de referencia (`PL`), IMERG (`PI`), caudal (`Q`) y lámina de escorrentía (`R`) cuando corresponda.

## 2. Relaciones y diagramas de dispersión

- [ ] Graficar IMERG frente a precipitación de referencia, con línea 1:1 y escalas comparables.
- [ ] Graficar precipitación de referencia frente a caudal.
- [ ] Graficar IMERG frente a caudal.
- [ ] Definir ejes y unidades. Para lluvia–caudal, presentar `Q` y apoyar la comparación de láminas con `R` cuando sea pertinente.
- [ ] Colorear los puntos por mes calendario o estación climática e indicar periodo y tamaño de muestra.
- [ ] Interpretar dirección, forma, fuerza, dispersión, agrupamientos, valores influyentes y posibles cambios de variabilidad con la magnitud.
- [ ] Para IMERG frente a precipitación de referencia, calcular sesgo medio firmado `PI - PL` en unidades originales, MAE y RMSE; explicar el sentido del sesgo respecto de la referencia. Si se informa PBIAS, definir fórmula, denominador y convención de signo.
- [ ] Calcular Pearson (`r`) y Spearman (`rho`) e interpretar sus diferencias. No presentar correlación como prueba de causalidad ni como evidencia suficiente de capacidad predictiva.

## 3. Rezagos y anomalías

- [ ] Evaluar si la precipitación de meses anteriores ayuda a explicar el caudal; definir el sentido de cada rezago y justificarlo considerando almacenamiento, nieve o regulación.
- [ ] No usar precipitación futura para predecir caudal pasado.
- [ ] Comparar las relaciones con datos originales y anomalías mensuales, retirando la climatología del mes calendario según la guía.
- [ ] Para el apoyo al grupo, calcular anomalías `a = X - media_mensual` y anomalías estandarizadas `z = (X - media_mensual) / desviacion_estandar_mensual` para las variables acordadas.
- [ ] Documentar y justificar un periodo de referencia fijo; reportar los años válidos por mes y advertir meses con desviación estándar nula, muy pequeña o estimada con pocos datos.
- [ ] Al usar anomalías dentro de un modelo con evaluación temporal, estimar la climatología solo con el bloque de ajuste y aplicarla sin recalcularla al bloque de evaluación.

## 4. Modelos candidatos

- [ ] Evaluar la estimación de precipitación de referencia a partir de IMERG.
- [ ] Evaluar la estimación de caudal a partir de precipitación de referencia o IMERG.
- [ ] Usar regresión lineal como referencia; comparar alternativas de complejidad razonable solo si los datos justifican transformaciones, una relación no lineal sencilla o rezagos.
- [ ] No forzar un modelo si la evidencia no respalda capacidad explicativa suficiente.
- [ ] Para cada modelo propuesto, registrar ecuación, variables, unidades, parámetros, supuestos, rango de aplicación y tratamiento de ceros o transformaciones.
- [ ] Explicar la selección frente a alternativas y discutir plausibilidad física. Aclarar que una relación estadística lluvia–caudal no reemplaza el balance hídrico ni garantiza conservación de masa.

## 5. Evaluación temporal fuera del ajuste

- [ ] Separar ajuste y evaluación mediante bloques temporales o años completos; justificar la partición y no mezclar aleatoriamente meses dependientes.
- [ ] Seleccionar modelos, rezagos, transformaciones y cualquier climatología usada para modelar exclusivamente con los datos de ajuste.
- [ ] En el periodo de evaluación, calcular sesgo, MAE y RMSE.
- [ ] Comparar la estimación de precipitación contra IMERG sin corrección y la estimación de caudal contra la climatología mensual del caudal; calcular las referencias usando solo el ajuste.
- [ ] Examinar residuos frente al tiempo, valores estimados y mes calendario; revisar estacionalidad residual, predicciones físicamente implausibles y estabilidad entre periodos.
- [ ] Concluir si existe una relación aprovechable, para qué meses o condiciones funciona y si mejora frente a la referencia. Un resultado negativo correctamente sustentado también es válido.

## 6. Interpretación, incertidumbre y fuentes

- [ ] Interpretar los resultados con mecanismos pertinentes a la cuenca y a los datos; para la relación lluvia–caudal, considerar explicaciones como orografía, nieve, almacenamiento y regulación solo cuando haya evidencia.
- [ ] Distinguir asociación, explicación física y predicción; discutir incertidumbres, limitaciones y explicaciones alternativas.
- [ ] Revisar posibles fuentes compartidas: IMERG Final incorpora pluviómetros y la precipitación de referencia podría incluir información satelital.
- [ ] Respaldar afirmaciones metodológicas y físicas con literatura revisada por pares o documentación técnica oficial; registrar referencias y DOI o enlace verificable.
- [ ] Vincular cada conclusión con resultados reproducibles, no solo con inspección visual.

## 7. Entregables y aporte al equipo

- [ ] Producir el análisis reproducible del rol B desde el dataset maestro.
- [ ] Guardar figuras y tablas legibles, con unidades, periodos y tamaños de muestra, en `figuras/` o en la ubicación acordada por el equipo.
- [ ] Entregar al equipo métricas, decisiones metodológicas, interpretación, limitaciones y referencias para integrar el informe y preparar la defensa oral.
- [ ] Registrar en `BITACORA_AGENTES.md` el estado, archivos producidos, validaciones, hallazgos y próximos pasos cuando Santiago apruebe esta checklist y corresponda actualizar el handoff.

## Referencias de cobertura

- Guía de la tarea: punto 2, secciones 2.1–2.3; anomalías estandarizadas, sección 3.2; rúbrica, páginas 16–17.
- Checklist vigente: `BITACORA_AGENTES.md`, entrada #3, sección 7.
- Plan del equipo: `documentos/plan_trabajo_equipo.pdf`, rol B.