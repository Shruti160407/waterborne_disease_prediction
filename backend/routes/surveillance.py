"""
============================================
Surveillance Routes - Health Data Collection
============================================
APIs for patient data, symptom reporting, offline sync,
SMS input, IoT sensors, heatmap, and dashboard stats.
"""

import sys
import uuid
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database.schema import get_db
from backend.utils.logger import app_logger

surveillance_bp = Blueprint("surveillance", __name__, url_prefix="/api")


# ============================================
# Patient Data Collection
# ============================================

@surveillance_bp.route("/patients", methods=["POST"])
def register_patient():
    """Register a new patient."""
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Patient name is required"}), 400

    pid = f"PAT-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO patients (patient_id, name, age, gender, village, district, 
                                  state, latitude, longitude, contact_phone, asha_worker_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid, data["name"], data.get("age"), data.get("gender"),
            data.get("village"), data.get("district"), data.get("state", "Assam"),
            data.get("latitude"), data.get("longitude"),
            data.get("contact_phone"), data.get("asha_worker_id")
        ))
        conn.commit()
        app_logger.info(f"Patient registered: {pid}")
        return jsonify({"patient_id": pid, "message": "Patient registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@surveillance_bp.route("/patients", methods=["GET"])
def list_patients():
    """List patients with optional filters."""
    village = request.args.get("village")
    district = request.args.get("district")
    limit = request.args.get("limit", 50, type=int)

    conn = get_db()
    query = "SELECT * FROM patients WHERE 1=1"
    params = []
    if village:
        query += " AND village = ?"
        params.append(village)
    if district:
        query += " AND district = ?"
        params.append(district)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify({"patients": [dict(r) for r in rows], "count": len(rows)}), 200


# ============================================
# Symptom Reporting
# ============================================

@surveillance_bp.route("/symptoms", methods=["POST"])
def report_symptoms():
    """Submit a symptom report from ASHA worker / clinic / volunteer."""
    data = request.get_json()
    if not data or not data.get("symptoms"):
        return jsonify({"error": "Symptoms field is required"}), 400

    report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO symptom_reports 
            (report_id, patient_id, reporter_type, reporter_id, symptoms, severity,
             onset_date, fever, diarrhea, vomiting, abdominal_pain, dehydration,
             blood_in_stool, skin_rash, jaundice, suspected_disease, water_source,
             notes, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            data.get("patient_id"),
            data.get("reporter_type", "asha_worker"),
            data.get("reporter_id"),
            data["symptoms"],
            data.get("severity", "moderate"),
            data.get("onset_date"),
            data.get("fever", False),
            data.get("diarrhea", False),
            data.get("vomiting", False),
            data.get("abdominal_pain", False),
            data.get("dehydration", False),
            data.get("blood_in_stool", False),
            data.get("skin_rash", False),
            data.get("jaundice", False),
            data.get("suspected_disease"),
            data.get("water_source"),
            data.get("notes"),
            data.get("latitude"),
            data.get("longitude")
        ))
        conn.commit()

        # Check if this triggers an alert pattern
        _check_outbreak_pattern(conn, data)

        app_logger.info(f"Symptom report: {report_id} | Disease: {data.get('suspected_disease')}")
        return jsonify({
            "report_id": report_id,
            "message": "Symptom report submitted successfully"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@surveillance_bp.route("/symptoms", methods=["GET"])
def list_symptoms():
    """List symptom reports with filters."""
    village = request.args.get("village")
    disease = request.args.get("disease")
    severity = request.args.get("severity")
    days = request.args.get("days", 7, type=int)
    limit = request.args.get("limit", 100, type=int)

    conn = get_db()
    query = "SELECT * FROM symptom_reports WHERE created_at >= datetime('now', ?)"
    params = [f"-{days} days"]

    if village:
        query += " AND latitude IS NOT NULL"
    if disease:
        query += " AND suspected_disease = ?"
        params.append(disease)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify({"reports": [dict(r) for r in rows], "count": len(rows)}), 200


# ============================================
# Water Quality Data Collection
# ============================================

@surveillance_bp.route("/water-quality", methods=["POST"])
def submit_water_quality():
    """Submit a water quality reading."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Data required"}), 400

    reading_id = f"WQ-{uuid.uuid4().hex[:8].upper()}"

    # Determine risk
    bacteria = data.get("bacteria_count_cfu_ml", 0)
    contaminant = data.get("contaminant_level_ppm", 0)
    ph = data.get("ph_level", 7.0)
    risk = "LOW"
    if bacteria > 1000 or contaminant > 50 or ph < 5.5 or ph > 9.0:
        risk = "HIGH"
    elif bacteria > 500 or contaminant > 30:
        risk = "MEDIUM"

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO water_quality
            (reading_id, source_name, source_type, village, district, latitude, longitude,
             ph_level, turbidity_ntu, dissolved_oxygen_mg_l, contaminant_level_ppm,
             nitrate_levels, lead_concentration, bacteria_count_cfu_ml, temperature,
             conductivity, tds, is_safe, risk_level, sensor_id, collected_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reading_id, data.get("source_name"), data.get("source_type"),
            data.get("village"), data.get("district"),
            data.get("latitude"), data.get("longitude"),
            data.get("ph_level"), data.get("turbidity_ntu"),
            data.get("dissolved_oxygen_mg_l"), data.get("contaminant_level_ppm"),
            data.get("nitrate_levels"), data.get("lead_concentration"),
            data.get("bacteria_count_cfu_ml"), data.get("temperature"),
            data.get("conductivity"), data.get("tds"),
            1 if risk == "LOW" else 0, risk,
            data.get("sensor_id"), data.get("collected_by")
        ))
        conn.commit()
        app_logger.info(f"Water quality reading: {reading_id} | Risk: {risk}")
        return jsonify({"reading_id": reading_id, "risk_level": risk}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@surveillance_bp.route("/water-quality", methods=["GET"])
def list_water_quality():
    """List water quality readings."""
    days = request.args.get("days", 7, type=int)
    village = request.args.get("village")
    risk = request.args.get("risk")
    limit = request.args.get("limit", 100, type=int)

    conn = get_db()
    query = "SELECT * FROM water_quality WHERE created_at >= datetime('now', ?)"
    params = [f"-{days} days"]
    if village:
        query += " AND village = ?"
        params.append(village)
    if risk:
        query += " AND risk_level = ?"
        params.append(risk)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify({"readings": [dict(r) for r in rows], "count": len(rows)}), 200


# ============================================
# IoT Sensor Data Ingestion
# ============================================

@surveillance_bp.route("/sensors", methods=["POST"])
def ingest_sensor_data():
    """Receive data from IoT water quality sensors."""
    data = request.get_json()
    if not data or not data.get("sensor_id"):
        return jsonify({"error": "sensor_id is required"}), 400

    conn = get_db()
    try:
        # Update sensor last reading
        conn.execute("""
            UPDATE iot_sensors SET last_reading_at = CURRENT_TIMESTAMP, 
            battery_level = ?, status = ? WHERE sensor_id = ?
        """, (
            data.get("battery_level"), 
            "active" if data.get("battery_level", 100) > 10 else "error",
            data["sensor_id"]
        ))

        # Also store as water quality reading
        reading_id = f"IOT-{uuid.uuid4().hex[:8].upper()}"
        bacteria = data.get("bacteria_count_cfu_ml", 0)
        contaminant = data.get("contaminant_level_ppm", 0)
        risk = "HIGH" if bacteria > 1000 or contaminant > 50 else "MEDIUM" if bacteria > 500 else "LOW"

        conn.execute("""
            INSERT INTO water_quality
            (reading_id, source_name, village, latitude, longitude,
             ph_level, turbidity_ntu, dissolved_oxygen_mg_l, contaminant_level_ppm,
             bacteria_count_cfu_ml, temperature, is_safe, risk_level, sensor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reading_id, f"IoT Sensor {data['sensor_id']}",
            data.get("village"), data.get("latitude"), data.get("longitude"),
            data.get("ph_level"), data.get("turbidity_ntu"),
            data.get("dissolved_oxygen_mg_l"), data.get("contaminant_level_ppm"),
            bacteria, data.get("temperature"),
            1 if risk == "LOW" else 0, risk, data["sensor_id"]
        ))

        conn.commit()
        app_logger.info(f"IoT sensor data: {data['sensor_id']} | Risk: {risk}")
        return jsonify({"reading_id": reading_id, "risk_level": risk, "status": "ingested"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@surveillance_bp.route("/sensors", methods=["GET"])
def list_sensors():
    """List all IoT sensors and their status."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM iot_sensors ORDER BY status, location_name").fetchall()
    conn.close()
    return jsonify({"sensors": [dict(r) for r in rows], "count": len(rows)}), 200


# ============================================
# Offline Data Sync
# ============================================

@surveillance_bp.route("/sync", methods=["POST"])
def sync_offline_data():
    """
    Receive batched offline data from field devices.
    Accepts an array of records collected while offline.
    """
    data = request.get_json()
    if not data or not isinstance(data.get("records"), list):
        return jsonify({"error": "Expected 'records' array"}), 400

    records = data["records"]
    results = {"synced": 0, "failed": 0, "errors": []}
    conn = get_db()

    for record in records:
        try:
            data_type = record.get("type", "symptom_report")
            payload = record.get("data", {})
            sync_id = f"SYNC-{uuid.uuid4().hex[:8].upper()}"

            conn.execute("""
                INSERT INTO sync_queue (sync_id, data_type, payload, source_device, status)
                VALUES (?, ?, ?, ?, 'synced')
            """, (sync_id, data_type, json.dumps(payload), data.get("device_id", "unknown")))

            # Process based on type
            if data_type == "symptom_report":
                report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
                conn.execute("""
                    INSERT OR IGNORE INTO symptom_reports 
                    (report_id, patient_id, reporter_type, symptoms, severity,
                     suspected_disease, water_source, latitude, longitude, is_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    report_id, payload.get("patient_id"), payload.get("reporter_type", "asha_worker"),
                    payload.get("symptoms", ""), payload.get("severity", "moderate"),
                    payload.get("suspected_disease"), payload.get("water_source"),
                    payload.get("latitude"), payload.get("longitude")
                ))
            elif data_type == "water_quality":
                wq_id = f"WQ-{uuid.uuid4().hex[:8].upper()}"
                conn.execute("""
                    INSERT OR IGNORE INTO water_quality
                    (reading_id, source_name, village, latitude, longitude,
                     ph_level, turbidity_ntu, bacteria_count_cfu_ml, risk_level, is_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    wq_id, payload.get("source_name"), payload.get("village"),
                    payload.get("latitude"), payload.get("longitude"),
                    payload.get("ph_level"), payload.get("turbidity_ntu"),
                    payload.get("bacteria_count_cfu_ml"), payload.get("risk_level", "LOW")
                ))

            results["synced"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(str(e))

    conn.commit()
    conn.close()
    app_logger.info(f"Offline sync: {results['synced']} synced, {results['failed']} failed")
    return jsonify(results), 200


# ============================================
# SMS-Based Input Fallback
# ============================================

@surveillance_bp.route("/sms-input", methods=["POST"])
def process_sms_input():
    """
    Process SMS-based symptom reports for areas with no internet.
    
    SMS Format: REPORT <village> <disease> <severity> <patient_count>
    Example: REPORT Majuli cholera severe 5
    """
    data = request.get_json()
    sms_body = data.get("message", data.get("Body", "")).strip()
    from_number = data.get("from", data.get("From", "unknown"))

    if not sms_body:
        return jsonify({"error": "Empty SMS message"}), 400

    parts = sms_body.upper().split()
    
    if len(parts) < 3 or parts[0] != "REPORT":
        return jsonify({
            "response": "Invalid format. Use: REPORT <village> <disease> <severity> <count>",
            "status": "format_error"
        }), 400

    village = parts[1].title() if len(parts) > 1 else "Unknown"
    disease = parts[2].lower() if len(parts) > 2 else "unknown"
    severity = parts[3].lower() if len(parts) > 3 else "moderate"
    count = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 1

    # Validate severity
    if severity not in ["mild", "moderate", "severe", "critical"]:
        severity = "moderate"

    conn = get_db()
    try:
        for i in range(count):
            report_id = f"SMS-{uuid.uuid4().hex[:8].upper()}"
            conn.execute("""
                INSERT INTO symptom_reports 
                (report_id, reporter_type, reporter_id, symptoms, severity,
                 suspected_disease, notes)
                VALUES (?, 'asha_worker', ?, ?, ?, ?, ?)
            """, (
                report_id, from_number,
                f"SMS reported: {disease} in {village}",
                severity, disease,
                f"SMS from {from_number}: {sms_body}"
            ))

        conn.commit()
        app_logger.info(f"SMS input processed: {village} | {disease} | {severity} | {count} reports")
        return jsonify({
            "response": f"Received: {count} {disease} case(s) in {village} ({severity}). Report ID: {report_id}",
            "status": "accepted",
            "reports_created": count
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================
# Dashboard Stats API
# ============================================

@surveillance_bp.route("/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Get aggregated dashboard statistics."""
    conn = get_db()
    try:
        stats = {}

        # Total patients
        stats["total_patients"] = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]

        # Symptom reports (last 7 days)
        stats["reports_7d"] = conn.execute(
            "SELECT COUNT(*) FROM symptom_reports WHERE created_at >= datetime('now', '-7 days')"
        ).fetchone()[0]

        # Reports today
        stats["reports_today"] = conn.execute(
            "SELECT COUNT(*) FROM symptom_reports WHERE created_at >= datetime('now', 'start of day')"
        ).fetchone()[0]

        # Disease breakdown
        disease_rows = conn.execute("""
            SELECT suspected_disease, COUNT(*) as count, 
                   SUM(CASE WHEN severity IN ('severe', 'critical') THEN 1 ELSE 0 END) as severe_count
            FROM symptom_reports 
            WHERE created_at >= datetime('now', '-7 days') AND suspected_disease IS NOT NULL
            GROUP BY suspected_disease 
            ORDER BY count DESC
        """).fetchall()
        stats["disease_breakdown"] = [dict(r) for r in disease_rows]

        # Water quality summary
        wq_rows = conn.execute("""
            SELECT risk_level, COUNT(*) as count 
            FROM water_quality WHERE created_at >= datetime('now', '-7 days')
            GROUP BY risk_level
        """).fetchall()
        stats["water_quality_summary"] = {r["risk_level"]: r["count"] for r in wq_rows}

        # Active sensors
        sensor_rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM iot_sensors GROUP BY status
        """).fetchall()
        stats["sensor_status"] = {r["status"]: r["count"] for r in sensor_rows}

        # Active alerts
        stats["active_alerts"] = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE acknowledged = 0"
        ).fetchone()[0]

        # Severity distribution
        sev_rows = conn.execute("""
            SELECT severity, COUNT(*) as count 
            FROM symptom_reports WHERE created_at >= datetime('now', '-7 days')
            GROUP BY severity
        """).fetchall()
        stats["severity_distribution"] = {r["severity"]: r["count"] for r in sev_rows}

        # Daily trend (last 7 days)
        trend_rows = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM symptom_reports 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """).fetchall()
        stats["daily_trend"] = [dict(r) for r in trend_rows]

        # Villages with highest cases
        village_rows = conn.execute("""
            SELECT village, COUNT(*) as cases
            FROM symptom_reports s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE s.created_at >= datetime('now', '-7 days')
            GROUP BY village
            ORDER BY cases DESC LIMIT 10
        """).fetchall()
        stats["hotspot_villages"] = [dict(r) for r in village_rows]

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================
# Heatmap Data API
# ============================================

@surveillance_bp.route("/heatmap", methods=["GET"])
def heatmap_data():
    """
    Get geo-located data for disease heatmap visualization.
    Returns symptom clusters, water quality markers, and sensor locations.
    """
    data_type = request.args.get("type", "all")
    days = request.args.get("days", 7, type=int)

    conn = get_db()
    result = {"symptom_clusters": [], "water_quality": [], "sensors": []}

    try:
        if data_type in ["all", "symptoms"]:
            rows = conn.execute("""
                SELECT latitude, longitude, suspected_disease, severity, 
                       COUNT(*) as case_count, created_at
                FROM symptom_reports 
                WHERE latitude IS NOT NULL 
                  AND created_at >= datetime('now', ?)
                GROUP BY ROUND(latitude, 2), ROUND(longitude, 2), suspected_disease
                ORDER BY case_count DESC
            """, (f"-{days} days",)).fetchall()
            result["symptom_clusters"] = [dict(r) for r in rows]

        if data_type in ["all", "water"]:
            rows = conn.execute("""
                SELECT latitude, longitude, risk_level, ph_level, 
                       bacteria_count_cfu_ml, source_name, created_at
                FROM water_quality 
                WHERE latitude IS NOT NULL 
                  AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """, (f"-{days} days",)).fetchall()
            result["water_quality"] = [dict(r) for r in rows]

        if data_type in ["all", "sensors"]:
            rows = conn.execute("""
                SELECT sensor_id, latitude, longitude, status, 
                       battery_level, location_name, last_reading_at
                FROM iot_sensors 
                WHERE latitude IS NOT NULL
            """).fetchall()
            result["sensors"] = [dict(r) for r in rows]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================
# Resource Allocation API
# ============================================

@surveillance_bp.route("/resources", methods=["GET"])
def get_resources():
    """Get resource allocation data across villages."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT r.*, 
                   (SELECT COUNT(*) FROM symptom_reports s 
                    JOIN patients p ON s.patient_id = p.patient_id 
                    WHERE p.village = r.village 
                    AND s.created_at >= datetime('now', '-7 days')) as recent_cases
            FROM resources r
            ORDER BY r.village, r.resource_type
        """).fetchall()

        # Group by village
        villages = {}
        for r in rows:
            v = r["village"]
            if v not in villages:
                villages[v] = {"village": v, "district": r["district"], "resources": [], "recent_cases": r["recent_cases"]}
            villages[v]["resources"].append({
                "type": r["resource_type"],
                "quantity": r["quantity"],
                "allocated": r["allocated"],
                "available": r["quantity"] - r["allocated"],
                "status": r["status"]
            })

        return jsonify({"allocations": list(villages.values())}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@surveillance_bp.route("/resources/allocate", methods=["POST"])
def allocate_resource():
    """Allocate resources to a village."""
    data = request.get_json()
    if not data or not data.get("village") or not data.get("resource_type"):
        return jsonify({"error": "village and resource_type required"}), 400

    conn = get_db()
    try:
        qty = data.get("quantity", 1)
        conn.execute("""
            UPDATE resources SET allocated = allocated + ?, updated_at = CURRENT_TIMESTAMP
            WHERE village = ? AND resource_type = ? AND (quantity - allocated) >= ?
        """, (qty, data["village"], data["resource_type"], qty))
        conn.commit()
        return jsonify({"message": f"Allocated {qty} {data['resource_type']} to {data['village']}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================
# Helper: Outbreak Pattern Detection
# ============================================

def _check_outbreak_pattern(conn, report_data):
    """Check if recent symptom reports indicate an outbreak pattern."""
    disease = report_data.get("suspected_disease")
    if not disease:
        return

    # Count reports of same disease in last 48 hours
    count = conn.execute("""
        SELECT COUNT(*) FROM symptom_reports 
        WHERE suspected_disease = ? AND created_at >= datetime('now', '-2 days')
    """, (disease,)).fetchone()[0]

    # If 5+ cases in 48 hours, trigger auto-alert
    if count >= 5:
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        conn.execute("""
            INSERT INTO alerts (alert_id, alert_type, risk_level, message, details)
            VALUES (?, 'outbreak', 'HIGH', ?, ?)
        """, (
            alert_id,
            f"⚠️ Outbreak pattern detected: {count} cases of {disease} in last 48 hours",
            json.dumps({"disease": disease, "case_count": count, "trigger": "auto_pattern"})
        ))
        app_logger.warning(f"OUTBREAK ALERT: {count} cases of {disease} detected!")
