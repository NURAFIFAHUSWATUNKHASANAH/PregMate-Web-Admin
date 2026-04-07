from datetime import datetime
from bson import ObjectId

class Craving:
    db = None
    collection = None  # 🔥 WAJIB ADA

    @staticmethod
    def set_db(db):
        Craving.db = db
        Craving.collection = db["cravings"]  # 🔥 set collection di sini

    @staticmethod
    def create(data):
        return Craving.collection.insert_one(data)

    @staticmethod
    def find_by_user(user_id):
        return list(Craving.collection.find({"user_id": ObjectId(user_id)}))

    @staticmethod
    def update_status(id, status):
        return Craving.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"status": status}}
        )