# Submerse SOP-OTDR — Public Notebooks

Jupyter notebooks and supporting library for State-of-Polarization OTDR analysis with Nokia SSU-A on the EllaLink trans-Atlantic cable. Developed in the [Submerse](https://submerse.eu/) project (EU Horizon Europe, grant 101095055).

## Contents

| Notebook | Description | Colab |
|---|---|---|
| [`notebooks/01_sop_otdr_preprocessing_intro.ipynb`](notebooks/01_sop_otdr_preprocessing_intro.ipynb) | Pre-processing pipeline: outliers, decimation, derotation, derived quantities | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/submerse-project/submerse-sop-otdr/blob/main/notebooks/01_sop_otdr_preprocessing_intro.ipynb) |
| [`notebooks/02_sop_otdr_observations_case_study.ipynb`](notebooks/02_sop_otdr_observations_case_study.ipynb) | Case study (select event at top): Jan 20 2025 Taiwan or Apr 3 2025 Reykjanes | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/submerse-project/submerse-sop-otdr/blob/main/notebooks/02_sop_otdr_observations_case_study.ipynb) |

> **Note:** Colab links assume this repository is published as `submerse-project/submerse-sop-otdr` on GitHub. Update the URLs if you use a different owner or repository name.

## Quick start

```bash
git clone https://github.com/submerse-project/submerse-sop-otdr.git
cd submerse-sop-otdr
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
jupyter lab
```

Launch Jupyter from the repository root so `src/` resolves correctly.

### Data

Case-study data (HDF5, MiniSEED, earthquake catalogue) is **not** stored in git.

1. Download the data archive from Zenodo: *DOI TBD*
2. Unzip into `data/` so these paths exist:
   - `data/processed/ellalink/hdf5/sops/`
   - `data/catalog/world/`
   - `data/seismographs/obs/`
   - `data/seismographs/land/2025-01-20T16_20_00/`

See [`data/README.md`](data/README.md) for layout details.

## Project layout

```
├── src/paths.py          # central path resolution (DataPaths)
├── src/soplib.py         # analysis library
├── notebooks/            # two public notebooks
├── scripts/              # data copy + notebook preparation
├── references.bib        # BibTeX citations
└── data/                 # case-study data (gitignored)
```

## References

Key papers cited in the notebooks:

- Zhan et al. (2021), *Science* — https://doi.org/10.1126/science.abe6648
- Mecozzi (2024), *J. Lightwave Technology*
- Costa et al. (2023)
- Damask (2005), *Polarization Optics in Telecommunications*

Full BibTeX: [`references.bib`](references.bib)

## Acknowledgments

SSU-A development: Pierre Mertz and team, Sumudu Edirisinghe. Cable access: EllaLink. OBS data: Universidade de Lisboa (Luis Matías, Carlos Corela, Susana Custódio). Funding: European Union Horizon Europe, Submerse (101095055).

## License

### Code and notebooks

Released under the [MIT License](LICENSE).

### Data archive (Zenodo)

The case-study data bundle is released under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt the data provided you give appropriate credit.

### Third-party data attribution

The Zenodo archive includes derived and redistributed data from external sources. Please also acknowledge:

#### IRIS land stations

Land-station waveforms were obtained from [IRIS Data Services](https://www.iris.edu/hq/). Use of IRIS data should follow the [IRIS data usage policy](https://www.iris.edu/hq/data_usage_policy). — The primary Atlantic-path stations used in the case-study notebooks are:

| Network | Station |
|---|---|
| PM | PLOUS |
| PM | PMOZ |
| PM | PMAR |
| IU | MACI |
| AF | SVMA |
| II | SACV |
| BR | ROSB |
| IU | RCBR |

The Jan 2025 land-station bundle may also include additional Iberian stations (`LX.MESJ`, `LX.MORF`, `PM.PCVE`, `PM.PFVI`, `PM.PTEO`) depending on the archive version.

#### OBS (ocean-bottom seismometer) data

OBS waveforms in the Jan 2025 case study were provided by **Universidade de Lisboa**. Please credit **Luis Matías**, **Carlos Corela**, and **Susana Custódio** as data authors.

#### USGS earthquake catalogue

Catalogue entries are from the [U.S. Geological Survey (USGS)](https://earthquake.usgs.gov/) Earthquake Hazards Program.

### Suggested attribution text for publications

> SOP-OTDR data from the EllaLink cable (Nokia SSU-A, Submerse project). Land seismic waveforms from IRIS Data Services (stations PM.PLOUS, PM.PMOZ, PM.PMAR, IU.MACI, AF.SVMA, II.SACV, BR.ROSB, IU.RCBR). OBS data courtesy of Universidade de Lisboa (Luis Matías, Carlos Corela, Susana Custódio). Earthquake catalogue from USGS.
