"""
============================================
Synthetic Health Dataset Generator
============================================
Generates realistic synthetic datasets for:
- Patient symptom data with seasonal trends
- Water quality readings across regions
- Disease outbreak patterns
- IoT sensor telemetry

Optimized for training outbreak prediction models.
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# Output directory
OUTPUT_DIR = Path(__file__).resolve().parent / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_symptom_dataset(n_records=5000, seed=42):
    """
    Generate synthetic symptom/patient dataset with realistic patterns.
    
    Includes:
    - Seasonal variation (monsoon = more waterborne diseases)
    - Geographic clustering
    - Age/gender demographics
    - Disease-symptom correlations
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # NE India villages with coordinates
    villages = [
        {"name": "Majuli", "district": "Majuli", "lat": 26.95, "lon": 94.17, "pop": 1700, "sanitation": 35},
        {"name": "Dhubri", "district": "Dhubri", "lat": 26.02, "lon": 89.98, "pop": 2200, "sanitation": 42},
        {"name": "Silchar", "district": "Cachar", "lat": 24.82, "lon": 92.78, "pop": 3100, "sanitation": 55},
        {"name": "Tezpur", "district": "Sonitpur", "lat": 26.63, "lon": 92.80, "pop": 2800, "sanitation": 60},
        {"name": "Jorhat", "district": "Jorhat", "lat": 26.75, "lon": 94.22, "pop": 3500, "sanitation": 58},
        {"name": "Dibrugarh", "district": "Dibrugarh", "lat": 27.47, "lon": 94.91, "pop": 4200, "sanitation": 65},
        {"name": "Nagaon", "district": "Nagaon", "lat": 26.35, "lon": 92.69, "pop": 2900, "sanitation": 48},
        {"name": "Barpeta", "district": "Barpeta", "lat": 26.32, "lon": 91.00, "pop": 1800, "sanitation": 38},
        {"name": "Goalpara", "district": "Goalpara", "lat": 26.17, "lon": 90.63, "pop": 2100, "sanitation": 40},
        {"name": "Kokrajhar", "district": "Kokrajhar", "lat": 26.40, "lon": 90.27, "pop": 1600, "sanitation": 32},
        {"name": "Morigaon", "district": "Morigaon", "lat": 26.25, "lon": 92.34, "pop": 1400, "sanitation": 30},
        {"name": "Hailakandi", "district": "Hailakandi", "lat": 24.68, "lon": 92.57, "pop": 1300, "sanitation": 28},
    ]
    
    diseases = {
        "cholera": {
            "symptoms": ["watery_diarrhea", "vomiting", "dehydration", "leg_cramps"],
            "seasonal_peak": [6, 7, 8, 9],  # Monsoon months
            "base_rate": 0.12,
            "water_corr": 0.85,
        },
        "typhoid": {
            "symptoms": ["fever", "headache", "abdominal_pain", "weakness", "diarrhea"],
            "seasonal_peak": [5, 6, 7, 8, 9, 10],
            "base_rate": 0.18,
            "water_corr": 0.70,
        },
        "diarrheal": {
            "symptoms": ["diarrhea", "abdominal_pain", "nausea", "dehydration"],
            "seasonal_peak": [6, 7, 8, 9],
            "base_rate": 0.30,
            "water_corr": 0.75,
        },
        "hepatitis_a": {
            "symptoms": ["jaundice", "fatigue", "nausea", "abdominal_pain", "dark_urine"],
            "seasonal_peak": [7, 8, 9, 10],
            "base_rate": 0.08,
            "water_corr": 0.65,
        },
        "leptospirosis": {
            "symptoms": ["fever", "headache", "muscle_pain", "jaundice", "rash"],
            "seasonal_peak": [7, 8, 9],
            "base_rate": 0.06,
            "water_corr": 0.60,
        },
        "dysentery": {
            "symptoms": ["bloody_diarrhea", "abdominal_pain", "fever", "dehydration"],
            "seasonal_peak": [6, 7, 8],
            "base_rate": 0.15,
            "water_corr": 0.80,
        },
        "giardiasis": {
            "symptoms": ["diarrhea", "gas", "bloating", "nausea", "weight_loss"],
            "seasonal_peak": [5, 6, 7, 8, 9],
            "base_rate": 0.11,
            "water_corr": 0.55,
        },
    }
    
    records = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(n_records):
        # Random date within 2 years
        day_offset = random.randint(0, 730)
        record_date = start_date + timedelta(days=day_offset)
        month = record_date.month
        
        # Choose village (weighted by population)
        village = random.choices(villages, weights=[v["pop"] for v in villages])[0]
        
        # Seasonal disease probability
        disease_probs = {}
        for d_name, d_info in diseases.items():
            prob = d_info["base_rate"]
            if month in d_info["seasonal_peak"]:
                prob *= (2.5 + random.uniform(0, 1))  # Monsoon boost
            # Lower sanitation = higher disease probability
            sanitation_factor = 1 + (100 - village["sanitation"]) / 100
            prob *= sanitation_factor
            disease_probs[d_name] = min(prob, 1.0)
        
        # Select disease based on probabilities
        disease = random.choices(
            list(disease_probs.keys()),
            weights=list(disease_probs.values())
        )[0]
        
        d_info = diseases[disease]
        
        # Generate symptoms
        n_symptoms = random.randint(2, len(d_info["symptoms"]))
        selected_symptoms = random.sample(d_info["symptoms"], n_symptoms)
        
        # Patient demographics
        age = int(np.clip(np.random.lognormal(3.2, 0.5), 1, 85))
        gender = random.choice(["M", "F"])
        
        # Severity correlates with age and sanitation
        severity_score = random.uniform(0, 1)
        if age < 5 or age > 60:
            severity_score += 0.3  # Children and elderly more severe
        if village["sanitation"] < 40:
            severity_score += 0.2
        
        severity = "mild"
        if severity_score > 0.8:
            severity = "critical"
        elif severity_score > 0.6:
            severity = "severe"
        elif severity_score > 0.35:
            severity = "moderate"
        
        # Water quality correlation
        water_contamination = random.uniform(0, 100) * (1 - village["sanitation"] / 100) * d_info["water_corr"]
        
        records.append({
            "date": record_date.strftime("%Y-%m-%d"),
            "month": month,
            "year": record_date.year,
            "patient_age": age,
            "patient_gender": gender,
            "village": village["name"],
            "district": village["district"],
            "latitude": round(village["lat"] + random.uniform(-0.05, 0.05), 4),
            "longitude": round(village["lon"] + random.uniform(-0.05, 0.05), 4),
            "disease": disease,
            "symptoms": ",".join(selected_symptoms),
            "severity": severity,
            "fever": 1 if "fever" in selected_symptoms else 0,
            "diarrhea": 1 if any(s in selected_symptoms for s in ["diarrhea", "watery_diarrhea", "bloody_diarrhea"]) else 0,
            "vomiting": 1 if "vomiting" in selected_symptoms or "nausea" in selected_symptoms else 0,
            "abdominal_pain": 1 if "abdominal_pain" in selected_symptoms else 0,
            "dehydration": 1 if "dehydration" in selected_symptoms else 0,
            "jaundice": 1 if "jaundice" in selected_symptoms else 0,
            "water_source": random.choice(["river", "well", "borewell", "pond", "tap", "handpump"]),
            "sanitation_coverage": village["sanitation"] + random.uniform(-5, 5),
            "population_density": village["pop"] + random.randint(-200, 200),
            "water_contamination_ppm": round(water_contamination, 2),
            "rainfall_mm": round(max(0, np.random.normal(
                350 if month in [6, 7, 8, 9] else 80 if month in [11, 12, 1, 2] else 150,
                50
            )), 1),
            "temperature_c": round(np.random.normal(
                32 if month in [4, 5, 6] else 28 if month in [7, 8, 9] else 22,
                3
            ), 1),
            "risk_level": "HIGH" if severity in ["severe", "critical"] else "MEDIUM" if severity == "moderate" else "LOW",
        })
    
    df = pd.DataFrame(records)
    
    # Save as CSV
    output_path = OUTPUT_DIR / "synthetic_symptoms_dataset.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {n_records} synthetic symptom records → {output_path}")
    
    return df


