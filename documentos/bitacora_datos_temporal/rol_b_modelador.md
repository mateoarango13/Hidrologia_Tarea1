# Registro del Rol B — Modelador

**Responsable:** Santiago Ortega.

**Alcance:** punto 2 (relaciones entre precipitación local, IMERG y caudal; modelos y evaluación temporal) y apoyo al equipo con anomalías estandarizadas. Mantener separadas las exploraciones de los resultados validados fuera de muestra.

## Registro B-20260928-01 — Comparación inicial y relaciones descriptivas

- Estado: PRELIMINAR / exploratorio.
- Fecha: 2026-09-28.
- Dataset: `datos/datos_mensuales_maipo.csv` (lectura; no modificado).
- Columnas: `P_local_mm` (mm/mes), `P_IMERG_mm` (mm/mes), `Caudal_m3s` (m3/s), `Q_lamina_mm` (mm/mes), `date`.
- Precipitación local–IMERG: 238 pares válidos, 2000-06 a 2020-03.
- Precipitación local–caudal: 469 pares válidos, 1980-01 a 2020-03.
- IMERG–caudal: 230 pares válidos, 2000-06 a 2020-03. Los pares con `Q_lamina_mm` tienen los mismos conteos.
- Regla de faltantes: casos completos por comparación; sin imputación.
- Reproducción de los gráficos y métricas iniciales: ejecutar `python scripts/04_analisis_precipitacion.py` desde la raíz del repositorio.
- Salidas: `figuras/figura_2_1_relaciones_scatter.png` y `figuras/tabla_2_1_metricas_relaciones.csv`.

### Resultados calculados

- IMERG frente a precipitación local: Pearson `r = 0.8875`; Spearman `rho = 0.8245`.
- Error definido como `PI - PL`: sesgo medio `-5.503 mm/mes`; MAE `27.344 mm/mes`; RMSE `48.656 mm/mes`; PBIAS `-8.764%`, calculado como `100 * sum(PI - PL) / sum(PL)`.
- En los pares comparados, IMERG es menor que la referencia en 103 meses y mayor en 135; mediana del error `+3.856 mm/mes`. Los cinco errores absolutos mayores aportan 52.35% de la suma de errores cuadrados.
- Correlación de series originales precipitación local–caudal: `r = -0.2009`, `rho = -0.3931`; IMERG–caudal: `r = -0.2772`, `rho = -0.4234`.
- Las medias mensuales alcanzan máximos distintos: precipitación local en junio (`179.01 mm/mes`) y caudal en diciembre (`210.71 m3/s`). La correlación descriptiva entre las 12 medias climatológicas es `r = -0.7676`.
- Al restar la media climatológica del mes, correlación contemporánea: local–caudal `r = 0.1648`, `rho = 0.1426`; IMERG–caudal `r = 0.1789`, `rho = 0.2325`.
- En la exploración de anomalías, lluvia en `t-k` frente a caudal en `t`, para `k=5` y `k=6`: precipitación local `r = 0.3827` y `0.4553`; IMERG `r = 0.4095` y `0.3924`.

### Interpretación y límites

- La correlación negativa contemporánea en las series originales coincide con el desfase entre las climatologías mensuales de precipitación y caudal. Es compatible con almacenamiento nival y deshielo, pero esta explicación necesita bibliografía regional y más evidencia; las correlaciones no prueban el mecanismo.
- La asociación contemporánea se vuelve débilmente positiva tras quitar la media mensual. Los valores de 5–6 meses son candidatos exploratorios, no prueba de causalidad ni de capacidad predictiva.
- La climatología de estas exploraciones se calculó con el periodo completo de cada par y se probaron varios rezagos sobre la misma muestra. No debe reportarse como validación. Para modelar, calcular climatología, seleccionar rezagos y ajustar parámetros usando solo el bloque de entrenamiento; evaluar en años completos retenidos y comparar contra las referencias simples del enunciado.
- El sesgo medio negativo no significa subestimación en todos los meses: el signo del error cambia con frecuencia y unos pocos extremos dominan RMSE.
- Pendiente: documentar interpretación completa por mes/intensidad, revisar fechas extremas, estandarizar anomalías según el periodo de referencia acordado y efectuar evaluación temporal fuera de muestra.

## Registro B-20260928-02 — Dispersión por estación, intensidad y meses influyentes

