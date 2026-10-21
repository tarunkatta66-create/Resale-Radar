"""
Generate realistic synthetic datasets for smartphones and laptops.
Fixed random seed (42) ensures reproducible generation.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_smartphones(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    brands = ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Google", "Vivo", "Oppo"]
    brand_probs = [0.22, 0.22, 0.14, 0.14, 0.08, 0.08, 0.06, 0.06]
    selected_brands = rng.choice(brands, size=n_samples, p=brand_probs)

    # Base price ranges by brand
    brand_price_specs = {
        "Apple": (55000, 150000, ["Mid", "Flagship"], [4, 6, 8, 12]),
        "Samsung": (12000, 140000, ["Entry", "Mid", "Flagship"], [3, 4, 6, 8, 12, 16]),
        "OnePlus": (25000, 75000, ["Mid", "Flagship"], [6, 8, 12, 16]),
        "Google": (38000, 110000, ["Mid", "Flagship"], [6, 8, 12]),
        "Xiaomi": (9000, 65000, ["Entry", "Mid", "Flagship"], [3, 4, 6, 8, 12]),
        "Realme": (8000, 45000, ["Entry", "Mid"], [3, 4, 6, 8]),
        "Vivo": (10000, 70000, ["Entry", "Mid", "Flagship"], [4, 6, 8, 12]),
        "Oppo": (10000, 65000, ["Entry", "Mid", "Flagship"], [4, 6, 8, 12]),
    }

    # Brand monthly depreciation lambda (Apple retains value best)
    brand_depreciation_rate = {
        "Apple": 0.018,
        "Google": 0.024,
        "Samsung": 0.026,
        "OnePlus": 0.027,
        "Xiaomi": 0.032,
        "Vivo": 0.032,
        "Oppo": 0.032,
        "Realme": 0.034,
    }

    storage_options = [64, 128, 256, 512]
    storage_mult = {64: 0.95, 128: 1.00, 256: 1.05, 512: 1.09}
    ram_mult = {3: 0.95, 4: 0.98, 6: 1.00, 8: 1.03, 12: 1.06, 16: 1.08}
    tier_mult = {"Entry": 0.95, "Mid": 1.00, "Flagship": 1.06}
    condition_mult = {"Like New": 1.00, "Good": 0.90, "Fair": 0.78, "Poor": 0.62}

    rows = []
    for brand in selected_brands:
        min_p, max_p, allowed_tiers, allowed_rams = brand_price_specs[brand]

        proc_tier = rng.choice(allowed_tiers)
        ram = int(rng.choice(allowed_rams))
        storage = int(rng.choice(storage_options))

        # Adjust price based on tier & storage & ram within brand range
        tier_weight = {"Entry": 0.15, "Mid": 0.5, "Flagship": 0.85}[proc_tier]
        spec_score = (tier_weight * 0.5) + (ram / 16.0 * 0.25) + (storage / 512.0 * 0.25)
        spec_score = np.clip(spec_score + rng.normal(0, 0.08), 0.0, 1.0)
        orig_price = min_p + spec_score * (max_p - min_p)
        orig_price = int(np.round(orig_price / 500) * 500)
        orig_price = max(8000, min(150000, orig_price))

        age_months = int(rng.integers(1, 61))

        # Battery health decreases with age
        expected_battery = 100.0 - (age_months * 0.45) + rng.normal(0, 3.5)
        battery_health = int(np.clip(np.round(expected_battery), 60, 100))

        conditions = ["Like New", "Good", "Fair", "Poor"]
        if age_months < 12:
            cond_p = [0.55, 0.35, 0.08, 0.02]
        elif age_months < 30:
            cond_p = [0.20, 0.50, 0.22, 0.08]
        else:
            cond_p = [0.05, 0.35, 0.40, 0.20]
        condition = rng.choice(conditions, p=cond_p)

        has_box_and_bill = int(rng.choice([1, 0], p=[0.65 if age_months < 24 else 0.40, 0.35 if age_months < 24 else 0.60]))

        # Target calculation:
        # original_price x exponential depreciation x condition multiplier x spec bonus x noise
        depr_rate = brand_depreciation_rate[brand]
        age_factor = np.exp(-depr_rate * age_months)
        cond_factor = condition_mult[condition]

        battery_factor = 0.94 + 0.12 * ((battery_health - 60.0) / 40.0)
        box_bill_factor = 1.03 if has_box_and_bill else 0.97
        spec_bonus = (
            storage_mult[storage]
            * ram_mult[ram]
            * tier_mult[proc_tier]
            * battery_factor
            * box_bill_factor
        )

        noise = rng.normal(1.0, 0.05)
        calc_price = orig_price * age_factor * cond_factor * spec_bonus * noise
        # Clip to at least 8% of original_price, and at most 95% of original_price
        clipped_price = np.clip(calc_price, 0.08 * orig_price, 0.95 * orig_price)
        final_price = int(np.round(clipped_price / 100.0) * 100.0)

        rows.append({
            "brand": brand,
            "original_price": orig_price,
            "age_months": age_months,
            "condition": condition,
            "storage_gb": storage,
            "ram_gb": ram,
            "battery_health_pct": battery_health,
            "processor_tier": proc_tier,
            "has_box_and_bill": has_box_and_bill,
            "resale_price": final_price,
        })

    return pd.DataFrame(rows)


def generate_laptops(n_samples: int = 2500, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    brands = ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI"]
    brand_probs = [0.20, 0.18, 0.18, 0.18, 0.12, 0.08, 0.06]
    selected_brands = rng.choice(brands, size=n_samples, p=brand_probs)

    brand_price_specs = {
        "Apple": (85000, 250000, ["Apple M-series"], ["SSD"], [8, 16, 32]),
        "Dell": (28000, 220000, ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD", "HDD"], [4, 8, 16, 32]),
        "HP": (26000, 200000, ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD", "HDD"], [4, 8, 16, 32]),
        "Lenovo": (25000, 210000, ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD", "HDD"], [4, 8, 16, 32]),
        "Asus": (27000, 230000, ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD", "HDD"], [8, 16, 32]),
        "Acer": (25000, 160000, ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD", "HDD"], [4, 8, 16]),
        "MSI": (45000, 240000, ["Core i5/Ryzen 5", "Core i7/Ryzen 7"], ["SSD"], [8, 16, 32]),
    }

    brand_depreciation_rate = {
        "Apple": 0.017,
        "Dell": 0.023,
        "Lenovo": 0.023,
        "HP": 0.024,
        "Asus": 0.025,
        "MSI": 0.026,
        "Acer": 0.028,
    }

    storage_options = [256, 512, 1024, 2048]
    screen_options = [13.3, 14.0, 15.6, 16.0, 17.3]
    storage_mult = {256: 0.96, 512: 1.00, 1024: 1.05, 2048: 1.09}
    storage_type_mult = {"SSD": 1.04, "HDD": 0.93}
    ram_mult = {4: 0.94, 8: 0.98, 16: 1.04, 32: 1.08}
    cpu_mult = {
        "Core i3/Ryzen 3": 0.94,
        "Core i5/Ryzen 5": 1.00,
        "Core i7/Ryzen 7": 1.06,
        "Apple M-series": 1.09,
    }
    gpu_mult = {"Integrated": 0.97, "Dedicated": 1.06}
    condition_mult = {"Like New": 1.00, "Good": 0.90, "Fair": 0.78, "Poor": 0.62}

    rows = []
    for brand in selected_brands:
        min_p, max_p, allowed_cpus, allowed_st_types, allowed_rams = brand_price_specs[brand]

        cpu = rng.choice(allowed_cpus)
        st_type = rng.choice(allowed_st_types)
        ram = int(rng.choice(allowed_rams))
        storage = int(rng.choice(storage_options))
        screen_size = float(rng.choice(screen_options))

        if brand == "Apple":
            gpu = rng.choice(["Integrated", "Dedicated"], p=[0.80, 0.20])
            if screen_size not in [13.3, 14.0, 16.0]:
                screen_size = rng.choice([13.3, 14.0, 16.0])
        elif brand == "MSI":
            gpu = "Dedicated"
        else:
            gpu = rng.choice(["Integrated", "Dedicated"], p=[0.6, 0.4])

        cpu_weight = {
            "Core i3/Ryzen 3": 0.15,
            "Core i5/Ryzen 5": 0.45,
            "Core i7/Ryzen 7": 0.80,
            "Apple M-series": 0.85,
        }[cpu]
        gpu_weight = 0.25 if gpu == "Dedicated" else 0.0
        ssd_weight = 0.10 if st_type == "SSD" else 0.0
        spec_score = (
            cpu_weight * 0.40
            + (ram / 32.0) * 0.25
            + (storage / 2048.0) * 0.15
            + gpu_weight
            + ssd_weight
        )
        spec_score = np.clip(spec_score + rng.normal(0, 0.08), 0.0, 1.0)
        orig_price = min_p + spec_score * (max_p - min_p)
        orig_price = int(np.round(orig_price / 1000) * 1000)
        orig_price = max(25000, min(250000, orig_price))

        age_months = int(rng.integers(1, 73))

        expected_battery = 100.0 - (age_months * 0.42) + rng.normal(0, 4.0)
        battery_health = int(np.clip(np.round(expected_battery), 50, 100))

        conditions = ["Like New", "Good", "Fair", "Poor"]
        if age_months < 14:
            cond_p = [0.52, 0.38, 0.08, 0.02]
        elif age_months < 36:
            cond_p = [0.20, 0.50, 0.22, 0.08]
        else:
            cond_p = [0.05, 0.35, 0.42, 0.18]
        condition = rng.choice(conditions, p=cond_p)

        depr_rate = brand_depreciation_rate[brand]
        age_factor = np.exp(-depr_rate * age_months)
        cond_factor = condition_mult[condition]

        battery_factor = 0.92 + 0.16 * ((battery_health - 50.0) / 50.0)
        screen_factor = 1.0 + (screen_size - 14.0) * 0.005
        spec_bonus = (
            storage_mult[storage]
            * storage_type_mult[st_type]
            * ram_mult[ram]
            * cpu_mult[cpu]
            * gpu_mult[gpu]
            * battery_factor
            * screen_factor
        )

        noise = rng.normal(1.0, 0.05)
        calc_price = orig_price * age_factor * cond_factor * spec_bonus * noise
        clipped_price = np.clip(calc_price, 0.08 * orig_price, 0.95 * orig_price)
        final_price = int(np.round(clipped_price / 100.0) * 100.0)

        rows.append({
            "brand": brand,
            "original_price": orig_price,
            "age_months": age_months,
            "condition": condition,
            "storage_gb": storage,
            "storage_type": st_type,
            "ram_gb": ram,
            "cpu_tier": cpu,
            "gpu_type": gpu,
            "screen_size_in": screen_size,
            "battery_health_pct": battery_health,
            "resale_price": final_price,
        })

    return pd.DataFrame(rows)


def main():
    print("Generating synthetic datasets...")
    df_phones = generate_smartphones(n_samples=3000, random_state=42)
    df_laptops = generate_laptops(n_samples=2500, random_state=42)

    phone_csv = DATA_DIR / "smartphones.csv"
    laptop_csv = DATA_DIR / "laptops.csv"

    df_phones.to_csv(phone_csv, index=False)
    df_laptops.to_csv(laptop_csv, index=False)

    print(f"\nSmartphones saved to: {phone_csv}")
    print(f"Shape: {df_phones.shape}")
    print(f"Nulls: {df_phones.isnull().sum().to_dict()}")
    print("\nSmartphones Head:")
    print(df_phones.head())
    print("\nSmartphones Describe:")
    print(df_phones.describe().round(2))

    print(f"\n{'='*60}\n")
    print(f"Laptops saved to: {laptop_csv}")
    print(f"Shape: {df_laptops.shape}")
    print(f"Nulls: {df_laptops.isnull().sum().to_dict()}")
    print("\nLaptops Head:")
    print(df_laptops.head())
    print("\nLaptops Describe:")
    print(df_laptops.describe().round(2))
    print("\nDataset generation completed successfully.")


if __name__ == "__main__":
    main()
