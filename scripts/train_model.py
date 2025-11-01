#Module 4 — Train ML model to learn dryness → fire relationship

import pandas as pd, os, json, numpy as np, joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

def train_fire_model(csv, model_out, th_path):
    # load historical dryness + fire samples
    df = pd.read_csv(csv)
    # ensure enough data to train
    if len(df) < 200:
        return model_out, None
    # feature = dryness index, label = fire or not
    X = df[['dryness']]
    y = df['fire_occurred']
    # split into train/test
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    # random forest model (simple + stable)
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        class_weight="balanced"
    )
    model.fit(Xtr, ytr)
    score = model.score(Xte, yte)  # accuracy on test data
    joblib.dump(model, model_out)  # save model

    # set dryness threshold from accuracy (higher skill → higher threshold)
    threshold = float(np.clip(score, 0.5, 0.85))

    # save threshold to JSON
    with open(th_path, "w") as f:
        json.dump({"risk_threshold": threshold}, f)

    return model_out, threshold

def run_module_4():
    # run training on stored historical dataset
    return train_fire_model(
        "../data/historical/training_data.csv",
        "../data/products/fire_risk_model.pkl",
        "../models/fire_threshold.json"
    )