- Estado: PRELIMINAR / descriptivo.
- Fecha: 2026-09-28.
- Dataset y regla de pares: los mismos 238 pares válidos P local–IMERG de 2000-06 a 2020-03; no se imputaron ni excluyeron meses del resultado principal.
- Código: las funciones `build_precipitation_group_diagnostics`, `build_influential_months` y `build_outlier_sensitivity` de `scripts/04_analisis_precipitacion.py`.
- Tablas: `figuras/tabla_2_1_errores_por_grupo.csv`, `figuras/tabla_2_1_meses_influyentes.csv` y `figuras/tabla_2_1_sensibilidad_extremos.csv`.

### Resultados calculados

- Sesgo `PI - PL` por estación austral: verano `+6.85 mm/mes` (`n=60`), otoño `-9.38` (`n=58`), invierno `-11.33` (`n=60`) y primavera `-8.28` (`n=60`). RMSE por estación: verano `14.20`, otoño `47.76`, invierno `76.72` y primavera `33.13 mm/mes`.
- Sesgo por cuartil de `P_local_mm`: `+14.00`, `+9.97`, `+6.43` y `-51.94 mm/mes` desde el cuartil menos lluvioso al más lluvioso. En el cuartil superior, MAE `58.75` y RMSE `88.52 mm/mes`; en el inferior, MAE `14.09` y RMSE `17.06 mm/mes`.
- Cinco mayores errores absolutos: junio 2000 `-334.60 mm`; mayo 2008 `-233.52`; junio 2005 `-217.22`; julio 2006 `-208.93`; agosto 2005 `-193.99` (todos `PI - PL`).
- Sensibilidad: Pearson completo `0.8875`; al retirar los cinco mayores errores absolutos solo como diagnóstico `0.8829`, mientras RMSE disminuye de `48.66` a `33.94 mm/mes`. No se retiran estos meses del análisis reportado.

### Interpretación y límites

- La diferencia media por estación y cuartil muestra que el sesgo agregado oculta errores de signo contrario: sobreestimación en verano y baja lluvia, y subestimación promedio en los cuartiles lluviosos y estaciones restantes.
- La mayor dispersión absoluta durante meses de precipitación intensa y la sensibilidad de RMSE a pocos extremos son resultados descriptivos. No prueban un mecanismo orográfico, problema de fuente o causalidad; las fechas señaladas deben cotejarse con los productos originales y sus metadatos.
- Pearson se mantiene alto al excluir los extremos en el análisis de sensibilidad, pero esos extremos siguen siendo parte de la habilidad/error real y permanecen en el conjunto principal.

## Registros siguientes

Copiar la plantilla de `00_INSTRUCCIONES.md` para cada análisis nuevo. No sobrescribir este registro: enlazarlo con un ID nuevo y conservar su estado exploratorio.

## Registro B-20260928-04 — Sustento científico con DOI

- Estado: bibliografía ampliada para contexto y discusión; no implica validación directa del dataset.
- Fecha: 2026-09-28.
- Integrante responsable: Santiago Ortega — Rol B.
- Agente: GitHub Copilot.
- Dossier: `documentos/bitacora_datos_temporal/referencias_sustento_rol_b.md`.
- El dossier ampliado mapea literatura y documentación de producto a cada subpunto 7.1–7.7; incluye referencias revisadas por pares con DOI, fichas NASA/EE y límites por geografía, escala, periodo, corrida y versión.
- Evidencia chilena directa: Rojas et al. (2021, DOI `10.1016/j.atmosres.2021.105454`) evalúa IMERG V06 en campañas invernales de 2015–2016 cerca de 36°S y documenta errores dependientes de elevación/régimen microfísico. Soto-Alvarez et al. (2020, DOI `10.1016/j.jsames.2020.102870`) compara 3IMERG/TMPA con 143 estaciones de Chile en 2014–2018; el resumen consultado no identifica claramente la versión de 3IMERG.
- da Silva et al. (2023, DOI `10.3390/rs15030573`) evalúa IMERG Early, no Final. Zambrano-Bigiarini et al. (2017, DOI `10.5194/hess-21-1295-2017`) caracteriza productos satelitales en Chile, pero los siete productos evaluados no incluyen IMERG.
- **Discrepancia de procedencia pendiente:** `scripts/02_descargar_satelite.py` selecciona `NASA/GPM_L3/IMERG_MONTHLY_V06`, no V07. Los DOI de producto mensual Final son `10.5067/GPM/IMERG/3B-MONTH/06` (V06) y `10.5067/GPM/IMERG/3B-MONTH/07` (V07). No etiquetar el CSV como V07 hasta verificar la exportación que lo originó.

