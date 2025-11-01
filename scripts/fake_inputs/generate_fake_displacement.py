#generating synthetic input for input into module 2
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

#Path where fake displacement raster will be saved
out_path = "../data/products/displacement.tif"

# Create a synthetic displacement grid
# Negative = ground sinking (drying), Positive = rising (rewetting)
rows, cols = 200, 200
data = np.random.uniform(-0.03, 0.01, size=(rows, cols))

#Set a synthetic map location and pixel size
#(top-left longitude, latitude, pixel_width, pixel_height)
transform = from_origin(102.0, -1.0, 0.0001, 0.0001)

profile = {
    "driver": "GTiff",
    "height": rows,
    "width": cols,
    "count": 1,
    "dtype": "float32",
    "transform": transform,
    "crs": "EPSG:4326"
}
os.makedirs("../data/products", exist_ok=True)

#Save displacement data as a GeoTIFF
with rasterio.open(out_path, "w", **profile) as dst:
    dst.write(data.astype("float32"), 1)

print(f"Fake displacement saved to {out_path}")
