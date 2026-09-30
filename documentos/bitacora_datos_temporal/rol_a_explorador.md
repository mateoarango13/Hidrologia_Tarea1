# Registro del Rol A — Explorador
# Proyecto: Tarea 1 - Hidrología (UNAL) - Análisis Hidroclimático de Cuenca
# Cuenca Asignada: Río Maipo en El Manzano (Código CAMELS-CL: 5710001)

> **AVISO IMPORTANTE:** Esta carpeta `documentos/bitacora_datos_temporal/` es temporal y compartida entre los roles A, B, C y D. Toda la carpeta debe eliminarse completamente antes de la entrega final y verificarse que no se incluya en el archivo ZIP final.

---

## Registro A.1: Control de Calidad (QA/QC), Agregación Temporal y Mapa de Disponibilidad
- **Estado:** VALIDADO ✅
- **Responsable:** Mateo Arango — Rol A (Explorador)
- **Fecha:** 2026-09-30
- **Punto de la tarea:** Puntos 1.1, 1.2 y 1.4
- **Pregunta analizada:** ¿Cuál es la cobertura, integridad temporal, completitud de faltantes y validez física de las series mensuales integradas? ¿Es correcta la conversión de caudales a lámina equivalente?
- **Dataset/fuente y versión:** CAMELS-CL (Alvarez-Garreton et al., 2018) para caudal y precipitación local CR2MET v2.0; GPM IMERG Final Monthly V06 (`NASA/GPM_L3/IMERG_MONTHLY_V06`); ERA5-Land Monthly (`ECMWF/ERA5_LAND/MONTHLY_AGGR`).
- **Archivo y columnas usadas:** `datos/datos_mensuales_maipo.csv`: `date`, `P_local_mm`, `P_IMERG_mm`, `Caudal_m3s`, `Q_lamina_mm`, `Temp_C`.
- **Variables y unidades:** Precipitación ($P_L, P_I$) en $\text{mm/mes}$; Caudal ($Q$) en $\text{m}^3/\text{s}$; Escorrentía en lámina ($R$) en $\text{mm/mes}$; Temperatura ($T$) en $^{\circ}\text{C}$.
- **Periodo analizado:** 1980-01 a 2020-04 (484 meses / 40.3 años).
- **n válido y regla para formar pares:** Serie local completa preservada con outer join. $P_L$: 483 meses válidos; $Q$ y $R$: 470 meses válidos; $P_I$ y $T$: 238 meses válidos (2000-06 a 2020-03).
- **Faltantes/exclusiones y motivo:** 
  - $P_L$: 1 faltante en 2020-04 (0.21%).
  - $Q$ y $R$: 14 faltantes (2.89%), distribuidos en interrupciones menores de la estación DGA. Cumple holgadamente el criterio del $< 10\%$ de faltantes de la guía.
  - $P_I$ y $T$: 246 meses sin cobertura previa a junio de 2000 (inicio de la era satelital TRMM/GPM). No se imputaron datos; se trataron con casos válidos por análisis.
- **Método, fórmula y supuestos:**
  - Conversión de caudal a lámina equivalente:
    $$R_m = \frac{Q_m \times (n_m \times 86400)}{A \times 10^6} \times 1000 = \frac{86.4 \times n_m}{A} \times Q_m$$
    donde $A = 4837.4\text{ km}^2$ y $n_m$ es el número exacto de días del mes $m$.
- **Transformaciones/referencia climatológica:** No aplica para control de calidad.
- **Código/comando reproducible:** `scripts/07_rol_a_explorador.py` ejecutado con Python 3.9.
- **Archivos de salida:**
  - `figuras/figura_1_1_series_cronologicas.png` (Series completas alineadas a 300 DPI).
  - `figuras/figura_1_4_disponibilidad_temporal_heatmap.png` (Matriz año-mes de disponibilidad).
  - `figuras/tabla_1_3_control_calidad.csv` (Auditoría de consistencia).

#### Resultados calculados
- Duplicados de fecha: 0.
- Valores negativos imposibles ($P < 0$, $Q < 0$): 0.
- Verificación manual mes Mayo 1980: $Q = 117.1968\text{ m}^3/\text{s}$, $n = 31\text{ días}$, $A = 4837.4\text{ km}^2$.
  - $R_{\text{teórico}} = \frac{86.4 \times 31}{4837.4} \times 117.196774 = 64.868111\text{ mm/mes}$.
  - $R_{\text{CSV}} = 64.868111\text{ mm/mes}$.
  - Discrepancia absoluta: $< 10^{-6}\text{ mm/mes}$ (coincidencia analítica exacta).

