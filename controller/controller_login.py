from flask import request, jsonify, session
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from models.datauser_model import User
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from models.userlog_model import UserLog
from firebase_admin import auth

GOOGLE_CLIENT_ID = '945236677336-pl4ua4gp1p388u0131uouanod6av77gp.apps.googleusercontent.com'


# ======== SET DATABASE ========
def set_db(database):
    global db
    db = database

# ======== LOGIN MANUAL ========
def login_user():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email dan Password harus diisi"}), 400

    user = User.find_by_email(email)
    if not user:
        return jsonify({"success": False, "message": "Email tidak terdaftar"}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Password salah"}), 401

    if not user.get("otp_verified", False):
        return jsonify({"success": False, "message": "Akun belum diverifikasi OTP"}), 403

    session["user_id"] = str(user["_id"])
    session["user_name"] = user["nama"]

    access_token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=timedelta(hours=1)
    )

    UserLog(db).log_activity(
        str(user["_id"]),
        "login",
        status="success",
        keterangan="Login manual"
    )

    return jsonify({
        "success": True,
        "message": "Login berhasil",
        "token": access_token,
        "user": {
            "_id": str(user["_id"]),
            "nama": user.get("nama", ""),
            "email": user["email"],
            "foto": user.get("foto", ""),
            "role": user.get("role", "ibu"),   # ⭐ TAMBAHAN
            "is_validated": user.get("is_validated", False)
        }
    }), 200

def login_google():
    data = request.get_json()
    token = data.get('firebaseToken')

    if not token:
        return jsonify({"success": False, "message": "Token Firebase diperlukan"}), 400

    try:
        # 🔥 VERIFY TOKEN (BENAR)
        decoded_token = auth.verify_id_token(token)

        email = decoded_token.get('email')
        name = decoded_token.get('name', 'User')
        picture = decoded_token.get('picture', '')

        if not email:
            return jsonify({"success": False, "message": "Email tidak ditemukan"}), 400

        user = User.find_by_email(email)

        # REGISTER OTOMATIS
        if not user:
            new_user = {
                "nama": name,
                "email": email,
                "foto": picture,
                "password": None,
                "created_at": datetime.utcnow()
            }
            inserted_id = User.insert_user(new_user)
            user = User.find_by_id(inserted_id)

        access_token = create_access_token(
            identity=str(user["_id"]),
            expires_delta=timedelta(hours=1)
        )

        return jsonify({
            "success": True,
            "token": access_token,
            "user": {
                "_id": str(user["_id"]),
                "nama": user.get("nama", ""),
                "email": user["email"],
                "foto": user.get("foto", "")
            }
        }), 200

    except Exception as e:
        print(f"[FIREBASE LOGIN ERROR] {e}")
        return jsonify({
            "success": False,
            "message": "Token Firebase tidak valid"
        }), 401
    
# ======== OPTIONAL: LOGIN PAGE UNTUK WEB ========
from flask import render_template
def login_page():
    return render_template("login.html")  # Jika mau support web
