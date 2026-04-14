import random
import string
import datetime
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from dateutil import parser

from models.datauser_model import User
from utils.mailer import send_email


def set_db(database):
    global db
    db = database
    User.set_db(database)


# ================================
# GENERATE PASSWORD RANDOM SUAMI
# ================================
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# ================================
# REGISTER USER
# ================================
def register_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Request harus JSON"}), 400

        nama = data.get("nama")
        email = data.get("email")
        password = data.get("password")

        nama_suami = data.get("nama_suami")
        email_suami = data.get("email_suami")

        if not nama or not email or not password:
            return jsonify({
                "message": "Nama, email, dan password harus diisi"
            }), 400

        if len(password) < 6:
            return jsonify({
                "message": "Password minimal 6 karakter"
            }), 400

        if User.find_by_email(email):
            return jsonify({
                "message": "Email sudah digunakan"
            }), 400

        hashed_password = generate_password_hash(password)

        otp = str(random.randint(100000, 999999))

        ibu_data = {
            "nama": nama,
            "email": email,
            "password": hashed_password,
            "role": "ibu",
            "partner_id": None,
            "otp": otp,
            "otp_verified": False,
            "otp_created_at": datetime.datetime.utcnow().isoformat(),
            "is_validated": False
        }

        ibu_id = User.insert_user(ibu_data)

        if not ibu_id:
            return jsonify({"message": "Gagal membuat akun ibu"}), 500

        suami_id = None

        # ========================
        # SUAMI
        # ========================
        if nama_suami and email_suami:
            if User.find_by_email(email_suami):
                return jsonify({
                    "message": "Email suami sudah digunakan"
                }), 400

            password_suami_plain = generate_random_password()
            password_suami_hash = generate_password_hash(password_suami_plain)

            suami_data = {
                "nama": nama_suami,
                "email": email_suami,
                "password": password_suami_hash,
                "role": "pendamping",
                "partner_id": str(ibu_id),
                "is_active": True,
                "otp_verified": True
            }

            suami_id = User.insert_user(suami_data)

            User.update_fields(str(ibu_id), {
                "partner_id": str(suami_id)
            })

            subject = "Akun Pendamping PregMate"
            body = f"""
Halo {nama_suami},

Email : {email_suami}
Password : {password_suami_plain}
"""

            send_email(email_suami, subject, body)

        # ========================
        # OTP EMAIL IBU (🔥 FIX UTAMA)
        # ========================
        subject = "Kode Verifikasi OTP"
        body = f"""
Halo {nama},

Kode OTP Anda adalah:
{otp}

Berlaku 10 menit.
"""

        email_success = send_email(email, subject, body)

        # 🔥 HANDLE GAGAL EMAIL
        if not email_success:
            print("WARNING: Email OTP gagal dikirim")

            return jsonify({
                "message": "Registrasi berhasil, tapi email OTP gagal dikirim",
                "user_id": str(ibu_id),
                "otp_debug": otp  # 🔥 sementara biar bisa lanjut testing
            }), 201

        return jsonify({
            "message": "Registrasi berhasil, silakan verifikasi OTP",
            "user_id": str(ibu_id),
            "partner_created": suami_id is not None
        }), 201

    except Exception as e:
        print("ERROR REGISTER:", str(e))
        return jsonify({
            "message": f"Gagal registrasi: {e}"
        }), 500

# ================================
# VERIFY OTP
# ================================
def verify_otp():

    try:

        data = request.get_json()

        user_id = data.get("user_id")
        otp_input = data.get("otp")

        if not user_id or not otp_input:
            return jsonify({
                "message": "User ID dan OTP harus diisi"
            }), 400

        user = User.find_by_id(user_id)

        if not user:
            return jsonify({
                "message": "User tidak ditemukan"
            }), 404

        if user.get("otp_verified"):
            return jsonify({
                "message": "Email sudah terverifikasi"
            }), 400

        now = datetime.datetime.utcnow()

        otp_created = parser.isoparse(user.get("otp_created_at"))

        if (now - otp_created).total_seconds() > 600:
            return jsonify({
                "message": "Kode OTP sudah kedaluwarsa"
            }), 400

        if otp_input == user.get("otp"):

            User.update_fields(user_id, {

                "otp_verified": True,
                "otp": None,
                "otp_created_at": None

            })

            token = create_access_token(
                identity=str(user_id),
                expires_delta=datetime.timedelta(hours=1)
            )

            return jsonify({
                "message": "Verifikasi berhasil",
                "token": token
            }), 200

        else:

            return jsonify({
                "message": "Kode OTP salah"
            }), 400

    except Exception as e:

        print(f"Error OTP: {e}")

        return jsonify({
            "message": f"Terjadi kesalahan: {e}"
        }), 500
    
def verify_otp():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        otp_input = data.get("otp")

        if not user_id or not otp_input:
            return jsonify({"message": "User ID dan OTP harus diisi"}), 400

        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"message": "User tidak ditemukan"}), 404

        if user.get("otp_verified"):
            return jsonify({"message": "Email sudah terverifikasi"}), 400

        now = datetime.datetime.utcnow()
        otp_created = parser.isoparse(user.get("otp_created_at"))
        if (now - otp_created).total_seconds() > 600:
            return jsonify({"message": "Kode OTP sudah kedaluwarsa"}), 400

        if otp_input == user.get("otp"):
            User.update_fields(user_id, {
                "otp_verified": True,
                "otp": None,
                "otp_created_at": None
            })
            token = create_access_token(identity=str(user_id), expires_delta=datetime.timedelta(hours=1))
            return jsonify({"message": "Verifikasi berhasil", "token": token}), 200
        else:
            return jsonify({"message": "Kode OTP salah"}), 400
    except Exception as e:
        print(f"Error OTP: {e}")
        return jsonify({"message": f"Terjadi kesalahan: {e}"}), 500
