# Sustento bibliográfico ampliado — Rol B

> **ARCHIVO TEMPORAL.** Este archivo y toda la carpeta `documentos/bitacora_datos_temporal/` deben borrarse antes de la entrega final.

## Alcance, evidencia y trazabilidad

Este dossier fundamenta los puntos 7.1–7.7 de la checklist de Santiago Ortega. Los metadatos y DOI se contrastaron en Crossref; se revisaron resúmenes editoriales o repositorios académicos cuando estuvieron disponibles, y se consultó la documentación NASA/Google Earth Engine para identificar el producto IMERG. Cada fuente se usa solo para la afirmación que realmente respalda.

Se distinguen cuatro niveles:

1. **Hechos del proyecto:** calculados del CSV y reproducibles con los scripts; los artículos no sustituyen esta evidencia.
2. **Método:** literatura para justificar comparaciones, métricas, bloques temporales y límites estadísticos.
3. **Mecanismo regional:** estudios de Chile central/Andes hacen algunas explicaciones plausibles, pero no prueban causalidad en este registro.
4. **Validación directa:** evidencia del mismo producto, escala, periodo y cuenca. No se halló una evaluación independiente de IMERG mensual sobre el polígono Maipo–El Manzano para este CSV.

### Advertencia decisiva de versión

El script `scripts/02_descargar_satelite.py` selecciona explícitamente `NASA/GPM_L3/IMERG_MONTHLY_V06`, cuya documentación lo identifica como IMERG mensual Final V06 y enlaza el DOI de producto [10.5067/GPM/IMERG/3B-MONTH/06](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/06). El DOI de producto V07 es distinto: [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07). La documentación NASA indica que Final integra ajuste con datos mensuales de pluviómetros.

Por tanto, las afirmaciones de `AGENTS.md` y handoffs que llaman V07 a los valores del CSV no concuerdan con el script vigente. El CSV no contiene metadatos que demuestren qué exportación concreta lo generó; la lectura prudente es **“el script apunta a V06; confirmar la procedencia del CSV antes de fijar la versión publicada”**. No trasladar resultados de estudios V06 o V07 entre versiones como si fueran equivalentes.

### Base local de hechos

- El CSV actual contiene 484 filas mensuales entre 1980-01 y 2020-04; `P_local_mm` tiene un vacío en 2020-04 y caudal tiene 14 vacíos (2.89%). Estos valores difieren de los metadatos antiguos que indican 483 meses hasta 2020-03 y menos de 2% de faltantes de caudal.
- Hay 238 pares válidos de precipitación local–IMERG (2000-06 a 2020-03), 469 de precipitación local–caudal (1980-01 a 2020-03) y 230 de IMERG–caudal (2000-06 a 2020-03). Se usaron casos completos por comparación y no se imputó.
- Los resultados de concordancia y rezagos exploratorios están registrados en `rol_b_modelador.md` y se reproducen con `scripts/04_analisis_precipitacion.py` y `scripts/05_anomalias_rezagos.py`. La evaluación temporal está implementada en `scripts/06_modelos_validacion_temporal.py`; sus cifras no son resultados bibliográficos.

## Mapa de evidencia por checklist

### 7.1 Preparación y validación

**Qué sustentar:** trazabilidad de la fuente, periodo, producto, unidades y muestra válida. El estándar no es “citar un artículo para el conteo”: los conteos/faltantes se calculan directamente del CSV. CAMELS-CL documenta un conjunto chileno de cuencas con múltiples fuentes meteorológicas, precipitación nacional y global, y limitaciones importantes de productos de precipitación en cabeceras de alta elevación y pendiente. NASA/EE documenta identidad, disponibilidad y escala del producto satelital.

**Aplicación local:** reportar columnas tal como aparecen (`P_local_mm`, `P_IMERG_mm`, `Caudal_m3s`, `Q_lamina_mm`, `Temp_C`, `date`), unidades, ventana y n de cada análisis. La referencia local se describe como CR2MET/observacional según los metadatos del proyecto; la composición concreta y posible uso de estaciones debe verificarse en los archivos fuente de CAMELS-CL antes de afirmar independencia estadística.

**Fuentes:** Alvarez-Garreton et al. (2018), DOI `10.5194/hess-22-5817-2018`; NASA GES DISC/Google Earth Engine, DOI de producto V06/07 arriba.

