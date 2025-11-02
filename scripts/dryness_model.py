# Module 2 — Live Dryness Calculator
import rasterio
import numpy as np
import os

MAX_DRY_CM = 10.0
RECOVERY_FACTOR = 0.3
STATE_FILE = "../data/products/dryness_state.npy"

def run_module_2():
    disp_path = "../data/inputs/displacement.tif"
    out_path  = "../data/products/dryness_index.tif"

    # Read displacement (LOS, m)
    with rasterio.open(disp_path) as src:
        disp = src.read(1).astype(np.float32)
        profile = src.profile

    # Convert to cm
    disp_cm = disp * 100.0

    # === HYDROLOGY UPDATE: peat moisture memory ===

    # drying from subsidence (negative displacement)
    increase = np.clip(-disp_cm, 0, None)  

    # rewetting from uplift (slower recovery)
    decrease = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR  

    if os.path.exists(STATE_FILE):
        dryness_cum = np.load(STATE_FILE)
    else:
        dryness_cum = np.zeros_like(disp_cm, dtype=np.float32)

    # physics-based peat moisture update
    dryness_cum = dryness_cum + 0.7*(increase/5) - 0.3*(decrease/5)

    # clamp to physical limits
    dryness_cum = np.clip(dryness_cum, 0, MAX_DRY_CM)

    np.save(STATE_FILE, dryness_cum)

    dryness_index = np.clip(dryness_cum / MAX_DRY_CM, 0, 1)


    # Write GeoTIFF
    profile.update(dtype=rasterio.float32)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(dryness_index.astype(np.float32), 1)

    return float(np.mean(dryness_index))