### Aplicación a los resultados observados

- **Desfase estacional/rezagos:** Masiokas et al. (2006, DOI `10.1175/JCLI3969.1`) cubre 30–37°S; Alvarez-Garreton et al. (2021, DOI `10.5194/hess-25-429-2021`) relaciona memoria hidrológica con nieve y agua subterránea en cuencas chilenas; Ayala et al. (2020, DOI `10.5194/tc-14-2005-2020`) estudia glaciares del Maipo. Estas fuentes apoyan hipótesis regionales, no prueban que el máximo exploratorio de lag 7 sea causal.
- **Error satelital e intensidad:** Tian et al. (2018, DOI `10.1175/JHM-D-17-0161.1`) encuentra dependencia con intensidad y densidad de pluviómetros en China. Rojas et al. ofrece evidencia IMERG V06 en montaña chilena, pero de campañas breves cerca de 36°S. Ninguna fuente valida directamente los valores mensuales areales de este CSV.
- **Orografía y referencia:** CAMELS-CL (Alvarez-Garreton et al., 2018, DOI `10.5194/hess-22-5817-2018`) documenta limitaciones de precipitación en cabeceras montañosas; Falvey & Garreaud (2007, DOI `10.1175/JHM562.1`) caracteriza lluvia orográfica en Chile central. Tapiador et al. (2020, DOI `10.1175/JHM-D-19-0116.1`) documenta el papel de pluviómetros en la calibración IMERG Final en España. Son contexto y justificación para auditar la referencia; no confirman un solapamiento CR2MET–GPCC específico.
- **Métricas y validación temporal:** Gupta et al. (2009, DOI `10.1016/j.jhydrol.2009.08.003`) apoya evaluar componentes complementarios de error. Klemeš (1986, DOI `10.1080/02626668609491024`) y Roberts et al. (2017, DOI `10.1111/ecog.02881`) sustentan separar temporalmente ajuste y evaluación cuando existe dependencia.

### Límite de la evidencia

No se halló una validación independiente de la serie IMERG mensual exacta del CSV sobre esta cuenca y periodo. Evitar las afirmaciones “subestimación orográfica demostrada en Maipo” y “el deshielo causa el rezago de siete meses”. Tratar la posible dependencia de fuentes como riesgo metodológico pendiente de comprobar, no como hecho.

## Registro B-20260928-03 — Anomalías estandarizadas y rezagos exploratorios

- Estado: PRELIMINAR / exploratorio; no es evaluación predictiva fuera de muestra.
- Fecha: 2026-09-28.
- Script reproducible: `scripts/05_anomalias_rezagos.py`.
- Referencia climatológica fija común: 2000-06 a 2020-03, la ventana de cobertura satelital completa coincidente con las series locales. Se eligió para comparar variables con la misma ventana de referencia; no se recortaron las series locales transformadas.
- Fórmulas por variable y mes calendario `j`: anomalía `a = X - media_j`; estandarizada `z = a / s_j`, con desviación estándar muestral (`ddof=1`). Se conserva la escala de medida en `a`; `z` es adimensional. Estandarización no implica normalidad ni equivale a SPI.
- Columnas de entrada: `P_local_mm`, `P_IMERG_mm`, `Caudal_m3s`, `Q_lamina_mm`, `Temp_C` y `date`.
- Cobertura de referencia mensual: 19–20 años válidos para precipitación local, IMERG y temperatura; 18–20 para caudal y lámina. No hubo desviaciones estándar mensuales nulas. Los conteos, medias, medianas y desviaciones estándar por mes están en `figuras/tabla_2_2_climatologia_referencia.csv`.
- Salidas reproducibles: `figuras/serie_2_2_anomalias_estandarizadas.csv`, `figuras/tabla_2_2_correlaciones_rezagos.csv` y `figuras/figura_2_2_correlaciones_rezagos.png`.

### Resultados calculados

