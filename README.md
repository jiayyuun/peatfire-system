
PEATGUARD Version 1.0.0 - PeatFire Early-Warning System (Synthetic Sentinel-1 Simulation)

PEATGUARD V1.0.0 is a fully automated peatland fire early-warning pipeline.
It simulates Sentinel-1 InSAR displacement, converts it to peat dryness, trains a model and predicts fire risk of the area.

Features
--------
- End-to-end autonomous pipeline
- Synthetic SAR data generator (no external API required)
- Physics-aware peat subsidence → dryness model
- ML model trained on cumulative dryness history
- Live monitoring + rolling dryness graph

Project Structure
-----------------
peatfire-system/
├── scripts/
│   ├── dryness_model.py
│   ├── module2_stream.py
│   ├── module3_historical.py
│   ├── module3_stream.py
│   ├── train_model.py
│   ├── risk_predictor.py
│   ├── run_pipeline.py
│   └── plot_dryness_live.py
├── data/
│   ├── inputs/
│   ├── products/
│   ├── historical/
│   └── raw_inputs/
├── models/
└── requirements.txt

Quick Start
-----------
1. Clone repository
   git clone https://github.com/jiayyuun/peatfire-system.git
   cd peatfire-system
2. Create environment
   conda create -n peatinsar python=3.10 -y
   conda activate peatinsar
   pip install -r requirements.txt

Running the System
------------------
Step 1 — Build historical synthetic dataset
   cd scripts
   python module3_historical.py
   python train_model.py
Step 2 — Start live synthetic displacement stream
   python module2_stream.py
Step 3 — Start background trainer (new data + continuous ML updates)
   python background_trainer.py
Step 4 — Run real‑time risk assessment
   python run_pipeline.py
Step 5 — Live rolling dryness chart
   python plot_dryness_live.py

Output Interpretation
---------------------
Dryness Index (0–1 scale):
- 0.0 → fully wet peat
- 1.0 → extremely dry peat

Risk levels:
- LOW — safe
- MEDIUM — drying trend
- HIGH — fire danger alert

Next Enhancements
-----------------
- Integrate real Sentinel‑1 .SAFE files
- SNAP‑based InSAR processing chain
- Web dashboard and alerting API


<img width="432" height="636" alt="image" src="https://github.com/user-attachments/assets/cb09546c-e264-4add-bf42-633aa848f007" />
