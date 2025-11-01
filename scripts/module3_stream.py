#Module 3 Stream — synthetic Sentinel-1 + fire data for ML training

import rasterio, numpy as np, pandas as pd, os
from datetime import datetime

RAW_DIR = "../data/raw_inputs/"
HIST_PATH = "../data/historical/training_data.csv"
STATE_PATH = "../data/historical/dryness_state.npy"

ABS_MAX_CM = 10            # max dryness memory cap
RECOVERY_FACTOR = 0.3      # rewet strength

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs("../data/historical", exist_ok=True)

def simulate_displacement(path):
    # random LOS displacement (m)
    disp = np.random.uniform(-0.02, 0.02, (200, 200))
    profile = {"driver":"GTiff","dtype":"float32","width":200,"height":200,"count":1}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(disp.astype(np.float32),1)

def run_module_3_stream():
    # new synthetic satellite pass file
    disp_path = f"{RAW_DIR}/raw_disp_{datetime.now().timestamp()}.tif"
    simulate_displacement(disp_path)

    # read displacement
    with rasterio.open(disp_path) as src:
        disp = src.read(1)

    # load cumulative dryness memory
    if os.path.exists(STATE_PATH):
        dryness_cum = np.load(STATE_PATH)
    else:
        dryness_cum = np.zeros_like(disp)

    # displacement → dryness change (cm)
    disp_cm = disp * 100
    step_sub = np.clip(-disp_cm,0,None)                   # drying
    step_up  = np.clip(disp_cm,0,None) * RECOVERY_FACTOR # re-wetting

    # update peat dryness memory
    dryness_cum = np.clip(dryness_cum + step_sub - step_up,0,ABS_MAX_CM)
    np.save(STATE_PATH, dryness_cum)

    # convert to 0-1 dryness index
    dryness_idx = np.clip(dryness_cum / ABS_MAX_CM,0,1)

    # dryness → fire probability
    fire_prob = dryness_idx
    fire_mask = (np.random.rand(*fire_prob.shape) < fire_prob * 0.15).astype(int)

    # sample 500 pixels for ML dataset
    idx = np.random.choice(dryness_idx.size, 500)
    batch = pd.DataFrame({
        "timestamp":[datetime.now()]*500,
        "dryness":dryness_idx.flatten()[idx],
        "fire_occurred":fire_mask.flatten()[idx]
    })

    # append to historical CSV
    batch.to_csv(
        HIST_PATH,
        mode="a",
        header=not os.path.exists(HIST_PATH),
        index=False
    )

    # return summary for logs
    return float(dryness_idx.mean()), int(fire_mask.mean()>0.01)
