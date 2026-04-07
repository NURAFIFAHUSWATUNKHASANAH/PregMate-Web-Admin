# models/histori_model.py
from bson import ObjectId

db = None
histori_collection = None

def set_db(database):
    global db, histori_collection
    db = database
    histori_collection = db["histori"]

def get_histori_by_user(user_id):
    """
    Return list histori untuk user tertentu
    """
    result = []
    cursor = histori_collection.find({"user_id": user_id}).sort("tanggal",-1)
    for h in cursor:
        result.append({
            "_id": str(h["_id"]),
            "user_id": h["user_id"],
            "label": h.get("label",""),
            "accuracy": h.get("accuracy",0),
            "tanggal": h.get("tanggal")
        })
    return result