# Tarea 1 — Análisis Hidroclimático de Cuenca
**Curso:** Hidrología — Universidad Nacional de Colombia (UNAL)  
**Cuenca de Estudio:** Río Maipo en El Manzano (Código CAMELS-CL: `5710001`)  
**Área de Drenaje:** $4837.4 \text{ km}^2$

---

## 📌 Descripción del Proyecto
Este repositorio contiene los datos, códigos de análisis y figuras para el desarrollo de la **Tarea 1**. El objetivo principal es realizar el análisis hidroclimático de largo plazo ($\ge 40$ años, 1980–2020) combinando información hidrometeorológica observada en tierra con productos satelitales y de reanálisis global (NASA GPM IMERG y ECMWF ERA5-Land).

---

## 📁 Estructura del Repositorio

```text
├── .gitignore                      # Exclusión de archivos pesados y temporales
├── AGENTS.md                       # Directrices y reglas para agentes de Inteligencia Artificial
├── BITACORA_AGENTES.md             # Cuaderno de coordinación y traspaso entre integrantes e IAs
├── README.md                       # Descripción general del proyecto
│
├── datos/                          # Datasets procesados livianos
│   └── datos_mensuales_maipo.csv   # Dataset Maestro (1980–2020: Caudal, Lluvia local, IMERG, ERA5)
│
├── documentos/                     # Enunciados, rúbricas y borradores del informe
│   ├── tarea_1_202602.pdf
│   └── plan_trabajo_equipo.pdf
│
├── figuras/                        # Gráficas generadas en alta resolución (>= 300 DPI)
│   └── grafica_1_1_series.png      # Series temporales consolidadas
│
└── scripts/                        # Código reproducible y documentado en Python
    ├── 01_preparar_datos.py        # Procesamiento inicial de CAMELS-CL y conversión a mm/mes
    ├── 02_descargar_satelite.py    # Extracción satelital (GPM IMERG y ERA5-Land) en Earth Engine
    └── 03_integrar_datos.py        # Fusión y consolidación en el Dataset Maestro
```

---

## 🤖 Protocolo para Agentes de Inteligencia Artificial
Si eres un agente de IA asistiendo a cualquiera de los integrantes del equipo:
1. **Reglas y convenciones:** Consulta obligatoriamente [AGENTS.md](AGENTS.md).
2. **Historial de avance y estado actual:** Revisa [BITACORA_AGENTES.md](BITACORA_AGENTES.md) antes de escribir código.
3. **Al finalizar tu sesión:** Registra tu entrada en [BITACORA_AGENTES.md](BITACORA_AGENTES.md) siguiendo la plantilla establecida.

---

## 🚀 Estado del Avance
- [x] **Fase 1:** Adquisición, validación y consolidación de series (Completada).
- [ ] **Fase 2:** Análisis estadístico y comparación de precipitación (Local vs GPM IMERG).
- [ ] **Fase 3:** Estimación de evapotranspiración (Hargreaves / Thornthwaite / Balance).
- [ ] **Fase 4:** Balance hídrico de cuenca, almacenamiento e informe escrito final.
