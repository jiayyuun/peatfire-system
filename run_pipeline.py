"""
run_pipeline.py — Main orchestrator for PeatFire-System
Runs Module 1A (InSAR) → 1B (VV backscatter) → Visualization
"""

from pathlib import Path
from real_sentinel.process_sentinel1 import SLC_Processor
from real_sentinel.sentinel1_grd import GRD_Processor
from real_sentinel.generate_maps import ResultVisualizer

def main():
    config_path = Path("real_sentinel/config.yaml")
  
    print("PEATFIRE SYSTEM PIPELINE")


    print("\n[1A] Processing Sentinel-1 SLC → InSAR displacement map...\n")
    slc = SLC_Processor(config_path)
    slc_outputs = slc.run_full_pipeline()

    print("\n[1B] Processing Sentinel-1 GRD → VV backscatter composite...\n")
    grd = GRD_Processor(config_path)
    vv_output = grd.run_full_pipeline()

    print("\n[MAP] Generating publication-quality maps...\n")
    viz = ResultVisualizer(config_path)
    viz.load_data()
    viz.plot_subsidence_map()
    print("Results saved to your reports directory.\n")

if __name__ == "__main__":
    main()
