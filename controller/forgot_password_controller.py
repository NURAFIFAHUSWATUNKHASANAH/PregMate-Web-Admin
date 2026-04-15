import random
import datetime
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from dateutil import parser
from models.datauser_model import User
from utils.mailer import send_whatsapp

OTP_EXPIRE_MINUTES = 10


# ================================
# REQUEST OTP (VIA WHATSAPP)
# ================================
def request_otp():
    try:
        data = request.get_json()
        phone = data.get("phone")

        if not phone:
            return jsonify({"error": "Nomor WhatsApp harus diisi"}), 400

        # normalize 08 -> 62
        if phone.startswith("08"):
            phone = "62" + phone[1:]

        user = User.find_by_phone(phone)
        if not user:
            return jsonify({"error": "Nomor tidak terdaftar"}), 404

        otp = str(random.randint(100000, 999999))

        User.update_fields(user["_id"], {
            "otp": otp,
            "otp_created_at": datetime.datetime.utcnow().isoformat()
        })

        message = f"""
Halo {user.get('nama')},

Anda menerima permintaan untuk mengatur ulang password akun PregMate Anda.

Kode OTP Anda adalah: {otp}
Berlaku selama: 10 menit

Silakan masukkan kode OTP ini di aplikasi PregMate untuk melanjutkan proses reset password.

Demi keamanan akun Anda, jangan bagikan kode ini kepada siapapun.

Salam hangat,
Tim PregMate
"""

        send_whatsapp(phone, message)

        return jsonify({"message": "OTP berhasil dikirim ke WhatsApp"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================
# RESET PASSWORD (VIA OTP WHATSAPP)
# ================================
def reset_password():
    try:
        data = request.get_json()

        phone = data.get("phone")
        otp = data.get("otp")
        new_password = data.get("new_password")

        if not phone or not otp or not new_password:
            return jsonify({"error": "Data tidak lengkap"}), 400

        if phone.startswith("08"):
            phone = "62" + phone[1:]

        user = User.find_by_phone(phone)
        if not user:
            return jsonify({"error": "User tidak ditemukan"}), 404

        stored_otp = user.get("otp")
        otp_created = user.get("otp_created_at")

        if stored_otp != otp:
            return jsonify({"error": "OTP salah"}), 400

        if not otp_created:
            return jsonify({"error": "OTP tidak valid"}), 400

        otp_time = parser.isoparse(otp_created)

        if (datetime.datetime.utcnow() - otp_time).total_seconds() > 600:
            return jsonify({"error": "OTP sudah kadaluarsa"}), 400

        hashed_password = generate_password_hash(new_password)

        User.update_fields(user["_id"], {
            "password": hashed_password,
            "otp": None,
            "otp_created_at": None
        })

        message = f"""
Halo {user.get('nama')},

Password akun PregMate Anda telah berhasil diperbarui.

Jika Anda tidak merasa melakukan perubahan ini, segera hubungi tim PregMate untuk keamanan akun Anda.

Terima kasih,
Tim PregMate
"""

        send_whatsapp(phone, message)

        return jsonify({"message": "Password berhasil direset"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500