- Las anomalías se generaron para todas las filas disponibles; IMERG y temperatura conservan sus vacíos fuera de la cobertura original. No se rellenaron faltantes.
- Definición del rezago: precipitación de anomalía en `t-k` frente a anomalía de caudal en `t`, para `k=0...12`. No se usó precipitación futura.
- Referencia `Caudal_m3s`: lag 0, precipitación local `r = 0.1569`, `rho = 0.1754`, `n=469`; IMERG `r = 0.1783`, `rho = 0.2368`, `n=230`.
- Mayor Pearson exploratorio: local a lag 7, `r = 0.4773`, `rho = 0.2953`, `n=463`; IMERG a lag 7, `r = 0.4222`, `rho = 0.3549`, `n=224`.
- La transformación `Q_lamina_mm` produce patrones de rezago similares; sus resultados completos están en la tabla CSV.

### Interpretación y límites

- Al retirar el ciclo anual, la asociación contemporánea es débilmente positiva; algunos rezagos anteriores dan asociaciones positivas más altas. El máximo cerca de siete meses es solo un candidato de investigación, compatible en principio con memoria/almacenamiento de cuenca, pero no identifica por sí mismo nieve, regulación ni otro mecanismo.
- El máximo depende de la climatología: la exploración anterior usó una referencia distinta y encontró otro rezago máximo. Se analizaron trece rezagos y series con autocorrelación; el máximo observado puede estar inflado por selección y dependencia temporal.
- La referencia común usa el periodo completo que incluye fechas que luego podrían usarse para evaluar modelos. Por ello, estos resultados son descriptivos. En validación, fijar periodo y climatología dentro del bloque de entrenamiento, seleccionar el rezago en ajuste y evaluar años completos retenidos frente a referencias simples.
- Para completar este punto se requiere justificar mecanismos con bibliografía regional, definir incertidumbre que respete la dependencia temporal y ejecutar evaluación bloqueada. No reportar estos coeficientes como habilidad predictiva.

## Registro B-20260928-05 — Primera evaluación cronológica de modelos

- Estado: EVALUACIÓN RETROSPECTIVA PRELIMINAR; un solo bloque externo, no demuestra estabilidad general.
- Fecha: 2026-09-28.
- Responsable: Santiago Ortega — Rol B.
- Dataset: `datos/datos_mensuales_maipo.csv`; no modificado.
- Script reproducible: `scripts/06_modelos_validacion_temporal.py`.
- Validación: script ejecutado sin errores con Python 3.13. Se separan bloques por fechas completas; selección de regresión/rezagos y climatologías ocurre antes del test y solo con ajuste/tuning. No se mezclan meses al azar.
- Métricas siempre definidas como `predicción - observado`; unidades según el objetivo. Las comparaciones de caudal se evalúan en las mismas fechas válidas para los modelos del mismo predictor.

### Particiones y resultados calculados

- **P local desde IMERG:** ajuste final 2000-06–2015-12; tuning 2013-01–2015-12; test válido 2016-01–2020-03 (`n=51`). IMERG sin corrección: sesgo `-0.982 mm/mes`, MAE `18.840`, RMSE `32.578`. La regresión lineal seleccionada en tuning y reajustada con todo el ajuste usa `max(0, -18.166964 + 1.411121 * P_IMERG_mm)`; test: sesgo `+0.640`, MAE `20.853`, RMSE `30.739 mm/mes`. Reduce RMSE, pero empeora MAE; no hay mejora uniforme.
- **Q desde precipitación local:** ajuste 1980-01–2011-12; tuning 2008-01–2011-12; test válido 2012-01–2020-03 (`n=91`). Climatología mensual Q: sesgo `+47.722 m3/s`, MAE `48.652`, RMSE `61.004`. Regresión contemporánea Q~P(t): `+47.490`, `54.349`, `59.710`. El modelo de anomalías selecciona `k=6` en tuning y aplica `Qhat = climatología_Q(mes) - 0.163069 + 0.309861 * anomalía_P_local(t-6)`; test: sesgo `+40.661`, MAE `41.915`, RMSE `51.434 m3/s`.
- **Q desde IMERG:** ajuste 2000-06–2015-12; tuning 2012-01–2015-12; test válido 2016-01–2020-03 (`n=51`). Climatología mensual Q: sesgo `+40.484 m3/s`, MAE `42.415`, RMSE `55.102`. Regresión contemporánea Q~P(t): `+36.166`, `47.051`, `51.994`. El modelo de anomalías selecciona `k=8` en tuning y aplica `Qhat = climatología_Q(mes) - 10.076085 + 0.538856 * anomalía_P_IMERG(t-8)`; test: sesgo `+26.396`, MAE `35.192`, RMSE `49.120 m3/s`.
- Las ecuaciones de anomalías suman al componente estimado la climatología mensual Q calculada en el entrenamiento. La anomalía del predictor también usa climatología del entrenamiento. Ninguna predicción final fue negativa.
- El mayor valor predicho fue `302.766 m3/s` para Q desde IMERG con lag 8; es alto respecto de parte del test y debe revisarse con los diagnósticos, pero no se excluyó ni se etiquetó como físicamente imposible. La prueba no incluye incertidumbre de predicción ni estabilidad multi-bloque.

