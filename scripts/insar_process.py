
# Run SNAP InSAR interferogram workflow from Python - module not used in demo
import subprocess
import os

GPT = "/Applications/snap/bin/gpt"

def run_insar(master, slave, workflow, output, memory="8G"):
# Runs an InSAR workflow using SNAP's command-line interface.

    master = os.path.expanduser(master)
    slave = os.path.expanduser(slave)
    workflow = os.path.expanduser(workflow)
    output = os.path.expanduser(output)

    #Check required files exist
    if not os.path.exists(master):
        raise FileNotFoundError(f"Master SAFE not found: {master}")
    if not os.path.exists(slave):
        raise FileNotFoundError(f"Slave SAFE not found: {slave}")
    if not os.path.exists(workflow):
        raise FileNotFoundError(f"Workflow XML not found: {workflow}")

    #Build command to run SNAP
    cmd = [
        GPT, workflow,
        f"-Pmaster={master}/manifest.safe",  
        f"-Pslave={slave}/manifest.safe",   
        "-Psubswath=IW2",                   
        "-Ppolarization=VV",                 
        f"-Pout={output}",                   
        f"-c {memory}"                       
    ]

    print("Running SNAP InSAR workflow...")
    print(" ".join(cmd))

    #Run SNAP 
    process = subprocess.Popen(" ".join(cmd), shell=True)
    process.communicate()
    #Check success
    if process.returncode == 0:
        print(f"Done. Output saved to: {output}")
    else:
        print("SNAP processing failed")
#example usage
if __name__ == "__main__":
    master = "~/peatfire-system/data/slc/S1A_IW_SLC__1SDV_20150612T222331_20150612T222359_006346_0085A3_F8ED.SAFE"
    slave  = "~/peatfire-system/data/slc/S1A_IW_SLC__1SDV_20150706T222332_20150706T222359_006696_008F4F_D740.SAFE"
    workflow = "~/peatfire-system/graphs/ifg_workflow.xml"
    output = "~/peatfire-system/data/products/kerumutan_ifg"

    run_insar(master, slave, workflow, output)
