from flask import Blueprint, request, jsonify
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from backend.database.mongodb import mongo_db, JWT_SECRET, JWT_EXPIRES_HOURS

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def require_auth(roles=None):
    """
    Middleware decorator for protecting routes.
    If roles is provided, ensures the user has one of the specified roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid authorization token"}), 401
            
            token = auth_header.split(" ")[1]
            
            try:
                decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                request.user = decoded_token  # attach user info to request
                
                if roles and decoded_token.get("role") not in roles:
                    return jsonify({"error": "Unauthorized access - Role not permitted"}), 403
                    
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user."""
    if not mongo_db.is_connected():
        return jsonify({"error": "Database connection failed"}), 500
        
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "User")  # Default to User
    
    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
        
    if role not in ["User", "Admin"]:
        return jsonify({"error": "Invalid role"}), 400
        
    users_coll = mongo_db.db.Users
    
    # Check if user already exists
    if users_coll.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists"}), 409
        
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    new_user = {
        "name": name,
        "email": email,
        "password": hashed_password.decode('utf-8'),
        "role": role,
        "created_at": datetime.utcnow()
    }
    
    users_coll.insert_one(new_user)
    
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT."""
    if not mongo_db.is_connected():
        return jsonify({"error": "Database connection failed"}), 500
        
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = mongo_db.db.Users.find_one({"email": email})
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401
        
    # Generate token
    token_payload = {
        "user_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS)
    }
    
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 200

@auth_bp.route("/me", methods=["GET"])
@require_auth()
def get_me():
    """Get current user details."""
    return jsonify({"user": request.user}), 200
