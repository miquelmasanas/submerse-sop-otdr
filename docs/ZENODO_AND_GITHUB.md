# Zenodo and GitHub — publishing guide

## Use both, for different jobs

| Platform | Host here | Why |
|---|---|---|
| **GitHub** | Code, notebooks, README, `references.bib` | Version control, browsing, issues |
| **Zenodo** | One `.zip` of HDF5 + MiniSEED + catalog + figures | Large binaries + citable DOI |

Zenodo-only is **not** recommended for code/notebooks.

## Simplest workflow

1. Develop in `public/` inside OTDR-processing.
2. Push `public/` to GitHub.
3. Build the Zenodo bundle:

```bash
cd public
python scripts/prepare_zenodo_archive.py --zip --store-only
```

This refreshes `data/zenodo_archive/` and creates `submerse-sop-otdr-data-v1.zip` (~3 GB) in the `public/` folder.

4. Upload the zip to Zenodo.
5. Add the Zenodo DOI to `README.md`.

No download script required initially — README tells users to unzip into `data/`.

## Zenodo upload steps

1. [zenodo.org](https://zenodo.org) → log in.
2. Upload → `submerse-sop-otdr-data-v1.zip` (in the `public/` folder after running `prepare_zenodo_archive.py`).
3. Title: *Submerse SOP-OTDR case-study data (EllaLink, Jan–Apr 2025)*.
4. License: **CC-BY-4.0** (data). In the Zenodo description, note IRIS/USGS attribution and credit OBS data to Universidade de Lisboa (Luis Matías, Carlos Corela, Susana Custódio). List IRIS stations used (see README).
5. Publish → copy DOI into README.

## GitHub steps

1. Create repo `submerse-sop-otdr` (public).
2. Push `public/` contents as repo root.
3. Ensure `.gitignore` excludes `data/processed/`, `data/seismographs/`, etc.
