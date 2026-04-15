from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from controller.notification_controller import kirim_notif_mood # Import fungsi notif


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
            {"$set": {"fcmToken": fcm_token}} # Gunakan fcmToken agar konsisten
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

        # 3. 🔥 TAMBAHKAN INI: Kirim Notif ke Pendamping
        # Kita gunakan format pesan untuk memberitahu pendamping
        pesan_untuk_pendamping = (
            f"Bunda membuat jadwal baru: {data['pesan']} "
            f"pada tanggal {data['tanggal']} jam {data['jam']} 🗓️"
        )
        
        # Panggil fungsi notif (pastikan fungsi ini sudah di-import)
        try:
            kirim_notif_mood(user_id, pesan_untuk_pendamping)
            print(f"✅ Notif jadwal berhasil dipicu untuk user: {user_id}")
        except Exception as e_notif:
            print(f"⚠️ Jadwal tersimpan, tapi notif gagal: {e_notif}")

        return jsonify({"message": "Jadwal berhasil disimpan dan notifikasi terkirim"}), 201

    except Exception as e:
        print(f"❌ Error memproses jadwal: {e}")
        return jsonify({"error": str(e)}), 500