### 7.2 Relaciones, dispersión y métricas

**Qué sustentar:** una correlación alta no mide por sí sola concordancia; conviene combinar error en unidades originales, sesgo y asociación. Pearson resume asociación lineal, Spearman asociación monótona por rangos, y MAE/RMSE describen error con sensibilidades distintas. Hossain y Huffman proponen evaluar precipitación satelital en dimensiones espacial, de recuperación y temporal; Gupta et al. analizan cómo el error cuadrático incorpora componentes distintos y por qué no debe usarse una única métrica.

**Aplicación local:** mantener explícito `error = PI - PL`, en mm/mes; sesgo negativo significa menor promedio IMERG frente a la referencia bajo esta convención. Definir PBIAS como `100 * sum(PI - PL) / sum(PL)`. Separar sesgo medio de error mensual: en estos pares la mediana del error es positiva aunque el promedio sea negativo, así que el promedio no caracteriza todos los meses. Desgloses estacionales/intensidad y análisis de influencia explican heterogeneidad, pero las fechas extremas siguen en la evaluación principal.

**Fuentes:** Hossain & Huffman (2008), DOI `10.1175/2007JHM925.1`; Gupta et al. (2009), DOI `10.1016/j.jhydrol.2009.08.003`; Willmott (1981), DOI `10.1080/02723646.1981.10642213`.

### 7.3 Anomalías, rezagos y estacionalidad

**Qué sustentar:** quitar la media mensual sirve para distinguir covariación interanual de la coincidencia creada por el ciclo anual. Sin embargo, la selección del máximo entre muchos rezagos y la autocorrelación afectan la interpretación y la incertidumbre de una correlación. Pyper y Peterman discuten explícitamente inferencia con series autocorrelacionadas.

**Aplicación local:** la dirección del lag es lluvia en `t-k` frente a caudal en `t`; nunca usar precipitación futura. El pico local cerca de siete meses cambia si cambia la climatología de referencia; se exploraron 13 lags sobre registros autocorrelacionados y las anomalías actuales usan una referencia que incluye toda la ventana común. Así, es una hipótesis exploratoria, no una estimación de un tiempo físico de tránsito ni una habilidad predictiva. Para modelar, ajustar climatología y seleccionar lag solo con los datos de entrenamiento.

**Fuentes:** Pyper & Peterman (1998), DOI `10.1139/f98-104`; Alvarez-Garreton et al. (2021), DOI `10.5194/hess-25-429-2021`; Masiokas et al. (2006), DOI `10.1175/JCLI3969.1`.

### 7.4 Modelos candidatos

**Qué sustentar:** el modelo más complejo no es automáticamente mejor. Una regresión lineal transparente y una climatología mensual sirven como baselines; transformaciones o rezagos se aceptan si se seleccionan en ajuste, mejoran error retenido y tienen interpretación defendible. P–Q empírica no es un balance hídrico: no representa por sí sola evapotranspiración, almacenamiento, nieve/glaciar, regulación ni conservación de masa.

**Aplicación local:** para IMERG→P local comparar contra IMERG sin corregir; para P→Q comparar contra la media mensual de Q del entrenamiento y una regresión lineal. Probar anomalías/rezagos como candidatos, no imponerlos. Expresar variable objetivo y predictor en unidades originales, explicar cualquier estandarización y volver a reportar métricas en mm/mes o m³/s.

**Fuentes:** Gupta et al. (2009), DOI `10.1016/j.jhydrol.2009.08.003`; Klemeš (1986), DOI `10.1080/02626668609491024`; Alvarez-Garreton et al. (2021), DOI `10.5194/hess-25-429-2021`.

### 7.5 Evaluación temporal fuera del ajuste

**Qué sustentar:** mezclar aleatoriamente meses dependientes permite que información temporal cercana aparezca en ajuste y evaluación y puede subestimar el error de predicción. Roberts et al. revisan particiones estructuradas y recomiendan bloqueo cuando hay dependencia; Klemeš es un antecedente clásico de prueba operacional de modelos hidrológicos; Bergmeir et al. precisan que la validez de cross-validation para series autorregresivas depende de supuestos y no implica que cualquier partición aleatoria sea apropiada para pronóstico hidrológico.

