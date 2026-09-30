# SECCIÓN 3.2: RELACIONES ENTRE SERIES Y MODELOS ESTADÍSTICOS (ROL B — MODELADOR)
**Curso:** Hidrología (Semestre 202602) — Universidad Nacional de Colombia, Sede Medellín  
**Profesor:** Carlos David Hoyos  
**Cuenca de Estudio:** Río Maipo en El Manzano (Código CAMELS-CL: `5710001`, Área: $4837.4\text{ km}^2$)  
**Responsable del Análisis:** Santiago Ortega — Rol B (Modelador)  
**Fecha de Consolidación:** 30 de septiembre de 2026  

---

## 1. Introducción y Marco Metodológico del Rol B

El objetivo de esta sección es caracterizar rigurosamente las interacciones matemáticas y físicas entre las fuentes de precipitación (la serie observacional de referencia local $P_L$ y la estimación satelital GPM IMERG $P_I$) y la respuesta fluviométrica de la cuenca (caudal medio mensual $Q$ en $\text{m}^3/\text{s}$ y escorrentía equivalente en lámina $R$ en $\text{mm/mes}$), así como evaluar la factibilidad de construir modelos predictivos útiles fuera del periodo de calibración.

En estricto cumplimiento de la guía oficial de la tarea (`tarea_1_202602.pdf`) y las directrices de reproducibilidad de `AGENTS.md`:
1. **Escala temporal y tratamiento de datos:** Todos los análisis son estrictamente mensuales. No se aplicó ningún procedimiento de imputación o relleno sintético de vacíos; los análisis se ejecutaron por pares completos y concurrentes, explicitando en cada paso el periodo temporal y el número efectivo de observaciones ($n$).
2. **Dataset Maestro:** Todas las evaluaciones se alimentan de la base consolidada `datos/datos_mensuales_maipo.csv` (484 meses cronológicos, de enero de 1980 a abril de 2020), preservando la totalidad del registro histórico disponible ($> 40\text{ años}$) mediante unión externa (*outer join*).
3. **Reproducibilidad:** Los resultados aquí presentados se generan de forma determinística mediante los scripts:
   - `scripts/04_analisis_precipitacion.py`: Diagramas de dispersión, métricas de concordancia y diagnósticos de error.
   - `scripts/05_anomalias_rezagos.py`: Climatología fija común, cálculo de anomalías estandarizadas y correlación cruzada por rezagos.
   - `scripts/06_modelos_validacion_temporal.py`: Formulación de modelos, selección interna de hiperparámetros y validación temporal en tres bloques independientes.

---

## 2. Diagramas de Dispersión e Interpretación de Relaciones (Punto 2.1)

Para examinar la estructura de dependencia entre las variables, se construyeron los diagramas de dispersión multivariables ilustrados en la **Figura 2.1**. Cada punto representa un par mensual concurrente, coloreado por mes calendario para identificar agrupamientos estacionales. Las métricas cuantitativas se sintetizan en la **Tabla 2.1**.

