"""Download datasets from Kaggle Datasets."""
import requests
import zipfile
import os
from pathlib import Path

TOKEN = "KGAT_efe8e2594937cb93dbe60f16edb7abd9"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://api.kaggle.com/v1"


def download_dataset(ref, dest_folder):
    """Download all files from a Kaggle dataset."""
    dest = DATA_DIR / dest_folder
    dest.mkdir(parents=True, exist_ok=True)

    # List files
    r = requests.get(f"{BASE}/datasets/{ref}/list", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  Failed to list: {r.status_code} {r.text[:200]}")
        r2 = requests.get(f"{BASE}/datasets/{ref}/list", headers=HEADERS, timeout=30)
        print(f"  Retry: {r2.status_code} {r2.text[:200]}")
        return

    files = r.json()
    print(f"  Files: {len(files)}")
    for f in files:
        name = f.get("name", "")
        if not name:
            continue
        local = dest / name
        if local.exists():
            print(f"    Skipping {name}")
            continue
        print(f"    Downloading {name}...")
        r = requests.get(
            f"{BASE}/datasets/{ref}/download/{name}",
            headers=HEADERS, stream=True, timeout=300,
        )
        if r.status_code != 200:
            print(f"    Failed: {r.status_code}")
            continue
        with open(local, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                fh.write(chunk)
        if name.endswith(".zip"):
            print(f"    Extracting {name}...")
            with zipfile.ZipFile(local) as zf:
                zf.extractall(dest)
            os.remove(local)
    print(f"  Done -> {dest}")


datasets = [
    ("thedevastator/hate-speech-and-offensive-language-detection", "hate_speech_davidson"),
    ("umitka/twitter-toxic-tweets", "toxic_tweets"),
]

for ref, folder in datasets:
    print(f"\nDownloading {ref}...")
    download_dataset(ref, folder)
print("\nAll done!")