### Archivos de salida

- `figuras/tabla_2_3_metricas_fuera_ajuste.csv`: resumen de sesgo, MAE, RMSE, periodo, n y extremos predichos.
- `figuras/tabla_2_3_seleccion_modelos_ajuste.csv`: candidatos, resultados de tuning, rezagos elegidos y coeficientes.
- `figuras/tabla_2_3_predicciones_fuera_ajuste.csv`: predicción/residuo por fecha (528 filas de modelo-fecha).
- `figuras/tabla_2_3_metricas_por_anio.csv`, `figuras/tabla_2_3_residuos_por_mes.csv`, `figuras/tabla_2_3_metricas_por_estacion.csv`: diagnósticos desglosados.
- `figuras/figura_2_3_validacion_modelos.png` y `figuras/figura_2_4_residuos_en_tiempo.png`: visualización de test, predicciones y residuos, 300 DPI.

### Interpretación, límites y siguiente paso

- En esta partición, los modelos de anomalías con rezago reducen MAE/RMSE frente a climatología mensual Q para ambos predictores, pero mantienen sesgo positivo. Esto respalda utilidad preliminar en estos bloques, no una capacidad general de pronóstico.
- La corrección lineal P_IMERG→P local presenta un intercambio MAE/RMSE y no supera todas las métricas. La lluvia–caudal empírica no reemplaza balance hídrico ni prueba causalidad.
- Los rezagos `6` y `8` son selecciones predictivas internas específicas de sus ventanas, distintas de la exploración descriptiva de correlación y no evidencia de tiempos físicos exactos de deshielo.
- Pendiente: evaluación de origen rodante/bloques externos adicionales, revisión de residuos y predicción máxima; confirmar V06/V07 del raster que originó el CSV y posible solapamiento de pluviómetros con CR2MET/GPCC.

## Registro B-20260930-06 — Evaluación de estabilidad en tres bloques externos

- Estado: EVALUACIÓN MULTIBLOQUE RETROSPECTIVA; estabilidad descriptiva en las ventanas evaluadas, no independencia estadística ni garantía de pronóstico futuro.
- Fecha: 2026-09-30.
- Responsable: Santiago Ortega — Rol B.
- Script: `scripts/06_modelos_validacion_temporal.py`.
- Salida nueva: `figuras/tabla_2_3_metricas_por_bloque.csv`. Se actualizaron también las predicciones, métricas agregadas, tablas por año/mes/estación y figuras 2.3–2.4.

### Diseño de evaluación

- Se usan tres ventanas externas no solapadas para los tres objetivos: bloque 1, test 2010-01–2012-12; bloque 2, test 2013-01–2015-12; bloque 3, test 2016-01–2020-03.
- Cada bloque tiene una ventana interna de selección de tres años inmediatamente anterior al test: 2007–2009, 2010–2012 y 2013–2015, respectivamente. El ajuste usa solo datos anteriores a esa ventana; después de seleccionar el método/rezago, los parámetros se reajustan con todos los datos previos al test.
- Las ventanas de test no se solapan y las fechas finales observadas dependen de datos válidos: n de precipitación local–IMERG = 36, 36 y 51; n de caudal para cada predictor = 36, 28 y 51. Se mantuvieron casos completos, sin imputación.
- En cada partición se volvieron a estimar las climatologías y a seleccionar modelos y rezagos sin usar el bloque externo. El entrenamiento es expansivo: datos de un bloque previo pasan a formar parte del histórico disponible en los siguientes. Por ello, los bloques permiten comparar variación temporal, pero no son réplicas independientes.
- Los diagnósticos por año, mes calendario y estación ahora se producen dentro de cada bloque. `tabla_2_3_metricas_por_bloque.csv` compara sesgo, MAE y RMSE; las predicciones guardan `outer_fold`, fechas nominales del test y variante elegida.

### Resultados calculados