#### Interpretación física
Las series temporales reflejan con alta fidelidad la dinámica de la cuenca: no existen saltos artificiales ni discontinuidades instrumentales. La temperatura ERA5-Land oscila entre $-11.9^{\circ}\text{C}$ en invierno y $+11.3^{\circ}\text{C}$ en verano, lo que concuerda con la elevación media de la cuenca ($3181\text{ m s.n.m.}$).

#### Incertidumbres y limitaciones
El registro satelital IMERG comienza en junio del año 2000, por lo que las comparaciones bi-producto se restringen a los 238 meses del periodo común (2000-06 a 2020-03).

---

## Registro A.2: Distribución Estadística Mensual, Histogramas y Diagramas de Caja
- **Estado:** VALIDADO ✅
- **Responsable:** Mateo Arango — Rol A (Explorador)
- **Fecha:** 2026-09-30
- **Punto de la tarea:** Punto 1.3
- **Pregunta analizada:** ¿Cuáles son las distribuciones de probabilidad, medidas de tendencia central, dispersión, asimetría y valores extremos de las variables hidroclimáticas?
- **Dataset/fuente y versión:** `datos/datos_mensuales_maipo.csv`.
- **Variables y unidades:** $P_L, P_I, R$ en $\text{mm/mes}$; $Q$ en $\text{m}^3/\text{s}$; $T$ en $^{\circ}\text{C}$.
- **Periodo analizado:** Comparación dual: Registro Completo Disponible (1980–2020) y Periodo Común (2000-06 a 2020-03).
- **Método, fórmula y supuestos:** Percentiles calculados mediante interpolación lineal continua (convención estándar de numpy/pandas). Bins idénticos ($25\text{ intervalos}$, ancho $26.4\text{ mm/mes}$) para comparar $P_L$ e $IMERG$ sobre los mismos 238 meses comunes. Diagramas de caja con bigotes a $1.5 \times \text{IQR}$ y marcador de media con diamante dorado.
- **Archivos de salida:**
  - `figuras/figura_1_2_histogramas_distribucion.png`
  - `figuras/figura_1_3_diagramas_caja.png`
  - `figuras/tabla_1_1_distribucion_estadistica.csv`
  - `figuras/tabla_1_2_meses_extremos.csv`

#### Resultados calculados
1. **Precipitación Local ($P_L$):**
   - Completo ($n=483$): Media $= 67.96\text{ mm}$, Mediana $= 25.85\text{ mm}$, Desv. Est. $= 101.20\text{ mm}$, Asimetría $= +2.80$, Curtosis $= 9.64$. Ceros: $4\text{ meses}$ ($0.83\%$).
   - Periodo común ($n=238$): Media $= 62.79\text{ mm}$, Mediana $= 25.56\text{ mm}$, Desv. Est. $= 92.29\text{ mm}$, Asimetría $= +2.87$, Curtosis $= 10.05$.
2. **Precipitación IMERG ($P_I$, $n=238$ común):**
   - Media $= 57.29\text{ mm}$, Mediana $= 32.76\text{ mm}$, Desv. Est. $= 58.70\text{ mm}$, Asimetría $= +1.89$, Curtosis $= 3.90$. Ceros: $0\text{ meses}$ ($0.0\%$, mínimo $= 2.83\text{ mm}$).
3. **Caudal Observado ($Q$ y $R$):**
   - $Q$ Completo ($n=470$): Media $= 112.48\text{ m}^3/\text{s}$, Mediana $= 87.06\text{ m}^3/\text{s}$, Max $= 592.84\text{ m}^3/\text{s}$, Asimetría $= +2.28$.
   - $R$ Completo ($n=470$): Media $= 61.06\text{ mm/mes}$, Mediana $= 47.28\text{ mm/mes}$, Max $= 328.13\text{ mm/mes}$.
4. **Temperatura ERA5-Land ($T$, $n=238$):**
   - Media $= -0.52^{\circ}\text{C}$, Mediana $= -1.04^{\circ}\text{C}$, Mínimo $= -11.89^{\circ}\text{C}$, Máximo $= +11.27^{\circ}\text{C}$, Asimetría $= +0.17$.
