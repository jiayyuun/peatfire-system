import time, os
import numpy as np
import rasterio
from rasterio.crs import CRS
from datetime import datetime
from synth_utils import (
    gaussian_field, planar_ramp, ar1_series, seasonal_component,
    los_from_vertical, default_transform
)

# Output path for synthetic displacement
INPUT_PATH = "../data/inputs/displacement.tif"
# File to store previous displacement state (for temporal memory)
STATE_PATH = "../data/temp/live_state.npz"
H, W = 200, 200 # Grid size (200 x 200 pixels)
INCIDENCE_DEG = 37.0 # Sentinel-1 incidence angle (approx)
PX = 30.0 # Pixel resolution (meters)
CRS_CODE = 3857 # Coordinate reference system (Web Mercator)


#creating synthetic map
def generate_live_displacement(t_idx):
    # Load previous state if exists, else start at zero
    if os.path.exists(STATE_PATH):
        prev = np.load(STATE_PATH)["dvert_prev"]
    else:
        prev = np.zeros((H, W), dtype="float32")

    #Build synthetic vertical motion in meters

    # Long-term drying subsidence trend (very slow)
    trend = 0.0002 * t_idx
    # Seasonal pattern (e.g., dry/wet seasons)
    season = seasonal_component(t_idx, amp_m=0.005, period=24)
    # Slight spatial tilt across the image (cm-level)
    ramp = planar_ramp(H, W, ax=2e-5, ay=-1.5e-5)
    # Spatially smooth random variation (noise pattern)
    innovation = gaussian_field(H, W, sigma_px=10, std=0.003)
    # AR(1) temporal process — gives smooth time evolution
    dvert = ar1_series(prev, innovation, phi=0.92) + trend + season + ramp
    # Convert vertical displacement → satellite LOS displacement
    dlos = los_from_vertical(dvert, incidence_deg=INCIDENCE_DEG).astype("float32")

    # save GeoTIFF
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": W, "height": H, "count": 1,
        "crs": CRS.from_epsg(CRS_CODE),
        "transform": default_transform(px=PX)
    }

    os.makedirs(os.path.dirname(INPUT_PATH), exist_ok=True)
    with rasterio.open(INPUT_PATH, "w", **profile) as dst:
        dst.write(dlos, 1)

    #Save current vertical displacement for next timestep
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    np.savez_compressed(STATE_PATH, dvert_prev=dvert.astype("float32"))

    print(f"[Module2] New displacement → {INPUT_PATH} @ {datetime.now().isoformat()}")


if __name__ == "__main__":
    print("Live displacement generator running (Module 2)")

    t = 0  #time counter
    while True:
        generate_live_displacement(t)
        t += 1
        time.sleep(10)   #generate new map every 10 seconds - (can edit to mimic more realistic timings if you want)