- **Lluvia local desde IMERG:** IMERG sin corrección obtuvo MAE/RMSE de 17.25/23.51, 18.96/25.14 y 18.84/32.58 mm/mes. La corrección seleccionada dentro de cada ajuste (lineal, log-lineal y lineal) obtuvo 21.94/31.79, 22.50/37.97 y 20.85/30.74 mm/mes. La corrección empeora MAE en los tres bloques y solo mejora RMSE en el tercero; no hay mejora consistente frente al producto sin corregir.
- **Caudal desde precipitación local:** los rezagos seleccionados fueron 6, 7 y 7 meses. Frente a la climatología mensual Q, cuyos MAE/RMSE fueron 50.76/64.97, 48.02/58.47 y 42.41/55.10 m3/s, el modelo de anomalías con rezago obtuvo 43.21/54.78, 38.44/48.54 y 38.04/48.80 m3/s. El sesgo fue positivo en los tres bloques: +42.90, +36.86 y +34.67 m3/s.
- **Caudal desde IMERG:** los rezagos seleccionados fueron 10, 7 y 7 meses. Frente a la misma referencia climatológica, el modelo de anomalías obtuvo MAE/RMSE de 49.25/64.06, 33.67/45.53 y 36.05/47.32 m3/s. El sesgo fue positivo: +48.16, +31.78 y +26.37 m3/s.
- Para ambos predictores de caudal, el modelo de anomalías con rezago redujo MAE y RMSE frente a la climatología mensual y a la regresión contemporánea en cada bloque. Esta consistencia es evidencia descriptiva de utilidad en las ventanas evaluadas; no establece causalidad ni desempeño fuera de esos periodos.
- No hubo predicciones negativas. Máximos predichos: 398.42 mm/mes para lluvia local corregida, 276.62 m3/s para caudal desde precipitación local y 263.62 m3/s para caudal desde IMERG. Revisar plausibilidad frente a observaciones antes de interpretarlos.

### Interpretación, límites y siguiente paso

- El punto 2.3 ya cuenta con comparación objetiva de estabilidad entre bloques, y las tablas mensual/estacional/anual no sustituyen esa comparación: son diagnósticos adicionales separados por bloque.
- Los modelos de caudal con rezago muestran mejoras de error frente a las referencias en las tres ventanas, pero mantienen sesgo positivo y el rezago seleccionado varía entre particiones. No interpretar los rezagos como tiempos físicos ni los bloques como independientes.
- La corrección de IMERG para estimar precipitación local no supera consistentemente la referencia sin corregir; no se recomienda afirmar que la corrección mejora el producto en general.
- Permanecen pendientes la revisión de predicciones máximas y la confirmación de la versión/corrida IMERG que generó el CSV, además de la trazabilidad de las fuentes pluviométricas.

## Registro B-20260930-07 — Auditoría empírica de máximos predichos

- Estado: REVISADO; magnitudes comparadas con observados y distribución de ajuste. No es certificación física independiente.
- Fecha: 2026-09-30.
- Responsable: Santiago Ortega — Rol B.
- Script actualizado: `scripts/06_modelos_validacion_temporal.py`.
- Evidencia reproducible: `figuras/tabla_2_3_maximos_predichos.csv`.

### Método de comprobación

- Para cada estrategia/modelo se tomó su mayor predicción externa y se recuperaron la fecha, el valor observado simultáneo, el error firmado, el máximo observado de ese mismo bloque y el P99/máximo del objetivo calculados solo con fechas anteriores al test.
- Se verificó que los tres bloques contuvieran las fechas asignadas, que el ajuste y la selección precedieran cada test y que las métricas por bloque coincidieran con las 936 predicciones individuales. Las aserciones dirigidas de los tres máximos pasaron.

### Resultados

- **Lluvia local desde IMERG:** máximo 398.422 mm/mes en 2015-08, bloque 2; observado simultáneo 240.486 mm/mes; error +157.936 mm/mes (+65.7%). El máximo observado en ese bloque fue 240.486 mm/mes. P99 del ajuste 509.645 mm/mes y máximo del ajuste 705.037 mm/mes. Cero predicciones negativas.
- **Caudal desde precipitación local:** máximo 276.618 m3/s en 2016-11, bloque 3; observado simultáneo 137.233 m3/s; error +139.385 m3/s (+101.6%). Máximo observado del bloque 186.000 m3/s; P99 del ajuste 410.385 m3/s y máximo 592.839 m3/s. Cero predicciones negativas.
- **Caudal desde IMERG:** máximo 263.624 m3/s en 2016-11, bloque 3; observado simultáneo 137.233 m3/s; error +126.391 m3/s (+92.1%). Máximo observado del bloque 186.000 m3/s; P99 y máximo del ajuste 410.385 y 592.839 m3/s. Cero predicciones negativas.
- En los tres casos, el máximo predicho está dentro del rango observado antes del test, por debajo del P99 de ajuste, pero supera el máximo observado de su bloque. Cada uno coincide con el mayor error absoluto de su respectivo bloque.

