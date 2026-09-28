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

## Registros siguientes

Copiar la plantilla de `00_INSTRUCCIONES.md` para cada análisis nuevo. No sobrescribir este registro: enlazarlo con un ID nuevo y conservar su estado exploratorio.