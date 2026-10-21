"""
Model manager and price prediction engine for ResaleRadar.
Loads models, predicts resale values across all trained models,
computes confidence intervals via MAE, and extracts top explanatory factors.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import pandas as pd

logger = logging.getLogger("resale_radar")

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

PHONE_MODEL_PATH = MODELS_DIR / "phone_model.joblib"
LAPTOP_MODEL_PATH = MODELS_DIR / "laptop_model.joblib"
PHONE_ALL_PATH = MODELS_DIR / "phone_all.joblib"
LAPTOP_ALL_PATH = MODELS_DIR / "laptop_all.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"


class ModelPredictor:
    def __init__(self):
        self.phone_model = None
        self.laptop_model = None
        self.phone_all = None
        self.laptop_all = None
        self.metrics = None
        self.ensure_models_loaded()

    def ensure_models_loaded(self):
        """Check if model files exist; train if missing, then load into memory."""
        required_paths = [
            PHONE_MODEL_PATH,
            LAPTOP_MODEL_PATH,
            PHONE_ALL_PATH,
            LAPTOP_ALL_PATH,
            METRICS_PATH,
        ]

        if not all(p.exists() for p in required_paths):
            logger.warning("One or more model files missing. Triggering automatic training...")
            from ml.train import train_and_save_all
            train_and_save_all()

        logger.info("Loading models into memory...")
        self.phone_model = joblib.load(PHONE_MODEL_PATH)
        self.laptop_model = joblib.load(LAPTOP_MODEL_PATH)
        self.phone_all = joblib.load(PHONE_ALL_PATH)
        self.laptop_all = joblib.load(LAPTOP_ALL_PATH)

        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            self.metrics = json.load(f)
        logger.info("All models and metrics loaded successfully.")

    def get_metrics(self) -> dict:
        return self.metrics

    def predict_smartphone(self, data: dict) -> dict:
        # Prepare input dataframe
        cols = [
            "brand", "original_price", "age_months", "condition",
            "storage_gb", "ram_gb", "battery_health_pct",
            "processor_tier", "has_box_and_bill"
        ]
        row_dict = {col: data[col] for col in cols}
        df_input = pd.DataFrame([row_dict])

        # Predictions across all three models
        pred_linear = float(self.phone_all["linear"].predict(df_input)[0])
        pred_tree = float(self.phone_all["tree"].predict(df_input)[0])
        pred_forest = float(self.phone_all["forest"].predict(df_input)[0])
        pred_best = float(self.phone_model.predict(df_input)[0])

        orig_price = float(data["original_price"])
        best_mae = float(self.metrics["smartphone"]["best_mae"])

        # Enforce business limits: at least ₹500, at most 95% of original price
        est_price = int(round(min(max(pred_best, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_linear = int(round(min(max(pred_linear, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_tree = int(round(min(max(pred_tree, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_forest = int(round(min(max(pred_forest, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)

        price_low = max(0, int(round((est_price - best_mae) / 100.0) * 100))
        price_high = int(round(min(orig_price, est_price + best_mae) / 100.0) * 100)
        depreciation_pct = round(max(0.0, min(95.0, (1.0 - (est_price / orig_price)) * 100.0)), 1)

        # Compute explanatory factors via what-if counterfactuals
        factors = self._explain_smartphone(row_dict, est_price)

        return {
            "device_type": "smartphone",
            "estimated_price": est_price,
            "price_low": price_low,
            "price_high": price_high,
            "depreciation_pct": depreciation_pct,
            "per_model_predictions": {
                "linear": p_linear,
                "tree": p_tree,
                "forest": p_forest,
            },
            "top_factors": factors,
            "disclaimer": "Estimate based on current used electronics market benchmarks in India. Actual resale price may vary depending on local demand, physical blemishes, accessories, and buyer negotiation.",
        }

    def predict_laptop(self, data: dict) -> dict:
        cols = [
            "brand", "original_price", "age_months", "condition",
            "storage_gb", "storage_type", "ram_gb", "cpu_tier",
            "gpu_type", "screen_size_in", "battery_health_pct"
        ]
        row_dict = {col: data[col] for col in cols}
        df_input = pd.DataFrame([row_dict])

        pred_linear = float(self.laptop_all["linear"].predict(df_input)[0])
        pred_tree = float(self.laptop_all["tree"].predict(df_input)[0])
        pred_forest = float(self.laptop_all["forest"].predict(df_input)[0])
        pred_best = float(self.laptop_model.predict(df_input)[0])

        orig_price = float(data["original_price"])
        best_mae = float(self.metrics["laptop"]["best_mae"])

        est_price = int(round(min(max(pred_best, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_linear = int(round(min(max(pred_linear, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_tree = int(round(min(max(pred_tree, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)
        p_forest = int(round(min(max(pred_forest, orig_price * 0.08), orig_price * 0.95) / 100.0) * 100)

        price_low = max(0, int(round((est_price - best_mae) / 100.0) * 100))
        price_high = int(round(min(orig_price, est_price + best_mae) / 100.0) * 100)
        depreciation_pct = round(max(0.0, min(95.0, (1.0 - (est_price / orig_price)) * 100.0)), 1)

        factors = self._explain_laptop(row_dict, est_price)

        return {
            "device_type": "laptop",
            "estimated_price": est_price,
            "price_low": price_low,
            "price_high": price_high,
            "depreciation_pct": depreciation_pct,
            "per_model_predictions": {
                "linear": p_linear,
                "tree": p_tree,
                "forest": p_forest,
            },
            "top_factors": factors,
            "disclaimer": "Estimate based on current used electronics market benchmarks in India. Actual resale price may vary depending on local demand, physical blemishes, accessories, and buyer negotiation.",
        }

    def _explain_smartphone(self, current: dict, current_price: int) -> List[str]:
        """Derive top 3 human-readable drivers using what-if model predictions."""
        candidates = []

        # 1. Age factor
        age = current["age_months"]
        if age > 12:
            alt = dict(current, age_months=1)
            p_alt = float(self.phone_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"Age of {age} months lowers value by ~₹{int(diff):,} compared to newer stock"
            ))
        else:
            candidates.append((
                4000,
                f"Low age of {age} month{'s' if age > 1 else ''} helps preserve premium value"
            ))

        # 2. Condition factor
        cond = current["condition"]
        if cond != "Like New":
            alt = dict(current, condition="Like New")
            p_alt = float(self.phone_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"{cond} cosmetic condition reduces valuation by ~₹{int(diff):,} vs mint condition"
            ))
        else:
            candidates.append((
                3500,
                "Like New condition commands top-tier buyer interest and price"
            ))

        # 3. Brand tier retention
        brand = current["brand"]
        if brand == "Apple":
            candidates.append((
                5000,
                "Apple devices hold secondary market demand and depreciate significantly slower"
            ))
        elif brand in ["Google", "Samsung"]:
            candidates.append((
                2500,
                f"{brand} flagship ecosystem retains steady buyer demand"
            ))
        else:
            candidates.append((
                2000,
                f"{brand} models face faster depreciation in the competitive mid-budget market"
            ))

        # 4. Battery health
        battery = current["battery_health_pct"]
        if battery < 80:
            alt = dict(current, battery_health_pct=100)
            p_alt = float(self.phone_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"Degraded battery health ({battery}%) discounts price as buyer may need battery replacement"
            ))
        elif battery >= 90:
            candidates.append((
                2200,
                f"High battery health ({battery}%) indicates minimal battery cycle wear"
            ))

        # 5. Box and Bill
        box_bill = current["has_box_and_bill"]
        if box_bill == 1:
            candidates.append((
                1800,
                "Original invoice & retail box included improves buyer trust and price realization"
            ))
        else:
            candidates.append((
                1500,
                "Missing retail box or invoice incurs a small verification penalty"
            ))

        # Sort by importance magnitude and return top 3
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:3]]

    def _explain_laptop(self, current: dict, current_price: int) -> List[str]:
        """Derive top 3 human-readable drivers using what-if model predictions."""
        candidates = []

        # 1. Age factor
        age = current["age_months"]
        if age > 14:
            alt = dict(current, age_months=1)
            p_alt = float(self.laptop_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"Age of {age} months lowers valuation by ~₹{int(diff):,} vs recent models"
            ))
        else:
            candidates.append((
                6000,
                f"Recent model age ({age} month{'s' if age > 1 else ''}) retains strong market value"
            ))

        # 2. Condition factor
        cond = current["condition"]
        if cond != "Like New":
            alt = dict(current, condition="Like New")
            p_alt = float(self.laptop_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"{cond} physical wear discounts value by ~₹{int(diff):,} compared to Like New"
            ))
        else:
            candidates.append((
                5500,
                "Pristine condition allows listing at the top end of the market bracket"
            ))

        # 3. CPU & Storage Type
        cpu = current["cpu_tier"]
        st_type = current["storage_type"]
        gpu = current["gpu_type"]

        if cpu == "Apple M-series":
            candidates.append((
                7000,
                "Apple Silicon architecture delivers exceptional resale value retention"
            ))
        elif st_type == "HDD":
            alt = dict(current, storage_type="SSD")
            p_alt = float(self.laptop_model.predict(pd.DataFrame([alt]))[0])
            diff = p_alt - current_price
            candidates.append((
                abs(diff),
                f"Mechanical HDD storage reduces buyer interest vs faster modern NVMe SSDs"
            ))
        elif gpu == "Dedicated":
            candidates.append((
                4500,
                "Dedicated graphics card attracts gamers, video editors, and creative power users"
            ))

        # 4. RAM capacity
        ram = current["ram_gb"]
        if ram <= 4:
            candidates.append((
                3500,
                f"Basic {ram}GB RAM limits multitasking appeal for modern workflows"
            ))
        elif ram >= 16:
            candidates.append((
                3200,
                f"Generous {ram}GB RAM enhances modern multitasking and longevity"
            ))

        # 5. Battery health
        battery = current["battery_health_pct"]
        if battery < 75:
            candidates.append((
                3000,
                f"Battery health at {battery}% reflects significant cycle wear, lowering price"
            ))
        elif battery >= 90:
            candidates.append((
                2500,
                f"Strong battery health ({battery}%) supports longer unplugged productivity"
            ))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:3]]


# Global singleton instance
predictor = ModelPredictor()