def generate_water_quality_dataset(n_records=3000, seed=42):
    """
    Generate synthetic water quality dataset with seasonal patterns.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    sources = [
        {"name": "Brahmaputra River", "type": "river", "lat": 26.75, "lon": 94.2, "base_quality": 0.6},
        {"name": "Manas River", "type": "river", "lat": 26.73, "lon": 91.0, "base_quality": 0.55},
        {"name": "Subansiri River", "type": "river", "lat": 27.1, "lon": 94.6, "base_quality": 0.65},
        {"name": "Majuli Well #1", "type": "well", "lat": 26.95, "lon": 94.17, "base_quality": 0.45},
        {"name": "Dhubri Borewell", "type": "borewell", "lat": 26.02, "lon": 89.98, "base_quality": 0.70},
        {"name": "Tezpur Handpump", "type": "handpump", "lat": 26.63, "lon": 92.80, "base_quality": 0.50},
        {"name": "Silchar Pond", "type": "pond", "lat": 24.82, "lon": 92.78, "base_quality": 0.35},
        {"name": "Jorhat Tap Water", "type": "tap", "lat": 26.75, "lon": 94.22, "base_quality": 0.80},
        {"name": "Nagaon Well", "type": "well", "lat": 26.35, "lon": 92.69, "base_quality": 0.40},
        {"name": "Barpeta Pond", "type": "pond", "lat": 26.32, "lon": 91.00, "base_quality": 0.30},
    ]
    
    records = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(n_records):
        day_offset = random.randint(0, 730)
        record_date = start_date + timedelta(days=day_offset)
        month = record_date.month
        
        source = random.choice(sources)
        quality = source["base_quality"]
        
        # Monsoon degrades water quality
        if month in [6, 7, 8, 9]:
            quality *= random.uniform(0.4, 0.7)
        elif month in [5, 10]:
            quality *= random.uniform(0.6, 0.85)
        
        # Generate parameters based on quality (lower quality = worse readings)
        inv_quality = 1 - quality
        
        ph = round(np.clip(np.random.normal(7.0 - inv_quality * 1.5, 0.5), 4.5, 9.5), 1)
        turbidity = round(max(0, np.random.exponential(5 + inv_quality * 30)), 1)
        do = round(np.clip(np.random.normal(8 - inv_quality * 4, 1), 1, 14), 1)
        contaminant = round(max(0, np.random.exponential(10 + inv_quality * 50)), 1)
        nitrate = round(max(0, np.random.exponential(5 + inv_quality * 20)), 1)
        lead = round(max(0, np.random.exponential(0.005 + inv_quality * 0.03)), 4)
        bacteria = int(max(0, np.random.exponential(100 + inv_quality * 1500)))
        temp = round(np.random.normal(32 if month in [4, 5, 6] else 28 if month in [7, 8, 9] else 22, 3), 1)
        rainfall = round(max(0, np.random.normal(
            350 if month in [6, 7, 8, 9] else 80 if month in [11, 12, 1, 2] else 150, 50
        )), 1)
        
        # Risk classification
        risk_score = 0
        if ph < 6.0 or ph > 8.5: risk_score += 2
        if turbidity > 20: risk_score += 2
        if do < 4: risk_score += 2
        if contaminant > 40: risk_score += 3
        if bacteria > 1000: risk_score += 3
        if lead > 0.015: risk_score += 2
        
        risk = "HIGH" if risk_score >= 6 else "MEDIUM" if risk_score >= 3 else "LOW"
        
        # Disease case estimates (correlated with water quality)
        cholera_cases = round(max(0, np.random.poisson(risk_score * 8 * (1.5 if month in [7,8,9] else 1))), 1)
        typhoid_cases = round(max(0, np.random.poisson(risk_score * 12 * (1.3 if month in [6,7,8,9] else 1))), 1)
        diarrheal_cases = round(max(0, np.random.poisson(risk_score * 25 * (1.4 if month in [7,8,9] else 1))), 1)
        
        records.append({
            "date": record_date.strftime("%Y-%m-%d"),
            "month": month,
            "source_name": source["name"],
            "source_type": source["type"],
            "latitude": round(source["lat"] + random.uniform(-0.03, 0.03), 4),
            "longitude": round(source["lon"] + random.uniform(-0.03, 0.03), 4),
            "contaminant_level_ppm": contaminant,
            "ph_level": ph,
            "turbidity_ntu": turbidity,
            "dissolved_oxygen_mg_l": do,
            "nitrate_levels": nitrate,
            "lead_concentration": lead,
            "bacteria_count_cfu_ml": bacteria,
            "temperature": temp,
            "rainfall": rainfall,
            "sanitation_coverage": round(random.uniform(25, 80), 1),
            "population_density": random.randint(500, 3000),
            "access_to_clean_water": round(random.uniform(20, 85), 1),
            "risk_level": risk,
            "risk_score": risk_score,
            "cholera_cases_per_100000": cholera_cases,
            "typhoid_cases_per_100000": typhoid_cases,
            "diarrheal_cases_per_100000": diarrheal_cases,
        })
    
    df = pd.DataFrame(records)
    output_path = OUTPUT_DIR / "synthetic_water_quality_dataset.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {n_records} synthetic water quality records → {output_path}")
    
    return df


def generate_sensor_telemetry(n_sensors=20, days=60, readings_per_day=24, seed=42):
    """
    Generate synthetic IoT sensor telemetry data with failure scenarios.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    records = []
    start_date = datetime(2024, 6, 1)  # Start in monsoon
    
    sensor_locations = [
        {"id": f"IOT-{i:03d}", "lat": 26.0 + random.uniform(0, 2), "lon": 90 + random.uniform(0, 5),
         "village": random.choice(["Majuli", "Dhubri", "Tezpur", "Jorhat", "Nagaon"]),
         "failure_day": random.choice([None, None, None, random.randint(20, 50)])}
        for i in range(n_sensors)
    ]
    
    for sensor in sensor_locations:
        battery = 100
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Check for sensor failure scenario
            if sensor["failure_day"] and day >= sensor["failure_day"]:
                if day == sensor["failure_day"]:
                    records.append({
                        "timestamp": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "sensor_id": sensor["id"],
                        "village": sensor["village"],
                        "status": "error",
                        "battery_level": max(0, battery),
                        "error": "sensor_failure",
                        "ph_level": None,
                        "turbidity_ntu": None,
                        "bacteria_count_cfu_ml": None,
                    })
                continue
            
            for hour in range(0, 24, 24 // min(readings_per_day, 24)):
                timestamp = current_date + timedelta(hours=hour)
                battery = max(0, battery - random.uniform(0.05, 0.15))
                
                # Simulate sudden spike (outbreak scenario)
                is_spike = random.random() < 0.02
                spike_multiplier = random.uniform(3, 8) if is_spike else 1
                
                records.append({
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "sensor_id": sensor["id"],
                    "village": sensor["village"],
                    "latitude": sensor["lat"],
                    "longitude": sensor["lon"],
                    "status": "active" if battery > 10 else "low_battery",
                    "battery_level": round(battery, 1),
                    "ph_level": round(np.clip(np.random.normal(7.0, 0.3) - (0.5 if is_spike else 0), 4, 10), 2),
                    "turbidity_ntu": round(max(0, np.random.exponential(8) * spike_multiplier), 1),
                    "bacteria_count_cfu_ml": int(max(0, np.random.exponential(200) * spike_multiplier)),
                    "contaminant_level_ppm": round(max(0, np.random.exponential(15) * spike_multiplier), 1),
                    "temperature": round(np.random.normal(30, 2), 1),
                    "dissolved_oxygen_mg_l": round(np.clip(np.random.normal(6, 1), 1, 12), 1),
                    "is_spike": is_spike,
                    "error": None,
                })
    
    df = pd.DataFrame(records)
    output_path = OUTPUT_DIR / "synthetic_sensor_telemetry.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {len(records)} sensor telemetry records → {output_path}")
    
    return df


