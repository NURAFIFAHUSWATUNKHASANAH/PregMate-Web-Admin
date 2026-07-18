from bson import ObjectId


class KategoriModel():
    collection=None

    @classmethod
    def set_db(cls,db):
        cls.collection=db["kategori"]

    @classmethod
    def get_all(cls):
        return list (cls.collection.find())
    
    @classmethod
    def get_by_id(cls,id):
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def create(cls,data):
        return cls.collection_create_one(data)
    
    @classmethod
    def edit(cls,data,id):
        return cls.collection.edit_one({"_id": ObjectId(id)}, {"$set": data})
    
    @classmethod
    def delete(cls,id):
        return cls.collection.delete_one({"_id": ObjectId(id)})