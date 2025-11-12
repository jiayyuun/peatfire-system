PEATGUARD v2.0 — Peatland Carbon & Canal Monitoring System

Sentinel-1 InSAR + VV Backscatter pipeline for detecting peat subsidence and canal degradation — designed for integration into carbon-credit MRV (Measurement, Reporting, Verification) workflows.

---

## System Architecture

        ┌────────────────────────┐
        │ Sentinel-1 SLC Pairs  │
        │  (module1A_slc.py)    │
        └──────────┬────────────┘
                   │  Phase → Displacement (mm/yr)
                   ▼
        ┌────────────────────────┐
        │  InSAR Processor (M1A) │
        │  Coherence + Quality   │
        └──────────┬────────────┘
                   │  subsidence_velocity.tif
                   ▼
        ┌────────────────────────┐
        │ Sentinel-1 GRD Stack   │
        │  (module1B_grd.py)     │
        └──────────┬────────────┘
                   │  VV Backscatter (dB)
                   ▼
        ┌────────────────────────┐
        │  Canal Detection Engine│
        │  (Module 2, optional)  │
        └──────────┬────────────┘
                   │  canal_confirmed.shp
                   ▼
        ┌────────────────────────┐
        │  Visualizer (M3)       │
        │  (generate_maps.py)    │
        └──────────┬────────────┘
                   │  Publication-quality maps
                   ▼
        ┌────────────────────────┐
        │  Carbon Credit Reports │
        │  (maps + metrics)      │
        └────────────────────────┘

Data flow: InSAR Subsidence → VV Backscatter → Canal Detection → Visualization → Carbon Reporting

---

## Features

- Automated Sentinel-1 SLC/GRD preprocessing via SNAP GPT XML graphs
- Subsidence velocity mapping (mm yr⁻¹) for hydrological stress tracking
- VV backscatter compositing to identify water canals and degradation lines
- Coherence masking for quality assurance
- Carbon-loss estimation from subsidence velocity (t CO₂ ha⁻¹ yr⁻¹)
- Publication-ready map visualizations for reports or dashboards
- Modular design: run individual modules or the full workflow
---

## Directory Structure
```
peatfire-system/
├── scripts/
│   └── graphs/                   # ESA SNAP GPT workflows
│       ├── 01_apply_orbit.xml
│       ├── 02_coregister.xml
│       ├── 03_interferogram.xml
│       ├── 04_topo_removal.xml
│       ├── 05_goldstein_filter.xml
│       ├── 06a_snaphu_export.xml
│       ├── 06b_snaphu_import.xml
│       ├── 07_phase_to_disp.xml
│       ├── 08_terrain_correct.xml
│       ├── 09_split.xml
│       └── 10_deburst.xml
│
├── real_sentinel/
│   ├── 1.process_sentinel1.py    # Module 1A: InSAR (SLC)
│   ├── 2.sentinel1_grd.py        # Module 1B: VV Backscatter (GRD)
│   ├── 3.generate_maps.py        # Module 3: Map Visualizer
│   └── config.yaml               # System configuration file
│
├── run_pipeline.py               # Unified pipeline runner
├── requirements.txt
├── README.md
└── .gitignore
```
---

## Installation

```bash
git clone https://github.com/jiayyuun/peatfire-system.git
cd peatfire-system

conda create -n peatguard python=3.10 -y
conda activate peatguard

pip install -r requirements.txt
```
Ensure ESA SNAP (v9 or higher) is installed:
https://step.esa.int/main/download/

Update the SNAP GPT path in config.yaml:
```
snap:
  gpt_path: "C:\\Program Files\\esa-snap\\bin\\gpt.exe"
```
---

## Running the Pipeline

A. Run the full workflow
```
python run_pipeline.py
```

B. Run individual modules
```
python real_sentinel/1.process_sentinel1.py    # Module 1A – InSAR
python real_sentinel/2.sentinel1_grd.py        # Module 1B – VV Backscatter
python real_sentinel/3.generate_maps.py        # Module 3 – Visualization
```
---

## Output Summary
| Output                  | Description                      |
| ----------------------- | -------------------------------- |
| subsidence_velocity.tif | Vertical displacement (mm yr⁻¹)  |
| coherence_median.tif    | Coherence layer (quality metric) |
| quality_mask.tif        | Mask of reliable pixels          |
| vv_median.tif           | Median VV backscatter (dB)       |
| canal_confirmed.shp     | Confirmed canal alignments       |
| canal_potential.shp     | Potential or degraded canals     |
| /reports/               | Publication-quality map outputs  |

---
## Output interpretation
Subsidence Velocity (mm yr⁻¹)
|     Range | Interpretation                   |
| --------: | -------------------------------- |
|     < −50 | Severe subsidence (drained peat) |
| −50 → −20 | Active drying zone               |
|   −20 → 0 | Stable or rewetted               |
|       > 0 | Noise or uplift                  |

Coherence
- 0.3 → Reliable interferometric phase
- < 0.3 → Vegetation or decorrelation noise

VV Backscatter (dB)
- < −18 dB → Likely water body or canal
- −10 dB → Vegetated or dry surface

## Roadmap

- Real-time dashboard (Backend design)
- Mobile alert module (SMS/Telegram) for high-risk canals
- AI-based canal segmentation (U-Net on VV composites)
- Cloud deployment with auto-report generation (PDF + map)
- Integration with PeatFire early-warning system

---

## Disclaimer

Research prototype for peatland carbon monitoring and canal degradation detection.
Intended for scientific, conservation, and carbon-credit applications.
Further calibration with carbon-credit calculation is ongoing.

---

## Citation

If you use PEATGUARD in your research or projects, please cite:

J. Yuun et al. (2025)
PEATGUARD v2.0: Sentinel-1 InSAR-based Monitoring System for Peatland Carbon and Canal Restoration
Nanyang Technological University, Singapore.
