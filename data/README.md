# Case-study data layout

Data for the Jan 20 2025 EllaLink / SSU-A notebooks.

Case-study data for the EllaLink / SSU-A notebooks. Two events are supported (see `src/case_studies.py`):

| Case | Day | Catalog | Land MiniSEED | OBS |
|---|---|---|---|---|
| `jan2025_taiwan` | 2025-01-20 | `19012025_21012025.csv` | `land/2025-01-20T16_20_00/` | yes |
| `apr2025_reykjanes` | 2025-04-03 | `Extract_20_03_2025_to_13_04_2025_North_Atlantic.csv` | `land/2025-04-03T14_00_00/` | no |

## Directory structure

```
data/
├── processed/ellalink/hdf5/sops/
│   ├── ellalink_sops_2025-01-20.h5
│   ├── ellalink_sops_2025-01-20_derotated.h5
│   ├── ellalink_sops_2025-04-03.h5
│   └── ellalink_sops_2025-04-03_derotated.h5
├── catalog/world/
│   ├── 19012025_21012025.csv
│   └── Extract_20_03_2025_to_13_04_2025_North_Atlantic.csv
└── seismographs/
    ├── obs/                          # Jan case only
    └── land/
        ├── 2025-01-20T16_20_00/
        └── 2025-04-03T14_00_00/
```

## Obtaining the data

Download the Zenodo archive (DOI TBD) and unzip into this `data/` folder.

A zip-ready mirror for upload is maintained at `data/zenodo_archive/` during local development.

Rebuild the Zenodo bundle:

```bash
python scripts/prepare_zenodo_archive.py --zip --store-only
```

Upload `submerse-sop-otdr-data-v1.zip` from the repository root. Unzip its contents into this `data/` folder.

## License and attribution

The Zenodo data bundle is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Third-party data included in the archive:

- **IRIS** — land-station MiniSEED waveforms ([IRIS Data Services](https://www.iris.edu/hq/)). Primary Atlantic-path stations: `PM.PLOUS`, `PM.PMOZ`, `PM.PMAR`, `IU.MACI`, `II.SACV`, `IU.RCBR` (see main README for the full table).
- **Universidade de Lisboa** — OBS HDF5 waveforms (Jan 2025 case). Authors: Luis Matías, Carlos Corela, Susana Custódio.
- **USGS** — earthquake catalogue CSV files ([USGS Earthquake Hazards Program](https://earthquake.usgs.gov/))

See the repository [README](../README.md#license) for full attribution guidance.

## HDF5 SOP format

Each daily SOP file contains:

- `timing/unix_ns` — UTC timestamps (nanoseconds)
- `data/magnitudes` — structured array with `S0_rNN` … `S3_rNN` per repeater span
- `header/` — dimension names, sample interval `dt`
- `cableSpec/` — link metadata (length, repeater count)

See `docs/data_layout.md` for more detail.
