"""Central path resolution for the public SOP-OTDR notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.case_studies import DEFAULT_CASE, CaseStudy


def get_repo_root(start: Path | None = None) -> Path:
    """Walk up from *start* (or cwd) until we find ``src/soplib.py``."""
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "src" / "soplib.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate repository root (expected src/soplib.py in tree)."
    )


@dataclass(frozen=True)
class DataPaths:
    """Standard data locations relative to the public repo root."""

    root: Path
    case: CaseStudy = DEFAULT_CASE

    @classmethod
    def from_cwd(
        cls, start: Path | None = None, case: CaseStudy | None = None
    ) -> "DataPaths":
        root = get_repo_root(start)
        return cls(root=root, case=case or DEFAULT_CASE)

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def hdf5_dir(self) -> Path:
        return self.data / "processed" / "ellalink" / "hdf5"

    def sop_hdf5_path(self, *, derotated: bool = False) -> Path:
        suffix = "_derotated" if derotated else ""
        name = f"{self.case.sop_hdf5_stem}{suffix}.h5"
        return self.hdf5_dir / "sops" / name

    @property
    def catalog_csv(self) -> Path:
        return self.data / "catalog" / "world" / self.case.catalog_file

    @property
    def obs_glob(self) -> str | None:
        if not self.case.has_obs:
            return None
        return str(self.data / "seismographs" / "obs" / "*.h5")

    @property
    def obs_location_png(self) -> Path:
        return self.data / "seismographs" / "obs" / "OBS_location.png"

    @property
    def land_mseed_dir(self) -> Path:
        return self.data / "seismographs" / "land" / self.case.land_mseed_subdir

    @property
    def land_stations_map_png(self) -> Path:
        return self.data / "seismographs" / "land" / "stations_map.png"

    @property
    def results_dir(self) -> Path:
        return self.root / "results" / self.case.results_subdir

    @property
    def zenodo_archive_dir(self) -> Path:
        return self.data / "zenodo_archive"
