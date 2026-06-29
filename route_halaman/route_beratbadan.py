from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from models.berat_badan_model import BeratBadan
from models.data_kehamilan_model import DataKehamilan
from models.datauser_model import User

# Blueprint
berat_badan_bp = Blueprint("berat_badan_bp", __name__)

# Set DB jika perlu dari app.py
def set_db(database):
    BeratBadan.set_db(database)
    DataKehamilan.set_db(database)

# ======================
# HELPER HITUNG MINGGU
# ======================
def get_minggu_kehamilan(tanggal, hpht):
    selisih = (tanggal - hpht).days
    return (selisih // 7) + 1

# ======================
# SUBMIT BERAT BADAN (FIX)
# ======================
@berat_badan_bp.route("", methods=["POST"])
@jwt_required()
def submit_berat_badan_route():
    try:
        user_id = str(get_jwt_identity())
        data = request.get_json()

        berat = data.get("berat_badan")
        tanggal_str = data.get("tanggal")

        # ======================
        # VALIDASI INPUT
        # ======================
        if berat is None:
            return jsonify({"message": "Berat badan wajib diisi"}), 400

        if not tanggal_str:
            return jsonify({"message": "Tanggal wajib diisi"}), 400

        tanggal = datetime.strptime(tanggal_str, "%Y-%m-%d")

        # ======================
        # HANDLE ROLE (PENDAMPING)
        # ======================
        try:
            user = User.find_by_id(user_id)
        except:
            user = None

        target_user_id = user_id

        if isinstance(user, dict) and user.get("role") == "pendamping":
            if user.get("partner_id"):
                target_user_id = str(user["partner_id"])

        # ======================
        # AMBIL DATA KEHAMILAN
        # ======================
        kehamilan = DataKehamilan.find_by_user(target_user_id)

        if not kehamilan:
            return jsonify({"message": "Data kehamilan belum ada"}), 400

        kehamilan_id = kehamilan.get("_id")

        hpht = datetime.strptime(kehamilan["hpht"], "%Y-%m-%d")

        minggu_input = get_minggu_kehamilan(tanggal, hpht)

        # ======================
        # CEK DUPLIKAT MINGGU
        # ======================
        bb_list = BeratBadan.find_by_user(target_user_id, kehamilan_id) or []

        for item in bb_list:
            tgl = item.get("tanggal")

            if not isinstance(tgl, datetime):
                continue

            minggu = get_minggu_kehamilan(tgl, hpht)

            if minggu == minggu_input:
                return jsonify({
                    "message": f"Minggu ke-{minggu_input} sudah diinput",
                    "minggu": minggu_input,
                    "error_code": "DUPLICATE_WEEK"
                }), 400

        # ======================
        # INSERT DATA
        # ======================
        entry = {
            "user_id": ObjectId(target_user_id),
            "kehamilan_id": ObjectId(kehamilan_id),
            "berat_badan": float(berat),
            "tanggal": tanggal,
            "created_at": datetime.utcnow()
        }

        BeratBadan.create(entry)

        return jsonify({
            "message": "Berhasil ditambahkan",
            "minggu": minggu_input
        }), 200

    except Exception as e:
        print("POST ERROR:", e)
        return jsonify({"message": "Terjadi kesalahan"}), 500
    
@berat_badan_bp.route("", methods=["GET"])
@jwt_required()
def get_riwayat_berat_badan_route():
    try:
        user_id = str(get_jwt_identity())

        try:
            user = User.find_by_id(user_id)
        except:
            user = None

        target_user_id = user_id

        if isinstance(user, dict) and user.get("role") == "pendamping":
            if user.get("partner_id"):
                target_user_id = str(user["partner_id"])

        kehamilan = DataKehamilan.find_by_user(target_user_id)

        if not kehamilan:
            return jsonify([])

        hpht = datetime.strptime(
            kehamilan["hpht"],
            "%Y-%m-%d"
        )

        kehamilan_id = kehamilan["_id"]

        bb_list = BeratBadan.find_by_user(
            target_user_id,
            kehamilan_id
        )

        minggu_map = {}

        for d in bb_list:

            if not isinstance(d, dict):
                continue

            tgl = d.get("tanggal")

            if not isinstance(tgl, datetime):
                continue

            minggu = get_minggu_kehamilan(
                tgl,
                hpht
            )

            if minggu in minggu_map:
                continue

            minggu_map[minggu] = {
                "_id": str(d["_id"]),
                "berat_badan": float(d["berat_badan"]),
                "tanggal": tgl.strftime("%Y-%m-%d")
            }

        result = sorted(
            minggu_map.values(),
            key=lambda x: datetime.strptime(
                x["tanggal"],
                "%Y-%m-%d"
            )
        )

        return jsonify(result)

    except Exception as e:
        print("GET ERROR:", e)
        return jsonify([]), 200
    
# ======================
# UPDATE
# ======================
@berat_badan_bp.route("/<id>", methods=["PUT"])
@jwt_required()
def update_berat_badan(id):
    try:
        user_id = str(get_jwt_identity())
        data = request.get_json()

        berat = data.get("berat_badan")
        tanggal = data.get("tanggal")

        if not berat:
            return jsonify({"message": "Berat wajib diisi"}), 400

        # ambil kehamilan
        kehamilan = DataKehamilan.find_by_user(user_id)
        if not kehamilan:
            return jsonify({"message": "Data kehamilan tidak ditemukan"}), 400

        kehamilan_id = kehamilan.get("_id")

        update_data = {
            "berat_badan": float(berat)
        }

        if tanggal:
            try:
                update_data["tanggal"] = datetime.strptime(tanggal, "%Y-%m-%d")
            except:
                update_data["tanggal"] = datetime.utcnow()

        result = BeratBadan.update(
            id=id,
            data=update_data,
            user_id=user_id,
            kehamilan_id=kehamilan_id
        )

        if result.matched_count == 0:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        return jsonify({"message": "Berhasil diupdate"}), 200

    except Exception as e:
        print("UPDATE ERROR:", e)
        return jsonify({"message": "Error update"}), 500
    
# ======================
# DELETE
# ======================
@berat_badan_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_berat_badan(id):
    try:
        user_id = str(get_jwt_identity())

        kehamilan = DataKehamilan.find_by_user(user_id)
        if not kehamilan:
            return jsonify({"message": "Data kehamilan tidak ditemukan"}), 400

        kehamilan_id = kehamilan.get("_id")

        result = BeratBadan.delete(
            id=id,
            user_id=user_id,
            kehamilan_id=kehamilan_id
        )

        if result.deleted_count == 0:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        return jsonify({"message": "Berhasil dihapus"}), 200

    except Exception as e:
        print("DELETE ERROR:", e)
        return jsonify({"message": "Error delete"}), 500