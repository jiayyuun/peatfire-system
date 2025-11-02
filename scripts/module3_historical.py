# Module 3 — Generate synthetic historical Sentinel-1 dryness + fire maps ONLY
# Output: /data/historical/dryness_maps/*.tif + /data/historical/fire_masks/*.tif

import numpy as np, os, rasterio, pandas as pd
from datetime import datetime, timedelta
from rasterio.crs import CRS
from synth_utils import (
    gaussian_field, planar_ramp, ar1_series, seasonal_component,
    los_from_vertical, fire_probability_from_dryness, cluster_mask,
    default_transform
)

# Grid size
H, W = 200, 200
EPOCHS = 120  # ~3.5 years at ~10 day repeat
ABS_MAX_CM = 10.0
RECOVERY_FACTOR = 0.3
INCIDENCE = 37.0

# Output directories
HIST_DRY_DIR   = "../data/historical/dryness_maps/"
HIST_FIRE_DIR  = "../data/historical/fire_masks/"

os.makedirs(HIST_DRY_DIR, exist_ok=True)
os.makedirs(HIST_FIRE_DIR, exist_ok=True)

def displacement_to_dryness(dlos, cum):
    disp_cm = dlos * 100
    step_sub = np.clip(-disp_cm, 0, None)
    step_up  = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR
    cum = np.clip(cum + step_sub - step_up, 0, ABS_MAX_CM)
    dryness = np.clip(cum / ABS_MAX_CM, 0, 1)
    return dryness, cum

def run_module3_historical():
    print(f"[HIST] Generating {EPOCHS} synthetic epochs...")
    cum = np.zeros((H, W), dtype="float32")
    start_date = datetime(2020, 1, 1)

    for t in range(EPOCHS):
        # Determine climate season cycle index (month)
        current_date = start_date + timedelta(days=10 * t)
        month = current_date.month

        # 🌧️ Seasonal rainfall / drying forcing (monsoon vs dry season)
        if month in [11, 12, 1, 2]:       # Wet monsoon: recharge phase
            seasonal_bias = +0.015
        elif month in [6, 7, 8, 9]:       # Peak dry: drying subsidence
            seasonal_bias = -0.025
        else:
            seasonal_bias = 0.0           # Transition seasons

        # 🌊 ENSO multi-year climate cycle (El Niño / La Niña)
        enso_phase = np.sin(2 * np.pi * (t / 90.0))   # 3-year oscillation approx
        enso_strength = 0.02 * enso_phase            # moderate effect scale
        # Positive enso_phase ≈ El Niño (extra drying), negative ≈ La Niña (wet)

        # Combine seasonal + ENSO forcing
        climate_bias = seasonal_bias + enso_strength

        # Add random drought or extreme rainfall pulse
        if np.random.rand() < 0.05:     # 5% chance drought wave
            climate_bias += -0.06
        if np.random.rand() < 0.03:     # 3% chance major rain recharge
            climate_bias += +0.08

        trend  = 0.00015 * t
        season = seasonal_component(t, amp_m=0.004, period=36)
        ramp   = planar_ramp(H, W, ax=1.2e-5, ay=-9e-6)
        noise  = gaussian_field(H, W, sigma_px=10, std=0.0025)

        dvert = (
            ar1_series(cum / 100.0, noise, phi=0.92)
            + trend
            + season
            + ramp
            + climate_bias        # 👈 NEW CLIMATE VARIABILITY INPUT
)
        dlos  = los_from_vertical(dvert, incidence_deg=INCIDENCE)

        dryness, cum = displacement_to_dryness(dlos, cum)

        fire_prob = fire_probability_from_dryness(dryness, bias=-1.1, scale=3.4)
        fire_mask = cluster_mask(fire_prob, cluster_sigma=2.0)

        ts = (start_date + timedelta(days=10*t)).strftime("%Y%m%d")
        dry_file  = f"{HIST_DRY_DIR}/dry_{ts}.tif"
        fire_file = f"{HIST_FIRE_DIR}/fire_{ts}.tif"

        profile = {
            "driver": "GTiff", "dtype": "float32",
            "width": W, "height": H, "count": 1,
            "crs": CRS.from_epsg(3857),
            "transform": default_transform(px=30)
        }

        with rasterio.open(dry_file,"w",**profile) as dst:
            dst.write(dryness.astype("float32"),1)
        with rasterio.open(fire_file,"w",**profile) as dst:
            dst.write(fire_mask.astype("uint8"),1)

        print(f"[HIST] Saved epoch {t+1}/{EPOCHS}: {ts}")

    print(f"\n✅ Synthetic historical rasters saved in:")
    print(f"   {HIST_DRY_DIR}")
    print(f"   {HIST_FIRE_DIR}")
    print("Now run fire_overlay.py, then module4_train.py")

if __name__ == "__main__":
    run_module3_historical()
