#Module 3 — Simulate historical satellite input + build cumulative dryness training data
import rasterio, numpy as np, pandas as pd, os
from datetime import datetime

RAW_DIR = "../data/raw_inputs/"
HIST_PATH = "../data/historical/training_data.csv"

# Max dry depth set to 10cm total displacement
MAX_DRY_CM = 10
# Fraction of upward movement treated as recovery (rewetting) similar to actual peats, there may be changes due to external factors other than water
RECOVERY_FACTOR = 0.3
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs("../data/historical", exist_ok=True)

def simulate_displacement(path):
    fake_disp = np.random.uniform(-0.02, 0.02, (100, 100))
    profile = {"driver":"GTiff","dtype":"float32","width":100,"height":100,"count":1}
    # Save fake satellite displacement map
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(fake_disp.astype(np.float32), 1)

def simulate_fire_mask(path, dryness):
    # Create random fire mask
    mask = (np.random.rand(*dryness.shape) < dryness * 0.15).astype("uint8")
    # Save as GeoTIFF
    profile = {"driver":"GTiff","dtype":"uint8","width":100,"height":100,"count":1}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(mask, 1)

def run_module_3_stream():
    #Make new synthetic displacement file name with timestamp
    disp_path = f"{RAW_DIR}/disp_{datetime.now().timestamp()}.tif"  
    #Create fake displacement raster
    simulate_displacement(disp_path)
    with rasterio.open(disp_path) as src:
        disp = src.read(1).astype(np.float32)

    # Convert m to cm
    disp_cm = disp * 100
    # Downward movement = drying
    step_sub = np.clip(-disp_cm, 0, None)
    # Upward movement = rewetting
    step_up = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR

    #Keep cumulative dryness across time
    global dryness_cum
    try:
        dryness_cum
    except NameError:
        dryness_cum = np.zeros_like(step_sub)

    dryness_cum = np.clip(dryness_cum + step_sub - step_up, 0, MAX_DRY_CM) # Update dryness = old + drying − rewetting
    #normalise dryness
    dryness_idx = np.clip(dryness_cum / MAX_DRY_CM, 0, 1)
    # Make new synthetic fire map based on dryness
    fire_path = f"{RAW_DIR}/fire_{datetime.now().timestamp()}.tif"
    simulate_fire_mask(fire_path, dryness_idx)
    with rasterio.open(fire_path) as src:  # Read fire mask
        fire = src.read(1)

    # Pick 500 random pixels for training
    n = 500
    idx = np.random.choice(len(dryness_idx.flatten()), n)
    # Log samples into training CSV
    batch = pd.DataFrame({
        "timestamp": [datetime.now()] * n,
        "dryness": dryness_idx.flatten()[idx],
        "fire_occurred": fire.flatten()[idx]
    })
    # Append new rows to CSV (add header only once)
    batch.to_csv(HIST_PATH, mode="a", header=not os.path.exists(HIST_PATH), index=False)
    # Return average dryness + fire yes/no indicator
    return float(np.mean(dryness_idx)), int(np.mean(fire) > 0.01)