### Interpretación y límite

- No hay evidencia empírica de extrapolación extrema ni de imposibilidad física basada en el rango observado. Sí hay sobreestimaciones severas en las fechas señaladas: los valores son magnitudes históricamente posibles, pero no representan fielmente esos meses. No usar esta comparación como prueba de habilidad para eventos extremos.
- La revisión de plausibilidad empírica queda atendida. Sigue pendiente confirmar la versión/corrida que originó `P_IMERG_mm` y la trazabilidad de las fuentes pluviométricas; los datos disponibles tampoco establecen límites físicos independientes.

## Registro B-20260930-08 — Auditoría de procedencia de `P_IMERG_mm`

- Estado: INVESTIGACIÓN DOCUMENTAL COMPLETADA; producto/corrida exacta que originó el CSV no confirmada.
- Fecha: 2026-09-30.
- Responsable: Santiago Ortega — Rol B.

### Evidencia inspeccionada

- El script actual y el script del commit inicial seleccionan `NASA/GPM_L3/IMERG_MONTHLY_V06`, banda `precipitation`, descrita allí en mm/hr. Aplican media espacial sobre el polígono `camels_cl_5710001/polygon/polygon.shp` a escala 10000 m, fechas 2000-06-01 a 2020-04-01 (límite final exclusivo) y conversión a mm/mes multiplicando por las horas del mes.
- El script de integración lee `datos_satelitales_imerg_era5.csv`, convierte el índice a mes y cambia el nombre `PI_mm` a `P_IMERG_mm`; no incluye metadatos de producto ni altera numéricamente esta columna.
- El commit inicial `1a59662` contiene el maestro y el descargador configurado con V06. En contraste, la entrada #1 de `BITACORA_AGENTES.md` declara V07. No se encontró una versión V07 del script de descarga en el historial.
- Las dos revisiones históricas del CSV contienen 238 valores IMERG en fechas comunes; los 238 valores son numéricamente idénticos. La reorganización del CSV no cambió `P_IMERG_mm`.
- En el repositorio no están el CSV intermedio de satélite, el shapefile del polígono, un manifiesto, identificadores de imágenes/tarea de Earth Engine ni registros de ejecución. El CSV maestro tampoco incluye esos metadatos.

### Conclusión y acciones necesarias

- La procedencia exacta queda **no confirmada**. La evidencia de código apunta a V06 como configuración prevista, pero no prueba que esa exportación generó los valores; la declaración histórica V07 es contradictoria. No etiquetar la columna existente como V06 o V07 con certeza.
- Consultar a quien ejecutó Earth Engine por el CSV intermedio original, el historial del Code Editor o el registro/exportación de la tarea. Si no se conserva, acordar una versión canónica y regenerar la columna desde la geometría y el periodo documentados. Esa sería una nueva generación y no una confirmación retroactiva.
- Para cualquier nueva exportación, guardar como manifiesto colección/versión, banda, fechas, geometría y hash, reductor y escala, unidad original y conversión, fecha/proyecto de ejecución, identificadores de imágenes/tarea y hash del resultado.

## Registro B-20260930-09 — Plausibilidad del pico histórico Q desde IMERG

- Estado: REVISADO; reconstrucción numérica reproducida desde el CSV maestro y la especificación histórica. Plausibilidad evaluada contra observaciones, sin certificación física independiente.
- Fecha: 2026-09-30.
- Responsable: Santiago Ortega — Rol B.
- Configuración histórica: ajuste hasta 2015-12, test 2016-01–2020-03 (`n=51`), selección interna 2012-01–2015-12, rezago `k=8` seleccionado en tuning.

### Reconstrucción

