"""Download monthly ERA5 mean sea-level pressure and 500 hPa geopotential."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "datos_pesados_ignorados"
YEARS = [str(year) for year in range(2000, 2021)]
MONTHS = [f"{month:02d}" for month in range(1, 13)]


def build_requests() -> list[tuple[str, dict[str, object], Path]]:
    common: dict[str, object] = {
        "product_type": ["monthly_averaged_reanalysis"],
        "year": YEARS,
        "month": MONTHS,
        "time": ["00:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "grid": [1.0, 1.0],
    }

    return [
        (
            "reanalysis-era5-single-levels-monthly-means",
            {**common, "variable": ["mean_sea_level_pressure"]},
            OUTPUT_DIR / "era5_msl_monthly_2000_2020_1deg.nc",
        ),
        (
            "reanalysis-era5-pressure-levels-monthly-means",
            {
                **common,
                "variable": ["geopotential"],
                "pressure_level": ["500"],
            },
            OUTPUT_DIR / "era5_geopotential_500hPa_monthly_2000_2020_1deg.nc",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the requests without connecting to CDS.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Download again even if a target file already exists.",
    )
    args = parser.parse_args()

    requests = build_requests()
    if args.dry_run:
        for dataset, request, target in requests:
            print(json.dumps({"dataset": dataset, "request": request, "target": str(target)}, indent=2))
        return

    try:
        import cdsapi
    except ImportError as error:
        raise SystemExit(
            "Missing cdsapi. Install it with: python -m pip install 'cdsapi>=0.7.7'"
        ) from error

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()

    for dataset, request, target in requests:
        if target.exists() and target.stat().st_size > 1_000_000 and not args.overwrite:
            print(f"Already present; skipping: {target}")
            continue

        print(f"Requesting {dataset} -> {target.name}")
        client.retrieve(dataset, request, str(target))
        if not target.exists() or target.stat().st_size <= 1_000_000:
            raise RuntimeError(f"Download did not produce a valid-sized file: {target}")
        print(f"Downloaded {target.stat().st_size / 1_000_000:.1f} MB: {target}")


if __name__ == "__main__":
    main()