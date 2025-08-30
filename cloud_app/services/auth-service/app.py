import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pymongo
import bcrypt
import redis
from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# MongoDB connection
client = pymongo.MongoClient(os.getenv('MONGODB_URL', 'mongodb://localhost:27017'))
db = client['medical_dictation']

# Redis connection for token blacklist
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# JWT token blacklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    token_in_redis = redis_client.get(jti)
    return token_in_redis is not None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "auth-service"}), 200

@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new doctor"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['email', 'password', 'name', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone_number = data['phone_number'].strip()
        
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({"error": "Invalid email address"}), 400
        
        # Check password strength
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
        # Check if user already exists
        existing_user = db.doctors.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "Email already registered"}), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create doctor record
        doctor = {
            "email": email,
            "name": name,
            "phone_number": phone_number,
            "hashed_password": password_hash,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = db.doctors.insert_one(doctor)
        doctor_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(
            identity=doctor_id,
            additional_claims={"email": email, "name": name}
        )
        
        logger.info(f"New doctor registered: {email}")
        
        return jsonify({
            "message": "Registration successful",
            "access_token": access_token,
            "doctor": {
                "id": doctor_id,
                "email": email,
                "name": name,
                "phone_number": phone_number
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Authenticate doctor and return JWT token"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        # Find doctor
        doctor = db.doctors.find_one({"email": email})
        if not doctor:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check if account is active
        if not doctor.get('is_active', True):
            return jsonify({"error": "Account is deactivated"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), doctor['hashed_password']):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Update last login
        db.doctors.update_one(
            {"_id": doctor['_id']},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(
            identity=str(doctor['_id']),
            additional_claims={
                "email": doctor['email'],
                "name": doctor['name']
            }
        )
        
        logger.info(f"Doctor logged in: {email}")
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "doctor": {
                "id": str(doctor['_id']),
                "email": doctor['email'],
                "name": doctor['name'],
                "phone_number": doctor['phone_number']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout doctor and blacklist token"""
    try:
        jti = get_jwt()['jti']
        # Add token to blacklist (expires with token)
        redis_client.set(jti, "", ex=app.config['JWT_ACCESS_TOKEN_EXPIRES'])
        
        return jsonify({"message": "Successfully logged out"}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current doctor's profile"""
    try:
        doctor_id = get_jwt_identity()
        
        doctor = db.doctors.find_one(
            {"_id": ObjectId(doctor_id)},
            {"hashed_password": 0}  # Exclude password from response
        )
        
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Convert ObjectId to string
        doctor['_id'] = str(doctor['_id'])
        
        return jsonify({"doctor": doctor}), 200
        
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"error": "Failed to get profile"}), 500

@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update doctor's profile"""
    try:
        doctor_id = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Fields that can be updated
        allowed_fields = ['name', 'phone_number']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field].strip()
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        update_data['updated_at'] = datetime.utcnow()
        
        # Update doctor
        result = db.doctors.update_one(
            {"_id": ObjectId(doctor_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Doctor not found"}), 404
        
        return jsonify({"message": "Profile updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({"error": "Failed to update profile"}), 500

@app.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("3 per minute")
def change_password():
    """Change doctor's password"""
    try:
        doctor_id = get_jwt_identity()
        data = request.json
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({"error": "Current and new passwords required"}), 400
        
        if len(new_password) < 8:
            return jsonify({"error": "New password must be at least 8 characters long"}), 400
        
        # Get doctor
        doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), doctor['hashed_password']):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        db.doctors.update_one(
            {"_id": ObjectId(doctor_id)},
            {
                "$set": {
                    "hashed_password": new_password_hash,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({"error": "Failed to change password"}), 500

@app.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify if JWT token is valid"""
    try:
        doctor_id = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            "valid": True,
            "doctor_id": doctor_id,
            "email": claims.get('email'),
            "name": claims.get('name')
        }), 200
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({"valid": False}), 401

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.errorhandler(422)
def handle_unprocessable_entity(e):
    return jsonify({"error": "Invalid JWT token"}), 422

@app.errorhandler(401)
def handle_unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)