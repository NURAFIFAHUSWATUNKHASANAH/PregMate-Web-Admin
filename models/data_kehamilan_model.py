from bson import ObjectId

class DataKehamilan:

    db = None

    @classmethod
    def set_db(cls, database):
        cls.db = database

    @classmethod
    def create(cls, data):
        return cls.db["data_kehamilan"].insert_one(data)

    @classmethod
    def find_by_user(cls, user_id):
        return cls.db["data_kehamilan"].find_one({
            "user_id": ObjectId(user_id),
            "status": "active"
        })