**Aplicación local:** reservar años completos al final como prueba cronológica; elegir normalización, climatología, rezago y parámetros dentro de bloques previos; calcular sesgo, MAE y RMSE sobre fechas comunes a todos los comparadores. Contrastar contra las dos referencias simples requeridas. Examinar residuos en tiempo, valor estimado y mes. Una única partición temporal solo da evidencia preliminar de esa ventana; para hablar de estabilidad conviene añadir evaluación de origen rodante/varios bloques.

**Fuentes:** Klemeš (1986), DOI `10.1080/02626668609491024`; Roberts et al. (2017), DOI `10.1111/ecog.02881`; Bergmeir, Hyndman & Koo (2018), DOI `10.1016/j.csda.2017.11.003`.

### 7.6 Interpretación física, incertidumbre y fuentes compartidas

**Nieve, agua subterránea y glaciares:** Masiokas et al. analizan 30–37°S y relacionan nieve regional con caudal anual y de temporada cálida; Cortés y Margulis reconstruyen nieve en los Andes extratropicales 27–37°S; Alvarez-Garreton et al. encuentran memoria hidrológica modulada por nieve y aguas subterráneas en cuencas chilenas; Ayala et al. modelan explícitamente la contribución glaciar al Maipo. En conjunto hacen razonable plantear mecanismos de almacenamiento y deshielo, pero no identifican el causante del pico empírico de correlación del proyecto.

**Orografía y estimación de precipitación:** Falvey y Garreaud estudian lluvia invernal y relieve en Chile central. El CAMELS-CL documenta incertidumbre en precipitación de cabeceras montañosas. Más directamente, Rojas et al. evalúan IMERG V06 durante dos campañas invernales cerca de 36°S y reportan subestimación del realce orográfico y mayores déficits en ciertos regímenes microfísicos y cotas elevadas. Es evidencia física regional directa sobre IMERG V06, pero las campañas son cortas, en otro transecto y no representan el promedio mensual de la cuenca Maipo. No trasladar sus porcentajes a este proyecto.

**Comparaciones nacionales chilenas:** Soto-Alvarez et al. comparan 3B42 V7 y 3IMERG durante 2014–2018 con 143 estaciones y cuatro macrozonas hidroclimáticas; la agregación temporal mejora las métricas y se observan diferencias costa/interior. El resumen consultado no especifica suficientemente la versión de 3IMERG para asignarla a V06 o V07. da Silva et al. estudian IMERG **Early**, 2015–2020; es otra corrida, no Final. Zambrano-Bigiarini et al. incluyen estaciones y gradientes chilenos, pero sus siete productos no incluyen IMERG. Estas fuentes dan contexto, no validación de la serie exacta.

**Posible dependencia de referencia:** el producto mensual IMERG Final aplica información de pluviómetros; la fuente local se describe como CR2MET/gauge-informed en documentación de CAMELS-CL/proyecto. Esto hace posible que las fuentes no sean independientes, pero no prueba que los mismos pluviómetros concretos entren en ambos productos. No afirmar dependencia efectiva sin identificar estaciones/periodos y la configuración usada. La validación frente a una referencia interpolada también incluye incertidumbre de esa referencia.

**Fuentes:** Masiokas et al. (2006), DOI `10.1175/JCLI3969.1`; Cortés & Margulis (2017), DOI `10.1002/2017GL073826`; Falvey & Garreaud (2007), DOI `10.1175/JHM562.1`; Ayala et al. (2020), DOI `10.5194/tc-14-2005-2020`; Alvarez-Garreton et al. (2021), DOI `10.5194/hess-25-429-2021`; Rojas et al. (2021), DOI `10.1016/j.atmosres.2021.105454`; Soto-Alvarez et al. (2020), DOI `10.1016/j.jsames.2020.102870`; da Silva et al. (2023), DOI `10.3390/rs15030573`; Zambrano-Bigiarini et al. (2017), DOI `10.5194/hess-21-1295-2017`; Tapiador et al. (2020), DOI `10.1175/JHM-D-19-0116.1`.

### 7.7 Entregables y comunicación

La literatura fundamenta las decisiones y límites; las tablas, cifras, gráficos y conclusión del Rol B deben ser reproducibles desde el CSV y sus scripts. Guardar fuente, columnas, periodo, n, unidades, regla de faltantes, versión del producto, fórmula y figuras/tablas. El informe del equipo debe citar los artículos por las proposiciones respaldadas, no acumular DOIs al final sin vincularlos a una afirmación.

