import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "aquaguard_ai")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-aquaguard-key")
JWT_EXPIRES_HOURS = 24

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[DB_NAME]
            
            # Test connection
            self.client.admin.command('ping')
            print(f"[SUCCESS] Successfully connected to MongoDB database: {DB_NAME}")
            
            # Setup collections and indexes
            self.setup_indexes()
            
            # Create default admin if not exists
            self.create_default_admin()
            
        except Exception as e:
            print(f"[ERROR] MongoDB Connection Error: {e}")
            self.client = None
            self.db = None

    def is_connected(self):
        return self.client is not None and self.db is not None

    def setup_indexes(self):
        if not self.is_connected(): return
        
        # Ensure email uniqueness for users
        self.db.Users.create_index("email", unique=True)
        # Fast lookups for alerts
        self.db.Alerts.create_index("created_at")
        self.db.WaterData.create_index([("latitude", 1), ("longitude", 1)])

    def create_default_admin(self):
        if not self.is_connected(): return
        
        admin_email = "admin@aquaguard.ai"
        if not self.db.Users.find_one({"email": admin_email}):
            hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            self.db.Users.insert_one({
                "name": "System Admin",
                "email": admin_email,
                "password": hashed_password.decode('utf-8'),
                "role": "Admin",
                "created_at": datetime.utcnow()
            })
            print("[SUCCESS] Default Admin created (admin@aquaguard.ai / admin123)")

# Singleton instance
mongo_db = DatabaseManager()
