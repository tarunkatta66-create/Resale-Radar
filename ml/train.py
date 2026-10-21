"""
Train and evaluate ML models for Smartphone and Laptop resale price prediction.
Trains Linear Regression, Decision Tree, and Random Forest models.
Saves best model, all models bundle, and evaluation metrics.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def format_feature_name(raw_name: str) -> str:
    """Turn transformer feature name into clean human-readable string."""
    if raw_name.startswith("cat__"):
        name = raw_name[len("cat__"):]
        known_cols = ["brand", "condition", "processor_tier", "storage_type", "cpu_tier", "gpu_type"]
        for col in known_cols:
            if name.startswith(f"{col}_"):
                val = name[len(col) + 1:]
                col_name = "CPU Tier" if col == "cpu_tier" else "GPU Type" if col == "gpu_type" else col.replace("_", " ").title()
                return f"{col_name}: {val}"
        return name.replace("_", " ").title()
    elif raw_name.startswith("num__"):
        name = raw_name[len("num__"):]
        mapping = {
            "original_price": "Original Price (INR)",
            "age_months": "Age (Months)",
            "storage_gb": "Storage (GB)",
            "ram_gb": "RAM (GB)",
            "battery_health_pct": "Battery Health (%)",
            "has_box_and_bill": "Has Box & Bill",
            "screen_size_in": "Screen Size (Inches)",
        }
        return mapping.get(name, name.replace("_", " ").title())
    return raw_name


def get_top_feature_importances(pipeline: Pipeline, top_n: int = 8) -> list:
    """Extract top N human readable feature importances from a fitted pipeline with RF."""
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    rf_model: RandomForestRegressor = pipeline.named_steps["model"]

    raw_features = preprocessor.get_feature_names_out()
    importances = rf_model.feature_importances_

    feature_imp = [
        {"feature": format_feature_name(feat), "importance": float(round(imp, 4))}
        for feat, imp in zip(raw_features, importances)
    ]
    feature_imp.sort(key=lambda x: x["importance"], reverse=True)
    return feature_imp[:top_n]


def train_device_models(
    device_name: str,
    df: pd.DataFrame,
    cat_cols: list[str],
    num_cols: list[str],
    target_col: str = "resale_price",
    random_state: int = 42,
) -> dict:
    X = df[cat_cols + num_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=random_state
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
            ("num", StandardScaler(), num_cols),
        ]
    )

    # 1. Linear Regression
    pipe_lr = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LinearRegression()),
    ])
    pipe_lr.fit(X_train, y_train)
    pred_lr = pipe_lr.predict(X_test)

    # 2. Decision Tree with tuning
    param_grid_dt = {
        "model__max_depth": [8, 10, 12, 16],
        "model__min_samples_split": [4, 8, 12],
    }
    base_dt = Pipeline([
        ("preprocessor", preprocessor),
        ("model", DecisionTreeRegressor(random_state=random_state)),
    ])
    grid_dt = GridSearchCV(base_dt, param_grid_dt, cv=4, scoring="neg_root_mean_squared_error", n_jobs=-1)
    grid_dt.fit(X_train, y_train)
    pipe_dt = grid_dt.best_estimator_
    pred_dt = pipe_dt.predict(X_test)

    # 3. Random Forest
    pipe_rf = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, max_depth=16, min_samples_split=4, random_state=random_state, n_jobs=-1)),
    ])
    pipe_rf.fit(X_train, y_train)
    pred_rf = pipe_rf.predict(X_test)

    models_dict = {
        "linear": pipe_lr,
        "tree": pipe_dt,
        "forest": pipe_rf,
    }

    preds_dict = {
        "linear": pred_lr,
        "tree": pred_dt,
        "forest": pred_rf,
    }

    metrics = {}
    best_model_name = None
    best_rmse = float("inf")

    for m_name, preds in preds_dict.items():
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        metrics[m_name] = {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4),
        }

        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = m_name

    top_features = get_top_feature_importances(pipe_rf, top_n=8)

    return {
        "models_dict": models_dict,
        "best_model_name": best_model_name,
        "best_pipeline": models_dict[best_model_name],
        "metrics": metrics,
        "top_features": top_features,
        "test_mae": metrics[best_model_name]["mae"],
    }


def train_and_save_all():
    print("=" * 60)
    print("TRAINING RESALERADAR MODELS")
    print("=" * 60)

    # 1. Smartphones
    phone_csv = DATA_DIR / "smartphones.csv"
    if not phone_csv.exists():
        from ml.generate_data import main as generate_all
        generate_all()

    df_phones = pd.read_csv(phone_csv)
    phone_cat = ["brand", "condition", "processor_tier"]
    phone_num = ["original_price", "age_months", "storage_gb", "ram_gb", "battery_health_pct", "has_box_and_bill"]

    phone_results = train_device_models("smartphone", df_phones, phone_cat, phone_num)

    # 2. Laptops
    laptop_csv = DATA_DIR / "laptops.csv"
    df_laptops = pd.read_csv(laptop_csv)
    laptop_cat = ["brand", "condition", "storage_type", "cpu_tier", "gpu_type"]
    laptop_num = ["original_price", "age_months", "storage_gb", "ram_gb", "screen_size_in", "battery_health_pct"]

    laptop_results = train_device_models("laptop", df_laptops, laptop_cat, laptop_num)

    # Save models
    # Best models
    phone_best_path = MODELS_DIR / "phone_model.joblib"
    laptop_best_path = MODELS_DIR / "laptop_model.joblib"
    joblib.dump(phone_results["best_pipeline"], phone_best_path, compress=3)
    joblib.dump(laptop_results["best_pipeline"], laptop_best_path, compress=3)

    # All models bundle
    phone_all_path = MODELS_DIR / "phone_all.joblib"
    laptop_all_path = MODELS_DIR / "laptop_all.joblib"
    joblib.dump(phone_results["models_dict"], phone_all_path, compress=3)
    joblib.dump(laptop_results["models_dict"], laptop_all_path, compress=3)

    # Metrics JSON
    metrics_data = {
        "smartphone": {
            "models": phone_results["metrics"],
            "best_model": phone_results["best_model_name"],
            "best_mae": phone_results["test_mae"],
            "feature_importances": phone_results["top_features"],
        },
        "laptop": {
            "models": laptop_results["metrics"],
            "best_model": laptop_results["best_model_name"],
            "best_mae": laptop_results["test_mae"],
            "feature_importances": laptop_results["top_features"],
        },
    }

    metrics_path = MODELS_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    # Print summary table
    print("\nMODEL PERFORMANCE EVALUATION TABLE:")
    print("-" * 75)
    print(f"{'Device':<12} | {'Model':<16} | {'MAE (INR)':<12} | {'RMSE (INR)':<12} | {'R2 Score':<8}")
    print("-" * 75)
    for dev, res in [("Smartphone", phone_results), ("Laptop", laptop_results)]:
        for m_name, m_metrics in res["metrics"].items():
            mark = " (BEST)" if m_name == res["best_model_name"] else ""
            print(f"{dev:<12} | {m_name + mark:<16} | {m_metrics['mae']:<12.2f} | {m_metrics['rmse']:<12.2f} | {m_metrics['r2']:<8.4f}")
    print("-" * 75)

    # Check file sizes
    print("\nSAVED MODEL FILE SIZES:")
    for p in [phone_best_path, laptop_best_path, phone_all_path, laptop_all_path, metrics_path]:
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name:<25}: {size_mb:.2f} MB")

    best_phone_r2 = phone_results["metrics"][phone_results["best_model_name"]]["r2"]
    best_laptop_r2 = laptop_results["metrics"][laptop_results["best_model_name"]]["r2"]
    print(f"\nBest Phone R2: {best_phone_r2:.4f} (Required: > 0.85)")
    print(f"Best Laptop R2: {best_laptop_r2:.4f} (Required: > 0.85)")
    assert best_phone_r2 > 0.85, f"Phone R2 {best_phone_r2} is not > 0.85"
    assert best_laptop_r2 > 0.85, f"Laptop R2 {best_laptop_r2} is not > 0.85"
    print("\nTraining completed successfully! All R2 thresholds satisfied.")


if __name__ == "__main__":
    train_and_save_all()
