#!/usr/bin/env python3
"""Download MovieLens ml-latest-small and convert to project format."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sample"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BASE_DIR / "data" / "ml-latest-small.zip"

    print("Downloading MovieLens ml-latest-small...")
    urllib.request.urlretrieve(URL, zip_path)

    extract_dir = BASE_DIR / "data" / "extracted"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_dir)

    source = extract_dir / "ml-latest-small"
    shutil.copy(source / "ratings.csv", DATA_DIR / "ratings.csv")
    shutil.copy(source / "movies.csv", DATA_DIR / "movies.csv")

    print(f"Saved to {DATA_DIR}")
    print("Restart backend to reload dataset.")


if __name__ == "__main__":
    main()
