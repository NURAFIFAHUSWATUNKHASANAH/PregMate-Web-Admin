from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId

from models.craving_model import Craving


@jwt_required()
def get_cravings():
    user_id = get_jwt_identity()

    data = Craving.find_by_user(user_id)

    result = []
    for item in data:
        result.append({
            "_id": str(item["_id"]),
            "makanan": item.get("makanan", ""),
            "keterangan": item.get("keterangan", ""),
            "status": item["status"],
            "created_at": item["created_at"]
        })

    return jsonify(result), 200


@jwt_required()
def add_craving():
    user_id = get_jwt_identity()
    data = request.get_json()

    craving = {
        "user_id": ObjectId(user_id),
        "makanan": data.get("makanan"),
        "keterangan": data.get("keterangan"),
        "status": "menunggu",
        "created_at": datetime.utcnow()
    }

    Craving.create(craving)

    return jsonify({"message": "berhasil"}), 200


@jwt_required()
def update_craving(id):
    data = request.get_json()

    status = data.get("status")
    if status not in ["menunggu", "dipenuhi", "nanti", "ditolak"]:
        return jsonify({"message": "Status tidak valid"}), 400

    Craving.update_status(id, status)

    return jsonify({"message": "updated"}), 200