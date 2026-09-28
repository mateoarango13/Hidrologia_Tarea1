# Registro temporal de datos y análisis del equipo

> **CARPETA TEMPORAL. BORRAR COMPLETA ANTES DE LA ENTREGA FINAL.**

## Propósito

Esta carpeta permite que cada integrante deje evidencia objetiva, rastreable y fácil de interpretar de su parte del trabajo. Sirve como insumo de coordinación y como apoyo para redactar el informe y preparar la sustentación. No sustituye el dataset maestro, los scripts reproducibles, las figuras oficiales, el informe ni la bitácora de handoff.

## Roles

- `rol_a_explorador.md`: caracterización y ciclo anual, punto 1.
- `rol_b_modelador.md`: relaciones y modelos, punto 2; apoyo con anomalías estandarizadas.
- `rol_c_tendencias_y_fourier.md`: tendencias y ciclos, puntos 3 y 4.
- `rol_d_climatologia_global.md`: conexiones climáticas globales, punto 5; coordinación editorial del informe.

## Reglas para cada registro

- Usar el dataset maestro `datos/datos_mensuales_maipo.csv` para los análisis que correspondan y conservar las series locales completas; no recortarlas por la cobertura de una fuente más corta.
- Informar nombres de columnas tal como aparecen en el archivo, unidades, periodo exacto, cantidad de pares/meses válidos, faltantes y su tratamiento. No convertir faltantes en ceros ni imputarlos sin documentar y justificarlo.
- Dejar método, fórmula, transformaciones, periodo de referencia y decisiones suficientes para reproducir cada resultado.
- Separar claramente **resultado calculado**, **interpretación física**, **hipótesis por verificar** y **limitación/incertidumbre**. No presentar asociación como causalidad ni un ajuste como validación.
- Registrar scripts, comandos, tablas, figuras y fuentes que respaldan cada afirmación. Las cifras deben poder rastrearse a un cálculo o fuente; no completar campos desconocidos por inferencia.
- Conservar resultados negativos y anomalías. No retirar datos extremos sin una regla y una justificación documentadas.
- Identificar las exploraciones preliminares como tales y señalar si la selección de método/rezago o el cálculo de referencias usó datos de evaluación.

## Plantilla de registro

Copiar este bloque en el archivo del rol y crear un registro por análisis o conjunto coherente de resultados:

```markdown
### Registro [ID único]
- Estado: PRELIMINAR | REVISADO | VALIDADO
- Responsable:
- Fecha:
- Punto de la tarea:
- Pregunta analizada:
- Dataset/fuente y versión:
- Archivo y columnas usadas:
- Variables y unidades:
- Periodo analizado:
- n válido y regla para formar pares:
- Faltantes/exclusiones y motivo:
- Método, fórmula y supuestos:
- Transformaciones/referencia climatológica:
- Código/comando reproducible:
- Archivos de salida:

#### Resultados calculados
- [Métrica o valor, unidad, precisión y periodo]

#### Interpretación física
- [Qué permiten afirmar los resultados y qué no]

#### Hipótesis por contrastar
- [Mecanismo o explicación alternativa; evidencia adicional necesaria]

#### Incertidumbres y limitaciones
- [Cobertura, dependencia temporal, fuentes compartidas, sensibilidad, etc.]

#### Referencias
- [Referencia formal, DOI/enlace y afirmación que respalda]

#### Revisión
- Revisó:
- Cambios o preguntas pendientes:
```

## Limpieza previa a la entrega

Antes de preparar o subir el paquete final, borrar la carpeta completa `documentos/bitacora_datos_temporal/`, incluidos este archivo y todos los registros de roles. Verificar que la carpeta no esté incluida en el ZIP final. Los scripts, datos, figuras oficiales, informe y `BITACORA_AGENTES.md` que estén fuera de esta carpeta no forman parte de esta limpieza.