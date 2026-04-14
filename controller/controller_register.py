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
        nama = data.get("nama")
        email = data.get("email")
        password = data.get("password")
        nama_suami = data.get("nama_suami")
        email_suami = data.get("email_suami")

        # Validasi dasar
        if not nama or not email or not password:
            return jsonify({"message": "Nama, email, dan password harus diisi"}), 400

        if User.find_by_email(email):
            return jsonify({"message": "Email sudah digunakan"}), 400

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(100000, 999999))

        # Simpan Akun Ibu
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

        # Simpan Akun Suami (Jika ada)
        suami_id = None
        if nama_suami and email_suami:
            if not User.find_by_email(email_suami):
                pass_suami_plain = generate_random_password()
                suami_data = {
                    "nama": nama_suami,
                    "email": email_suami,
                    "password": generate_password_hash(pass_suami_plain),
                    "role": "pendamping",
                    "partner_id": str(ibu_id),
                    "is_active": True,
                    "otp_verified": True
                }
                suami_id = User.insert_user(suami_data)
                User.update_fields(str(ibu_id), {"partner_id": str(suami_id)})
                
                # Email ke Suami (Jangan biarkan error email menghentikan proses)
                subj_suami = "Akun Pendamping PregMate"
                body_suami = f"Halo {nama_suami}, login dengan Email: {email_suami} & Password: {pass_suami_plain}"
                send_email(email_suami, subj_suami, body_suami)

        # Kirim OTP ke Ibu
        subject_otp = "Kode Verifikasi OTP PregMate"
        body_otp = f"Halo {nama}, Kode OTP Anda adalah: {otp}"
        
        email_sent = send_email(email, subject_otp, body_otp)

        # RESEP RAHASIA: Tetap return 201 meskipun email gagal
        # Jika email gagal, kamu bisa cek OTP langsung di Database MongoDB Atlas untuk testing
        return jsonify({
            "message": "Registrasi berhasil, silakan cek email untuk OTP" if email_sent else "Registrasi berhasil, tetapi gagal mengirim email OTP.",
            "user_id": str(ibu_id),
            "email_status": "sent" if email_sent else "failed"
        }), 201

    except Exception as e:
        print(f"CRITICAL REGISTER ERROR: {e}")
        return jsonify({"message": f"Terjadi kesalahan server: {e}"}), 500

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