## Fichas bibliográficas verificadas

### Productos y evaluaciones en Chile

1. **NASA GES DISC / Google Earth Engine.** IMERG Final mensual V06, conjunto `NASA/GPM_L3/IMERG_MONTHLY_V06`, disponible desde 2000-06 hasta 2021-09 en el catálogo EE. [DOI de datos V06: 10.5067/GPM/IMERG/3B-MONTH/06](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/06). La ficha indica que Final emplea análisis mensual de pluviómetros para generar el producto de investigación. **Sirve para identidad, resolución/cobertura y linaje; no es una validación de exactitud en Maipo.**

2. **NASA GES DISC / Google Earth Engine.** IMERG Final mensual V07, conjunto `NASA/GPM_L3/IMERG_MONTHLY_V07`, DOI de datos [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07). La ficha actual cubre 1998-01 a 2025-09. **No citar V07 como fuente de valores exportados por el script vigente V06 sin verificar/reprocesar.**

3. **Alvarez-Garreton, C., Mendoza, P. A., Boisier, J. P., Addor, N., Galleguillos, M., Zambrano-Bigiarini, M., et al. (2018).** “The CAMELS-CL dataset: catchment attributes and meteorology for large sample studies – Chile dataset.” *Hydrology and Earth System Sciences, 22*, 5817–5846. [DOI: 10.5194/hess-22-5817-2018](https://doi.org/10.5194/hess-22-5817-2018). Presenta series meteorológicas de precipitación nacionales y globales para 516 cuencas; informa discrepancias entre productos y subestimación sistemática de precipitación en cuencas de cabecera montañosas (altitud y pendiente altas) en regiones húmedas. **Contexto nacional/proveniencia; no identifica por sí solo el origen ni la magnitud del sesgo del CSV en Maipo.** Dataset CAMELS-CL: [PANGAEA 894885](https://doi.org/10.1594/PANGAEA.894885).

4. **Soto-Alvarez, M., Alcayaga, H., Alarcon, V. J., Caamaño, D., Palma, S., & Escanilla-Minchel, R. (2020).** “Evaluation of products 3B42 v7 and 3IMERG for the hydroclimatic regions of Chile.” *Journal of South American Earth Sciences, 104*, 102870. [DOI: 10.1016/j.jsames.2020.102870](https://doi.org/10.1016/j.jsames.2020.102870). Resumen verificado: cuatro macrozonas, 143 estaciones, 2014–2018; rendimiento mejora al agregar temporalmente y hay diferencias costa/interior; autores consideran útil 3IMERG en zonas centrales/sureñas. **No inferir una versión 3IMERG no especificada en el resumen ni tomar sus métricas por las de Maipo.**

5. **Rojas, Y., Minder, J. R., Campbell, L. S., Massmann, A. K., & Garreaud, R. (2021).** “Assessment of GPM IMERG satellite precipitation estimation and its dependence on microphysical rain regimes over the mountains of south-central Chile.” *Atmospheric Research, 253*, 105454. [DOI: 10.1016/j.atmosres.2021.105454](https://doi.org/10.1016/j.atmosres.2021.105454). Evalúa IMERG **V06** contra pluviómetros y radares de perfilado de CCOPE (invierno 2015) y ChOMPS (invierno 2016), cerca de 36°S. Reporta que IMERG capta el patrón general de realce orográfico, pero subestima su magnitud; en campañas/sitios altos los errores dependen de elevación y régimen microfísico, con déficit mayor para lluvia cálida que para lluvia iniciada por hielo. **Es la evidencia IMERG–Chile montañoso más próxima; no es la misma cuenca, agregación mensual ni ventana larga del CSV.**

6. **da Silva, L. et al. (2023).** “Assessment of the IMERG Early-Run Precipitation Estimates over South American Country of Chile.” *Remote Sensing, 15*(3), 573. [DOI: 10.3390/rs15030573](https://doi.org/10.3390/rs15030573). Compara IMERG **Early** con observaciones en escalas espaciales/temporales, 2015–2020; informa desempeño espacial relativamente mejor en zona central y ligera sobreestimación general. **Early es baja latencia, no Final; el resultado nacional no valida IMERG mensual Final V06/V07 del Maipo.**

7. **Zambrano-Bigiarini, M., Nauditt, A., Birkel, C., Verbist, K., & Ribbe, L. (2017).** “Temporal and spatial evaluation of satellite-based rainfall estimates across the complex topographical and climatic gradients of Chile.” *Hydrology and Earth System Sciences, 21*, 1295–1320. [DOI: 10.5194/hess-21-1295-2017](https://doi.org/10.5194/hess-21-1295-2017). Evalúa siete productos frente a 366 estaciones y destaca dependencia por clima, estación, elevación e intensidad; los productos analizados no incluyen IMERG. **Útil para diseño de validación en Chile y representatividad de referencia, no para atribuirle un resultado a IMERG.**

8. **Yang, Z., Hsu, K., Sorooshian, S., Xu, X., Braithwaite, D., & Verbist, K. (2016).** “Bias adjustment of satellite-based precipitation estimation using gauge observations: A case study in Chile.” *Journal of Geophysical Research: Atmospheres, 121*, 3790–3806. [DOI: 10.1002/2015JD024540](https://doi.org/10.1002/2015JD024540). Propone ajuste QM-GW para PERSIANN-CCS diario, con calibración 2009–2013 y validación 2014. **Ejemplo metodológico chileno de calibración y validación separada; producto distinto, no evidencia para corregir IMERG automáticamente.**

### Hidrología andina, nieve y memoria

9. **Masiokas, M. H., Villalba, R., Luckman, B. H., Le Quesne, C., & Aravena, J. C. (2006).** “Snowpack Variations in the Central Andes of Argentina and Chile, 1951–2005.” *Journal of Climate, 19*(24), 6334–6352. [DOI: 10.1175/JCLI3969.1](https://doi.org/10.1175/JCLI3969.1). Para 30–37°S documenta el papel del manto nival en caudales de Chile central/Argentina centro-occidental y asociación entre nieve y caudales anuales/cálidos. **Apoya plausibilidad regional, no un lag exacto ni predicción en El Manzano.**

10. **Cortés, G., & Margulis, S. (2017).** “Impacts of El Niño and La Niña on interannual snow accumulation in the Andes.” *Geophysical Research Letters, 44*, 6859–6867. [DOI: 10.1002/2017GL073826](https://doi.org/10.1002/2017GL073826). Reanálisis de nieve 27–37°S, 1984–2015. **Contexto espacialmente pertinente de variabilidad de nieve; no atribuye los rezagos de este CSV.**

11. **Falvey, M., & Garreaud, R. D. (2007).** “Wintertime Precipitation Episodes in Central Chile: Associated Meteorological Conditions and Orographic Influences.” *Journal of Hydrometeorology, 8*(2), 171–193. [DOI: 10.1175/JHM562.1](https://doi.org/10.1175/JHM562.1). Estudia eventos de precipitación y efectos orográficos en Chile central. **Describe mecanismo/región; no es una validación de satélite.**

12. **Ayala, A., Farías-Barahona, D., Huss, M., Pellicciotti, F., McPhee, J., & Farinotti, D. (2020).** “Glacier runoff variations since 1955 in the Maipo River basin, in the semiarid Andes of central Chile.” *The Cryosphere, 14*, 2005–2027. [DOI: 10.5194/tc-14-2005-2020](https://doi.org/10.5194/tc-14-2005-2020). Modela contribución de glaciares al caudal del Maipo y cambios en el periodo 1955–2016. **Evidencia directa de que hielo/almacenamiento importan en la cuenca; no permite concluir que explique por sí solo correlaciones mensuales ni sesgos de precipitación.**

13. **Alvarez-Garreton, C., Boisier, J. P., Garreaud, R., Seibert, J., & Vis, M. (2021).** “Progressive water deficits during multiyear droughts in basins with long hydrological memory in Chile.” *Hydrology and Earth System Sciences, 25*, 429–446. [DOI: 10.5194/hess-25-429-2021](https://doi.org/10.5194/hess-25-429-2021). En 106 cuencas y con CAMELS-CL/HBV encuentra memoria modulada por nieve y aguas subterráneas; en cuencas nivales, el caudal otoñal puede asociarse con precipitación del año previo. **Justifica estudiar memoria y almacenamiento; no identifica la causa del máximo de lag 7 de este análisis.**

14. **Favier, V., Falvey, M., Rabatel, A., Praderio, E., & López, D. (2009).** “Interpreting discrepancies between discharge and precipitation in high-altitude area of Chile's Norte Chico region (26–32°S).” *Water Resources Research, 45*, W02424. [DOI: 10.1029/2008WR006802](https://doi.org/10.1029/2008WR006802). Caso regional al norte de Maipo que trata medición de precipitación, nieve y glaciares en altura. **Advertencia comparativa, no transferencia cuantitativa.**

### Errores de precipitación y métricas

15. **Hossain, F., & Huffman, G. J. (2008).** “Investigating Error Metrics for Satellite Rainfall Data at Hydrologically Relevant Scales.” *Journal of Hydrometeorology, 9*(3), 563–575. [DOI: 10.1175/2007JHM925.1](https://doi.org/10.1175/2007JHM925.1). Propone considerar dimensiones espaciales, de recuperación y temporales en evaluación satelital. **Sustenta métricas complementarias y análisis por escala; no indica un umbral universal de aceptación.**

16. **Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).** “Decomposition of the Mean Squared Error and NSE Performance Criteria.” *Journal of Hydrology, 377*(1–2), 80–91. [DOI: 10.1016/j.jhydrol.2009.08.003](https://doi.org/10.1016/j.jhydrol.2009.08.003). Descompone error cuadrático/NSE y muestra que una puntuación única oculta rasgos distintos. **Apoya reportar sesgo, MAE y RMSE juntos, además de asociación.**

17. **Willmott, C. J. (1981).** “On the Validation of Models.” *Physical Geography, 2*(2), 184–194. [DOI: 10.1080/02723646.1981.10642213](https://doi.org/10.1080/02723646.1981.10642213). Referencia metodológica general sobre validación. **Complementaria; la defensa de métricas hidrológicas específicas se apoya principalmente en Gupta et al. y Hossain & Huffman.**

18. **Tian, F., Hou, S., Yang, L., Hu, H., & Hou, A. (2018).** “How Does the Evaluation of the GPM IMERG Rainfall Product Depend on Gauge Density and Rainfall Intensity?” *Journal of Hydrometeorology, 19*(2), 339–349. [DOI: 10.1175/JHM-D-17-0161.1](https://doi.org/10.1175/JHM-D-17-0161.1). En China observa que intensidad y densidad de pluviómetros afectan métricas; IMERG sobrestima lluvia ligera y subestima la fuerte en ese caso. **Motiva el desglose local; no transfiere magnitudes/regímenes a los Andes.**

19. **Tapiador, F. J., Navarro, A., García-Ortega, E., Merino, A., Sánchez, J. L., Marcos, C., & Kummerow, C. (2020).** “The Contribution of Rain Gauges in the Calibration of the IMERG Product.” *Journal of Hydrometeorology, 21*(2), 161–182. [DOI: 10.1175/JHM-D-19-0116.1](https://doi.org/10.1175/JHM-D-19-0116.1). Evaluación española relaciona desempeño con orografía y disponibilidad de pluviómetros GPCC para calibración. **Apoya advertir sobre posible dependencia de referencias; no demuestra solapamiento entre estaciones CR2MET y GPCC en Maipo.**

20. **Hosseini-Moghari, S.-M., & Tang, Q. (2020).** “Validation of GPM IMERG V05 and V06 Precipitation Products over Iran.” *Journal of Hydrometeorology, 21*(5), 1011–1037. [DOI: 10.1175/JHM-D-19-0269.1](https://doi.org/10.1175/JHM-D-19-0269.1). Útil como evaluación por clima/intensidad de V05/V06 fuera de Sudamérica. **Contexto externo secundario; no evidencia de rendimiento andino.**

### Validación temporal y dependencia de series

21. **Klemeš, V. (1986).** “Operational testing of hydrological simulation models.” *Hydrological Sciences Journal, 31*(1), 13–24. [DOI: 10.1080/02626668609491024](https://doi.org/10.1080/02626668609491024). Referencia clásica sobre cómo probar modelos hidrológicos con datos temporalmente separados y escenarios operacionales. **Sustenta no evaluar solo con el mismo periodo de ajuste.**

22. **Roberts, D. R., Bahn, V., Ciuti, S., et al. (2017).** “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure.” *Ecography, 40*(8), 913–929. [DOI: 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881). Revisión/simulaciones sobre dependencias y validación en bloques; advierte que particiones aleatorias pueden subestimar error para datos estructurados. **Referencia metodológica general, no específica de hidrología.**

23. **Bergmeir, C., Hyndman, R. J., & Koo, B. (2018).** “A note on the validity of cross-validation for evaluating autoregressive time series prediction.” *Computational Statistics & Data Analysis, 120*, 70–83. [DOI: 10.1016/j.csda.2017.11.003](https://doi.org/10.1016/j.csda.2017.11.003). Explica supuestos bajo los cuales cross-validation puede ser válida en series autorregresivas. **No es licencia para mezclar aleatoriamente meses de un proceso hidrológico estacional; el esquema debe corresponder al objetivo de pronóstico.**

24. **Pyper, B. J., & Peterman, R. M. (1998).** “Comparison of methods to account for autocorrelation in correlation analyses of fish data.” *Canadian Journal of Fisheries and Aquatic Sciences, 55*(9), 2127–2140. [DOI: 10.1139/f98-104](https://doi.org/10.1139/f98-104). Estudia cómo autocorrelación afecta inferencia de correlaciones en series temporales ambientales. **Apoya cautela estadística en los rezagos; dominio aplicado distinto.**

## Síntesis y redacción defendible

> “La climatología muestra máximos estacionales distintos para lluvia y caudal. La importancia del manto nival y de la memoria hidrológica está documentada en Andes centrales y cuencas chilenas, y la contribución glaciar se ha estudiado específicamente en el Maipo. El máximo exploratorio de correlación de anomalías de lluvia previa y caudal aparece cerca de siete meses con una referencia climatológica, pero cambia al cambiar el periodo de referencia y no identifica por sí solo un mecanismo ni habilidad predictiva. Se interpreta como hipótesis compatible con almacenamiento nival/subterráneo/glaciar, pendiente de contraste fuera de muestra.”

> “En los pares mensuales disponibles, IMERG presenta sesgo medio negativo con la convención `PI - PL`, mientras el error cambia entre intensidades y estaciones. Evaluaciones publicadas en Chile central y en las montañas del centro-sur chileno muestran que el comportamiento satelital varía por región, elevación, escala temporal y régimen de precipitación. El estudio montañoso de Rojas et al. (2021) evaluó IMERG V06 durante dos campañas de invierno; su resultado no se transfiere directamente al promedio mensual de toda la cuenca. Por ahora no se atribuye el error observado a la orografía ni se afirma independencia entre la referencia local y los pluviómetros usados por IMERG Final.”

### Afirmaciones que sí/no permite la evidencia

- **Sí:** en la literatura existe evidencia directa de errores de IMERG V06 en montañas de Chile central-sur y una comparación chilena 3IMERG/3B42V7 en varias regiones; esos estudios justifican comprobar región, elevación, estación, intensidad y escala.
- **Sí:** la literatura regional respalda estudiar nieve, glaciares, aguas subterráneas y memoria como hipótesis hidrológicas razonables para Maipo/Andes centrales.
- **No:** “Rojas et al. demuestra que nuestro error mensual de Maipo es una subestimación orográfica de X%”. El producto, ventana espacial/temporal y muestra no coinciden.
- **No:** “El deshielo causa el lag 7”. Los artículos no analizaron estos pares ni este procedimiento de selección de rezago.
- **No:** “La comparación es independiente” o “hay solapamiento confirmado” entre CR2MET y GPCC sin inventarios de estaciones y trazabilidad de ambos productos.
- **No:** “V07” para el CSV solo porque aparece en handoffs; el script apunta a V06 y la versión exportada debe verificarse.

## Puntos pendientes de la checklist

- Confirmar la versión exacta del raster/exportación que originó `P_IMERG_mm`; guardar identificador Earth Engine, fecha de ejecución, propiedad temporal, unidad y transformación.
- Auditar la fuente y tratamiento de `P_local_mm` y la posible intersección de estaciones con GPCC. Hasta entonces, tratar dependencia como riesgo, no como hecho.
- La prueba temporal existente es un único holdout cronológico. Si se necesita afirmar estabilidad, completar bloques de origen rodante o más de un periodo retenido.
- La interpretación cuantitativa completa de los resultados de modelos se mantiene separada y pendiente de aprobación para su incorporación en los registros acordados.

**Limpieza:** borrar íntegramente `documentos/bitacora_datos_temporal/` antes de la entrega final y excluirla del ZIP.