5. **Meses Extremos Históricos:**
   - Máximos de Lluvia Local: Junio 1982 ($705.0\text{ mm}$), Junio 2000 ($612.7\text{ mm}$), Julio 1987 ($609.4\text{ mm}$). Coinciden con eventos severos de El Niño Oscilación del Sur (ENSO).
   - Máximos de Caudal: Enero 1983 ($592.8\text{ m}^3/\text{s}$, $328.1\text{ mm}$) y Diciembre 1982 ($539.5\text{ m}^3/\text{s}$). Se presentan exactamente 6 meses después de la lluvia récord de junio 1982.
   - Mínimos de Caudal: Julio 2019 ($24.8\text{ m}^3/\text{s}$, $13.7\text{ mm}$), Junio 2019 ($28.8\text{ m}^3/\text{s}$) y Agosto 2019 ($31.2\text{ m}^3/\text{s}$), correspondientes al año pico hiperárido de la Megasequía de Chile central.

#### Interpretación física
- **Sesgo de media vs mediana:** En precipitación y caudal, la media supera con creces a la mediana ($\text{Media } P_L = 68\text{ mm}$ vs $\text{Mediana } 26\text{ mm}$), reflejando una fuerte asimetría positiva hacia la derecha gobernada por eventos extremos episódicos asociados a ríos atmosféricos y tormentas frontales invernales. La mediana es el estadístico más robusto para representar la condición mensual típica.
- **Diferencia entre $P_L$ e IMERG:** IMERG presenta una distribución más concentrada y con colas menos pesadas (desviación estándar de $58.7\text{ mm}$ frente a $92.3\text{ mm}$ de $P_L$; curtosis de $3.90$ vs $10.05$). IMERG sobreestima en meses de baja intensidad (no registra ningún valor de cero, mínimo $2.83\text{ mm}$) y subestima los picos frontales más intensos ($318\text{ mm}$ máximo en IMERG frente a $613\text{ mm}$ en $P_L$), un rasgo conocido de los algoritmos de microondas satelitales en terreno montañoso complejo (Rojas et al., 2021).

---

## Registro A.3: Climatología de 12 Meses, Régimen Pluvio-Nival y Estabilidad Temporal
- **Estado:** VALIDADO ✅
- **Responsable:** Mateo Arango — Rol A (Explorador)
- **Fecha:** 2026-09-30
- **Punto de la tarea:** Punto 1.5 (1.5.a, 1.5.b, 1.5.c)
- **Pregunta analizada:** ¿Cómo se comporta el ciclo anual medio de las variables? ¿Qué procesos físicos explican el desfase entre lluvia y caudal? ¿Es estable el régimen entre subperiodos frente a la Megasequía?
- **Dataset/fuente:** `datos/datos_mensuales_maipo.csv`.
- **Periodo analizado:** Periodo Común (2000-06 a 2020-03) para climatología comparada; Subperiodo 1 (1980–1999) vs Subperiodo 2 (2000–2020) para estabilidad temporal.
- **Método, fórmula e índices:** 
  - Climatología multianual de 12 meses (media, mediana, desv. est., $Q_1, Q_3$, P10, P90, CV).
  - Índice de Estacionalidad de Walsh & Lawler (1981):
    $$SI = \frac{1}{R_{\text{anual}}} \sum_{m=1}^{12} \left| x_m - \frac{R_{\text{anual}}}{12} \right|$$
- **Archivos de salida:**
  - `figuras/figura_1_5_ciclo_anual_climatologia.png`
  - `figuras/figura_1_6_curvas_anuales_individuales.png`
  - `figuras/figura_1_7_estabilidad_subperiodos.png`
  - `figuras/tabla_1_4_climatologia_mensual.csv`
  - `figuras/tabla_1_5_subperiodos_estabilidad.csv`
  - `figuras/tabla_1_6_sintesis_clasificacion.csv`

#### Resultados calculados
1. **Ciclo Anual de Precipitación ($P_L$):**
   - Mes pico: Junio ($168.08\text{ mm/mes}$, mediana $132.59\text{ mm/mes}$), seguido de Julio ($123.72\text{ mm}$) y Agosto ($118.28\text{ mm}$).
   - Mes mínimo: Marzo ($10.75\text{ mm/mes}$), seguido de Febrero ($12.28\text{ mm}$) y Enero ($13.41\text{ mm}$).
   - Amplitud del ciclo medio: $157.33\text{ mm/mes}$.
   - Índice de Estacionalidad de Walsh & Lawler: $SI_P = 0.774$ (régimen marcadamente estacional de invierno mediterráneo).
