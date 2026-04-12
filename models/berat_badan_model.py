from bson import ObjectId
from datetime import datetime

class BeratBadan:
    db = None

    @classmethod
    def set_db(cls, database):
        cls.db = database

    @classmethod
    def create(cls, data):
        return cls.db["berat_badan"].insert_one(data)

    @classmethod
    def find_by_user(cls, user_id, kehamilan_id):
        return list(cls.db["berat_badan"].find({
            "user_id": ObjectId(user_id),
            "kehamilan_id": ObjectId(kehamilan_id)
        }).sort("tanggal", 1))

    @classmethod
    def update(cls, id, data, user_id, kehamilan_id):
        return cls.db["berat_badan"].update_one(
            {
                "_id": ObjectId(id),
                "user_id": ObjectId(user_id),
                "kehamilan_id": ObjectId(kehamilan_id)  # ✅ TAMBAH
            },
            {"$set": data}
        )

    @classmethod
    def delete(cls, id, user_id, kehamilan_id):
        return cls.db["berat_badan"].delete_one(
            {
                "_id": ObjectId(id),
                "user_id": ObjectId(user_id),
                "kehamilan_id": ObjectId(kehamilan_id)  # ✅ TAMBAH
            }
        )