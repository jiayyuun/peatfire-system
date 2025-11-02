# Module 3 — Clean historical data & build ML training table
import rasterio
import numpy as np
import pandas as pd
import glob, os
from datetime import datetime

DRYNESS_DIR = "../data/historical/dryness_maps/"
FIRE_DIR     = "../data/historical/fire_masks/"
OUT_CSV      = "../data/historical/training_data.csv"

SAMPLES_PER_FILE = 500  # number of pixels sampled per timestamp

def load_raster(path):
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile
    return arr, profile

def build_training_data():
    dryness_files = sorted(glob.glob(f"{DRYNESS_DIR}/*.tif"))
    fire_files    = sorted(glob.glob(f"{FIRE_DIR}/*.tif"))

    assert len(dryness_files) == len(fire_files), \
        "Mismatch: dryness maps and fire masks count differ!"

    all_rows = []

    for dry_file, fire_file in zip(dryness_files, fire_files):
        # Extract timestamp from filename
        ts = os.path.basename(dry_file).split("_")[1].replace(".tif", "")
        timestamp = datetime.strptime(ts, "%Y%m%d")

        # Load rasters
        dry_map, _  = load_raster(dry_file)
        fire_map, _ = load_raster(fire_file)

        # Ensure shapes match
        if dry_map.shape != fire_map.shape:
            print(f"[WARN] shape mismatch skipped: {dry_file}")
            continue

        # Flatten
        dry_flat  = dry_map.flatten()
        fire_flat = fire_map.flatten()

        # Remove NaNs
        mask = ~np.isnan(dry_flat)
        dry_flat  = dry_flat[mask]
        fire_flat = fire_flat[mask]

        # Random sample
        idx = np.random.choice(len(dry_flat), min(SAMPLES_PER_FILE, len(dry_flat)), replace=False)

        batch = pd.DataFrame({
            "timestamp": [timestamp]*len(idx),
            "dryness": dry_flat[idx],
            "fire_occurred": fire_flat[idx].astype(int)
        })

        all_rows.append(batch)
        print(f"[OK] Processed {ts} → {len(batch)} samples")

    # Combine and save
    full = pd.concat(all_rows)
    full.to_csv(OUT_CSV, index=False)

    print(f"\n✅ Module 3 complete — training dataset saved to {OUT_CSV}")
    print(f"Total samples: {len(full)}")

if __name__ == "__main__":
    build_training_data()
