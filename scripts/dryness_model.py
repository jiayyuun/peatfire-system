# Module 2 — Live Dryness Calculator
import rasterio
import numpy as np
import os

# Maximum dryness set to 10 cm total displacement
MAX_DRY_CM = 10

# Fraction of upward movement treated as recovery (rewetting)
RECOVERY_FACTOR = 0.3  

STATE_FILE = "../data/products/dryness_state.npy"

def run_module_2():
    # Input latest displacement raster (from Module 1)
    disp_path = "../data/inputs/displacement.tif"
    out_path  = "../data/products/dryness_index.tif"

    with rasterio.open(disp_path) as src:
        disp = src.read(1).astype(np.float32)
        profile = src.profile

    # Convert m → cm
    disp_cm = disp * 100

    # Drying = downward movement (negative displacement)
    increase = np.clip(-disp_cm, 0, None)

    # Rewetting = upward movement * slower recovery factor
    decrease = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR

    # Load cumulative dryness state or initialize
    if os.path.exists(STATE_FILE):
        dryness_cum = np.load(STATE_FILE)
    else:
        dryness_cum = np.zeros_like(disp_cm)

    # Hydrology update (as per your paragraph)
    # dryness_new = dryness_old + 0.7*(increase/5) - 0.3*(decrease/5)
    dryness_cum = dryness_cum + 0.7 * (increase / 5) - 0.3 * (decrease / 5)

    # Clamp to 0–10 cm range
    dryness_cum = np.clip(dryness_cum, 0, MAX_DRY_CM)

    # Save updated cumulative state
    np.save(STATE_FILE, dryness_cum)

    # Normalize 0 → 1 dryness index
    dryness_index = np.clip(dryness_cum / MAX_DRY_CM, 0, 1)

    # Save raster output
    profile.update(dtype=rasterio.float32)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(dryness_index.astype(np.float32), 1)

    return float(np.mean(dryness_index))
