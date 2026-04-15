from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from controller.notification_controller import kirim_notif_jadwal


jadwal_bp = Blueprint('jadwal', __name__)
db = None

def set_db(database):
    global db
    db = database

@jadwal_bp.route('/jadwal', methods=['POST'])
def buat_jadwal():
    try:
        data = request.get_json()
        required_fields = ("user_id", "tanggal", "jam", "pesan", "fcmToken")
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Data tidak lengkap"}), 400

        user_id = data["user_id"]
        fcm_token = data["fcmToken"]

        # 1. Update Token User (Ibu)
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"fcmToken": fcm_token}}
        )

        # 2. Simpan Jadwal ke DB
        jadwal_data = {
            "user_id": user_id,
            "tanggal": data["tanggal"],
            "jam": data["jam"],
            "pesan": data["pesan"],
            "dikirim": data.get("dikirim", False),
            "created_at": datetime.utcnow()
        }
        db.schedules.insert_one(jadwal_data)

        # 3. Kirim Notif dengan Judul yang Benar
        pesan_notif = f"Bunda membuat jadwal: {data['pesan']} ({data['tanggal']} {data['jam']})"
        
        try:
            # Pakai fungsi khusus jadwal
            kirim_notif_jadwal(user_id, pesan_notif) 
            print(f"✅ Notif jadwal terkirim")
        except Exception as e_notif:
            print(f"⚠️ Gagal kirim notif: {e_notif}")

        return jsonify({"message": "Jadwal berhasil disimpan"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500