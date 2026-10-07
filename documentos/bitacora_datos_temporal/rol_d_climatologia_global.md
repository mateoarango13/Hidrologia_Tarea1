# Registro del Rol D — Climatólogo Global

**Alcance del equipo:** punto 5: relacionar el caudal con el Pacífico global/ENSO, incluyendo análisis espacial de temperatura superficial del mar (SST). Además, el plan del equipo asigna a este rol la coordinación editorial del informe final; separar esa integración de los resultados científicos propios.

**Estado inicial:** sin registros añadidos. Completar con evidencia propia; no inferir resultados a partir de este encabezado.

## Registros científicos

Copiar la plantilla de `00_INSTRUCCIONES.md` para cada análisis. Identificar fuente, versión, variable, dominio espacial, periodo común, n, tratamiento de faltantes, prueba estadística, corrección por comparaciones múltiples si aplica, incertidumbre y límites de interpretación causal/predictiva.

## Registro editorial del equipo

Anotar decisiones de integración, versiones de figuras/tablas, contribuciones recibidas y asuntos pendientes. No alterar resultados registrados por otros roles sin dejar trazabilidad y confirmación del responsable.

## Registro D-20261006-01 — Preparación de descargas ERA5

- Estado: PREPARACIÓN VALIDADA EN SECO; descargas pendientes de autenticación CDS.
- Responsable: Bryan Salazar — Rol D.
- Fecha: 2026-10-06.
- Punto de la tarea: Punto 5, campos climáticos globales.
- Productos previstos: `reanalysis-era5-single-levels-monthly-means`, variable `mean_sea_level_pressure`; `reanalysis-era5-pressure-levels-monthly-means`, variable `geopotential`, nivel `500 hPa`.
- Periodo/frecuencia: mensual, enero de 2000 a diciembre de 2020, 252 fechas por variable.
- Salida prevista: NetCDF, dominio global, rejilla solicitada de 1°; documentar que ERA5 nativo del catálogo tiene resolución de 0.25°.
- Código: `scripts/08_descargar_era5_mensual.py`. Su `--dry-run` imprimió correctamente datasets, parámetros y nombres de salida. `get_errors` no reportó errores.
- Archivos previstos en `datos_pesados_ignorados/`: `era5_msl_monthly_2000_2020_1deg.nc` y `era5_geopotential_500hPa_monthly_2000_2020_1deg.nc`. A la fecha de este registro, no han sido descargados ni verificados.
- Prerrequisitos pendientes: el chequeo local indicó que `cdsapi` no estaba instalado y que no existía `%USERPROFILE%\\.cdsapirc`; la sesión no pudo completar la instalación. También se deben aceptar los términos de ambos datasets dentro de CDS.

### Resultado validado

- Solo se validó la construcción de las solicitudes en seco; no se descargaron datos, no se comprobaron dimensiones/unidades y no se calcularon correlaciones.

### Limitaciones y siguiente paso

- La ejecución requiere cuenta CDS, aceptación manual de los términos y token personal configurado localmente. No compartir el token con agentes ni incorporarlo al repositorio.
- Instalar `cdsapi`, configurar el token según la documentación oficial de Windows y ejecutar `python scripts/08_descargar_era5_mensual.py`. Después validar cobertura mensual, variables, unidades y coordenadas antes de producir mapas.

## Registro D-20261007-02 — Punto 5 ejecutado (apoyo de Tomás Gómez, Rol C)
- Estado: REVISADO (pendiente revisión del Rol D y verificación de referencias).
- Datos: ERA5 mensual global 1°, 1979–2020, SST/PNM/Z500 en `datos/campos_era5/` (script 15).
- Método: correlación por mes calendario a través de los años (ℓ = 0; Q–SST con ℓ = 6), anomalías con referencia 2000-06/2020-03, n_eff (Bretherton et al. 1999), FDR BH α = 0.10 por mapa; índices a priori Niño 3.4, PNM Pacífico SE y Z500 Chile central.
- Resultado: control local robusto (PNM/Z500 abr–oct, |r| 0.4–0.7); ENSO ago–oct para P_L y todo el año para Q vía nieve; no estacionario después de 2000.
- Código: scripts 16–19 y `p5_comun.py`. Informe: `documentos/punto5_teleconexiones_analisis.tex`.
- Revisó: pendiente (Bryan Salazar).
