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
        nama = data.get("nama")
        phone = normalize_phone(data.get("phone"))
        password = data.get("password")
        nama_suami = data.get("nama_suami")
        phone_suami = normalize_phone(data.get("phone_suami"))

        if not nama or not phone or not password:
            return jsonify({"message": "Data ibu harus lengkap"}), 400

        if User.find_by_phone(phone):
            return jsonify({"message": "Nomor ibu sudah digunakan"}), 400

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(100000, 999999))

        # CREATE IBU
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
        if nama_suami and phone_suami:
            if User.find_by_phone(phone_suami):
                return jsonify({"message": "Nomor suami sudah digunakan"}), 400

            plain_password_suami = generate_random_password()
            
            suami_id = User.insert_user({
                "nama": nama_suami,
                "phone": phone_suami,
                "password": generate_password_hash(plain_password_suami),
                "temp_password": plain_password_suami, # SIMPAN UNTUK DIKIRIM NANTI
                "role": "pendamping",
                "partner_id": str(ibu_id),
                "otp": None,
                "otp_verified": True
            })

            User.update_fields(str(ibu_id), {"partner_id": str(suami_id)})

        # KIRIM WA HANYA KE IBU
        send_whatsapp(
            phone,
f"""Halo Ibu {nama},

🌸 Selamat datang di *PregMate*, aplikasi pendamping kesehatan ibu hamil.

Untuk mengaktifkan akun Anda, silakan gunakan kode OTP berikut:

    🔐 *Kode OTP:* {otp}
    ⏳ *Masa berlaku:* 10 menit

Silakan masukkan kode OTP tersebut pada halaman verifikasi di aplikasi PregMate.

⚠️ Demi keamanan akun, jangan pernah membagikan kode OTP ini kepada siapa pun, termasuk pihak yang mengatasnamakan PregMate.

Terima kasih telah mempercayai PregMate sebagai pendamping perjalanan kehamilan Anda.

Salam hangat,
*Tim PregMate*"""
    )

        return jsonify({
            "message": "Registrasi berhasil",
            "user_id": str(ibu_id),
            "partner_created": suami_id is not None
        }), 201

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
# ================================
# VERIFY OTP
# ================================
def verify_otp():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        otp_input = data.get("otp")

        user = User.find_by_id(user_id)
        if not user or otp_input != user.get("otp"):
            return jsonify({"message": "OTP salah atau user tidak ditemukan"}), 400

        # Update status verifikasi
        User.update_fields(user_id, {
            "otp_verified": True,
            "otp": None,
            "otp_created_at": None
        })

        # --- KIRIM WA KE PENDAMPING JIKA ADA ---
        partner_id = user.get("partner_id")
        if partner_id:
            pendamping = User.find_by_id(partner_id)
            if pendamping:
                plain_pass = pendamping.get("temp_password")
                send_whatsapp(
                    pendamping.get("phone"),
f"""
Halo Bapak {pendamping.get("nama")},

Akun Anda sebagai pendamping di aplikasi PregMate telah berhasil diaktifkan.

Anda kini resmi terhubung untuk mendampingi Ibu {user.get("nama")} dalam memantau perjalanan kesehatan kehamilan.

Berikut adalah detail akses akun Anda:
    Nama        : {pendamping.get("nama")}
    Nomor Login : {pendamping.get("phone")}
    Password    : {plain_pass}

Langkah selanjutnya:
1. Unduh aplikasi PregMate di smartphone Anda.
2. Login menggunakan kredensial di atas.
3. Demi keamanan, mohon segera ubah password setelah login pertama kali.

Terima kasih atas dedikasi Anda dalam mendukung kesehatan kehamilan Ibu {user.get("nama")}.

Salam hangat,
Tim PregMate
    """
    )
                # Opsional: Hapus temp_password setelah dikirim
                # User.update_fields(partner_id, {"temp_password": None})

        token = create_access_token(identity=str(user_id))
        return jsonify({"message": "Berhasil verifikasi", "token": token}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500