#Module 3 — Build synthetic HISTORICAL dataset, Simulates several years of Sentinel-1 cycles BEFORE system goes live., Used to train the ML threshold model (Module 4)
import numpy as np, pandas as pd, os, rasterio
from datetime import datetime, timedelta
from rasterio.crs import CRS
from synth_utils import (
    gaussian_field, planar_ramp, ar1_series, seasonal_component,
    los_from_vertical, fire_probability_from_dryness, cluster_mask,
    default_transform
)

# Synthetic raster size(in pixels)
H, W = 200, 200
# 120 synthetic satellite passes ≈ 3.5 years at ~10-day repeat
EPOCHS = 120
# Physics constants - can change if you want to experiment
ABS_MAX_CM = 10.0          # max dryness accumulation (cm)
RECOVERY_FACTOR = 0.3       # percentage of peat recovery during re-wetting
INCIDENCE = 37.0            # Sentinel-1 incidence angle - used to cater to angular tilt

# Output paths
TRAIN_OUT = "../data/historical/training_data.csv"
HIST_DISP_DIR = "../data/historical/displacement/"
HIST_FIRE_DIR = "../data/historical/fires/"
# Make folders if missing
os.makedirs("../data/historical", exist_ok=True)
os.makedirs(HIST_DISP_DIR, exist_ok=True)
os.makedirs(HIST_FIRE_DIR, exist_ok=True)

#Convert LOS displacement to cumulative dryness
#cum = previous dryness memory
#dlos = current displacement (m)
def displacement_to_dryness(dlos, cum):
    disp_cm = dlos * 100                       # convert m to cm
    step_sub = np.clip(-disp_cm, 0, None)      # drying (subsidence)
    step_up  = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR  # rewetting (uplift)
    cum = np.clip(cum + step_sub - step_up, 0, ABS_MAX_CM)   # update memory
    dryness = np.clip(cum / ABS_MAX_CM, 0, 1)  # normalize 0–1
    return dryness, cum

#Create synthetic historic Sentinel-1 displacement + dryness + fire masks
def run_module3_historical():
    print(f"[HIST] Generating {EPOCHS} synthetic displacement epochs...")
    rows = []                                    # holds training rows
    cum = np.zeros((H, W), dtype="float32")      # dryness memory map
    start_date = datetime(2020, 1, 1)            # start year

    for t in range(EPOCHS):
        #Generate synthetic vertical ground motion
        trend = 0.00015 * t                      # long-term drying trend
        season = seasonal_component(t, amp_m=0.004, period=36)  # seasonal cycle
        ramp = planar_ramp(H, W, ax=1.2e-5, ay=-9e-6)            # spatial tilt
        innovation = gaussian_field(H, W, sigma_px=10, std=0.0025)  # spatial noise
        # AR-1 model gives smooth time evolution
        dvert = ar1_series(cum / 100.0, innovation, phi=0.92) + trend + season + ramp
        # Convert vertical → LOS for Sentinel-1 geometry
        dlos = los_from_vertical(dvert, incidence_deg=INCIDENCE)
        # Update cumulative dryness index
        dryness, cum = displacement_to_dryness(dlos, cum)
        # Simulate fire occurrence probability from dryness
        fire_prob = fire_probability_from_dryness(dryness, bias=-1.1, scale=3.4)
        # Make realistic clustered fire scars
        fire_mask = cluster_mask(fire_prob, cluster_sigma=2.0)
        # Build filenames for this timestamp
        ts = (start_date + timedelta(days=10*t)).strftime("%Y%m%d")
        disp_file = f"{HIST_DISP_DIR}/disp_{ts}.tif"
        fire_file = f"{HIST_FIRE_DIR}/fire_{ts}.tif"

        #Save displacement + fire rasters
        profile = {
            "driver":"GTiff","dtype":"float32",
            "width":W,"height":H,"count":1,
            "crs":CRS.from_epsg(3857),
            "transform":default_transform(px=30)
        }
        with rasterio.open(disp_file,"w",**profile) as dst:
            dst.write(dlos.astype("float32"),1)
        with rasterio.open(fire_file,"w",**profile) as dst:
            dst.write(fire_mask.astype("uint8"),1)

        # Random sample from map to create tabular training data
        flat_dry = dryness.flatten()
        flat_fire = fire_mask.flatten()
        idx = np.random.default_rng().choice(flat_dry.size, 400, replace=False)

        rows.append(pd.DataFrame({
            "timestamp": [(start_date + timedelta(days=10*t)).isoformat()] * len(idx),
            "dryness": flat_dry[idx],
            "fire_occurred": flat_fire[idx]
        }))

        print(f"[HIST] Epoch {t+1}/{EPOCHS} saved")

    #Combine all rows + save CSV
    full = pd.concat(rows)
    full.to_csv(TRAIN_OUT, index=False)

    print(f"\nHistorical training dataset built → {TRAIN_OUT}")
    print(f"Total samples: {len(full)}")
    print("Now run module4 to train the ML model.")


if __name__ == "__main__":
    run_module3_historical()
