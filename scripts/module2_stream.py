import time, os
import numpy as np
import rasterio
from rasterio.crs import CRS
from datetime import datetime
from synth_utils import (
    gaussian_field, planar_ramp, ar1_series,
    los_from_vertical, default_transform
)

# ---------------------------
# Demo-cycle configuration
# ---------------------------
DRY_STEPS   = 10   # steps of drying per cycle
WET_STEPS   = 5    # steps of rewetting per cycle
SLEEP_SEC   = 5    # wall-clock seconds per step (tune for speed)
CYCLE_LEN   = DRY_STEPS + WET_STEPS

# Bias magnitudes (vertical displacement, meters per step)
DRY_BIAS    = -0.012   # subsidence (drying)
WET_BIAS    = +0.008   # uplift (rewetting)

# Random extremes
P_DROUGHT   = 0.12     # chance of a drought shock during dry phase
DROUGHT_MAG = -0.03    # sudden extra subsidence (m)
P_STORM     = 0.08     # chance of a storm pulse during wet phase
STORM_MAG   = +0.03    # sudden uplift (m)

# Slow background trend (very small)
TREND_COEF  = 0.00005  # m/step

# Noise / AR(1) memory
AR_PHI      = 0.93
NOISE_STD   = 0.0005
NOISE_SIGMA = 10       # pixel correlation scale

# Geometry / IO
H, W = 200, 200
INCIDENCE_DEG = 37.0
PX = 30.0
CRS_CODE = 3857

INPUT_PATH = "../data/inputs/displacement.tif"  # LOS displacement output (m)
STATE_PATH = "../data/temp/live_state.npz"      # stores previous vertical field


def generate_live_displacement(t_idx: int):
    """Generate one synthetic displacement frame with balanced dry/wet cycles."""

    # Load previous vertical displacement (for AR(1) memory)
    if os.path.exists(STATE_PATH):
        prev = np.load(STATE_PATH)["dvert_prev"]
    else:
        prev = np.zeros((H, W), dtype="float32")

    # Decide phase in this step (balanced demo: 10 dry → 5 wet)
    phase_step = t_idx % CYCLE_LEN
    phase = "DRY" if phase_step < DRY_STEPS else "WET"

    # Phase bias
    phase_bias = DRY_BIAS if phase == "DRY" else WET_BIAS

    # Background trend (very slow)
    trend = TREND_COEF * t_idx

    # Spatial structure + AR(1) temporal evolution
    ramp = planar_ramp(H, W, ax=2e-5, ay=-1.5e-5)
    innovation = gaussian_field(H, W, sigma_px=NOISE_SIGMA, std=NOISE_STD)

    # Vertical displacement (meters)
    dvert = ar1_series(prev, innovation, phi=AR_PHI) + ramp + trend + phase_bias

    # Extremes: drought during DRY, storms during WET
    if phase == "DRY" and np.random.rand() < P_DROUGHT:
        dvert = dvert + DROUGHT_MAG
        shock = "DROUGHT"
    elif phase == "WET" and np.random.rand() < P_STORM:
        dvert = dvert + STORM_MAG
        shock = "STORM"
    else:
        shock = "-"

    # Debug: vertical stats (meters)
    print(f"[STREAM] t={t_idx:04d} phase={phase:3s} shock={shock:7s} "
          f"dvert stats (m): mean={dvert.mean():.5f} min={dvert.min():.5f} max={dvert.max():.5f}")

    # Convert vertical → LOS for Sentinel-1 geometry (meters)
    dlos = los_from_vertical(dvert, incidence_deg=INCIDENCE_DEG).astype("float32")

    # Save GeoTIFF
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

    # Persist vertical state for AR(1) memory
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    np.savez_compressed(STATE_PATH, dvert_prev=dvert.astype("float32"))

    print(f"[Module2] Wrote LOS displacement → {INPUT_PATH} @ {datetime.now().isoformat()}")


if __name__ == "__main__":
    print("Live displacement generator running (Module 2 — Balanced Demo Mode)")
    t = 0
    while True:
        generate_live_displacement(t)
        t += 1
        time.sleep(SLEEP_SEC)
