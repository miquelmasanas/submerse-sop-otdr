# HDF5 data layout (SSU-A SOP)

## SOP files (`ellalink_sops_YYYY-MM-DD.h5`)

| Group / dataset | Description |
|---|---|
| `timing/unix_ns` | int64 UTC timestamps (nanoseconds since epoch) |
| `data/magnitudes` | Structured float32 array: `S0_r00`…`S3_r81` (Stokes parameters per repeater) |
| `header/dimensionNames` | Comma-separated column names |
| `header/dt` | Sample interval (seconds) |
| `cableSpec/n_repeaters` | Number of repeater spans |
| `cableSpec/length_km` | Approximate cable length |

Derotated files (`*_derotated.h5`) contain the same schema after outlier cleaning, decimation, and spherical derotation (see preprocessing notebook).

## OBS HDF5

Each OBS file has a `waveforms/` group. Datasets carry attributes `station`, `channel`, `starttime`, `delta`. Use `soplib.load_OBS_h5_smart()` or `load_all_OBS_h5_recursive()`.

## Catalogue CSV

USGS export with columns: `time`, `mag`, `place`, `latitude`, `longitude`, `depth`.
