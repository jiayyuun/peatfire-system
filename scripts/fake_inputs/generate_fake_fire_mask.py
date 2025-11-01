#generating fake fire data to plot a synthetic fire map for overlay in module 3
import numpy as np
import rasterio
import os

#Path to the dryness map and output fire mask
dry_path = "../data/products/dryness_index.tif"
out_path = "../data/products/fire_mask.tif"

if not os.path.exists(dry_path):
    raise FileNotFoundError("Dryness map not found. Run module 2 first.")

#Loading dryness index map
with rasterio.open(dry_path) as src:
    dry = src.read(1)
    profile = src.profile

h, w = dry.shape
mask = np.zeros((h, w), dtype="uint8")

#Create random fire clusters in very dry areas
np.random.seed(42) 
for _ in range(12):
    cy = np.random.randint(0, h)     #random cluster center (y)
    cx = np.random.randint(0, w)     #random cluster center (x)
    r = np.random.randint(6, 14)     #random radius for cluster

    # create a grid and select pixels inside circle
    yy, xx = np.ogrid[:h, :w]
    region = (yy - cy)**2 + (xx - cx)**2 <= r*r

    #mark region as fire only if dryness is high
    mask[region & (dry > 0.60)] = 1

# Update raster metadata for fire map
profile.update(dtype="uint8")

#Save fire mask raster
with rasterio.open(out_path, "w", **profile) as dst:
    dst.write(mask, 1)

print(f"Fake fire mask saved → {out_path}")
print(f"Fire pixels: {mask.sum()}")