- Fórmula almacenada: `Qhat(t) = climatología_Q(mes(t)) - 10.076085 + 0.538856 * anomalía_IMERG(t-8)`.
- La predicción máxima se reproduce en 2016-12 como `302.766 m3/s`. La climatología de diciembre del ajuste es `220.970 m3/s`.
- Predictor que entra en esa fecha: IMERG de 2016-04 = `197.997 mm/mes`; media de abril del ajuste = `27.502 mm/mes`; anomalía = `+170.495 mm/mes`. Intercepto más término de pendiente aportan `+81.796 m3/s`; sumados a la climatología se recupera `302.766 m3/s`.

### Comparación observacional

- Caudal observado en 2016-12 = `170.677 m3/s`: error predicho-observado `+132.089 m3/s`, un exceso de `77.4%` sobre lo medido (predicción/observado = `1.77`).
- El máximo observado en todo el test fue `186.000 m3/s` en 2017-01; P99 del test = `178.339 m3/s`. El pico predicho es `1.63` veces el máximo del test y lo supera en `116.766 m3/s`.
- Entre los 35 diciembres observados del ajuste: mediana `200.903 m3/s`, P90 `350.039`, P95 `369.110`, máximo `539.452 m3/s` (1982-12). El pico modelado está cerca del percentil empírico 74 de diciembres. En el conjunto de ajuste completo, P99 Q = `410.385 m3/s` y máximo = `592.839 m3/s`.
- Test sin predicciones negativas; sesgo global del modelo en esa prueba `+26.396 m3/s`, MAE `35.192 m3/s`, RMSE `49.120 m3/s`.

### Conclusión y límites

- `302.766 m3/s` está dentro del rango histórico de caudales de diciembre y bajo el P99 general del ajuste; no es una magnitud físicamente imposible según el registro disponible. No obstante, sobreestima marcadamente el caudal de diciembre de 2016 y queda por encima de todos los caudales observados del test. El contexto de los diciembres de 2016–2019 fue más seco que la climatología histórica.
- Conclusión defendible: magnitud plausible respecto del historial estacional, pero predicción deficiente para esa fecha y ese bloque; no es evidencia de capacidad para predecir máximos/crecidas. La respuesta al lag 8 es asociativa, no causal, y el modelo no impone un límite físico superior.
- El máximo de la evaluación multibloque actual es `263.624 m3/s` en 2016-11 porque el lag/ajuste se seleccionan por ventana. Es otro modelo evaluado; no reemplaza esta reconstrucción histórica de `302.766 m3/s`.

## Registro B-20260930-10 — Coordinación de climatología con el punto 1.5

- Estado: VENTANA DE ROL B VERIFICADA; acuerdo integrado con Rol A pendiente.
- Fecha: 2026-09-30.
- Responsable: Santiago Ortega — Rol B.

### Requisito y verificación

- La guía 1.5.a pide climatologías mensuales sobre un periodo común y los mismos pares válidos al comparar fuentes; 3.2 pide un periodo fijo, explícito y justificado para anomalías.
- El script `scripts/05_anomalias_rezagos.py` usa 2000-06 a 2020-03 para las cinco variables (`P_local_mm`, `P_IMERG_mm`, `Caudal_m3s`, `Q_lamina_mm`, `Temp_C`). La tabla `figuras/tabla_2_2_climatologia_referencia.csv` registra conteos, años válidos, medias, medianas y desviaciones estándar por mes.
- Verificación del CSV maestro: el intervalo contiene 238 meses; `P_local_mm` e `P_IMERG_mm` tienen las mismas fechas válidas en cada uno de los doce meses, con 238 pares y 19–20 años válidos por mes. La referencia de precipitación usada por Rol B coincide así con la muestra local–IMERG de la ventana común.
- El registro de Rol A sigue vacío y no se encontró tabla o figura del punto 1.5. No puede afirmarse que el equipo ya acordó esta referencia.

### Propuesta y siguiente paso

- Proponer 2000-06 a 2020-03 como referencia común integrada para comparar PL, PI, Q, R y temperatura y apoyar las anomalías de Rol B. Mantener la serie local completa para análisis de largo plazo; cualquier climatología local 1980–2020 adicional debe identificarse como ventana distinta y no confundirse con la comparación común que incluye PI.
- La tabla de Rol B no contiene cuartiles ni percentiles 10/90 exigidos por 1.5.a y no reemplaza el entregable completo de Rol A.
- Solicitar a Rol A/equipo confirmación de la ventana, y después verificar que sus tablas y figuras de 1.5 la usen. No se editó el archivo de Rol A ni se atribuyó al rol una decisión no registrada.