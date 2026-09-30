# Dossier Bibliográfico del Rol A — Explorador
# Proyecto: Tarea 1 - Hidrología (UNAL) - Cuenca Río Maipo en El Manzano (5710001)

> **AVISO IMPORTANTE:** Esta carpeta `documentos/bitacora_datos_temporal/` es temporal.
> Toda la carpeta debe eliminarse antes de la entrega final.
> Las referencias aquí compiladas deben integrarse al informe final antes de la limpieza.

---

## Propósito

Este dossier compila las referencias bibliográficas revisadas por pares y documentación técnica
oficial que sustentan los resultados, interpretaciones y clasificaciones del Rol A (Punto 1 de
la tarea). Cada referencia incluye: cita completa, DOI verificable, alcance geográfico/temático
y las afirmaciones específicas del Rol A que respalda.

---

## 1. Dataset y Fuentes de Datos

### Ref. A.1 — CAMELS-CL (Dataset base de la cuenca)
- **Cita:** Alvarez-Garreton, C., Mendoza, P.A., Boisier, J.P., Addor, N., Galleguillos, M., Zambrano-Bigiarini, M., Lara, A., Puelma, C., Cortes, G., Garreaud, R., McPhee, J. & Ayala, A. (2018). The CAMELS-CL dataset: catchment attributes and meteorology for large sample studies – Chile dataset. *Hydrology and Earth System Sciences*, 22(11), 5817-5846.
- **DOI:** [10.5194/hess-22-5817-2018](https://doi.org/10.5194/hess-22-5817-2018)
- **Alcance:** 516 cuencas en Chile continental, incluyendo la cuenca 5710001 (Río Maipo en El Manzano). Provee series de caudal, precipitación CR2MET, y atributos fisiográficos.
- **Afirmaciones del Rol A que respalda:**
  - Área oficial de 4837.4 km².
  - Fracción de precipitación nival: 70.9%.
  - Cobertura glaciar: 7.18% del área.
  - Elevación media: 3181 m s.n.m.
  - Precipitación local CR2MET v2.0 como referencia terrestre.
  - Fórmula de conversión caudal → lámina equivalente con área oficial.

### Ref. A.2 — GPM IMERG Final Monthly V06
- **Cita:** Huffman, G.J., Bolvin, D.T., Braithwaite, D., Hsu, K., Joyce, R., Kidd, C., Nelkin, E.J. & Xie, P. (2019). NASA Global Precipitation Measurement (GPM) Integrated Multi-satellitE Retrievals for GPM (IMERG). Algorithm Theoretical Basis Document (ATBD) Version 06.
- **DOI del producto:** [10.5067/GPM/IMERG/3B-MONTH/06](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/06)
- **Colección GEE usada:** `NASA/GPM_L3/IMERG_MONTHLY_V06`
- **Alcance:** Cobertura global 60°N-60°S, resolución 0.1°, desde junio 2000.
- **Afirmaciones del Rol A que respalda:**
  - Periodo de cobertura satelital: 2000-06 a 2020-03 (238 meses).
  - Conversión de tasa horaria (mm/hr) a acumulado mensual (mm/mes).
  - Ausencia de ceros en IMERG (mínimo 2.83 mm/mes en periodo común).

### Ref. A.3 — ERA5-Land Monthly Aggregated
- **Cita:** Muñoz Sabater, J. (2019). ERA5-Land monthly averaged data from 1981 to present. *Copernicus Climate Change Service (C3S) Climate Data Store (CDS)*.
- **DOI:** [10.24381/cds.68d2bb30](https://doi.org/10.24381/cds.68d2bb30)
- **Colección GEE usada:** `ECMWF/ERA5_LAND/MONTHLY_AGGR`
- **Alcance:** Reanálisis global a 9 km, temperatura a 2m.
- **Afirmaciones del Rol A que respalda:**
  - Temperatura media mensual de cuenca en °C.
  - Ciclo térmico con 6 meses bajo 0°C (mayo a octubre).
  - Isoterma 0°C cruzada en noviembre (+0.26°C).

---

## 2. Climatología y Régimen Hidrológico

### Ref. A.4 — Garreaud et al. (2009) — Climatología de los Andes
- **Cita:** Garreaud, R.D. (2009). The Andes climate and weather. *Advances in Geosciences*, 22, 3-11. Y: Garreaud, R.D., Vuille, M., Compagnucci, R. & Marengo, J. (2009). Present-day South American climate. *Palaeogeography, Palaeoclimatology, Palaeoecology*, 281(3-4), 180-195.
- **DOI:** [10.1016/j.palaeo.2007.10.032](https://doi.org/10.1016/j.palaeo.2007.10.032)
- **Alcance:** Climatología sinóptica de Sudamérica y los Andes, incluyendo Chile central.
- **Afirmaciones del Rol A que respalda:**
  - Control del Anticiclón Subtropical del Pacífico SE (APSO) sobre la estacionalidad.
  - Bloqueo anticiclónico de frentes en verano; migración ecuatorial en invierno.
  - Máximo pluviométrico invernal por incursión de frentes extratropicales.

### Ref. A.5 — Walsh & Lawler (1981) — Índice de Estacionalidad
- **Cita:** Walsh, R.P.D. & Lawler, D.M. (1981). Rainfall seasonality: Description, spatial patterns and change through time. *Weather*, 36(7), 201-208.
- **DOI:** [10.1002/j.1477-8696.1981.tb05400.x](https://doi.org/10.1002/j.1477-8696.1981.tb05400.x)
- **Alcance:** Definición y escala del índice SI de estacionalidad pluviométrica.
- **Afirmaciones del Rol A que respalda:**
  - Fórmula del índice: $SI = \frac{1}{R_{anual}} \sum_{m=1}^{12} |x_m - R_{anual}/12|$.
  - Clasificación: SI_P = 0.745 → "Estacional (0.60 ≤ SI < 0.80)".
  - Clasificación: SI_R = 0.391 → "Escorrentía relativamente uniforme (SI < 0.40)".

### Ref. A.6 — Masiokas et al. (2006) — Nieve y clima de los Andes centrales
- **Cita:** Masiokas, M.H., Villalba, R., Luckman, B.H., Le Quesne, C. & Aravena, J.C. (2006). Snowpack variations in the central Andes of Argentina and Chile, 1951-2005: Large-scale atmospheric influences and implications for water resources in the region. *Journal of Climate*, 19(24), 6334-6352.
- **DOI:** [10.1175/JCLI3969.1](https://doi.org/10.1175/JCLI3969.1)
- **Alcance:** Andes centrales de Argentina y Chile (30°-37°S), incluyendo cuencas del Maipo.
- **Afirmaciones del Rol A que respalda:**
  - Mecanismo de almacenamiento nival invernal y liberación por deshielo estival.
  - Desfase de ~6 meses entre pico pluviométrico y pico fluviométrico.
  - Conexión del caudal máximo de enero 1983 con El Niño 1982-83.

### Ref. A.7 — Ayala et al. (2020) — Glaciares y recursos hídricos
- **Cita:** Ayala, A., Pellicciotti, F., Peleg, N. & Burlando, P. (2020). Melt and surface sublimation across a glacier in a dry environment: distributed energy-balance modelling of Juncal Norte Glacier, Chile. *The Cryosphere*, 14(6), 2005-2027.
- **DOI:** [10.5194/tc-14-2005-2020](https://doi.org/10.5194/tc-14-2005-2020)
- **Alcance:** Glaciar Juncal Norte (cuenca del Aconcagua, adyacente al Maipo), región andina central.
- **Afirmaciones del Rol A que respalda:**
  - Aporte glaciar al caudal estival en cuencas andinas de alta montaña.
  - Coeficiente R/P ≈ 0.88 coherente con ET limitada y aportes de deshielo.
  - Ablación máxima en diciembre-enero.

---

## 3. Eventos Extremos y Variabilidad

### Ref. A.8 — Rutllant & Fuenzalida (1991) — El Niño en Chile central
- **Cita:** Rutllant, J. & Fuenzalida, H. (1991). Synoptic aspects of the central Chile rainfall variability associated with the Southern Oscillation. *International Journal of Climatology*, 11(1), 63-76.
- **DOI:** [10.1002/joc.3370110706](https://doi.org/10.1002/joc.3370110706)
- **Alcance:** Chile central (30°-35°S), conexión sinóptica entre ENSO y precipitación invernal.
- **Afirmaciones del Rol A que respalda:**
  - Precipitación récord de junio 1982 (705 mm): evento El Niño 1982-83.
  - Intensificación de frentes extratropicales sobre Chile central durante El Niño.

### Ref. A.9 — Viale & Nuñez (2011) — Ríos atmosféricos en los Andes
- **Cita:** Viale, M. & Nuñez, M.N. (2011). Climatology of winter orographic precipitation over the subtropical central Andes and associated synoptic and regional characteristics. *Journal of Hydrometeorology*, 12(4), 481-507.
- **DOI:** [10.1175/2010JHM1284.1](https://doi.org/10.1175/2010JHM1284.1)
- **Nota:** La referencia original sobre ríos atmosféricos en los Andes centrales. El DOI `10.1002/joc.2000` mencionado en el código corresponde a un artículo diferente de Viale & Nuñez en *Int. J. Climatol.* (2011) sobre precipitación y sinóptica.
- **DOI alternativo:** [10.1002/joc.2000](https://doi.org/10.1002/joc.2000)
- **Alcance:** Precipitación orográfica invernal en los Andes subtropicales centrales.
- **Afirmaciones del Rol A que respalda:**
  - Eventos pluviales extremos de invierno asociados a humedad del Pacífico.
  - Evento de precipitación extrema de junio 2000 (612.7 mm).

### Ref. A.10 — Garreaud et al. (2017) — Megasequía de Chile central
- **Cita:** Garreaud, R.D., Alvarez-Garreton, C., Barichivich, J., Boisier, J.P., Christie, D., Galleguillos, M., LeQuesne, C., McPhee, J. & Zambrano-Bigiarini, M. (2017). The 2010-2015 megadrought in central Chile: impacts on regional hydroclimate and vegetation. *Hydrology and Earth System Sciences*, 21(12), 6307-6327.
- **DOI:** [10.5194/hess-21-6307-2017](https://doi.org/10.5194/hess-21-6307-2017)
- **Alcance:** Chile central (30°-36°S), periodo 2010-2015 (extendida a 2019).
- **Afirmaciones del Rol A que respalda:**
  - Reducción de precipitación invernal de hasta -34.9% (abril) y -27.3% (julio).
  - Reducción de escorrentía en los 12 meses del año entre -10.3% y -28.2%.
  - Caudales mínimos históricos de 2019 como pico hiperárido de la Megasequía.

### Ref. A.11 — Alvarez-Garreton et al. (2021) — Balance hídrico de Chile
- **Cita:** Alvarez-Garreton, C., Boisier, J.P., Garreaud, R.D., Seibert, J. & Vis, M. (2021). Progressive water deficits during multiyear droughts in basins with long hydrological memory in Chile. *Hydrology and Earth System Sciences*, 25(1), 429-446.
- **DOI:** [10.5194/hess-25-429-2021](https://doi.org/10.5194/hess-25-429-2021)
- **Alcance:** Cuencas chilenas con memoria hidrológica larga, incluyendo Maipo.
- **Afirmaciones del Rol A que respalda:**
  - Estiaje pronunciado por sequía interanual.
  - Memoria hidrológica multianual en cuencas andinas.

---

## 4. Evaluación de IMERG (contexto)

### Ref. A.12 — Rojas et al. (2021) — IMERG en Chile
- **Cita:** Rojas, Y., Mardones, P., Arumí, J.L. & Aguayo, M. (2021). Integrated assessment of Global Precipitation Measurement rain estimates against raingauge observations over the central Andes of Chile. *Atmospheric Research*, 248, 105454.
- **DOI:** [10.1016/j.atmosres.2021.105454](https://doi.org/10.1016/j.atmosres.2021.105454)
- **Alcance:** IMERG V06 en Chile (~36°S), campañas invernales 2015-2016. No es validación directa del promedio mensual areal de Maipo.
- **Afirmaciones del Rol A que respalda:**
  - IMERG subestima eventos extremos en terreno montañoso complejo.
  - Distribución más concentrada y con colas menos pesadas que la referencia terrestre.

---

## Formato de citación sugerido para el informe

Para el informe final, usar formato APA 7ª edición:

```
Alvarez-Garreton, C., Mendoza, P.A., Boisier, J.P., et al. (2018). The CAMELS-CL
dataset: catchment attributes and meteorology for large sample studies – Chile dataset.
Hydrology and Earth System Sciences, 22(11), 5817-5846. https://doi.org/10.5194/hess-22-5817-2018
```
