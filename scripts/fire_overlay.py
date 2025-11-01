# Module 3 — Simulate historical satellite input + build cumulative dryness training data
import rasterio, numpy as np, pandas as pd, os
from datetime import datetime

RAW_DIR = "../data/raw_inputs/"
HIST_PATH = "../data/historical/training_data.csv"

MAX_DRY_CM = 10
RECOVERY_FACTOR = 0.3  # rewetting slower than drying

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs("../data/historical", exist_ok=True)


def simulate_displacement(path, seasonal_bias):

    # base random displacement, normal dist to force variability
    fake_disp = np.random.normal(loc=seasonal_bias, scale=0.03, size=(100,100))

    # 5% chance extreme drought pulse
    if np.random.rand() < 0.05:
        fake_disp += -0.10

    # 3% chance heavy rainstorm recharge
    if np.random.rand() < 0.03:
        fake_disp += 0.12

    # peat dome shape: center wetter, edges dry faster
    rows, cols = fake_disp.shape
    y, x = np.ogrid[:rows, :cols]
    dist = np.sqrt((x-cols/2)**2 + (y-rows/2)**2)
    edge_factor = dist / dist.max()  # 0 center → 1 edge
    fake_disp += edge_factor * -0.02  # edges dry faster

    # Save raster
    profile = {"driver":"GTiff","dtype":"float32","width":100,"height":100,"count":1}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(fake_disp.astype(np.float32), 1)


def simulate_fire_mask(path, dryness):
    mask = (np.random.rand(*dryness.shape) < dryness * 0.15).astype("uint8")
    profile = {"driver":"GTiff","dtype":"uint8","width":100,"height":100,"count":1}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(mask, 1)


def run_module_3_stream():

    # seasonal sinus forcing (more realistic than if/else)
    doy = datetime.now().timetuple().tm_yday
    season_wave = np.sin(2 * np.pi * (doy / 365))
    seasonal_bias = 0.03 * season_wave - 0.02  # peaks dry, troughs wet

    disp_path = f"{RAW_DIR}/disp_{datetime.now().timestamp()}.tif"
    simulate_displacement(disp_path, seasonal_bias)

    with rasterio.open(disp_path) as src:
        disp = src.read(1).astype(np.float32)

    disp_cm = disp * 100
    step_sub = np.clip(-disp_cm, 0, None)
    step_up = np.clip(disp_cm, 0, None) * RECOVERY_FACTOR

    # Initialize dryness memory on first run — random 0–3 cm head start
    global dryness_cum
    try:
        dryness_cum
    except NameError:
        dryness_cum = np.random.uniform(0, 3, disp.shape)

    # exponential memory decay (like groundwater)
    dryness_cum = dryness_cum * 0.995 + step_sub - step_up
    dryness_cum = np.clip(dryness_cum, 0, MAX_DRY_CM)

    dryness_idx = np.clip(dryness_cum / MAX_DRY_CM, 0, 1)

    fire_path = f"{RAW_DIR}/fire_{datetime.now().timestamp()}.tif"
    simulate_fire_mask(fire_path, dryness_idx)

    with rasterio.open(fire_path) as src:
        fire = src.read(1)

    # sample 500 random pixels
    idx = np.random.choice(len(dryness_idx.flatten()), 500)
    batch = pd.DataFrame({
        "timestamp": [datetime.now()] * 500,
        "dryness": dryness_idx.flatten()[idx],
        "fire_occurred": fire.flatten()[idx]
    })

    batch.to_csv(HIST_PATH, mode="a", header=not os.path.exists(HIST_PATH), index=False)

    return float(np.mean(dryness_idx)), int(np.mean(fire) > 0.01)
