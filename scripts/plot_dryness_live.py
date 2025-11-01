#Plot live last 20 dryness values

import pandas as pd
import matplotlib.pyplot as plt
import time, os

LOG_FILE = "../data/products/dryness_log.csv"

plt.ion()  # interactive plotting
fig, ax = plt.subplots()

def plot_live():
    while True:
        # check log file exists and has data
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
            df = pd.read_csv(LOG_FILE, names=["time", "dryness"])
            df = df.tail(20)  # last 20 records

            ax.clear()
            ax.plot(df["time"], df["dryness"], linewidth=2)
            ax.set_title("Live Dryness Index")
            ax.set_ylabel("Index (0–1)")
            ax.set_xlabel("Time")
            ax.set_ylim(0, 1)

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.pause(0.1)

        time.sleep(2)  # update every 2s

if __name__ == "__main__":
    plot_live()
