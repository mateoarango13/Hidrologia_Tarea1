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