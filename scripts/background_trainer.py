#to get data from module 3 and train module 4 in the background
import time, os, sys
from contextlib import redirect_stdout

sys.path.append(os.path.dirname(__file__))

# Module 3: simulate new satellite data, then append to historical CSV
from module3_stream import run_module_3_stream
# Module 4: retrain ML model with updated historical data
from train_model import run_module_4

def silent(fn):
    """Run a function without printing anything to the terminal."""
    with open(os.devnull, 'w') as f, redirect_stdout(f):
        return fn()

print("Background trainer active (Module 3 & 4)\n")
# Script runs forever to micmic countinous sentinel data

while True:
    #Add new synthetic satellite + fire data to history
    silent(run_module_3_stream)

    #Retrain model and update threshold in the background
    silent(run_module_4)

    # Wait before next update cycle (60 sec per data set generated - can change longer if you want to mimic 6-12 days)
    time.sleep(60)
