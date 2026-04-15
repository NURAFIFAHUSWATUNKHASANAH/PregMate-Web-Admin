from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.tas_bersalin_model import TasBersalinModel

# ===================== TOGGLE =====================
@jwt_required()
def toggle_tas_bersalin():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Body request kosong"}), 422

    kehamilan_id = data.get("kehamilan_id")
    category = data.get("category")
    name = data.get("name")

    if not all([kehamilan_id, category, name]):
        return jsonify({"msg": "Data tidak lengkap"}), 422

    result = TasBersalinModel.toggle_item(
        user_id=user_id,
        kehamilan_id=kehamilan_id,
        category=category,
        name=name,
        detail=data.get("detail", ""),
        is_checked=data.get("isChecked", False)
    )

    if result:
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 500


# ===================== GET =====================
@jwt_required()
def get_tas_bersalin():
    user_id = get_jwt_identity()
    kehamilan_id = request.args.get("kehamilan_id")

    if not kehamilan_id or kehamilan_id == "null":
        return jsonify({"msg": "kehamilan_id tidak valid"}), 422

    data = TasBersalinModel.get_items(user_id, kehamilan_id)

    return jsonify({
        "status": "success",
        "data": [
            {
                "name": x.get("name"),
                "detail": x.get("detail", ""),
                "category": x.get("category"),
                "isChecked": x.get("isChecked", False)
            }
            for x in data
        ]
    }), 200