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
        user_id = data.get("user_id")
        # Ambil kehamilan_id dari Flutter
        kehamilan_id = data.get("kehamilan_id") 

        # 1. Simpan ke koleksi schedules
        jadwal_data = {
            "user_id": user_id,
            "kehamilan_id": ObjectId(kehamilan_id) if kehamilan_id else None,
            "tanggal": data["tanggal"],
            "jam": data["jam"],
            "pesan": data["pesan"],
            "dikirim": False,
            "created_at": datetime.utcnow()
        }
        db.schedules.insert_one(jadwal_data)

        # 2. Format pesan
        isi_pesan = f"Bunda membuat jadwal: {data['pesan']} ({data['tanggal']} {data['jam']})"

        # 3. Simpan ke histori informasi (Supaya muncul di list notifikasi aplikasi)
        db.informasi.insert_one({
            "user_id": str(user_id),
            "kehamilan_id": ObjectId(kehamilan_id) if kehamilan_id else None,
            "tipe": "jadwal",
            "pesan": isi_pesan,
            "tanggal": datetime.utcnow()
        })

        # 4. Kirim Notif ke Pendamping
        try:
            kirim_notif_jadwal(user_id, isi_pesan, kehamilan_id)
        except Exception as e:
            print(f"⚠️ Gagal kirim FCM: {e}")

        return jsonify({"status": "success", "message": "Jadwal berhasil disimpan"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500