# Synthetic physics to mimic Sentinel-1 displacement + peat drying behaviour
import numpy as np
from scipy.ndimage import gaussian_filter
from affine import Affine

def gaussian_field(h, w, sigma_px=12, std=0.005, seed=None):
    # create smooth noise (looks like atmosphere / natural variation)
    rng = np.random.default_rng(seed)
    z = rng.normal(0, 1, (h, w))
    z = gaussian_filter(z, sigma=sigma_px, mode="reflect")  # blur for realism
    z = z / (np.std(z) + 1e-8) * std  # scale to displacement magnitude
    return z

def planar_ramp(h, w, ax=0.00002, ay=-0.000015):
    # slow tilt across area (like land very slowly bending)
    yy, xx = np.mgrid[0:h, 0:w]
    return ax * xx + ay * yy

def ar1_series(prev, innovation, phi=0.9):
    # AR(1) time memory: today ~ mostly yesterday + some noise
    return phi * prev + innovation

def seasonal_component(t_idx, amp_m=0.005, period=24):
    # seasonal cycle (wet to dry seasons)
    return amp_m * np.sin(2*np.pi * (t_idx % period) / period)

def los_from_vertical(d_vert_m, incidence_deg=37.0):
    # convert real vertical motion to what Sentinel-1 sees
    c = np.cos(np.deg2rad(incidence_deg))
    return d_vert_m * c

def default_transform(px=30.0, x0=0.0, y0=0.0):
    # georeference grid: each pixel = 30m, simple origin
    return Affine.translation(x0, y0) * Affine.scale(px, px)

def logistic(p):
    # helper for soft probability curve
    return 1.0 / (1.0 + np.exp(-p))

def fire_probability_from_dryness(dry_idx, bias=-1.0, scale=3.0):
    # map dryness level to chance of fire (more dry = higher chance)
    return logistic(bias + scale * dry_idx)

def cluster_mask(prob, seed=None, cluster_sigma=2.5):
    # make fire patches (not random single pixels)
    rng = np.random.default_rng(seed)
    raw = rng.uniform(size=prob.shape) < prob  # sample pixel-wise fires
    smooth = gaussian_filter(raw.astype(float), cluster_sigma)  # blob them
    return (smooth > 0.35).astype("uint8")  # convert to mask
