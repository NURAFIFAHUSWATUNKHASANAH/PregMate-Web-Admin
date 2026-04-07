from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from datetime import datetime
from models.berat_badan_model import BeratBadan

@jwt_required()
def submit_berat_badan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        berat = data.get("berat_badan")
        tanggal = data.get("tanggal") or datetime.utcnow().strftime("%Y-%m-%d")

        if berat is None:
            return jsonify({"message": "Berat badan wajib diisi"}), 400

        entry = {
            "user_id": ObjectId(user_id),
            "berat_badan": float(berat),
            "tanggal": datetime.strptime(tanggal, "%Y-%m-%d"),
            "created_at": datetime.utcnow()
        }

        BeratBadan.create(entry)
        return jsonify({"message": "Berat badan berhasil ditambahkan"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Terjadi kesalahan"}), 500
    
@jwt_required()
def get_riwayat_berat_badan():
        try:
            user_id = get_jwt_identity()
            data = BeratBadan.find_by_user(user_id)
            result = [
                {"berat_badan": d["berat_badan"], "tanggal": d["tanggal"].strftime("%Y-%m-%d")}
                for d in data
            ]
            return jsonify(result)
        except Exception as e:
            print(e)
            return jsonify({"message": "Terjadi kesalahan"}), 500