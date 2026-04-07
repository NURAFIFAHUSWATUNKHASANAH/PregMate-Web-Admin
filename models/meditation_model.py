from bson import ObjectId

class MeditationSession:

    db = None

    @classmethod
    def set_db(cls, database):
        cls.db = database

    @classmethod
    def find_all(cls):
        return list(cls.db["meditation_sessions"].find())

    @classmethod
    def create(cls, data):
        return cls.db["meditation_sessions"].insert_one(data)