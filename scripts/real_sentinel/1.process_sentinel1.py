"""
MODULE 1A: Sentinel-1 SLC Processing (InSAR Displacement)
Process SLC pairs to extract vertical subsidence velocity

Output: subsidence_velocity.tif, coherence_median.tif, quality_mask.tif
"""

import subprocess
import yaml
from pathlib import Path
import rasterio
import numpy as np
from datetime import datetime
import xml.etree.ElementTree as ET
import shutil

class SLC_Processor:
    def __init__(self, config_path="uh/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.gpt = Path(self.config['snap']['gpt_path'])
        self.master = Path(self.config['sentinel1']['slc_master'])
        self.slave = Path(self.config['sentinel1']['slc_slave'])
        self.output_dir = Path(self.config['output']['products'])
        self.temp_dir = Path(self.config['output']['temp'])
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Configuration loaded")
        print(f"  Master: {self.master.name}")
        print(f"  Slave: {self.slave.name}")
    
    def verify_inputs(self):
        """Check if input files exist"""
        if not self.master.exists():
            raise FileNotFoundError(f"Master SLC not found: {self.master}")
        if not self.slave.exists():
            raise FileNotFoundError(f"Slave SLC not found: {self.slave}")
        if not self.gpt.exists():
            raise FileNotFoundError(f"SNAP GPT not found: {self.gpt}")
        print("✓ Input files verified")
    
    def run_gpt(self, graph_xml, output_name, **params):
        """Execute SNAP GPT command (Windows-safe)"""
        output_path = self.temp_dir / output_name
        
        # Build GPT command
        cmd = [
            str(self.gpt),
            str(graph_xml),
            f"-Poutput={output_path}",
        ]
        
        # Add custom parameters
        for key, val in params.items():
            cmd.append(f"-P{key}={val}")
        
        # Add cache size
        cmd.extend(["-c", f"{self.config['snap']['cache_size_gb']}G"])
        
        print(f"\n▶ Running: {graph_xml.stem}")
        print(f"  Output: {output_name}")
        
        # Execute with Windows encoding
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

    def step0_split(self):
        """Split the master and slave SLC products into subswaths/polarizations."""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\09_split.xml")
        
        master_split = self.run_gpt(
            graph,
            "master_split.dim",
            input=str(self.master),
            subswath=self.config['processing']['subswath'],
            polarization=self.config['processing']['polarization']
        )
        
        slave_split = self.run_gpt(
            graph,
            "slave_split.dim",
            input=str(self.slave),
            subswath=self.config['processing']['subswath'],
            polarization=self.config['processing']['polarization']
        )
        
        return master_split, slave_split

    def step1_apply_orbit(self, master_split, slave_split):
        """Apply precise orbit files to split products"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\01_apply_orbit.xml")
        
        master_out = self.run_gpt(
            graph, 
            "master_orbit.dim",
            input=str(master_split)
        )
        
        slave_out = self.run_gpt(
            graph,
            "slave_orbit.dim",
            input=str(slave_split)
        )
        
        return master_out, slave_out
    
    def step2_coregister(self, master_orb, slave_orb):
        """Back-geocode coregistration"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\02_coregister.xml")
        
        coreg_out = self.run_gpt(
            graph,
            "coregistered.dim",
            master=str(master_orb),
            slave=str(slave_orb),
            subswath=self.config['processing']['subswath'],
            polarization=self.config['processing']['polarization']
        )
        
        return coreg_out
    
    def step3_interferogram(self, coreg):
        """Generate interferogram + coherence"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\03_interferogram.xml")
        
        ifg_out = self.run_gpt(
            graph,
            "interferogram.dim",
            input=str(coreg),
            subswath=self.config['processing']['subswath']
        )
        
        return ifg_out
    
    def step3b_deburst(self, ifg):
        """Deburst AFTER interferogram formation (correct TOPS workflow)"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\10_deburst.xml")
        
        deburst_out = self.run_gpt(
            graph,
            "deburst.dim",
            input=str(ifg)
        )
        
        return deburst_out
    
    def step4_topo_phase_removal(self, deburst):
        """Remove topographic phase using DEM"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\04_topo_removal.xml")
        
        dem_path = self.config['dem']['path']
        dem_param = "" if dem_path == "auto" else str(Path(dem_path))
        
        topo_out = self.run_gpt(
            graph,
            "topo_removed.dim",
            input=str(deburst),
            dem=dem_param  # empty = SNAP auto-downloads SRTM
        )
        
        return topo_out
    
    def step5_goldstein_filter(self, topo):
        """Phase filtering (reduce noise)"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\05_goldstein_filter.xml")
        
        filt_out = self.run_gpt(
            graph,
            "filtered.dim",
            input=str(topo)
        )
        
        return filt_out
    
    def step6_unwrap(self, filtered):
        """Phase unwrapping using SNAP's SnaphuExport operator"""
        
        print(f"\n▶ Running: Phase unwrapping with SnaphuExport")
        
        # Step 1: Use SnaphuExport to prepare data for SNAPHU
        graph_export = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\06a_snaphu_export.xml")
        snaphu_folder = self.temp_dir / "snaphu_export"
        
        if snaphu_folder.exists():
            shutil.rmtree(snaphu_folder)
        snaphu_folder.mkdir()
        
        # Run SnaphuExport (this handles all the complex phase extraction)
        cmd = [
            str(self.gpt),
            str(graph_export),
            f"-Pinput={filtered}",
            f"-PtargetFolder={snaphu_folder}",
            "-c", f"{self.config['snap']['cache_size_gb']}G"
        ]
        
        print(f"  Exporting for SNAPHU...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"❌ SnaphuExport failed:\n{result.stderr}")
            raise RuntimeError("SnaphuExport failed")
        
        # Step 2: Find the SNAPHU config file created by SnaphuExport
        conf_files = list(snaphu_folder.glob("*.conf"))
        if not conf_files:
            raise RuntimeError(f"No SNAPHU config found in {snaphu_folder}")
        
        snaphu_conf = conf_files[0]
        print(f"  Found config: {snaphu_conf.name}")
        
        # Step 3: Run SNAPHU
        snaphu_exe = Path.home() / ".snap/auxdata/snaphu/win64/snaphu.exe"
        
        if not snaphu_exe.exists():
            raise RuntimeError(
                f"Snaphu not found: {snaphu_exe}\n"
                "Install via SNAP: Tools → Plugins → SNAPHU Unwrapping"
            )
        
        print(f"  Running SNAPHU (this may take 10-30 minutes)...")
        
        result = subprocess.run(
            [str(snaphu_exe), str(snaphu_conf.name)],
            cwd=str(snaphu_folder),
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        if result.returncode != 0:
            print(f"  SNAPHU stdout: {result.stdout}")
            print(f"  SNAPHU stderr: {result.stderr}")
            raise RuntimeError("SNAPHU unwrapping failed")
        
        print(f"  ✓ Unwrapping complete")
        
        # Step 4: Import unwrapped phase back into SNAP
        graph_import = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\06b_snaphu_import.xml")
        unwrap_out = self.temp_dir / "unwrapped.dim"
        
        cmd = [
            str(self.gpt),
            str(graph_import),
            f"-Pinput={filtered}",
            f"-Pfolder={snaphu_folder}",
            f"-Poutput={unwrap_out}",
            "-c", f"{self.config['snap']['cache_size_gb']}G"
        ]
        
        print(f"  Importing unwrapped phase into SNAP...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"❌ SnaphuImport failed:\n{result.stderr}")
            raise RuntimeError("SnaphuImport failed")
        
        print(f"✓ Complete: unwrapped.dim")
        
        return unwrap_out
        
    def step7_phase_to_displacement(self, unwrapped):
        """Convert phase to LOS displacement (meters)"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\07_phase_to_disp.xml")
        
        disp_out = self.run_gpt(
            graph,
            "displacement.dim",
            input=str(unwrapped)
        )
        
        return disp_out
    
    def step8_terrain_correction(self, disp):
        """Geocode to map coordinates"""
        graph = Path(r"C:\Users\swedha\OneDrive\vscode\MR PEATLAND\peatfire-system-1\graphs\08_terrain_correct.xml")
        
        final_out = self.run_gpt(
            graph,
            "geocoded.dim",
            input=str(disp),
            pixelSpacingInMeter=30  # 30m output resolution
        )
        
        return final_out
    
    def extract_products(self, geocoded_dim):
        """Extract GeoTIFFs from BEAM-DIMAP format"""
        print("\n▶ Extracting final products...")
        
        # Read BEAM-DIMAP data folder
        data_dir = geocoded_dim.parent / (geocoded_dim.stem + ".data")
        
        # Find displacement band (typically named "Phase_ifg_*.img")
        disp_img = list(data_dir.glob("Phase_ifg_*.img"))[0]
        coh_img = list(data_dir.glob("coh_*.img"))[0]
        
        # Convert to GeoTIFF
        subsidence_tif = self.output_dir / "subsidence_velocity.tif"
        coherence_tif = self.output_dir / "coherence_median.tif"
        
        # Use GDAL to convert (rasterio wrapper)
        with rasterio.open(disp_img) as src:
            profile = src.profile
            profile.update(driver='GTiff', compress='lzw')
            
            disp_data = src.read(1)
            
            # Convert phase to vertical displacement (mm/yr)
            # Assume 12-day repeat, convert to annual rate
            wavelength_m = 0.056  # Sentinel-1 C-band
            days_between = 12
            
            # Phase (radians) → LOS displacement (m) → vertical (m) → mm/yr
            los_m = disp_data * (wavelength_m / (4 * np.pi))
            incidence_rad = np.deg2rad(self.config['processing'].get('incidence_angle', 37))
            vertical_m = los_m / np.cos(incidence_rad)
            vertical_mm_yr = vertical_m * 1000 * (365.25 / days_between)
            
            with rasterio.open(subsidence_tif, 'w', **profile) as dst:
                dst.write(vertical_mm_yr.astype('float32'), 1)
        
        # Coherence (copy as-is)
        with rasterio.open(coh_img) as src:
            profile = src.profile
            profile.update(driver='GTiff', compress='lzw')
            coh_data = src.read(1)
            
            with rasterio.open(coherence_tif, 'w', **profile) as dst:
                dst.write(coh_data, 1)
        
        # Generate quality mask
        quality_tif = self.output_dir / "quality_mask.tif"
        coh_threshold = self.config['processing']['coherence_threshold']
        quality_mask = (coh_data >= coh_threshold).astype('uint8')
        
        profile.update(dtype='uint8')
        with rasterio.open(quality_tif, 'w', **profile) as dst:
            dst.write(quality_mask, 1)
        
        print(f"✓ Subsidence velocity: {subsidence_tif}")
        print(f"✓ Coherence: {coherence_tif}")
        print(f"✓ Quality mask: {quality_tif}")
        
        return subsidence_tif, coherence_tif, quality_tif
        
    def run_full_pipeline(self):
        print("\n" + "="*50)
        print("MODULE 1A: SENTINEL-1 SLC PROCESSING")
        print("="*50)
        
        start_time = datetime.now()
        
        try:
            self.verify_inputs()
            
            # CORRECTED PROCESSING ORDER FOR SENTINEL-1 TOPS:
            
            # Step 0: Split (select subswath and polarization)
            master_split, slave_split = self.step0_split()
            
            # Step 1: Apply orbit files (BEFORE coregistration, BEFORE deburst)
            master_orb, slave_orb = self.step1_apply_orbit(master_split, slave_split)
            
            # Step 2: Coregister (Back-Geocoding for TOPS - needs burst structure)
            coreg = self.step2_coregister(master_orb, slave_orb)
            
            # Step 3: Interferogram (still in burst mode)
            ifg = self.step3_interferogram(coreg)
            
            # Step 3b: Deburst (AFTER interferogram - this is the correct position)
            deburst = self.step3b_deburst(ifg)
            
            # Step 4: Topographic phase removal
            topo = self.step4_topo_phase_removal(deburst)
            
            # Step 5: Goldstein filtering
            filt = self.step5_goldstein_filter(topo)
            
            # Step 6: Phase unwrapping
            unwrap = self.step6_unwrap(filt)
            
            # Step 7: Phase to displacement
            disp = self.step7_phase_to_displacement(unwrap)
            
            # Step 8: Terrain correction
            geocoded = self.step8_terrain_correction(disp)
            
            # Extract final products
            outputs = self.extract_products(geocoded)
            
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            print(f"\n✓ MODULE 1A COMPLETE ({elapsed:.1f} minutes)")
            print(f"  Products saved to: {self.output_dir}")
            
            return outputs
            
        except Exception as e:
            print(f"\n❌ PIPELINE FAILED: {e}")
            raise

if __name__ == "__main__":
    processor = SLC_Processor()
    processor.run_full_pipeline()
