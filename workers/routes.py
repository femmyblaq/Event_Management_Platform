from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from configuration.db import get_connection
worker_bp = Blueprint("workers", __name__)

@worker_bp.route("/profile", methods=["POST"])
@jwt_required()
def create_worker_profile():
    data = request.get_json(silent=True) or {}

    bio = data.get("bio")
    experience_years = data.get("experience_years")
    location = data.get("location")
    expected_rate = data.get("expected_rate")

    if(isinstance(experience_years, bool) or not isinstance(experience_years, int) or not 0<=experience_years <=255):
        return jsonify({"success": False, "message": "Experience years must be an integer between 0 and 255."})

    if expected_rate is not None:
        try:
            expected_rate = float(expected_rate)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Expected rate must be a valid number"}), 400
    if expected_rate < 0:
        return jsonify({"success": False, "message": "Expected rate cannot be negative"}), 400
    
    user_id = int(get_jwt_identity())

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            pass
    except Exception as e:
        return jsonify({"success": False, "message": f"Something happend: {str(e)}"}), 500