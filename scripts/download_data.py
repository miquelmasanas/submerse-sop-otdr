#!/usr/bin/env python3
"""Download and extract the Zenodo case-study archive into data/."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
MARKER = DATA_ROOT / "processed" / "ellalink" / "hdf5" / "sops"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.zenodo import (  # noqa: E402
    ARCHIVE_FILENAME,
    ZENODO_DOI,
    archive_download_url,
    record_id,
)


def _fetch_record(record: str) -> dict:
    api = f"https://zenodo.org/api/records/{record}"
    with urllib.request.urlopen(api, timeout=60) as resp:
        return json.load(resp)


def resolve_download_url(*, record: str | None = None) -> tuple[str, str]:
    """Return (download_url, filename) for the Zenodo archive."""
    rid = record or record_id()
    try:
        payload = _fetch_record(rid)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise SystemExit(
                f"Zenodo record {rid} not found. If the record is still a draft, "
                "publish it first or set SUBMERSE_ZENODO_RECORD_ID."
            ) from exc
        raise

    status = payload.get("status", "unknown")
    if status != "published":
        print(f"Warning: Zenodo record {rid} status is {status!r}, not published.")

    files = payload.get("files", [])
    for entry in files:
        key = entry.get("key", "")
        if key == ARCHIVE_FILENAME:
            links = entry.get("links", {})
            url = links.get("self") or links.get("download")
            if url:
                return url, key

    for entry in files:
        key = entry.get("key", "")
        if key.endswith(".zip"):
            links = entry.get("links", {})
            url = links.get("self") or links.get("download")
            if url:
                print(f"Using Zenodo file {key!r} (configured name: {ARCHIVE_FILENAME!r})")
                return url, key

    if files:
        raise SystemExit(
            f"No .zip file found on Zenodo record {rid}. Files: "
            f"{[f.get('key') for f in files]}"
        )

    return archive_download_url(record=rid), ARCHIVE_FILENAME


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading\n  {url}\n  -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "submerse-sop-otdr/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        chunk = 8 * 1024 * 1024
        done = 0
        with dest.open("wb") as out:
            while True:
                block = resp.read(chunk)
                if not block:
                    break
                out.write(block)
                done += len(block)
                if total:
                    pct = 100 * done / total
                    print(
                        f"\r  {done / (1024**3):.2f} / {total / (1024**3):.2f} GB "
                        f"({pct:.1f}%)",
                        end="",
                    )
        print()


def _check_zip_layout(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        tops = {name.split("/")[0] for name in zf.namelist() if name and not name.endswith("/")}
        tops |= {name.split("/")[0] for name in zf.namelist() if "/" in name}
    if tops == {"zenodo_archive"} or (len(tops) == 1 and "zenodo_archive" in tops):
        raise SystemExit(
            "Zip has an extra zenodo_archive/ folder. Unzip manually and move "
            "contents up one level, or rebuild with prepare_zenodo_archive.py."
        )
    expected = {"processed", "catalog", "seismographs", "ATTRIBUTION.txt"}
    if not expected.intersection(tops):
        print(f"Warning: unexpected zip top-level entries: {sorted(tops)}")


def _extract(zip_path: Path, dest: Path) -> None:
    print(f"Extracting into {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        print(f"  {len(members)} files")
        zf.extractall(dest)
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=f"Default Zenodo DOI: https://doi.org/{ZENODO_DOI}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download even if data/processed/.../sops already exists",
    )
    parser.add_argument(
        "--record",
        help="Zenodo record ID override (default: src/zenodo.py or SUBMERSE_ZENODO_RECORD_ID)",
    )
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help="Keep the downloaded zip in the repository root",
    )
    args = parser.parse_args()

    if MARKER.is_dir() and not args.force:
        print(f"Data already present at {MARKER}")
        print("Use --force to re-download.")
        return

    url, filename = resolve_download_url(record=args.record)
    zip_path = REPO_ROOT / filename
    _download(url, zip_path)
    _check_zip_layout(zip_path)
    _extract(zip_path, DATA_ROOT)
    if not args.keep_zip:
        zip_path.unlink(missing_ok=True)
        print(f"Removed temporary {zip_path.name}")


if __name__ == "__main__":
    main()
