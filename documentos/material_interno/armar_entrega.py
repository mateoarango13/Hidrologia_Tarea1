"""Arma la carpeta y el ZIP de entrega final de la Tarea 1.

Copia del repositorio solo lo que exige la guía (informe, códigos, datos usados,
productos del análisis, README y evidencia de uso de IA) y el dashboard.
Deja fuera el material interno, los borradores por punto (documentos/anexos/, con cifras
de versiones anteriores), los archivos auxiliares de LaTeX, cachés y metadatos de
calidad de ASTER que no se usan.

Uso, desde la raíz del repositorio:
    python documentos/material_interno/armar_entrega.py
Resultado: entrega_final/<NOMBRE>/ (versionada en GitHub) y entrega_final/<NOMBRE>.zip
(ignorado por git: supera el límite de 100 MB de GitHub; se genera localmente).
"""
import shutil
import sys
import zipfile
from pathlib import Path

NOMBRE = "Tarea1_Hidrologia_RioMaipo_5710001"
ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "entrega_final"
DESTINO = SALIDA / NOMBRE

# (origen relativo a ROOT, patrón glob, destino relativo al paquete)
SELECCION = [
    (".", "requirements.txt", "."),
    (".", "AGENTS.md", "."),
    (".", "BITACORA_AGENTES.md", "."),
    ("documentos", "informe_final_tarea1.pdf", "documentos"),
    ("documentos", "informe_final_tarea1.tex", "documentos"),
    ("scripts", "*.py", "scripts"),
    ("datos", "datos_mensuales_maipo.csv", "datos"),
    ("datos", "datos_mensuales_procesados.csv", "datos"),
    ("datos", "datos_satelitales_imerg_era5.csv", "datos"),
    ("datos/campos_ersst", "*.nc", "datos/campos_ersst"),
    ("datos/camels_cl_5710001", "*.csv", "datos/camels_cl_5710001"),
    ("datos/camels_cl_5710001/polygon", "polygon.*", "datos/camels_cl_5710001/polygon"),
    ("datos/campos_era5", "*.nc", "datos/campos_era5"),
    ("datos/campos_era5", "*.geojson", "datos/campos_era5"),
    ("datos/ASTGTM_003-20261004_142607", "*_dem.tif", "datos/ASTGTM_003-20261004_142607"),
    ("figuras", "*.png", "figuras"),
    ("figuras", "*.csv", "figuras"),
    ("dashboard", "dashboard_autocontenido.html", "dashboard"),
    ("dashboard", "index.html", "dashboard"),
    ("dashboard/css", "*.css", "dashboard/css"),
    ("dashboard/js", "*.js", "dashboard/js"),
    ("dashboard/vendor/fontawesome/css", "*.css", "dashboard/vendor/fontawesome/css"),
    ("dashboard/vendor/fontawesome/webfonts", "*.woff2", "dashboard/vendor/fontawesome/webfonts"),
    ("dashboard/vendor/fuentes", "*", "dashboard/vendor/fuentes"),
]


def main():
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    n = 0
    for origen, patron, destino in SELECCION:
        archivos = sorted(p for p in (ROOT / origen).glob(patron) if p.is_file())
        if not archivos:
            sys.exit(f"ERROR: no se encontró {origen}/{patron}")
        (DESTINO / destino).mkdir(parents=True, exist_ok=True)
        for p in archivos:
            shutil.copy2(p, DESTINO / destino / p.name)
            n += 1

    # README de la entrega (describe el paquete, no el repositorio de trabajo)
    shutil.copy2(ROOT / "documentos/material_interno/README_entrega.md", DESTINO / "README.md")
    n += 1

    zip_path = SALIDA / f"{NOMBRE}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(DESTINO.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(SALIDA).as_posix())

    tam = sum(p.stat().st_size for p in DESTINO.rglob("*") if p.is_file())
    print(f"{n} archivos copiados a {DESTINO.relative_to(ROOT)} ({tam / 1e6:.1f} MB)")
    print(f"ZIP: {zip_path.relative_to(ROOT)} ({zip_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
