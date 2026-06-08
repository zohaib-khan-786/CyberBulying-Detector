"""
Download datasets from Kaggle using the Kaggle API.
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import requests

TOKEN = "KGAT_efe8e2594937cb93dbe60f16edb7abd9"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://api.kaggle.com/api/v1"


def download_competition(ref: str, dest: Path):
    print(f"Downloading {ref} to {dest}...")
    dest.mkdir(parents=True, exist_ok=True)
    r = requests.get(f"{BASE}/competitions/{ref}/list", headers=HEADERS)
    r.raise_for_status()
    files = r.json()
    print(f"Files found: {len(files)}")
    for f in files:
        name = f.get("name", "")
        size_mb = f.get("totalBytes", 0) / 1_000_000
        print(f"  {name} ({size_mb:.1f} MB)")
    for f in files:
        name = f.get("name", "")
        if not name:
            continue
        local = dest / name
        if local.exists():
            print(f"  Skipping {name}")
            continue
        print(f"  Downloading {name}...")
        r = requests.get(
            f"{BASE}/competitions/{ref}/download/{name}", headers=HEADERS, stream=True, timeout=300
        )
        r.raise_for_status()
        with open(local, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                fh.write(chunk)
        if name.endswith(".zip"):
            print(f"  Extracting {name}...")
            with zipfile.ZipFile(local) as zf:
                zf.extractall(dest)
            os.remove(local)
    print("Done!")


if __name__ == "__main__":
    download_competition("jigsaw-toxic-comment-classification-challenge", DATA_DIR / "jigsaw")
