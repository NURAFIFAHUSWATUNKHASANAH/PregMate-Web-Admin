from bson import ObjectId

class UkuranJaninModel:
    collection = None

    @classmethod
    def set_db(cls, db):
        cls.collection = db["ukuran_janin"]

    @classmethod
    def get_all(cls, search_query=None):
        query = {}
        if search_query:
            # Bisa mencari angka minggu atau nama buah secara case-insensitive
            query = {
                "$or": [
                    {"minggu": {"$regex": str(search_query), "$options": "i"}},
                    {"buah": {"$regex": search_query, "$options": "i"}}
                ]
            }
        # Mengurutkan berdasarkan minggu secara ascending (1)
        return list(cls.collection.find(query).sort("minggu", 1))

    @classmethod
    def get_by_id(cls, item_id):
        return cls.collection.find_one({"_id": ObjectId(item_id)})

    @classmethod
    def insert(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, item_id, data):
        return cls.collection.update_one({"_id": ObjectId(item_id)}, {"$set": data})

    @classmethod
    def delete(cls, item_id):
        return cls.collection.delete_one({"_id": ObjectId(item_id)})