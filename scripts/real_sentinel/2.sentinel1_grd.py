"""
MODULE 1B: Sentinel-1 GRD Processing (Backscatter for Canal Detection)
Process GRD images to extract VV backscatter (dark linear features = canals)

Output: vv_median.tif
"""

import subprocess
import yaml
from pathlib import Path
import rasterio
import numpy as np
from datetime import datetime

class GRD_Processor:
    def __init__(self, config_path="config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.gpt = Path(self.config['snap']['gpt_path'])
        self.grd_files = [Path(f) for f in self.config['sentinel1']['grd_files']]
        self.output_dir = Path(self.config['output']['products'])
        self.temp_dir = Path(self.config['output']['temp'])
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Configuration loaded")
        print(f"  GRD files: {len(self.grd_files)}")
    
    def verify_inputs(self):
        """Check if GRD files exist"""
        for grd in self.grd_files:
            if not grd.exists():
                raise FileNotFoundError(f"GRD not found: {grd}")
        if not self.gpt.exists():
            raise FileNotFoundError(f"SNAP GPT not found: {self.gpt}")
        print("✓ Input files verified")
    
    def run_gpt(self, graph_xml, output_name, **params):
        """Execute SNAP GPT command"""
        output_path = self.temp_dir / output_name
        
        cmd = [
            str(self.gpt),
            str(graph_xml),
            f"-Poutput={output_path}",
        ]
        
        for key, val in params.items():
            cmd.append(f"-P{key}={val}")
        
        cmd.extend(["-c", f"{self.config['snap']['cache_size_gb']}G"])
        
        print(f"\n▶ Running: {graph_xml.stem}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=False
        )
        
        if result.returncode != 0:
            print(f"❌ ERROR:\n{result.stderr}")
            raise RuntimeError(f"GPT failed: {graph_xml.stem}")
        
        print(f"✓ Complete: {output_name}")
        return output_path
    
    def process_single_grd(self, grd_path, idx):
        """Process one GRD image: calibrate → terrain-correct → dB"""
        print(f"\n--- Processing GRD {idx+1}/{len(self.grd_files)} ---")
        
        # Step 1: Apply orbit file
        graph1 = Path("graphs/grd_01_orbit.xml")
        orbit_out = self.run_gpt(
            graph1,
            f"grd_{idx}_orbit.dim",
            input=str(grd_path)
        )
        
        # Step 2: Calibrate to sigma0
        graph2 = Path("graphs/grd_02_calibrate.xml")
        cal_out = self.run_gpt(
            graph2,
            f"grd_{idx}_calibrated.dim",
            input=str(orbit_out),
            polarization=self.config['processing']['polarization']
        )
        
        # Step 3: Speckle filtering (Lee Sigma 7x7)
        graph3 = Path("graphs/grd_03_speckle_filter.xml")
        filt_out = self.run_gpt(
            graph3,
            f"grd_{idx}_filtered.dim",
            input=str(cal_out)
        )
        
        # Step 4: Terrain correction (geocode)
        graph4 = Path("graphs/grd_04_terrain_correct.xml")
        tc_out = self.run_gpt(
            graph4,
            f"grd_{idx}_tc.dim",
            input=str(filt_out),
            pixelSpacingInMeter=30
        )
        
        # Step 5: Convert to dB
        graph5 = Path("graphs/grd_05_db_convert.xml")
        db_out = self.run_gpt(
            graph5,
            f"grd_{idx}_db.dim",
            input=str(tc_out)
        )
        
        return db_out
    
    def create_median_composite(self, processed_grds):
        """Stack GRDs and compute median (reduces speckle noise)"""
        print("\n▶ Creating median composite...")
        
        # Read all VV bands
        vv_stack = []
        profile = None
        
        for grd_dim in processed_grds:
            data_dir = grd_dim.parent / (grd_dim.stem + ".data")
            vv_img = list(data_dir.glob("Sigma0_VV_db*.img"))[0]
            
            with rasterio.open(vv_img) as src:
                if profile is None:
                    profile = src.profile
                    profile.update(driver='GTiff', compress='lzw')
                
                vv_data = src.read(1)
                vv_stack.append(vv_data)
        
        # Compute median across time (robust to outliers)
        vv_median = np.nanmedian(np.stack(vv_stack, axis=0), axis=0)
        
        # Save output
        output_tif = self.output_dir / "vv_median.tif"
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(vv_median.astype('float32'), 1)
        
        print(f"✓ VV median composite: {output_tif}")
        return output_tif
    
    def run_full_pipeline(self):
        """Execute complete GRD workflow"""
        print("\n" + "="*50)
        print("MODULE 1B: SENTINEL-1 GRD PROCESSING")
        print("="*50)
        
        start_time = datetime.now()
        
        try:
            self.verify_inputs()
            
            # Process each GRD
            processed = []
            for i, grd in enumerate(self.grd_files):
                result = self.process_single_grd(grd, i)
                processed.append(result)
            
            # Create median composite
            vv_median = self.create_median_composite(processed)
            
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            print(f"\n✓ MODULE 1B COMPLETE ({elapsed:.1f} minutes)")
            print(f"  Product saved to: {vv_median}")
            
            return vv_median
            
        except Exception as e:
            print(f"\n❌ PIPELINE FAILED: {e}")
            raise

if __name__ == "__main__":
    processor = GRD_Processor()
    processor.run_full_pipeline()
