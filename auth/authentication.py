from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError
from extension import bcrypt, jwt
import secrets
from email_service import send_verification_email
from configuration.db import get_connection
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Data must not be empty."})
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not name:
        return jsonify({"success": False, "message":  "Name cannot be empty, Name is required."}), 400
    
    if role not in ["VENDOR", "WAITER", "PLANNER"]:
        return jsonify({"success": False, "message":  "Choose a valid role."}), 400

    if not email:
        return jsonify({"success": False, "message":  "Mail cannot be empty."})
    
    if not password:
        return jsonify({"success": False, "message":  "Password cannot be empty."})
    
    name = name.strip()
    email = email.strip().lower()

    if len(name) < 2:
        return jsonify({"success":  False, "message": "Name must contain at least 3 character."})
    if len(name) > 100:
        return jsonify({
            "success":  False, "message": "Name cannot exceed 100 character."
        })
    
    if len(email) > 255:
        return jsonify({
            "success": False,
            "message": "Email cannot exceed 255 character."
        })

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must not contain at least 8 characters."
        })
    try:
        validate_email(email)
    except EmailNotValidError as e:
        print(f"Error: {str(e)}")
    
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    verification_token = secrets.token_urlsafe(32)

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                            INSERT INTO users (name,  email, password, role, verification_token) 
                            VALUE (%s, %s, %s, %s, %s) 
                        """, (name, email, hashed_password, role, verification_token))
            
            conn.commit()
            verification_link = f"https://event-management-platform-1-343z.onrender.com/verify-email/{verification_token}"
            html=f"""
                    <html>
                        <body>
                            <h1>Welcome {name}!</h1>
                            <p>Click below to verify your account.</p>
                            <a href="{verification_link}">Verify Account</a>
                        </body>
                    </html>
                """
            send_verification_email(email, "Verify Email", html)

            return jsonify({
                "success": True,
                "message": "User registrered successfully."
            }), 201
    except Exception as e:
        return jsonify(
                        {
                        "success": False, 
                         "message": "Failed to register user", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT id FROM users
                           WHERE verification_token = %s
                        """, (token))
            
            user = cursor.fetchone()
            if not user:
                return jsonify({"success": False, "message": "Invalide verification link!"}), 400
            
            cursor.execute("""
                            UPDATE users SET is_verified = TRUE,
                            verification_token = NULL WHERE id = %s
                        """, (user["id"],))
            return jsonify({"success": True, "message": "User verified successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
            if conn:
                conn.close()

@auth_bp.route("/login", methods=["POST"])
def login(request):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Data cannot be empty."})
    
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and Password cannot be empty."}), 400
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                                SELECT id, name, emai, password, role, is_verified 
                                FROM users WHERE email = %s
                            """, (email))
            user = cursor.fetchone()
            if not user:
                return jsonify({"success": False, "message": "Invalid email or password!"}), 400
            
            if not bcrypt.check_password_hash(user["password"], password):
                return jsonify({"success": False, "message": "Incorrect password!"}), 401
            
            if not user["is_verified"]:
                return jsonify({"success": False, "message": "Please verify your email before logging in."}), 403

            access_token = jwt.create_access_token(identity=user["id"],
                                                   additional_claims={"role": user["role"], "email": user["email"]})
            return jsonify({"success": True,
                            "message": "Login successful.",
                            "access_token": access_token,
                            "user": {
                                "id": user["id"],
                                "name": user["name"],
                                "email": user["email"],
                                "role":  user["role"]
                            }}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
            if conn:
                conn.close()

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Data cannot be empty."})
    
    email = data.get("email")
    if not email:
        return jsonify({"success": False, "message": "Email cannot be empty."}), 400
    
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT id, name FROM users WHERE email = %s
                        """, (email))
            user = cursor.fetchone()
            if not user:
                return jsonify({"success": False, "message": "User with this email does not exist."}), 404
            
            reset_token = secrets.token_urlsafe(32)
            cursor.execute("""
                            UPDATE users SET reset_token = %s WHERE id = %s
                        """, (reset_token, user["id"]))
            conn.commit()

            reset_link = f"https://event-management-platform-1-343z.onrender.com/reset-password/{reset_token}"
            html=f"""
                    <html>
                        <body>
                            <h1>Password Reset Request</h1>
                            <p>Click below to reset your password.</p>
                            <a href="{reset_link}">Reset Password</a>
                        </body>
                    </html>
                """
            send_verification_email(email, "Reset Password", html)

            return jsonify({"success": True, "message": "Password reset link sent to your email."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if conn:
             conn.close()