from datetime import datetime

class TipsNewbornModel:
    collection = None

    @classmethod
    def set_db(cls, db):
        cls.collection = db["master_tips_newborn"]

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one({
            "title": data["title"],
            "desc": data["desc"],
            "video": data["video"],  # filename
            "steps": data.get("steps", []),
            "created_at": datetime.utcnow()
        })

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def get_by_id(cls, id):
        from bson import ObjectId
        return cls.collection.find_one({"_id": ObjectId(id)})

    @classmethod
    def update(cls, id, data):
        from bson import ObjectId
        return cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "title": data["title"],
                "desc": data["desc"],
                "video": data["video"],
                "steps": data.get("steps", [])
            }}
        )

    @classmethod
    def delete(cls, id):
        from bson import ObjectId
        return cls.collection.delete_one({"_id": ObjectId(id)})