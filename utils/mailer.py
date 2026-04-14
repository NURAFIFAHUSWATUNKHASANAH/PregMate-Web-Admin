import datetime
import os
import random
import smtplib
from email.mime.text import MIMEText
from flask import request, jsonify
from bson import ObjectId
from flask import jsonify
from werkzeug.security import generate_password_hash
from models.datauser_model import User

OTP_EXPIRE_MINUTES = 10

def send_email(to_email, subject, message):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        # 🔥 DEBUG WAJIB
        print("SMTP_USER:", smtp_user)
        print("SMTP_PASS:", smtp_password)

        if not smtp_user or not smtp_password:
            raise Exception("SMTP env tidak terbaca")

        msg = MIMEText(message)
        msg['Reply-To'] = smtp_user
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()

        print("EMAIL BERHASIL DIKIRIM")
        return True

    except Exception as e:
        print("EMAIL ERROR:", str(e))
        return False

def request_otp():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request harus JSON"}), 400

        email = data.get('email')
        if not email:
            return jsonify({"error": "Email harus diisi"}), 400

        user = User.find_by_email(email)
        if not user:
            return jsonify({"error": "Email tidak ditemukan"}), 404

        user_id = user["_id"] if isinstance(user["_id"], ObjectId) else ObjectId(user["_id"])

        otp = f"{random.randint(100000, 999999)}"

        otp_data = {
            "otp": otp,
            "otp_expired_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRE_MINUTES)
        }

        User.db.users.update_one({"_id": user_id}, {"$set": otp_data})

        subject = "Kode OTP untuk Reset Password"
        message = f"Kode OTP Anda adalah: {otp}. Berlaku {OTP_EXPIRE_MINUTES} menit."

        success = send_email(email, subject, message)

        # 🔥 PENTING: JANGAN RETURN 500
        if not success:
            print("WARNING: Email gagal dikirim, tapi API tetap sukses")
            return jsonify({
                "message": "OTP dibuat (email mungkin gagal dikirim)",
                "otp_debug": otp  # 🔥 sementara untuk testing
            }), 200

        return jsonify({"message": "OTP berhasil dikirim ke email"}), 200

    except Exception as e:
        print("ERROR request_otp:", str(e))
        return jsonify({"error": str(e)}), 500
    
def reset_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request harus JSON"}), 400

        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')

        if not email or not otp or not new_password:
            return jsonify({"error": "Email, OTP, dan password baru harus diisi"}), 400

        user = User.find_by_email(email)
        if not user:
            return jsonify({"error": "Email tidak ditemukan"}), 404

        user_id = user["_id"] if isinstance(user["_id"], ObjectId) else ObjectId(user["_id"])

        stored_otp = user.get('otp')
        otp_expired_at = user.get('otp_expired_at')

        # ❌ OTP salah
        if stored_otp != otp:
            return jsonify({"error": "OTP salah"}), 400

        # ❌ OTP tidak ada
        if not otp_expired_at:
            return jsonify({"error": "OTP tidak valid"}), 400

        # ❗ HANDLE kalau dari DB jadi string
        if isinstance(otp_expired_at, str):
            otp_expired_at = datetime.datetime.fromisoformat(otp_expired_at)

        # ❌ FIX datetime.utcnow()
        if datetime.datetime.utcnow() > otp_expired_at:
            return jsonify({"error": "OTP sudah kadaluwarsa"}), 400

        # HASH PASSWORD
        hashed_password = generate_password_hash(new_password)

        User.db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "password": hashed_password,
                "otp": None,
                "otp_expired_at": None
            }}
        )

        return jsonify({"message": "Password berhasil direset"}), 200

    except Exception as e:
        print("ERROR reset_password:", str(e))
        return jsonify({"error": str(e)}), 500