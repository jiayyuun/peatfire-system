# PEATGUARD v1.0.0 — Peatland Fire Early-Warning System

Synthetic Sentinel-1 peat subsidence → dryness → fire-risk early-warning pipeline.

---

## System Architecture

```
        ┌────────────────────────┐
        │  Synthetic Sentinel-1  │
        │  Displacement Stream  │
        │ (module2_stream.py)   │
        └──────────┬────────────┘
                   │  Vertical displacement (cm)
                   ▼
        ┌────────────────────────┐
        │   Dryness Model (M2)  │
        │  dryness_model.py      │
        │  physics-informed      │
        └──────────┬────────────┘
                   │  Dryness index (0-1)
                   ▼
        ┌────────────────────────┐
        │ Historical Data Engine │
        │ module3_historical.py  │
        │ + fire_overlay.py      │
        └──────────┬────────────┘
                   │  Synthetic features + labels
                   ▼
        ┌────────────────────────┐
        │   ML Fire-Risk Model   │
        │   train_model.py       │
        │   (updates over time)  │
        └──────────┬────────────┘
                   │  model.pkl
                   ▼
        ┌────────────────────────┐
        │ Real-Time Inference    │
        │ run_pipeline.py        │
        └──────────┬────────────┘
                   │ Risk level (LOW/MED/HIGH)
                   ▼
        ┌────────────────────────┐
        │  Live Dryness Plot     │
        │ plot_dryness_live.py   │
        └────────────────────────┘
```

> Data flow: **Displacement → Dryness → Risk → Visualization**




---

## Features

- Synthetic Sentinel-1 displacement (monsoon + ENSO + extremes)
- Physics-informed peat subsidence → dryness model
- Cumulative hydrology memory + partial-rewetting
- Synthetic training dataset + fire-label synthesis
- ML-based fire-risk classifier
- Real-time dryness & risk output
- Auto-generated chart for last 10 timesteps

---

## Directory Structure

```
peatfire-system/
├── scripts/
│   ├── dryness_model.py        # Module 2: displacement → dryness
│   ├── module2_stream.py       # Live synthetic Sentinel-1 stream
│   ├── module3_historical.py   # Synthetic historical generator
│   ├── fire_overlay.py         # Raster → CSV converter
│   ├── train_model.py          # ML model trainer (Module 4)
│   ├── risk_predictor.py       # Risk inference (Module 5)
│   ├── run_pipeline.py         # Real-time dryness + risk
│   └── plot_dryness_live.py    # Dryness chart
├── data/
│   ├── inputs/
│   ├── products/
│   └── historical/
├── models/
└── requirements.txt
```

---

## Installation

```bash
git clone https://github.com/jiayyuun/peatfire-system.git
cd peatfire-system

conda create -n peatinsar python=3.10 -y
conda activate peatinsar

pip install -r requirements.txt
```

---

## Running the Pipeline

### 1) Generate historical data + train model
```bash
cd scripts
python module3_historical.py
python fire_overlay.py
python train_model.py
```

### 2) Start live Sentinel-1 stream (Terminal 1)
```bash
python module2_stream.py
```

### 3) Real-time fire-risk engine (Terminal 2)
```bash
python run_pipeline.py
```

### 4) Live dryness visualizer (Terminal 3)
```bash
python plot_dryness_live.py
```

---

## Output Interpretation

### Dryness Index (0–1)

| Value | Meaning |
|------:|--------|
| 0.0 | Fully saturated (safe) |
| 0.5 | Drying trend |
| 0.75 | High stress |
| 1.0 | Critical dryness |

### Fire-Risk Levels

| Level | Meaning |
|------:|--------|
| LOW | Safe |
| MEDIUM | Drying trend detected |
| HIGH | Fire danger alert |

---

## Roadmap

- Real Sentinel-1 ingestion (.SAFE)
- SNAP / MintPy InSAR pipeline
- Real peat hydrology validation data
- NASA FIRMS integration
- Web dashboard (Mapbox) + SMS/Telegram alerts

---

## Disclaimer

Research prototype for peat fire early-warning.  
Future work will integrate real SAR processing + ground truthing.

---