def generate_outbreak_scenarios():
    """
    Generate specific outbreak scenario datasets for testing alert logic.
    """
    scenarios = []
    
    # Scenario 1: Sudden cholera outbreak in Majuli
    scenario1 = {
        "name": "Cholera Outbreak - Majuli",
        "description": "Sudden spike of cholera cases following flood contamination",
        "timeline": []
    }
    for day in range(14):
        cases = 2 if day < 3 else (5 * (day - 2)) if day < 7 else max(5, 35 - (day - 7) * 5)
        scenario1["timeline"].append({
            "day": day + 1,
            "date": (datetime.now() - timedelta(days=14 - day)).strftime("%Y-%m-%d"),
            "new_cases": cases,
            "risk_level": "HIGH" if cases > 10 else "MEDIUM" if cases > 5 else "LOW",
            "water_contamination_ppm": round(20 + cases * 3, 1),
            "bacteria_count": int(200 + cases * 100),
        })
    scenarios.append(scenario1)
    
    # Scenario 2: Sensor failure during outbreak
    scenario2 = {
        "name": "Sensor Failure During Outbreak - Dhubri",
        "description": "IoT sensors go offline during critical contamination event",
        "timeline": []
    }
    for day in range(10):
        sensor_active = day < 4 or day > 7
        scenario2["timeline"].append({
            "day": day + 1,
            "sensor_status": "active" if sensor_active else "failed",
            "cases": 3 + day * 4 if day >= 3 else 1,
            "data_available": sensor_active,
            "risk_level": "UNKNOWN" if not sensor_active else "HIGH" if day >= 5 else "MEDIUM",
        })
    scenarios.append(scenario2)
    
    # Scenario 3: Gradual contamination across multiple villages
    scenario3 = {
        "name": "Multi-Village Contamination Spread",
        "description": "Contamination spreading downstream through river system",
        "timeline": []
    }
    villages_in_order = ["Majuli", "Jorhat", "Nagaon", "Tezpur"]
    for day in range(21):
        affected = villages_in_order[:min(len(villages_in_order), max(1, day // 5 + 1))]
        scenario3["timeline"].append({
            "day": day + 1,
            "affected_villages": affected,
            "total_cases": sum(range(len(affected))) * 5 + day * 3,
            "risk_level": "HIGH" if len(affected) >= 3 else "MEDIUM" if len(affected) >= 2 else "LOW",
        })
    scenarios.append(scenario3)
    
    output_path = OUTPUT_DIR / "outbreak_scenarios.json"
    with open(output_path, "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"✅ Generated {len(scenarios)} outbreak scenarios → {output_path}")
    
    return scenarios


if __name__ == "__main__":
    print("=" * 60)
    print("  SYNTHETIC DATASET GENERATOR")
    print("=" * 60)
    
    print("\n📊 Generating symptom dataset...")
    symptom_df = generate_symptom_dataset(5000)
    
    print("\n💧 Generating water quality dataset...")
    water_df = generate_water_quality_dataset(3000)
    
    print("\n📡 Generating IoT sensor telemetry...")
    sensor_df = generate_sensor_telemetry(20, 60, 4)
    
    print("\n🚨 Generating outbreak scenarios...")
    scenarios = generate_outbreak_scenarios()
    
    print("\n" + "=" * 60)
    print("  ALL DATASETS GENERATED SUCCESSFULLY!")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Summary statistics
    print(f"\n📈 Symptom Dataset: {len(symptom_df)} records")
    print(f"   Diseases: {symptom_df['disease'].nunique()} types")
    print(f"   Villages: {symptom_df['village'].nunique()} locations")
    print(f"   Date range: {symptom_df['date'].min()} to {symptom_df['date'].max()}")
    
    print(f"\n💧 Water Quality Dataset: {len(water_df)} records")
    print(f"   Risk distribution: {water_df['risk_level'].value_counts().to_dict()}")
    
    print(f"\n📡 Sensor Telemetry: {len(sensor_df)} records")
    print(f"   Sensors: {sensor_df['sensor_id'].nunique()}")
