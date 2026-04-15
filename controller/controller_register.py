import random
import string
import datetime
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from models.datauser_model import User
from utils.mailer import send_email, send_whatsapp
from dateutil import parser
import random
import string
import datetime
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from models.datauser_model import User
from utils.mailer import send_whatsapp


# ================================
# SET DB
# ================================
def set_db(database):
    global db
    db = database
    User.set_db(database)


# ================================
# NORMALIZE PHONE
# ================================
def normalize_phone(phone):
    if phone and phone.startswith("08"):
        return "62" + phone[1:]
    return phone


# ================================
# GENERATE PASSWORD SUAMI
# ================================
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def register_user():
    try:
        data = request.get_json()

        # ================= IBU =================
        nama = data.get("nama")
        phone = normalize_phone(data.get("phone"))
        password = data.get("password")

        # ================= SUAMI =================
        nama_suami = data.get("nama_suami")
        phone_suami = normalize_phone(data.get("phone_suami"))

        # VALIDASI
        if not nama or not phone or not password:
            return jsonify({"message": "Data ibu harus lengkap"}), 400

        if len(password) < 6:
            return jsonify({"message": "Password minimal 6 karakter"}), 400

        # CEK DUPLIKAT IBU
        if User.find_by_phone(phone):
            return jsonify({"message": "Nomor ibu sudah digunakan"}), 400

        # HASH PASSWORD IBU
        hashed_password = generate_password_hash(password)

        # OTP
        otp = str(random.randint(100000, 999999))

        # ================= CREATE IBU =================
        ibu_id = User.insert_user({
            "nama": nama,
            "phone": phone,
            "password": hashed_password,
            "role": "ibu",
            "partner_id": None,
            "otp": otp,
            "otp_verified": False,
            "otp_created_at": datetime.datetime.utcnow().isoformat()
        })

        suami_id = None

        # ================= CREATE SUAMI =================
        if nama_suami and phone_suami:

            if User.find_by_phone(phone_suami):
                return jsonify({"message": "Nomor suami sudah digunakan"}), 400

            plain_password_suami = generate_random_password()

            suami_id = User.insert_user({
                "nama": nama_suami,
                "phone": phone_suami,
                "password": generate_password_hash(plain_password_suami),
                "role": "pendamping",
                "partner_id": str(ibu_id),
                "otp": None,
                "otp_verified": True
            })

            # link ibu ↔ suami
            User.update_fields(str(ibu_id), {
                "partner_id": str(suami_id)
            })

            # ================= WA SUAMI (PROFESSIONAL) =================
            send_whatsapp(
                phone_suami,
f"""
Halo Bapak {nama_suami},

Akun Anda sebagai pendamping di aplikasi PregMate telah berhasil dibuat.

Anda akan mendampingi Ibu {nama} dalam perjalanan kesehatan kehamilan.

Berikut detail akun Anda:
Nama        : {nama_suami}
Nomor Login : {phone_suami}
Password    : {plain_password_suami}

Langkah selanjutnya:
1. Unduh aplikasi PregMate di smartphone Anda.
2. Login menggunakan nomor dan password di atas.
3. Demi keamanan, segera ubah password setelah login pertama kali.

Terima kasih telah menjadi pendamping dalam perjalanan kesehatan Ibu {nama}.

Salam hangat,
Tim PregMate
"""
            )

        # ================= WA IBU (OTP PROFESSIONAL) =================
        send_whatsapp(
            phone,
f"""
Halo Ibu {nama},

Selamat datang di PregMate, aplikasi pendamping kesehatan ibu hamil.

Untuk mengaktifkan akun Anda, silakan gunakan kode OTP berikut:

Kode OTP : {otp}
Berlaku  : 10 menit

Cara verifikasi:
Masukkan kode OTP tersebut pada aplikasi PregMate.

Demi keamanan akun Anda, jangan pernah membagikan kode ini kepada siapapun.

Terima kasih telah mempercayai PregMate sebagai pendamping kehamilan Anda.

Salam hangat,
Tim PregMate
"""
        )

        return jsonify({
            "message": "Registrasi berhasil",
            "user_id": str(ibu_id),
            "partner_created": suami_id is not None
        }), 201

    except Exception as e:
        print("ERROR REGISTER:", e)
        return jsonify({"message": str(e)}), 500
# ================================
# VERIFY OTP
# ================================

def verify_otp():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        otp_input = data.get("otp")

        if not user_id or not otp_input:
            return jsonify({"message": "Data tidak lengkap"}), 400

        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"message": "User tidak ditemukan"}), 404

        if user.get("otp_verified"):
            return jsonify({"message": "Sudah diverifikasi"}), 400

        otp_created = parser.isoparse(user.get("otp_created_at"))

        if (datetime.datetime.utcnow() - otp_created).total_seconds() > 600:
            return jsonify({"message": "OTP kadaluarsa"}), 400

        if otp_input != user.get("otp"):
            return jsonify({"message": "OTP salah"}), 400

        # update
        User.update_fields(user_id, {
            "otp_verified": True,
            "otp": None,
            "otp_created_at": None
        })

        token = create_access_token(identity=str(user_id))

        return jsonify({
            "message": "Berhasil verifikasi",
            "token": token
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 500