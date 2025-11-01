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
    # Input latest displacement raster (from synthetic satellite stream)
    disp_path = "../data/inputs/displacement.tif"
    # Output dryness index map (0-1)
    out_path  = "../data/products/dryness_index.tif"

    with rasterio.open(disp_path) as src:
        disp = src.read(1).astype(np.float32)  # Read displacement map
        profile = src.profile

    disp_cm = disp * 100
    step_sub = np.clip(-disp_cm, 0, None) # Downward movement = drying; only take positive drying values
    step_up  = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR # Upward movement = rewetting; only take positive uplift values * recovery factor

    #Load cumulative dryness if exists, else initialize with zeros
    if os.path.exists(STATE_FILE):
        dryness_cum = np.load(STATE_FILE)
    else:
        dryness_cum = np.zeros_like(step_sub)
    dryness_cum = np.ones_like(step_sub) * 2.0  # start at 2cm dryness


    # Save updated cumulative state for next cycle
    np.save(STATE_FILE, dryness_cum)

    # Convert cumulative cm into normalized dryness index (0 to 1)
    dryness_index = np.clip(dryness_cum / MAX_DRY_CM, 0, 1)
    
    profile.update(dtype=rasterio.float32)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(dryness_index.astype(np.float32), 1)
    
    return float(np.mean(dryness_index))
