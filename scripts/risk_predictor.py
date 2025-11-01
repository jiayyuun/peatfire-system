#Module 5 — Predict fire risk using dryness & learned threshold

import json, os

def load_threshold(default=0.65):
    # load threshold from training output, use default if file missing
    try:
        with open("../models/fire_threshold.json", "r") as f:
            data = json.load(f)
            return float(data.get("risk_threshold", default))
    except:
        return default

def classify_risk(dryness, threshold):
    # compare dryness vs learned threshold
    if dryness >= threshold + 0.10:
        return "HIGH"   # well above danger line
    elif dryness >= threshold:
        return "MEDIUM" # touching danger line
    else:
        return "LOW"    # below danger line

def run_module_5(dryness_value=0.75):
    # main entry — load threshold, classify
    threshold = load_threshold()
    risk = classify_risk(dryness_value, threshold)
    return risk

if __name__ == "__main__":
    run_module_5()