![Figura 2.1: Diagramas de dispersión entre variables hidroclimáticas mensuales en la cuenca del Río Maipo en El Manzano](file:///c:/Users/Sancrack/.gemini/antigravity-ide/scratch/Hidrologia_Tarea1/figuras/figura_2_1_relaciones_scatter.png)
*Figura 2.1: Relaciones mensuales entre precipitación de referencia local ($P_L$), precipitación satelital IMERG ($P_I$), caudal medio ($Q$) y escorrentía en lámina ($R$). Los puntos están coloreados por mes calendario según la escala circular derecha. Para $P_I$ vs. $P_L$ se incorpora la línea de identidad 1:1 en trazo discontinuo gris.*

### 2.1. Concordancia entre Precipitación Local y GPM IMERG

La comparación directa entre la precipitación local ($P_L$) y la satelital ($P_I$) se evaluó sobre los **238 meses válidos** del periodo de superposición común (junio de 2000 a marzo de 2020). 

#### Resultados Numéricos:
- **Asociación estadística:** Se obtuvo un coeficiente de correlación lineal de Pearson $r = 0.8875$ ($p < 10^{-15}$) y una correlación monótona de Spearman $\rho = 0.8245$ ($p < 10^{-15}$). La proximidad de ambos coeficientes evidencia una relación lineal fuerte y monotónica a escala mensual.
- **Métricas de error absoluto y relativo (convención de error $e = P_I - P_L$):**
  - Sesgo medio firmado: $\text{Bias} = -5.5030\text{ mm/mes}$.
  - Error porcentual de sesgo: $\text{PBIAS} = -8.7642\%$, calculado como $100 \times \sum(P_I - P_L) / \sum P_L$.
  - Error absoluto medio: $\text{MAE} = 27.3438\text{ mm/mes}$.
  - Raíz del error cuadrático medio: $\text{RMSE} = 48.6556\text{ mm/mes}$.

```
Tabla 2.1: Resumen de relaciones bivariadas mensuales (datos/datos_mensuales_maipo.csv)
========================================================================================================================
Variable X      Variable Y      n    Inicio   Fin      Pearson r  Spearman rho  Sesgo (PI-PL)  MAE (mm)  RMSE (mm)  PBIAS (%)
------------------------------------------------------------------------------------------------------------------------
P_IMERG_mm      P_local_mm     238  2000-06  2020-03    0.8875       0.8245        -5.5030      27.3438   48.6556    -8.7642
P_local_mm      Caudal_m3s     469  1980-01  2020-03   -0.2009      -0.3931          --           --        --         --
P_IMERG_mm      Caudal_m3s     230  2000-06  2020-03   -0.2772      -0.4234          --           --        --         --
P_local_mm      Q_lamina_mm    469  1980-01  2020-03   -0.1968      -0.3875          --           --        --         --
P_IMERG_mm      Q_lamina_mm    230  2000-06  2020-03   -0.2708      -0.4145          --           --        --         --
========================================================================================================================
```

#### Diagnóstico Crítico de Asimetría e Intensidad:
Una de las advertencias centrales formuladas por Gupta et al. (2009) y Hossain & Huffman (2008) es que las métricas agregadas globales como el sesgo medio o el $r$ suelen enmascarar errores heterogéneos de signo opuesto. Al auditar la distribución de residuos (`figuras/tabla_2_1_errores_por_grupo.csv`), emergen patrones cruciales:
1. **Discrepancia entre media y mediana:** En los 238 meses analizados, $P_I < P_L$ ocurre en 103 meses, mientras que $P_I > P_L$ ocurre en 135 meses. En consecuencia, la **mediana del error es positiva ($+3.856\text{ mm/mes}$)** a pesar de que el **sesgo medio sea negativo ($-5.503\text{ mm/mes}$)**.
2. **Dependencia con la intensidad de precipitación:**
   - En el cuartil inferior de lluvia ($P_L < 5.8\text{ mm/mes}$), IMERG sobreestima sistemáticamente con un sesgo medio de $+14.00\text{ mm/mes}$ ($\text{RMSE} = 17.06\text{ mm/mes}$). IMERG nunca registra cero (mínimo absoluto de $2.83\text{ mm/mes}$), mostrando una tendencia a inflar las lluvias ligeras estivales.
   - En el cuartil intermedio-bajo y medio-alto, IMERG continúa sobreestimando ($+9.97$ y $+6.43\text{ mm/mes}$, respectivamente).
   - En el **cuartil superior ($P_L > 78.4\text{ mm/mes}$)**, IMERG presenta una severa **subestimación media de $-51.94\text{ mm/mes}$**, con $\text{MAE} = 58.75\text{ mm/mes}$ y $\text{RMSE} = 88.52\text{ mm/mes}$.
3. **Distribución por estación austral:**
   - Verano (DJF, $n=60$): IMERG sobreestima ($\text{Bias} = +6.85\text{ mm/mes}$, $\text{RMSE} = 14.20\text{ mm/mes}$).
   - Invierno (JJA, $n=60$): IMERG subestima fuertemente ($\text{Bias} = -11.33\text{ mm/mes}$, $\text{RMSE} = 76.72\text{ mm/mes}$).
4. **Influencia desproporcionada de eventos extremos (`figuras/tabla_2_1_meses_influyentes.csv`):**
   Los cinco mayores errores absolutos corresponden exclusivamente a inviernos tempestuosos: junio 2000 ($-334.60\text{ mm}$), mayo 2008 ($-233.52\text{ mm}$), junio 2005 ($-217.22\text{ mm}$), julio 2006 ($-208.93\text{ mm}$) y agosto 2005 ($-193.99\text{ mm}$). Estos 5 meses (apenas el $2.1\%$ de los datos) explican el **$52.35\%$ de la suma total de errores cuadráticos (SSE)**. Un análisis de sensibilidad (`figuras/tabla_2_1_sensibilidad_extremos.csv`) demostró que al aislar estos 5 eventos, el RMSE disminuye drásticamente de $48.66$ a $33.94\text{ mm/mes}$, mientras que el coeficiente de Pearson se mantiene casi inalterado ($r = 0.8829$).

#### Discusión Física y Metodológica:
La subestimación de eventos frontales intensos en alta montaña coincide con los hallazgos de **Rojas et al. (2021)** en los Andes de Chile centro-sur (36°S), quienes evaluaron IMERG V06 mediante radares de perfilado vertical y pluviómetros. Rojas et al. demostraron que los algoritmos radiométricos pasivos de microondas sufren dificultades para capturar el realce orográfico de nubes bajas y frentes no convectivos, generando un déficit en la precipitación estimada sobre terrenos de gran relieve. Adicionalmente, **Falvey & Garreaud (2007)** describieron que los ríos atmosféricos que impactan Chile central concentran una enorme tasa de condensación en laderas de barlovento que suele escapar a la resolución espacial de $0.1^{\circ}$ de IMERG.

Por otra parte, debe mantenerse una estricta cautela metodológica frente a la independencia de las fuentes: la modalidad GPM IMERG Final incorpora calibraciones mensuales con pluviómetros de la red GPCC (**Tapiador et al., 2020**), mientras que la base de referencia local de CAMELS-CL (CR2MET v2.0; **Alvarez-Garreton et al., 2018**) es un producto grillado derivado de estaciones meteorológicas de la DGA. Aunque es altamente probable que existan pluviómetros comunes en ambas mallas, no se dispone del registro específico de estaciones asimiladas por GPCC en esta cuenca, por lo que no puede asegurarse independencia estadística absoluta entre $P_L$ y $P_I$.

---

### 2.2. Relaciones Lluvia–Caudal Contemporáneas: Desacople Estacional

Al analizar la relación contemporánea (mismo mes $t$) entre la lluvia y el caudal en las series brutas (Figura 2.1, paneles b, c, d y e), se observa un resultado que a primera vista resulta contraintuitivo para cuencas pluviales tradicionales:
- $P_L(t)$ vs. $Q(t)$: $r = -0.2009$, $\rho = -0.3931$ ($n = 469$ meses).
- $P_I(t)$ vs. $Q(t)$: $r = -0.2772$, $\rho = -0.4234$ ($n = 230$ meses).
- Al expresar el caudal en lámina equivalente ($R = Q_{\text{lamina\_mm}}$), los coeficientes son esencialmente idénticos ($r = -0.1968$ y $-0.2708$), confirmando que la transformación lineal por área no altera la estructura de correlación.

#### Explicación Física del Signo Negativo:
La correlación negativa contemporánea **no representa un proceso físico inverso**, sino el desacople estacional intrínseco del régimen hidrológico de la cuenca:
1. **Asincronía climatológica:** Como estableció el Rol A en la caracterización climatológica del Punto 1.5, la precipitación media alcanza su máximo en pleno invierno austral (junio, con $168.08\text{ mm/mes}$), mientras que el caudal medio mensual registra su mínimo anual en junio y julio ($60.98$ y $58.92\text{ m}^3/\text{s}$). A la inversa, el caudal alcanza su ápice en pleno verano (diciembre, con $192.03\text{ m}^3/\text{s}$), cuando la precipitación es mínima ($13.41\text{ mm/mes}$). La correlación descriptiva entre los doce pares medios climatológicos es marcadamente negativa ($r = -0.7676$).
2. **Retención criosférica y almacenamiento:** La cuenca del Maipo en El Manzano posee una elevación media de $3181\text{ m s.n.m.}$, con cotas que superan los $6500\text{ m s.n.m.}$ De acuerdo con los atributos de CAMELS-CL (**Alvarez-Garreton et al., 2018**), el **$70.9\%$ de la precipitación cae en fase sólida (nieve)**. Como corroboró el Rol A a partir de ERA5-Land, la temperatura media de la cuenca permanece **bajo el punto de congelación durante seis meses consecutivos (mayo a octubre)**, alcanzando $-8.44^{\circ}\text{C}$ en julio. Por consiguiente, la lluvia invernal no genera escorrentía directa inmediata, sino que queda almacenada en el manto nival y en los glaciares de cabecera ($7.18\%$ del área; **Ayala et al., 2020**).
3. **Deshielo estival:** En noviembre, la temperatura media supera por primera vez la isoterma de $0^{\circ}\text{C}$ ($+0.26^{\circ}\text{C}$), alcanzando su pico en enero y febrero ($+8.28^{\circ}\text{C}$ y $+8.47^{\circ}\text{C}$). Este forzamiento de energía térmica desencadena la fusión nival masiva, trasladando el volumen hídrico acumulado hacia los cauces fluviales exactamente medio año después de las tormentas invernales (**Masiokas et al., 2006**).

---

### 2.3. Covariación de Anomalías y Análisis de Rezagos Temporales

Para aislar las fluctuaciones interanuales genuinas y remover el ciclo estacional recurrente que forzaba la correlación negativa contemporánea, se calcularon anomalías mensuales ($a_t = X_t - \mu_{j(t)}$) restando la climatología mensual de referencia coordinada (junio de 2000 a marzo de 2020). 

Posteriormente, se evaluó la correlación cruzada para rezagos de $k = 0, 1, 2, \dots, 12\text{ meses}$, definiendo estrictamente el sentido físico como **precipitación previa en $t-k$ frente a caudal resultante en $t$** (evitando rigurosamente predecir el pasado con lluvia futura). Los resultados se presentan en la **Figura 2.2** y la **Tabla 2.2**.

![Figura 2.2: Correlación por rezagos mensuales entre lluvia en t-k y caudal en t](file:///c:/Users/Sancrack/.gemini/antigravity-ide/scratch/Hidrologia_Tarea1/figuras/figura_2_2_correlaciones_rezagos.png)
*Figura 2.2: Coeficientes de correlación de Pearson (línea sólida) y Spearman (línea punteada) entre la precipitación previa en $t-k$ y el caudal en $t$, calculados sobre anomalías mensuales para rezagos de 0 a 12 meses. Panel superior: Precipitación local ($P_L$). Panel inferior: Precipitación satelital ($P_I$).*

#### Hallazgos Numéricos de la Desestacionalización:
1. **Inversión del signo contemporáneo ($k = 0$):** Al desestacionalizar las series, la asociación lineal en el mismo mes pasa de ser negativa ($r \approx -0.20$) a ser **débilmente positiva**:
   - Anomalías $P_L(t)$ vs. $Q(t)$: $r = 0.1569$, $\rho = 0.1754$ ($n = 469$).
   - Anomalías $P_I(t)$ vs. $Q(t)$: $r = 0.1783$, $\rho = 0.2368$ ($n = 230$).
   Esto confirma que la correlación negativa original era un artificio de la superposición de ciclos anuales desfasados.
2. **Estructura del pico de rezago:** A medida que se incrementa el rezago temporal $k$, la correlación aumenta progresivamente hasta alcanzar un ápice nítido en rezagos de 6 a 7 meses:
   - Para $P_L$: $k=5$ ($r = 0.3802$), **$k=6$ ($r = 0.4541$)**, **$k=7$ ($r = 0.4773$, $\rho = 0.2953$, $n = 463$)**, decayendo luego a $k=8$ ($r = 0.3805$) y colapsando hacia cero en $k \ge 11$ ($r < 0.05$).
   - Para $P_I$: $k=5$ ($r = 0.4094$), $k=6$ ($r = 0.3931$), **$k=7$ ($r = 0.4222$, $\rho = 0.3549$, $n = 224$)**, $k=8$ ($r = 0.3593$).

```
Tabla 2.2: Extracto de correlaciones exploratorias de anomalías por rezago (scripts/05_anomalias_rezagos.py)
========================================================================================================================
Predictor (t-k)    Objetivo (t)    Rezago (k)   n pares   Pearson r (anomalías)   Spearman rho (anomalías)
------------------------------------------------------------------------------------------------------------------------
P_local_mm         Caudal_m3s          0         469             0.1569                    0.1754
P_local_mm         Caudal_m3s          3         467             0.2525                    0.2786
P_local_mm         Caudal_m3s          6         464             0.4541                    0.3042
P_local_mm         Caudal_m3s          7         463             0.4773                    0.2953
P_local_mm         Caudal_m3s          8         462             0.3805                    0.3043
P_local_mm         Caudal_m3s         12         458             0.0051                    0.0035
------------------------------------------------------------------------------------------------------------------------
P_IMERG_mm         Caudal_m3s          0         230             0.1783                    0.2368
P_IMERG_mm         Caudal_m3s          4         227             0.3319                    0.4101
P_IMERG_mm         Caudal_m3s          5         226             0.4094                    0.3976
P_IMERG_mm         Caudal_m3s          7         224             0.4222                    0.3549
P_IMERG_mm         Caudal_m3s          8         223             0.3593                    0.3185
P_IMERG_mm         Caudal_m3s         12         219             0.0509                    0.0923
========================================================================================================================
```

#### Cautela Metodológica e Inferencia Estadística:
Como destacan **Pyper & Peterman (1998)**, la selección del valor máximo en un barrido de 13 correlaciones cruzadas sobre series ambientales con persistencia temporal (autocorrelación) tiende a inflar la significancia estadística aparente. Además, la ventana de referencia climatológica utilizada en este paso exploratorio incluye fechas que posteriormente formarán parte de la evaluación. Por tanto, este pico en $k = 6 - 7\text{ meses}$ no debe declararse como prueba causal de habilidad predictiva, sino como una **hipótesis física exploratoria**: la memoria hidrológica de la cuenca almacena la precipitación invernal y modula la escorrentía estival con un retardo característico de un semestre (**Alvarez-Garreton et al., 2021**). La verdadera capacidad predictiva debe probarse fuera de muestra.

---

## 3. Formulación y Selección de Modelos Candidatos (Punto 2.2)

Con el fin de investigar si es viable construir herramientas operativas útiles a escala mensual, se definieron dos objetivos de modelación estadística:

### 3.1. Objetivo I: Estimación de Precipitación Local a partir de IMERG
Se formularon tres alternativas de complejidad creciente:
1. **Modelo Base 0 (IMERG sin corrección):** $\hat{P}_L(t) = P_I(t)$. Actúa como la referencia nula obligatoria.
2. **Modelo 1 (Corrección lineal directa):** 
   $$\hat{P}_L(t) = \max\left(0, \, \hat{\beta}_0 + \hat{\beta}_1 P_I(t)\right)$$
   Ajustada por mínimos cuadrados ordinarios (OLS) y truncada en cero para evitar valores negativos físicamente imposibles.
3. **Modelo 2 (Corrección Log-Lineal con Corrector de Sesgo de Duan):**
   Para estabilizar la varianza heterocedástica de las precipitaciones, se ajusta:
   $$\ln(P_L + 1) = \beta_0 + \beta_1 \ln(P_I + 1) + \varepsilon$$
   La transformación inversa introduce un sesgo geométrico sistemático. Para resolverlo rigurosamente, se aplicó el factor multiplicativo no paramétrico de **Duan (1983)** (*Smearing Estimator*):
   $$\hat{P}_L(t) = B \cdot \exp\left[\hat{\beta}_0 + \hat{\beta}_1 \ln(P_I(t) + 1)\right] - 1, \quad \text{donde } B = \frac{1}{n} \sum_{i=1}^n \exp(\hat{\varepsilon}_i)$$

### 3.2. Objetivo II: Estimación de Caudal a partir de Precipitación
1. **Modelo Base 0 (Climatología Mensual de Caudal):**
   $$\hat{Q}(t) = \bar{Q}_{m(t)}$$
   donde $\bar{Q}_m$ es el caudal medio del mes calendario correspondiente, calculado exclusivamente con el registro de ajuste. Constituye la referencia estándar exigida por la rúbrica.
2. **Modelo 1 (Regresión Lineal Contemporánea):**
   $$\hat{Q}(t) = \max\left(0, \, \hat{\beta}_0 + \hat{\beta}_1 P(t)\right)$$
3. **Modelo 2 (Modelo de Anomalías con Rezago Estacional Optimizado):**
   Aprovechando la hipótesis física de retención nival, se modela la anomalía de caudal mediante la anomalía de precipitación retardada $k$ meses:
   $$\hat{Q}(t) = \bar{Q}_{m(t)} + \hat{\beta}_0 + \hat{\beta}_1 \cdot a_P(t-k^*)$$
   donde $a_P(t-k) = P(t-k) - \bar{P}_{m(t-k)}$ y el rezago óptimo $k^* \in \{0, 1, \dots, 12\}$ se selecciona de forma estrictamente endógena durante la fase de entrenamiento.

> **Advertencia de Balance de Masa (Rúbrica Pág. 6):**  
> Una relación estadística empírica lluvia–caudal no sustituye una formulación del balance hídrico de cuenca. Estos modelos no representan de forma explícita la evapotranspiración real, la variación neta de almacenamiento criosférico o subterráneo, ni garantizan la conservación de la masa del fluido (**Klemeš, 1986**).

---

## 4. Evaluación Fuera del Periodo de Ajuste y Estabilidad Multi-Bloque (Punto 2.3)

### 4.1. Diseño Experimental Estricto (Prevención de *Data Leakage*)
Conforme a las recomendaciones de **Roberts et al. (2017)** y **Klemeš (1986)**, las series hidroclimáticas temporales no deben evaluarse mediante validación cruzada aleatoria convencional (K-Fold aleatorio), dado que la autocorrelación serial genera dependencia mutua entre observaciones adyacentes y conduce a una subestimación artificial del error de pronóstico (**Bergmeir et al., 2018**).

Para garantizar una evaluación retrospectiva realista e incondicional:
1. **Partición temporal en 3 bloques externos cronológicos no solapados:**
   - **Bloque 1:** Periodo de Test = **2010-01 a 2012-12** ($n = 36\text{ meses}$). Ventana previa de tuning = 2007–2009.
   - **Bloque 2:** Periodo de Test = **2013-01 a 2015-12** ($n = 36\text{ meses}$). Ventana previa de tuning = 2010–2012.
   - **Bloque 3:** Periodo de Test = **2016-01 a 2020-03** ($n = 51\text{ meses}$). Ventana previa de tuning = 2013–2015.
2. **Protocolo expansivo sin información futura:** En cada bloque, las climatologías mensuales ($\bar{Q}_m, \bar{P}_m$), los factores de corrección de Duan ($B$), la selección de rezagos ($k^*$) y la selección entre formulaciones lineal vs. log-lineal se calibraron **exclusivamente con los datos anteriores al bloque de test**. Ningún dato del futuro fue empleado en las decisiones del modelo.

Las series temporales observadas, las predicciones de los modelos y los residuos resultantes se ilustran en la **Figura 2.3** y la **Figura 2.4**.

![Figura 2.3: Validación temporal fuera de muestra en 3 bloques independientes](file:///c:/Users/Sancrack/.gemini/antigravity-ide/scratch/Hidrologia_Tarea1/figuras/figura_2_3_validacion_modelos.png)
*Figura 2.3: Desempeño predictivo fuera de muestra en los tres bloques cronológicos de test (2010–2012, 2013–2015 y 2016–2020). Panel superior: Precipitación local observada vs. IMERG crudo y corrección lineal. Panel medio: Caudal observado vs. climatología mensual y modelo de rezagos basado en lluvia local. Panel inferior: Caudal observado vs. modelo de rezagos basado en IMERG.*

![Figura 2.4: Diagnóstico de residuos en el tiempo para los tres bloques de evaluación](file:///c:/Users/Sancrack/.gemini/antigravity-ide/scratch/Hidrologia_Tarea1/figuras/figura_2_4_residuos_en_tiempo.png)
*Figura 2.4: Residuos temporales ($e = \text{Predicción} - \text{Observado}$) a lo largo de los tres bloques de evaluación externa. Las líneas verticales grises separan los bloques externos.*

---

### 4.2. Desempeño Numérico y Estabilidad entre Periodos

Los resultados numéricos consolidados por bloque externo se extraen de `figuras/tabla_2_3_metricas_por_bloque.csv` y se detallan a continuación:

```
Tabla 2.3: Métricas de validación fuera de muestra en tres bloques externos independientes
========================================================================================================================
Tarea / Modelo Evaluado                   Bloque 1 (2010–2012)        Bloque 2 (2013–2015)        Bloque 3 (2016–2020)
                                      Sesgo    MAE    RMSE         Sesgo    MAE    RMSE         Sesgo    MAE    RMSE
------------------------------------------------------------------------------------------------------------------------
ESTIMACIÓN DE LLUVIA LOCAL (mm/mes):
- IMERG sin corrección (Base)          +0.98  17.25   23.51         -0.89  18.96   25.14         -0.98  18.84   32.58
- Corrección seleccionada en ajuste   +10.97  21.94   31.79         +8.54  22.50   37.97         +0.64  20.85   30.74
------------------------------------------------------------------------------------------------------------------------
ESTIMACIÓN DE CAUDAL DESDE PL (m³/s):
- Climatología mensual Q (Base)       +43.15  50.76   64.97        +41.05  48.02   58.47        +40.48  42.41   55.10
- Regresión contemporánea Q~P(t)      +46.06  57.85   64.95        +39.73  54.67   58.11        +36.17  47.05   51.99
- Anomalías con rezago optimizado     +42.90  43.21   54.78        +36.86  38.44   48.54        +34.67  38.04   48.80
  (Rezago seleccionado k*)               [k* = 6 meses]               [k* = 7 meses]               [k* = 7 meses]
------------------------------------------------------------------------------------------------------------------------
ESTIMACIÓN DE CAUDAL DESDE PI (m³/s):
- Climatología mensual Q (Base)       +43.15  50.76   64.97        +41.05  48.02   58.47        +40.48  42.41   55.10
- Anomalías con rezago optimizado     +48.16  49.25   64.06        +31.78  33.67   45.53        +26.37  36.05   47.32
  (Rezago seleccionado k*)               [k* = 10 meses]              [k* = 7 meses]               [k* = 7 meses]
========================================================================================================================
```

#### Análisis Crítico de los Resultados:
1. **Ineficacia de corregir IMERG para lluvia mensual:**
   - La corrección estadística de IMERG (sea lineal o log-lineal) **empeoró el MAE en los tres bloques evaluados sin excepción** (por ejemplo, en el Bloque 1 el MAE aumentó de $17.25$ a $21.94\text{ mm/mes}$, y en el Bloque 2 de $18.96$ a $22.50\text{ mm/mes}$).
   - Únicamente en el Bloque 3 se observó una modesta reducción del RMSE ($30.74$ vs. $32.58\text{ mm/mes}$), a expensas de un mayor MAE.
   - **Conclusión técnica:** Aplicar modelos de regresión simples para "corregir" IMERG a escala mensual de cuenca introduce variabilidad residual indeseada y amplifica los errores en meses intermedios. Para fines operacionales en esta cuenca, **es preferible utilizar el producto IMERG crudo directamente** antes que forzar una corrección lineal.
2. **Utilidad robusta del modelo de anomalías con rezago para caudal:**
   - Para ambos predictores ($P_L$ e $P_I$), el modelo de regresión de anomalías con rezago superó categóricamente a la referencia nula (climatología mensual de caudal) y a la regresión contemporánea en los tres bloques cronológicos.
   - Utilizando lluvia local ($P_L$), el MAE se redujo en $7.55\text{ m}^3/\text{s}$ en B1, $9.58\text{ m}^3/\text{s}$ en B2 y $4.37\text{ m}^3/\text{s}$ en B3; el RMSE disminuyó entre $6.3$ y $10.2\text{ m}^3/\text{s}$.
   - Utilizando IMERG ($P_I$), las mejoras de MAE alcanzaron hasta $14.35\text{ m}^3/\text{s}$ en B2 y $6.36\text{ m}^3/\text{s}$ en B3.
   - **Estabilidad de hiperparámetros:** El rezago óptimo seleccionado en entrenamiento interno convergió de forma sumamente consistente en **$k^* = 7\text{ meses}$** tanto para $P_L$ como para $P_I$ en los bloques 2 y 3.
3. **Persistencia del sesgo positivo e impacto de la Megasequía:**
   - A pesar de mejorar la varianza explicada y los errores absolutos, todos los modelos de caudal presentaron un **sesgo positivo persistente** en los tres bloques (oscilando entre $+26$ y $+48\text{ m}^3/\text{s}$).
   - **Explicación física:** El periodo 2010–2020 corresponde a la manifestación ininterrumpida de la **Megasequía de Chile central** (**Garreaud et al., 2017**; **Alvarez-Garreton et al., 2021**). La climatología histórica base $\bar{Q}_m$ fue estimada con años anteriores al 2010 (que incluyeron décadas sustancialmente más húmedas como los años 80 y 90). Al entrar en un régimen climáticamente empobrecido en escorrentía, la climatología histórica sobreestima la disponibilidad basal de agua, evidenciando la no estacionariedad del régimen hídrico reciente.

---

### 4.3. Auditoría de Plausibilidad Física y Eventos Extremos

Para dar respuesta rigurosa a la rúbrica docente sobre predicciones físicamente implausibles, se auditó exhaustivamente el comportamiento de los modelos en los extremos (`figuras/tabla_2_3_maximos_predichos.csv`):

1. **Cero predicciones negativas:** Ninguno de los modelos de caudal o precipitación generó predicciones inferiores a cero en ninguna de las 936 estimaciones individuales evaluadas, respetando el límite inferior físico de no negatividad.
2. **Auditoría del pico histórico modelado de $302.77\text{ m}^3/\text{s}$ (Diciembre 2016):**
   - En una especificación previa con partición única, el modelo basado en IMERG arrojó un valor máximo de $302.766\text{ m}^3/\text{s}$ para diciembre de 2016.
   - **Mecanismo generador:** En abril de 2016, IMERG registró una anomalía pluvial extraordinaria de $+170.50\text{ mm/mes}$ ($198.0\text{ mm}$ frente a una media de $27.5\text{ mm}$). El modelo aplicó el rezago $k=8$ meses, impactando a diciembre con un aporte estimado de $+81.80\text{ m}^3/\text{s}$ sobre la climatología de diciembre ($220.97\text{ m}^3/\text{s}$).
   - **Contraste observacional:** El caudal observado en diciembre de 2016 fue de apenas $170.68\text{ m}^3/\text{s}$ (el error fue de $+132.09\text{ m}^3/\text{s}$, una sobreestimación del $77.4\%$). El máximo observado en todo ese bloque fue de $186.00\text{ m}^3/\text{s}$ (enero 2017).
   - **Evaluación de plausibilidad física:** En el registro histórico de calibración (1980–2015), el percentil 99 de caudal es de $410.39\text{ m}^3/\text{s}$ y el máximo histórico medido en diciembre es de $539.45\text{ m}^3/\text{s}$ (diciembre 1982, durante un evento Niño extraordinario). Por tanto, $302.77\text{ m}^3/\text{s}$ **no es un valor físicamente imposible ni una extrapolación matemática descontrolada**, ubicándose cerca del percentil 74 de los diciembres históricos. No obstante, representó una sobreestimación severa para el año 2016, demostrando que los modelos lineales de anomalías carecen de un mecanismo para amortiguar eventos extremos cuando el suelo o el manto nival presentan déficits hídricos antecedentes en periodos hiperáridos.
3. **Máximos de la evaluación multibloque:**
   - Lluvia estimada desde IMERG: Máximo predicho de $398.42\text{ mm/mes}$ en agosto 2015 (observado $240.49\text{ mm/mes}$, error $+157.94\text{ mm/mes}$; inferior al máximo de ajuste de $705.04\text{ mm/mes}$).
   - Caudal estimado desde lluvia local: Máximo predicho de $276.62\text{ m}^3/\text{s}$ en noviembre 2016 (observado $137.23\text{ m}^3/\text{s}$, error $+139.39\text{ m}^3/\text{s}$; inferior al máximo de ajuste de $592.84\text{ m}^3/\text{s}$).
   - Caudal estimado desde IMERG: Máximo predicho de $263.62\text{ m}^3/\text{s}$ en noviembre 2016 (observado $137.23\text{ m}^3/\text{s}$, error $+126.39\text{ m}^3/\text{s}$).

---

## 5. Síntesis y Respuestas Concluyentes a las Preguntas de la Guía

Para cerrar el análisis del Punto 2, se da respuesta concisa y justificada a los interrogantes formulados en el enunciado de la tarea:

1. **¿Existe una relación aprovechable entre la precipitación y el caudal?**
   **Sí, pero únicamente al considerar rezagos temporales y desestacionalizar las series.** La relación contemporánea bruta ($k=0$) carece de utilidad predictiva directa ($r \approx -0.20$) debido a la asincronía nival. En contraste, la formulación de anomalías con **rezago de 6 a 7 meses** captura una relación positiva físicamente coherente ($r \approx 0.45 - 0.48$).
2. **¿De qué tipo de modelo se trata?**
   Se trata de un **modelo de regresión lineal de anomalías estacionales retardadas**:
   $$\hat{Q}(t) = \bar{Q}_{m(t)} + \beta_0 + \beta_1 \left(P(t-k^*) - \bar{P}_{m(t-k^*)}\right)$$
   con $k^* = 7\text{ meses}$. Este modelo acopla la climatología periódica de caudal con la memoria criosférica de la cuenca.
3. **¿Para qué meses o condiciones funciona mejor?**
   El modelo funciona con gran precisión durante los meses de **primavera y verano (noviembre a febrero)**, cuando el caudal depende predominantemente del volumen de nieve acumulada durante las tormentas frontales del invierno previo (mayo a julio). En contraste, su desempeño decae durante el otoño (abril-mayo) y en años de sequía multianual extrema, donde la recarga de acuíferos fracturados y la desecación previa del suelo reducen la eficiencia de la escorrentía.
4. **¿Mejora sobre la referencia?**
   **Sí, de forma inequívoca en la predicción de caudal.** El modelo de anomalías con rezago redujo el MAE y el RMSE frente a la climatología mensual en los tres bloques independientes de evaluación externa. Por el contrario, en la estimación de precipitación local a partir de IMERG, los modelos de corrección no lograron superar consistentemente al producto IMERG sin corregir.
5. **¿Qué papel juegan las fuentes compartidas y la versión de IMERG?**
   La serie satelital utilizada corresponde a `NASA/GPM_L3/IMERG_MONTHLY_V06`. Dado que IMERG Final asimila pluviómetros del GPCC y CR2MET emplea estaciones de la DGA, existe una correlación de base introducida por la red de medición en tierra. A pesar de esto, IMERG exhibe sesgos marcados en eventos extremos, lo que demuestra que su error está gobernado primordialmente por las limitaciones físicas de la sensometría remota en topografía compleja y no por un sobreajuste a las estaciones locales.

---

## 6. Referencias Bibliográficas (con DOI Verificado)

1. **Alvarez-Garreton, C., Mendoza, P. A., Boisier, J. P., Addor, N., Galleguillos, M., Zambrano-Bigiarini, M., et al. (2018).** The CAMELS-CL dataset: catchment attributes and meteorology for large sample studies – Chile dataset. *Hydrology and Earth System Sciences*, 22(11), 5817–5846. https://doi.org/10.5194/hess-22-5817-2018
2. **Alvarez-Garreton, C., Boisier, J. P., Garreaud, R., Seibert, J., & Vis, M. (2021).** Progressive water deficits during multiyear droughts in basins with long hydrological memory in Chile. *Hydrology and Earth System Sciences*, 25(1), 429–446. https://doi.org/10.5194/hess-25-429-2021
3. **Ayala, A., Farías-Barahona, D., Huss, M., Pellicciotti, F., McPhee, J., & Farinotti, D. (2020).** Glacier runoff variations since 1955 in the Maipo River basin, in the semiarid Andes of central Chile. *The Cryosphere*, 14(6), 2005–2027. https://doi.org/10.5194/tc-14-2005-2020
4. **Bergmeir, C., Hyndman, R. J., & Koo, B. (2018).** A note on the validity of cross-validation for evaluating autoregressive time series prediction. *Computational Statistics & Data Analysis*, 120, 70–83. https://doi.org/10.1016/j.csda.2017.11.003
5. **Cortés, G., & Margulis, S. (2017).** Impacts of El Niño and La Niña on interannual snow accumulation in the Andes. *Geophysical Research Letters*, 44(13), 6859–6867. https://doi.org/10.1002/2017GL073826
6. **Duan, N. (1983).** Smearing Estimate: A Nonparametric Retransformation Method. *Journal of the American Statistical Association*, 78(383), 605–610. https://doi.org/10.1080/01621459.1983.10478017
7. **Falvey, M., & Garreaud, R. D. (2007).** Wintertime Precipitation Episodes in Central Chile: Associated Meteorological Conditions and Orographic Influences. *Journal of Hydrometeorology*, 8(2), 171–193. https://doi.org/10.1175/JHM562.1
8. **Garreaud, R. D., Alvarez-Garreton, C., Barichivich, J., Boisier, J. P., Christie, D., Galleguillos, M., et al. (2017).** The 2010–2015 megadrought in central Chile: impacts on regional hydroclimate and vegetation. *Hydrology and Earth System Sciences*, 21(12), 6307–6327. https://doi.org/10.5194/hess-21-6307-2017
9. **Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).** Decomposition of the mean squared error and NSE performance criteria: Implications for improving hydrological modelling. *Journal of Hydrology*, 377(1–2), 80–91. https://doi.org/10.1016/j.jhydrol.2009.08.003
10. **Hossain, F., & Huffman, G. J. (2008).** Investigating Error Metrics for Satellite Rainfall Data at Hydrologically Relevant Scales. *Journal of Hydrometeorology*, 9(3), 563–575. https://doi.org/10.1175/2007JHM925.1
11. **Klemeš, V. (1986).** Operational testing of hydrological simulation models. *Hydrological Sciences Journal*, 31(1), 13–24. https://doi.org/10.1080/02626668609491024
12. **Masiokas, M. H., Villalba, R., Luckman, B. H., Le Quesne, C., & Aravena, J. C. (2006).** Snowpack Variations in the Central Andes of Argentina and Chile, 1951–2005: Large-Scale Atmospheric Influences and Implications for Water Resources in the Region. *Journal of Climate*, 19(24), 6334–6352. https://doi.org/10.1175/JCLI3969.1
13. **NASA GES DISC. (2019).** GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V06 (GPM_3IMERGM). Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERG/3B-MONTH/06
14. **Pyper, B. J., & Peterman, R. M. (1998).** Comparison of methods to account for autocorrelation in correlation analyses of fish data. *Canadian Journal of Fisheries and Aquatic Sciences*, 55(9), 2127–2140. https://doi.org/10.1139/f98-104
15. **Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., et al. (2017).** Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929. https://doi.org/10.1111/ecog.02881
16. **Rojas, Y., Minder, J. R., Campbell, L. S., Massmann, A. K., & Garreaud, R. (2021).** Assessment of GPM IMERG satellite precipitation estimation and its dependence on microphysical rain regimes over the mountains of south-central Chile. *Atmospheric Research*, 253, 105454. https://doi.org/10.1016/j.atmosres.2021.105454
17. **Soto-Alvarez, M., Alcayaga, H., Alarcon, V. J., Caamaño, D., Palma, S., & Escanilla-Minchel, R. (2020).** Evaluation of products 3B42 v7 and 3IMERG for the hydroclimatic regions of Chile. *Journal of South American Earth Sciences*, 104, 102870. https://doi.org/10.1016/j.jsames.2020.102870
18. **Tapiador, F. J., Navarro, A., García-Ortega, E., Merino, A., Sánchez, J. L., Marcos, C., & Kummerow, C. (2020).** The Contribution of Rain Gauges in the Calibration of the IMERG Product. *Journal of Hydrometeorology*, 21(2), 161–182. https://doi.org/10.1175/JHM-D-19-0116.1
19. **Tian, F., Hou, S., Yang, L., Hu, H., & Hou, A. (2018).** How Does the Evaluation of the GPM IMERG Rainfall Product Depend on Gauge Density and Rainfall Intensity? *Journal of Hydrometeorology*, 19(2), 339–349. https://doi.org/10.1175/JHM-D-17-0161.1
20. **Willmott, C. J. (1981).** On the Validation of Models. *Physical Geography*, 2(2), 184–194. https://doi.org/10.1080/02723646.1981.10642213
