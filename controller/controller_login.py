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
userlog_model = None

def set_db(database):
    global db, userlog_model
    db = database
    userlog_model = UserLog(database)

def format_phone(phone):
    if phone.startswith("08"):
        return "62" + phone[1:]
    return phone

# ======== LOGIN MANUAL ========
def login_user():
    data = request.get_json()

    phone = data.get("phone")
    password = data.get("password")

    if not phone or not password:
        return jsonify({
            "success": False,
            "message": "Nomor WhatsApp dan Password harus diisi"
        }), 400

    # format 08 -> 62
    if phone.startswith("08"):
        phone = "62" + phone[1:]

    user = User.find_by_phone(phone)

    if not user:
        return jsonify({
            "success": False,
            "message": "Nomor tidak terdaftar"
        }), 404

    if not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Password salah"
        }), 401

    access_token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=timedelta(hours=1)
    )

    # ===== LOG LOGIN =====
    userlog_model.log_activity(
        user_id=str(user["_id"]),
        action="Login",
        status="success",
        keterangan=f"{user.get('nama')} berhasil login"
    )
    
    return jsonify({
        "success": True,
        "token": access_token,
        "user": {
            "_id": str(user["_id"]),
            "nama": user.get("nama", ""),
            "phone": user.get("phone", ""),
            "foto": user.get("foto", ""),
            "role": user.get("role", "ibu"),
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
