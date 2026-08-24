"""Registry of public case studies (one row per event / analysis day)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaseStudy:
    id: str
    day: str
    catalog_file: str
    land_mseed_subdir: str
    has_obs: bool
    label: str
    mag_threshold: float = 5.0
    event_window_start: str | None = None
    event_window_end: str | None = None
    results_subdir: str = ""

    @property
    def sop_hdf5_stem(self) -> str:
        return f"ellalink_sops_{self.day}"


JAN2025_TAIWAN = CaseStudy(
    id="jan2025_taiwan",
    day="2025-01-20",
    catalog_file="19012025_21012025.csv",
    land_mseed_subdir="2025-01-20T16_20_00",
    has_obs=True,
    label="Taiwan teleseismic event (20 Jan 2025)",
    mag_threshold=5.0,
    event_window_start="2025-01-20 16:00:00",
    event_window_end="2025-01-20 20:00:00",
    results_subdir="20jan2025_observations",
)

APR2025_REYKJANES = CaseStudy(
    id="apr2025_reykjanes",
    day="2025-04-03",
    catalog_file="Extract_20_03_2025_to_13_04_2025_North_Atlantic.csv",
    land_mseed_subdir="2025-04-03T14_00_00",
    has_obs=False,
    label="Reykjanes Ridge M6.9 (3 Apr 2025)",
    mag_threshold=5.0,
    event_window_start="2025-04-03 12:00:00",
    event_window_end="2025-04-03 18:00:00",
    results_subdir="03apr2025_observations",
)

CASES: dict[str, CaseStudy] = {
    JAN2025_TAIWAN.id: JAN2025_TAIWAN,
    APR2025_REYKJANES.id: APR2025_REYKJANES,
}

DEFAULT_CASE = JAN2025_TAIWAN


def get_case(case_id: str) -> CaseStudy:
    try:
        return CASES[case_id]
    except KeyError as exc:
        known = ", ".join(sorted(CASES))
        raise KeyError(f"Unknown case '{case_id}'. Known cases: {known}") from exc
