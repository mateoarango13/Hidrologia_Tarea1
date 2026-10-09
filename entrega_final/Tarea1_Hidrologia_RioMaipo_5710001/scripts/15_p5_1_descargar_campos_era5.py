"""
Punto 5.1 — Descarga de campos climáticos globales mensuales (ERA5).

Campos (justificación en el informe del punto 5):
  * SST: temperatura superficial del mar (ERA5 single levels, `sea_surface_temperature`).
  * MSL: presión media al nivel del mar (ERA5 single levels, `mean_sea_level_pressure`).
  * Z500: geopotencial a 500 hPa (ERA5 pressure levels, `geopotential`); se convierte a
    ALTURA geopotencial dividiendo por g0 = 9.80665 m/s² en el procesamiento.

Decisiones:
  * Producto: "monthly_averaged_reanalysis" (promedio mensual; time = 00:00 representa el mes).
  * Periodo: 1979-01 a 2020-12. Cubre el registro de P_L y Q (1980-2020) y diciembre de
    1979 para rezagos (enero 1980 con ℓ = 1 se empareja con diciembre 1979).
  * Dominio: global. Malla regular de 1° pedida a CDS (interpolada desde 0.25° nativo):
    resolución moderada adecuada para patrones de gran escala (guía, punto 5.1).
  * Requisitos: cuenta CDS, licencias aceptadas en ambos datasets, ~/.cdsapirc con la
    clave personal (nunca dentro del repositorio) y `pip install "cdsapi>=0.7.7" netCDF4`.

Uso:
  python scripts/15_p5_1_descargar_campos_era5.py --dry-run   # solo muestra solicitudes
  python scripts/15_p5_1_descargar_campos_era5.py             # descarga y verifica
  python scripts/15_p5_1_descargar_campos_era5.py --verify    # solo verifica lo descargado

Salidas (versionadas en GitHub por excepción del .gitignore; incluir en el ZIP final):
  datos/campos_era5/era5_msl_sst_mensual_1979_2020_1deg.nc
  datos/campos_era5/era5_z500_mensual_1979_2020_1deg.nc
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "datos" / "campos_era5"
YEARS = [str(year) for year in range(1979, 2021)]
MONTHS = [f"{month:02d}" for month in range(1, 13)]
COMMON = {
    "product_type": ["monthly_averaged_reanalysis"],
    "year": YEARS,
    "month": MONTHS,
    "time": ["00:00"],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "grid": [1.0, 1.0],
}
REQUESTS = [
    ("reanalysis-era5-single-levels-monthly-means",
     {**COMMON, "variable": ["mean_sea_level_pressure", "sea_surface_temperature"]},
     OUTPUT_DIR / "era5_msl_sst_mensual_1979_2020_1deg.nc"),
    ("reanalysis-era5-pressure-levels-monthly-means",
     {**COMMON, "variable": ["geopotential"], "pressure_level": ["500"]},
     OUTPUT_DIR / "era5_z500_mensual_1979_2020_1deg.nc"),
]


def unzip_if_needed(target: Path) -> None:
    """CDS puede entregar un ZIP aunque se pida 'unarchived'; se extrae y se renombra."""
    if not zipfile.is_zipfile(target):
        return
    with zipfile.ZipFile(target) as archive:
        members = [m for m in archive.namelist() if m.endswith(".nc")]
        extract_dir = target.with_suffix("")
        archive.extractall(extract_dir)
    target.unlink()
    if len(members) == 1:
        (extract_dir / members[0]).rename(target)
        extract_dir.rmdir()
        print(f"  ZIP extraído -> {target.name}")
    else:
        print(f"  ZIP con varios archivos extraído en {extract_dir} : {members}")


def verify(target: Path) -> None:
    import xarray as xr

    if not target.exists():
        print(f"FALTA: {target.name}")
        return
    ds = xr.open_dataset(target)
    time_name = "valid_time" if "valid_time" in ds.coords else "time"
    times = ds[time_name].values
    print(f"\n{target.name}  ({target.stat().st_size / 1e6:.1f} MB)")
    print(f"  dimensiones: {dict(ds.sizes)}")
    print(f"  tiempo: {str(times.min())[:7]} a {str(times.max())[:7]} ({len(times)} meses; esperados {len(YEARS) * 12})")
    print(f"  latitud: {float(ds.latitude.min())} a {float(ds.latitude.max())}; "
          f"longitud: {float(ds.longitude.min())} a {float(ds.longitude.max())}")
    for name, var in ds.data_vars.items():
        if var.ndim < 2:
            continue
        frac_nan = float(var.isnull().mean())
        print(f"  {name}: unidades={var.attrs.get('units')}, '{var.attrs.get('long_name')}', "
              f"fracción NaN={frac_nan:.3f}, rango=[{float(var.min()):.1f}, {float(var.max()):.1f}]")
    ds.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Mostrar solicitudes sin conectarse.")
    parser.add_argument("--verify", action="store_true", help="Solo verificar archivos descargados.")
    parser.add_argument("--overwrite", action="store_true", help="Descargar aunque el archivo exista.")
    args = parser.parse_args()

    if args.dry_run:
        for dataset, request, target in REQUESTS:
            print(json.dumps({"dataset": dataset, "target": str(target.relative_to(ROOT)),
                              "request": {**request, "year": f"{YEARS[0]}..{YEARS[-1]}"}}, indent=2))
        return

    if not args.verify:
        import cdsapi

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        client = cdsapi.Client()
        for dataset, request, target in REQUESTS:
            if target.exists() and target.stat().st_size > 1_000_000 and not args.overwrite:
                print(f"Ya existe, se omite: {target.name}")
                continue
            print(f"Solicitando {dataset} -> {target.name} (puede quedar en cola varios minutos)")
            client.retrieve(dataset, request, str(target))
            unzip_if_needed(target)

    for _, _, target in REQUESTS:
        verify(target)


if __name__ == "__main__":
    main()
