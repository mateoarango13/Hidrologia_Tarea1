# Registro del Rol C — Cazador de Tendencias

**Alcance del equipo:** puntos 3 y 4: tendencias hidroclimáticas, métodos lineales/no lineales y paramétricos/no paramétricos, variación por décadas y análisis espectral/Fourier. Registrar por separado series originales, anomalías y anomalías estandarizadas cuando corresponda.

**Estado inicial:** sin registros añadidos. Completar con evidencia propia; no inferir resultados a partir de este encabezado.

## Registros

Copiar la plantilla de `00_INSTRUCCIONES.md` para cada análisis. Informar periodo, cobertura y n válido por variable, supuestos, unidades del espectro, resolución temporal y ciclos observados. Diferenciar asociación exploratoria de tendencia y documentar cambios de fuente.
### Registro C.1 — Tendencias (puntos 3.2 a 3.5)
- Estado: REVISADO (pendiente verificación de referencias)
- Responsable: Tomás Gómez (con Claude Code)
- Fecha: 2026-10-04
- Punto de la tarea: 3.2, 3.3, 3.4, 3.5 (insumo de 3.6)
- Pregunta analizada: ¿qué variables cambian, cuánto, en qué meses y con qué robustez?
- Dataset/fuente y versión: `datos/datos_mensuales_maipo.csv` (CAMELS-CL; IMERG Final V06 según script 02; ERA5-Land)
- Archivo y columnas usadas: `P_local_mm`, `P_IMERG_mm`, `Caudal_m3s`, `Temp_C`
- Variables y unidades: mm/mes, mm/mes, m³/s, °C; pendientes por década
- Periodo analizado: registro completo por variable (P_L 1980-01/2020-03; Q 1980-01/2020-04; P_I y T 2000-06/2020-03) y periodo común 2000-06/2020-03
- n válido y regla para formar pares: 483 / 238 / 470 / 238 meses; subseries mensuales de 19–41 años
- Faltantes/exclusiones y motivo: 14 meses de Q sin rellenar (NaN); fechas reales como variable temporal
- Método, fórmula y supuestos: OLS (IC HAC Newey-West), OLS con efectos de mes, Kendall estacional + Sen estacional (p por bootstrap de bloques de 3 años), MK con Hamed-Rao + Theil-Sen, LOESS robusto, Pettitt, FDR Benjamini-Hochberg (α = 0.05)
- Transformaciones/referencia climatológica: a = X − μ_j, z = a/s_j; referencia fija 2000-06/2020-03
- Código/comando reproducible: `python scripts/09_p3_2_anomalias.py` → `10` → `11` → `12`
- Archivos de salida: `figuras/figura_3_*`, `figuras/tabla_3_*`, `figuras/serie_3_*`

#### Resultados calculados
- Q: −18.2 m³/s/déc [−26.7, −9.7] (OLS-HAC sobre a); Sen −14.9; 12/12 meses negativos y significativos tras FDR (OLS).
- P_L: −10.2 mm/mes/déc (p = 0.004) concentrado en may–jul; Sen estacional −1.1 (p = 0.08).
- P_I: −15.5 mm/mes/déc (OLS sobre a, p = 0.004). T: +0.28 °C/déc (p = 0.27).
- Hasta 2009 sin tendencia significativa en P_L ni Q; Pettitt 2007 (Q) / 2010 (P_L); ΔAIC tendencia–escalón ≈ 0.2.

#### Interpretación física
- El déficit de precipitación invernal se transfiere al caudal de todos los meses mediante el almacenamiento nival (máximo descenso en el deshielo de dic–ene).

#### Hipótesis por contrastar
- Memoria hidrológica (residuo −23 mm/año después de 2010), calentamiento, regulación de El Yeso y extracciones, artefacto del periodo e inhomogeneidad IMERG/CR2MET.

#### Incertidumbres y limitaciones
- 20 años para P_I y T; referencia seca que infla z antes de 2000; Q de mayo de 1993 (z = 16.5) por verificar; no se distingue tendencia de salto.

#### Referencias
- Ver bibliografía de `documentos/punto3_tendencias_analisis.tex` (pendiente de verificación).

#### Revisión
- Revisó: pendiente
- Cambios o preguntas pendientes: confirmar contexto de intervención (El Yeso, Alto Maipo) y versión de IMERG.

### Registro C.2 — Fourier (puntos 4.1 y 4.2)
- Estado: REVISADO (pendiente verificación de referencias)
- Responsable: Tomás Gómez (con Claude Code)
- Fecha: 2026-10-04
- Punto de la tarea: 4.1, 4.2
- Pregunta analizada: ¿en qué escalas se concentra la variabilidad y hay periodos dominantes?
- Dataset/fuente y versión: igual que C.1
- Archivo y columnas usadas: igual que C.1
- Variables y unidades: DEP unilateral [unidad]²/(ciclo/mes)
- Periodo analizado: 1980-04/2020-03 (N = 480; P_L, Q) y 2001-04/2020-03 (N = 228; las 4 variables)
- n válido y regla para formar pares: tramos de años hidrológicos completos, Δt = 1 mes, Δf = 1/N
- Faltantes/exclusiones y motivo: 14 (8 en el periodo común) meses de Q rellenados interpolando la anomalía; efecto evaluado con el tramo continuo 1990-12/2014-11 y Lomb-Scargle sin relleno
- Método, fórmula y supuestos: periodograma boxcar y Hann, Welch (Hann, 120 meses, 50 %); fondo AR(1) con umbrales 95 % puntual y global por Monte Carlo (1000 series)
- Transformaciones/referencia climatológica: C (centrada), A (anomalía centrada), AD (A sin tendencia lineal)
- Código/comando reproducible: `python scripts/13_p4_1_preparacion_espectral.py` → `14`
- Archivos de salida: `figuras/figura_4_*`, `figuras/tabla_4_*`, `figuras/serie_4_1_series_espectrales.csv`

#### Resultados calculados
- Fracción de varianza anual (C): T 0.93, P_I 0.55, Q 0.46, P_L 0.32. Parseval = 1.00.
- Anomalías: P_L r1 = 0.15 (casi blanco); Q r1 = 0.81, ~60 % de la varianza en T > 18 meses.
- Ningún pico interanual supera el umbral global AR(1); el periodo dominante cambia con el estimador (2.7 / 20 / 1.7 años).

#### Interpretación física
- La cuenca filtra la precipitación (pasa-bajos) por almacenamiento nival, glaciar y subterráneo.

#### Hipótesis por contrastar
- Vínculo de la banda de 2–7 años con ENSO (a evaluar en el punto 5); papel de la regulación en el enrojecimiento.

#### Incertidumbres y limitaciones
- Pocos ciclos en periodos largos; los espectros de potencia no dan la fase (el desfase viene de los puntos 1 y 2).

#### Referencias
- Ver bibliografía de `documentos/punto4_fourier_analisis.tex`.

#### Revisión
- Revisó: pendiente
- Cambios o preguntas pendientes: ninguna metodológica abierta.
