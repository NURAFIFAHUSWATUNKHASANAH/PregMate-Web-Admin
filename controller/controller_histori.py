# controller/controller_histori.py
from flask import request, jsonify
from bson import ObjectId
from datetime import datetime

db = None
histori_collection = None
users_collection = None

def set_db(database):
    global db, histori_collection, users_collection
    db = database
    histori_collection = db["histori"]
    users_collection = db["users"]

def get_histori(user_id):
    """
    Ambil histori senam yoga.
    Jika user role = pendamping, ambil histori pasangan (partner_id)
    """
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"status":"error","message":"User tidak ditemukan"}), 404

    if user.get("role") == "pendamping":
        partner_id = user.get("partner_id")
        if not partner_id:
            return jsonify({"status":"error","message":"Belum ada pasangan"}), 400
        user_id_to_query = partner_id
    else:
        user_id_to_query = user_id

    histori_cursor = histori_collection.find({"user_id": user_id_to_query}).sort("tanggal", -1)
    histori_list = []
    for h in histori_cursor:
        histori_list.append({
        "_id": str(h["_id"]),
        "user_id": h["user_id"],
        "label": h.get("label",""),
        "accuracy": h.get("accuracy",0),
        "tanggal": h.get("tanggal", datetime.utcnow()).isoformat()  # <- ISO 8601 string
    })

    return jsonify({
        "status": "success",
        "data": histori_list
    })

def get_histori_by_user(user_id):
    """
    Ambil histori untuk user tertentu (list)
    """
    result = []
    cursor = histori_collection.find({"user_id": user_id}).sort("tanggal",-1)
    for h in cursor:
        result.append({
            "_id": str(h["_id"]),
            "user_id": h["user_id"],
            "label": h.get("label",""),
            "accuracy": h.get("accuracy",0),
            "tanggal": h.get("tanggal").isoformat() if h.get("tanggal") else None
        })
    return result

def save_histori(data):
    """
    Simpan histori latihan baru ke DB
    """
    user_id = data.get("user_id")
    label = data.get("label", "")
    accuracy = data.get("accuracy", 0)
    tanggal_str = data.get("tanggal")

    if not user_id or not label or accuracy is None or not tanggal_str:
        return {"status": "error", "message": "Data tidak lengkap"}, 400

    try:
        # Konversi tanggal dari string ISO8601 ke datetime
        tanggal = datetime.fromisoformat(tanggal_str)
    except Exception:
        tanggal = datetime.utcnow()

    histori_doc = {
        "user_id": user_id,
        "label": label,
        "accuracy": accuracy,
        "tanggal": tanggal
    }

    try:
        histori_collection.insert_one(histori_doc)
        return {"status": "success", "message": "Histori tersimpan"}, 201
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500