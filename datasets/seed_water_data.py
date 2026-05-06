import os
import sys
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

# Add project root to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.mongodb import mongo_db

def seed_water_data():
    if not mongo_db.is_connected():
        print("[ERROR] MongoDB not connected")
        return

    csv_path = os.path.join(os.path.dirname(__file__), 'east_region_india_water_disease_cleaned.csv')
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    records = df.to_dict('records')
    
    for i, record in enumerate(records):
        # Simulate recent dates over the last 30 days
        days_ago = (len(records) - i) % 30
        record['created_at'] = datetime.utcnow() - timedelta(days=days_ago)
        
        # Calculate a simple risk level based on Contaminant and Bacteria
        contaminant = record.get('Contaminant Level (ppm)', 0)
        bacteria = record.get('Bacteria Count (CFU/mL)', 0)
        
        # Arbitrary thresholds for demo purposes
        if bacteria > 2000 or contaminant > 30:
            record['risk_level'] = 'HIGH'
        elif bacteria > 1000 or contaminant > 10:
            record['risk_level'] = 'MEDIUM'
        else:
            record['risk_level'] = 'LOW'

    coll = mongo_db.db.water_data
    coll.drop()
    coll.insert_many(records)
    
    print(f"[SUCCESS] Inserted {len(records)} records into water_data collection.")
    print("\n--- Sample Record ---")
    sample = coll.find_one()
    # Exclude _id for printing cleanly
    if sample and '_id' in sample:
        del sample['_id']
    for k, v in sample.items():
        print(f"{k}: {v}")
    print("---------------------\n")

if __name__ == '__main__':
    seed_water_data()
