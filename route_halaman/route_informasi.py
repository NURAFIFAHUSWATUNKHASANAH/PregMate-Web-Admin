from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

informasi_bp = Blueprint("informasi_bp", __name__)

db = None
informasi_collection = None
users_collection = None


def set_db(database):
    global db, informasi_collection, users_collection
    db = database
    informasi_collection = db["informasi"]
    users_collection = db["users"]


@informasi_bp.route("/informasi", methods=["GET"])
@jwt_required()
def get_informasi():

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User tidak ditemukan"
        }), 404

    role = user.get("role")

    # =========================
    # JIKA ROLE IBU
    # =========================
    if role == "ibu":

        data = list(
            informasi_collection.find({
                "user_id": user_id
            }).sort("tanggal", -1)
        )

    # =========================
    # JIKA ROLE PENDAMPING
    # =========================
    elif role == "pendamping":

        partner_id = user.get("partner_id")

        data = list(
            informasi_collection.find({
                "user_id": partner_id
            }).sort("tanggal", -1)
        )

    else:
        data = []

    return jsonify({
        "status": "success",
        "data": data
    })