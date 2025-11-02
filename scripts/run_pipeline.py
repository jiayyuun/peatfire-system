# Main pipeline: run dryness calc (module 2) + fire risk (module 5)

import sys, os, time
from datetime import datetime

# allow importing local modules
sys.path.append(os.path.dirname(__file__))

# suppress noisy raster warnings - bc we are using synthetic data now, so it doesn't fully have the geolocations etc like real sentinel data
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", module="rasterio")

from dryness_model import run_module_2   # compute dryness index
from risk_predictor import run_module_5  # classify risk

# timestamp helper
def ts(): 
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# simple loading bar
def bar(text):
    for i in range(25):
        time.sleep(0.03)
        print(f"\r{text} [{'█'*i}{'░'*(24-i)}]", end="")
    print()

# run pipeline
print(f"\nSystem time: {ts()}\n")

bar("Processing new satellite dryness data")
dryness = run_module_2()  # get live/most recent dryness index

bar("Assessing wildfire danger")
risk = run_module_5(dryness)  # classify risk level

print(f"\nDryness Index: {dryness:.3f}")
print(f"Final Fire Risk Level: {risk}")

# log dryness for live plotting
log_path = "../data/products/dryness_log.csv"
with open(log_path, "a") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{dryness:.4f}\n")

# console alert printed out
if risk == "HIGH":
    print("ALERT — High wildfire danger!")
elif risk == "MEDIUM":
    print("CAUTION — Drying trend detected.")
else:
    print("SAFE — No action needed.")

# --- Plot recent dryness history (last 10) ---
try:
    import pandas as pd
    import matplotlib.pyplot as plt

    df = pd.read_csv("../data/products/dryness_log.csv", header=None, names=["timestamp", "dryness"])

    # Keep last 10 readings
    tail = df.tail(10)

    # Create plot
    plt.figure(figsize=(6, 3))
    plt.plot(tail["timestamp"], tail["dryness"], marker="o", linewidth=2)
    plt.xticks(rotation=45, ha="right")
    plt.title("Recent Dryness Index (Last 10 datapoints)")
    plt.ylabel("Dryness Index (0–1)")
    plt.ylim(0, 1)
    plt.tight_layout()

    plt.show()

except Exception as e:
    print(f"[WARN] Could not plot history: {e}")

