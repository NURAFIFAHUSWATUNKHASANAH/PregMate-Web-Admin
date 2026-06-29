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
    
@jadwal_bp.route('/jadwal', methods=['GET'])
def get_jadwal():

    user_id = request.args.get("user_id")

    # cari kehamilan aktif
    kehamilan = db.data_kehamilan.find_one({
        "user_id": ObjectId(user_id),
        "status": "active"
    })

    if not kehamilan:
        return jsonify([])

    kehamilan_id = kehamilan["_id"]

    data = list(
        db.schedules.find({
            "user_id": user_id,
            "kehamilan_id": kehamilan_id
        })
    )

    for d in data:
        d["_id"] = str(d["_id"])
        d["kehamilan_id"] = str(d["kehamilan_id"])

    return jsonify(data)

@jadwal_bp.route('/jadwal/<id>', methods=['PUT'])
def update_jadwal(id):
    try:
        data = request.get_json()

        update_data = {
            "tanggal": data["tanggal"],
            "jam": data["jam"],
            "pesan": data["pesan"],
        }

        db.schedules.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return jsonify({
            "status": "success",
            "message": "Jadwal berhasil diupdate"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@jadwal_bp.route('/jadwal/<id>', methods=['DELETE'])
def delete_jadwal(id):
    try:
        result = db.schedules.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            return jsonify({
                "status": "error",
                "message": "Jadwal tidak ditemukan"
            }), 404

        return jsonify({
            "status": "success",
            "message": "Jadwal berhasil dihapus"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500