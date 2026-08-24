#!/usr/bin/env python3
"""Build data/zenodo_archive/ and optional upload zip for Zenodo."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
ZENODO_ROOT = DATA_ROOT / "zenodo_archive"
ZIP_PATH = REPO_ROOT / "submerse-sop-otdr-data-v1.zip"

# Paths under data/ included in the Zenodo bundle (relative to data/).
INCLUDE_PATHS = [
    Path("processed/ellalink/hdf5/sops"),
    Path("catalog/world"),
    Path("seismographs/land"),
    Path("seismographs/obs"),
]

ATTRIBUTION_TEXT = """Submerse SOP-OTDR case-study data (EllaLink / Nokia SSU-A)
================================================================

License: Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

Contents
--------
- SOP-OTDR HDF5 (raw and derotated) for 2025-01-20 and 2025-04-03
- USGS earthquake catalogues (CSV)
- IRIS land-station MiniSEED waveforms
- OBS HDF5 waveforms (Jan 2025 case)

Third-party attribution
-----------------------
IRIS Data Services — land stations including PM.PLOUS, PM.PMOZ, PM.PMAR,
IU.MACI, AF.SVMA, II.SACV, BR.ROSB, IU.RCBR (and additional Iberian stations
in the Jan 2025 bundle where present).

Universidade de Lisboa — OBS data authors: Luis Matías, Carlos Corela,
Susana Custódio.

USGS Earthquake Hazards Program — catalogue CSV files.

Funding: EU Horizon Europe, Submerse project (grant 101095055).
"""


def mirror_path(rel: Path) -> None:
    src = DATA_ROOT / rel
    dst = ZENODO_ROOT / rel
    if not src.exists():
        print(f"SKIP (missing source): {rel}")
        return
    if src.is_dir():
        if dst.exists() and dst.is_file():
            dst.unlink()
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"OK  {rel}")


def build_archive() -> None:
    ZENODO_ROOT.mkdir(parents=True, exist_ok=True)
    for rel in INCLUDE_PATHS:
        mirror_path(rel)
    (ZENODO_ROOT / "ATTRIBUTION.txt").write_text(ATTRIBUTION_TEXT, encoding="utf-8")
    print(f"Wrote {ZENODO_ROOT / 'ATTRIBUTION.txt'}")


def build_zip(*, compression: int = zipfile.ZIP_DEFLATED) -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    files = sorted(p for p in ZENODO_ROOT.rglob("*") if p.is_file())
    print(f"Zipping {len(files)} files -> {ZIP_PATH.name}")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=compression) as zf:
        for path in files:
            arcname = path.relative_to(ZENODO_ROOT).as_posix()
            zf.write(path, arcname)
            print(f"  + {arcname}")
    size_gb = ZIP_PATH.stat().st_size / (1024**3)
    print(f"Created {ZIP_PATH} ({size_gb:.2f} GB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Also create submerse-sop-otdr-data-v1.zip in the repo root",
    )
    parser.add_argument(
        "--store-only",
        action="store_true",
        help="Use ZIP_STORED (no compression) when building the zip",
    )
    args = parser.parse_args()

    build_archive()
    if args.zip:
        comp = zipfile.ZIP_STORED if args.store_only else zipfile.ZIP_DEFLATED
        build_zip(compression=comp)


if __name__ == "__main__":
    main()
