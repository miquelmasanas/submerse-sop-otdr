"""Zenodo metadata for the public case-study data bundle."""

from __future__ import annotations

import os

ZENODO_RECORD_ID = "22085542"
ZENODO_DOI = "10.5281/zenodo.22085542"

# Filename on Zenodo; update if the uploaded archive is renamed.
ARCHIVE_FILENAME = "nokia_sop_otdr_ssu_A_archive.zip"

GITHUB_REPO = "miquelmasanas/submerse-sop-otdr"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"


def record_id() -> str:
    """Return the Zenodo record ID from config or environment."""
    env = os.environ.get("SUBMERSE_ZENODO_RECORD_ID", "").strip()
    if env:
        return env
    return ZENODO_RECORD_ID


def archive_download_url(*, record: str | None = None) -> str:
    rid = record or record_id()
    return (
        f"https://zenodo.org/records/{rid}/files/{ARCHIVE_FILENAME}?download=1"
    )