2. **Ciclo Anual de Caudal ($Q$ y $R$):**
   - Mes pico: Diciembre ($192.03\text{ m}^3/\text{s}$, $106.29\text{ mm/mes}$, mediana $145.66\text{ m}^3/\text{s}$), seguido de Enero ($177.99\text{ m}^3/\text{s}$, $98.52\text{ mm/mes}$).
   - Mes mínimo: Julio ($58.92\text{ m}^3/\text{s}$, $32.61\text{ mm/mes}$) y Junio ($60.98\text{ m}^3/\text{s}$, $32.66\text{ mm/mes}$).
   - Índice de Estacionalidad: $SI_R = 0.402$ (régimen estacional amortiguado por almacenamiento).
   - **Desfase Hidrológico:** 6 meses exactos entre el pico pluviométrico (junio) y el pico fluviométrico (diciembre).
3. **Ciclo Térmico ERA5-Land ($T$):**
   - Meses bajo cero ($T < 0^{\circ}\text{C}$): Mayo ($-4.30^{\circ}\text{C}$), Junio ($-7.78^{\circ}\text{C}$), Julio ($-8.44^{\circ}\text{C}$), Agosto ($-7.30^{\circ}\text{C}$), Septiembre ($-5.71^{\circ}\text{C}$), Octubre ($-2.89^{\circ}\text{C}$). Durante 6 meses consecutivos la cuenca promedia temperaturas bajo el punto de congelación.
   - Transición isotérmica: Noviembre ($+0.26^{\circ}\text{C}$) cruza la isoterma de $0^{\circ}\text{C}$, desatando el deshielo masivo.
   - Mes más cálido: Febrero ($+8.47^{\circ}\text{C}$) y Enero ($+8.28^{\circ}\text{C}$).
4. **Impacto de la Megasequía (1980–1999 vs 2000–2020):**
   - La escorrentía en lámina ($R$) disminuyó en **los 12 meses del año sin excepción**:
     - Enero: $-25.2\%$ ($-32.76\text{ mm/mes}$).
     - Febrero: $-23.7\%$ ($-20.66\text{ mm/mes}$).
     - Mayo: $-28.2\%$ ($-12.81\text{ mm/mes}$).
     - Diciembre: $-16.6\%$ ($-21.21\text{ mm/mes}$).
   - La precipitación invernal sufrió caídas de hasta $-34.9\%$ en abril, $-25.6\%$ en mayo, $-27.3\%$ en julio y $-31.3\%$ en septiembre.

#### Interpretación física y mecanismos
- **Control climático regional:** El clima de Chile central está regido por la oscilación estacional del Anticiclón Subtropical del Pacífico Suroriental (APSO). En verano, el APSO se ubica en latitudes más altas, bloqueando los frentes extratropicales y produciendo condiciones secas y despejadas. En invierno, el APSO migra hacia el ecuador, permitiendo la incursión de tormentas frontales del cinturón de oestes y ríos atmosféricos (Garreaud et al., 2017).
- **Proceso de transformación en la cuenca (Régimen Pluvio-Nival):** Con una cota media de $3181\text{ m s.n.m.}$ y alturas de hasta $6550\text{ m s.n.m.}$, el atributo CAMELS-CL indica que el **$70.9\%$ de la precipitación cae como nieve** en días fríos. La precipitación de invierno se almacena temporalmente como manto nival en la alta cordillera (retención criosférica). En primavera y verano (noviembre a enero), el incremento de radiación solar y la superación del umbral de $0^{\circ}\text{C}$ desencadenan el derretimiento de la nieve y el aporte glaciar ($7.18\%$ del área de la cuenca son glaciares), produciendo el caudal máximo en pleno verano seco.
- **Relación $R/P$:** El coeficiente anual multianual es de $\approx 0.89$, un valor muy elevado típico de cuencas de alta montaña donde la evapotranspiración real es limitada por temperaturas bajo cero la mayor parte del año y el balance recibe aportes de derretimiento de glaciares y permafrost.

---

## Registro A.4: Clasificación Hidroclimática Mensual Propuesta
- **Régimen Hidrológico:** Régimen Nivo-Pluvial de Alta Montaña Mediterránea.
- **Criterios Cuantitativos:**
  1. Fracción nival de precipitación: $70.9\% > 50\%$ (predominio nival).
  2. Desfase estacional: Pico pluviométrico en Junio vs Pico fluviométrico en Diciembre (desfase de 6 meses).
  3. Coeficiente de estacionalidad de precipitación: $SI_P = 0.77$ (invierno marcadamente húmedo).
  4. Duración de temporada fría bajo congelación: 6 meses ($T_{\text{media}} < 0^{\circ}\text{C}$ de mayo a octubre).
  5. Crecida estival: El caudal de diciembre-enero ($185\text{ m}^3/\text{s}$) triplica al estiaje invernal de junio-julio ($60\text{ m}^3/\text{s}$).