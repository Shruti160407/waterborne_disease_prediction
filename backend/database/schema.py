"""
============================================
Database Schema & Initialization
============================================
SQLite database for health surveillance data.
Tables: patients, symptoms, water_quality, predictions,
        iot_sensors, alerts, sync_queue, resources
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "surveillance.db"


def get_db():
    """Get a database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database with all tables."""
    conn = get_db()
    cursor = conn.cursor()

    # ---- Patients ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT CHECK(gender IN ('M', 'F', 'O')),
        village TEXT,
        district TEXT,
        state TEXT DEFAULT 'Assam',
        latitude REAL,
        longitude REAL,
        contact_phone TEXT,
        asha_worker_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Symptom Reports ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptom_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT UNIQUE NOT NULL,
        patient_id TEXT REFERENCES patients(patient_id),
        reporter_type TEXT DEFAULT 'asha_worker' CHECK(reporter_type IN ('asha_worker', 'clinic', 'volunteer', 'self')),
        reporter_id TEXT,
        symptoms TEXT NOT NULL,
        severity TEXT DEFAULT 'moderate' CHECK(severity IN ('mild', 'moderate', 'severe', 'critical')),
        onset_date TEXT,
        fever BOOLEAN DEFAULT 0,
        diarrhea BOOLEAN DEFAULT 0,
        vomiting BOOLEAN DEFAULT 0,
        abdominal_pain BOOLEAN DEFAULT 0,
        dehydration BOOLEAN DEFAULT 0,
        blood_in_stool BOOLEAN DEFAULT 0,
        skin_rash BOOLEAN DEFAULT 0,
        jaundice BOOLEAN DEFAULT 0,
        suspected_disease TEXT,
        water_source TEXT,
        notes TEXT,
        latitude REAL,
        longitude REAL,
        is_synced BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Water Quality Readings ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_quality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_id TEXT UNIQUE NOT NULL,
        source_name TEXT,
        source_type TEXT CHECK(source_type IN ('river', 'well', 'borewell', 'pond', 'tap', 'handpump', 'other')),
        village TEXT,
        district TEXT,
        latitude REAL,
        longitude REAL,
        ph_level REAL,
        turbidity_ntu REAL,
        dissolved_oxygen_mg_l REAL,
        contaminant_level_ppm REAL,
        nitrate_levels REAL,
        lead_concentration REAL,
        bacteria_count_cfu_ml REAL,
        temperature REAL,
        conductivity REAL,
        tds REAL,
        is_safe BOOLEAN,
        risk_level TEXT DEFAULT 'LOW' CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        sensor_id TEXT,
        collected_by TEXT,
        is_synced BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- IoT Sensors ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS iot_sensors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id TEXT UNIQUE NOT NULL,
        sensor_type TEXT DEFAULT 'water_quality',
        location_name TEXT,
        village TEXT,
        district TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'error', 'maintenance')),
        battery_level REAL,
        last_reading_at TIMESTAMP,
        installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Predictions ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id TEXT UNIQUE NOT NULL,
        prediction_type TEXT DEFAULT 'outbreak' CHECK(prediction_type IN ('outbreak', 'water_quality', 'image_detection')),
        input_data TEXT,
        risk_level TEXT,
        cholera_risk REAL,
        typhoid_risk REAL,
        diarrheal_risk REAL,
        overall_score REAL,
        model_used TEXT,
        village TEXT,
        district TEXT,
        latitude REAL,
        longitude REAL,
        alert_triggered BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Alerts History ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT UNIQUE NOT NULL,
        alert_type TEXT DEFAULT 'auto' CHECK(alert_type IN ('auto', 'manual', 'sensor', 'outbreak', 'escalation')),
        risk_level TEXT NOT NULL,
        message TEXT NOT NULL,
        village TEXT,
        district TEXT,
        latitude REAL,
        longitude REAL,
        sms_sent BOOLEAN DEFAULT 0,
        email_sent BOOLEAN DEFAULT 0,
        acknowledged BOOLEAN DEFAULT 0,
        acknowledged_by TEXT,
        acknowledged_at TIMESTAMP,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Offline Sync Queue ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_id TEXT UNIQUE NOT NULL,
        data_type TEXT NOT NULL CHECK(data_type IN ('symptom_report', 'water_quality', 'patient', 'sensor_reading')),
        payload TEXT NOT NULL,
        source_device TEXT,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'synced', 'failed')),
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        synced_at TIMESTAMP
    )
    """)

    # ---- Resources ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_type TEXT NOT NULL CHECK(resource_type IN ('medical_team', 'ors_packets', 'water_purifier', 'chlorine_tablets', 'iv_fluids', 'ambulance', 'testing_kit')),
        village TEXT,
        district TEXT,
        quantity INTEGER DEFAULT 0,
        allocated INTEGER DEFAULT 0,
        status TEXT DEFAULT 'available',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---- Indexes for performance ----
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symptoms_patient ON symptom_reports(patient_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symptoms_date ON symptom_reports(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symptoms_disease ON symptom_reports(suspected_disease)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symptoms_location ON symptom_reports(latitude, longitude)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_location ON water_quality(latitude, longitude)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_date ON water_quality(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_date ON alerts(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_risk ON alerts(risk_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensors_status ON iot_sensors(status)")

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Database initialized at: {DB_PATH}")


def seed_demo_data():
    """Seed the database with demo data for testing."""
    import uuid
    import random
    from datetime import datetime, timedelta

    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    count = cursor.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    if count > 0:
        print("[INFO] Demo data already exists, skipping seed.")
        conn.close()
        return

    # Demo villages in NE India (Assam region)
    villages = [
        {"name": "Majuli", "district": "Majuli", "lat": 26.95, "lon": 94.17},
        {"name": "Dhubri", "district": "Dhubri", "lat": 26.02, "lon": 89.98},
        {"name": "Silchar", "district": "Cachar", "lat": 24.82, "lon": 92.78},
        {"name": "Tezpur", "district": "Sonitpur", "lat": 26.63, "lon": 92.80},
        {"name": "Jorhat", "district": "Jorhat", "lat": 26.75, "lon": 94.22},
        {"name": "Dibrugarh", "district": "Dibrugarh", "lat": 27.47, "lon": 94.91},
        {"name": "Nagaon", "district": "Nagaon", "lat": 26.35, "lon": 92.69},
        {"name": "Barpeta", "district": "Barpeta", "lat": 26.32, "lon": 91.00},
        {"name": "Goalpara", "district": "Goalpara", "lat": 26.17, "lon": 90.63},
        {"name": "Kokrajhar", "district": "Kokrajhar", "lat": 26.40, "lon": 90.27},
    ]

    diseases = ["cholera", "typhoid", "diarrheal", "hepatitis_a", "leptospirosis", "dysentery"]
    water_sources = ["river", "well", "borewell", "pond", "tap", "handpump"]
    severities = ["mild", "moderate", "severe", "critical"]

    # Seed patients
    patients = []
    for i in range(80):
        v = random.choice(villages)
        pid = f"PAT-{uuid.uuid4().hex[:8].upper()}"
        patients.append(pid)
        cursor.execute("""
            INSERT INTO patients (patient_id, name, age, gender, village, district, state, latitude, longitude, asha_worker_id)
            VALUES (?, ?, ?, ?, ?, ?, 'Assam', ?, ?, ?)
        """, (
            pid,
            f"Patient_{i+1}",
            random.randint(2, 75),
            random.choice(["M", "F"]),
            v["name"], v["district"],
            v["lat"] + random.uniform(-0.05, 0.05),
            v["lon"] + random.uniform(-0.05, 0.05),
            f"ASHA-{random.randint(100, 999)}"
        ))

    # Seed symptom reports (over last 30 days)
    for i in range(200):
        v = random.choice(villages)
        days_ago = random.randint(0, 30)
        report_date = datetime.now() - timedelta(days=days_ago)
        disease = random.choice(diseases)
        severity = random.choices(severities, weights=[40, 35, 20, 5])[0]
        cursor.execute("""
            INSERT INTO symptom_reports 
            (report_id, patient_id, reporter_type, symptoms, severity, onset_date, 
             fever, diarrhea, vomiting, abdominal_pain, dehydration, blood_in_stool,
             suspected_disease, water_source, latitude, longitude, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"RPT-{uuid.uuid4().hex[:8].upper()}",
            random.choice(patients),
            random.choice(["asha_worker", "clinic", "volunteer"]),
            f"Symptoms for {disease}",
            severity,
            (report_date - timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
            random.choice([0, 1]),
            1 if disease in ["cholera", "diarrheal", "dysentery"] else random.choice([0, 1]),
            1 if disease in ["cholera"] else random.choice([0, 1]),
            random.choice([0, 1]),
            1 if severity in ["severe", "critical"] else random.choice([0, 1]),
            1 if disease == "dysentery" else 0,
            disease,
            random.choice(water_sources),
            v["lat"] + random.uniform(-0.05, 0.05),
            v["lon"] + random.uniform(-0.05, 0.05),
            report_date.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # Seed water quality readings
    for i in range(120):
        v = random.choice(villages)
        days_ago = random.randint(0, 30)
        reading_date = datetime.now() - timedelta(days=days_ago)
        ph = round(random.uniform(5.5, 8.5), 1)
        bacteria = random.randint(10, 2000)
        contaminant = round(random.uniform(1, 80), 1)
        risk = "HIGH" if bacteria > 1000 or contaminant > 50 else "MEDIUM" if bacteria > 500 or contaminant > 30 else "LOW"
        cursor.execute("""
            INSERT INTO water_quality
            (reading_id, source_name, source_type, village, district, latitude, longitude,
             ph_level, turbidity_ntu, dissolved_oxygen_mg_l, contaminant_level_ppm,
             nitrate_levels, lead_concentration, bacteria_count_cfu_ml, temperature,
             is_safe, risk_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"WQ-{uuid.uuid4().hex[:8].upper()}",
            f"{v['name']} {random.choice(['River', 'Well', 'Pond', 'Tap'])}",
            random.choice(water_sources),
            v["name"], v["district"],
            v["lat"] + random.uniform(-0.05, 0.05),
            v["lon"] + random.uniform(-0.05, 0.05),
            ph,
            round(random.uniform(1, 40), 1),
            round(random.uniform(2, 10), 1),
            contaminant,
            round(random.uniform(1, 30), 1),
            round(random.uniform(0.001, 0.05), 3),
            bacteria,
            round(random.uniform(20, 38), 1),
            1 if risk == "LOW" else 0,
            risk,
            reading_date.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # Seed IoT sensors
    for v in villages:
        for j in range(random.randint(1, 3)):
            cursor.execute("""
                INSERT INTO iot_sensors (sensor_id, sensor_type, location_name, village, district, latitude, longitude, status, battery_level)
                VALUES (?, 'water_quality', ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"IOT-{v['name'][:3].upper()}-{j+1:03d}",
                f"{v['name']} Sensor #{j+1}",
                v["name"], v["district"],
                v["lat"] + random.uniform(-0.02, 0.02),
                v["lon"] + random.uniform(-0.02, 0.02),
                random.choice(["active", "active", "active", "inactive"]),
                round(random.uniform(20, 100), 0)
            ))

    # Seed resources
    resource_types = ["medical_team", "ors_packets", "water_purifier", "chlorine_tablets", "iv_fluids", "ambulance", "testing_kit"]
    for v in villages:
        for rtype in random.sample(resource_types, random.randint(3, 6)):
            qty = random.randint(10, 500) if rtype != "medical_team" else random.randint(1, 5)
            cursor.execute("""
                INSERT INTO resources (resource_type, village, district, quantity, allocated, status)
                VALUES (?, ?, ?, ?, ?, 'available')
            """, (rtype, v["name"], v["district"], qty, random.randint(0, qty // 2)))

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Seeded demo data: 80 patients, 200 symptom reports, 120 water readings, {len(villages)*2} sensors")


if __name__ == "__main__":
    init_db()
    seed_demo_data()
