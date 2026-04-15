from datetime import datetime
from bson import ObjectId

class TasBersalinModel:
    collection = None

    @classmethod
    def set_db(cls, db):
        cls.collection = db["tas_bersalin"]

    # ===================== TOGGLE ITEM (SHARED DATA) =====================
    @classmethod
    def toggle_item(cls, user_id, kehamilan_id, category, name, detail, is_checked):
        try:
            u_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id

            return cls.collection.update_one(
                {
                    "kehamilan_id": k_id,
                    "category": category,
                    "name": name
                },
                {
                    "$set": {
                        "detail": detail,
                        "isChecked": is_checked,
                        "updated_by": u_id,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            print(f"❌ Error toggle_item: {e}")
            return None

    # ===================== GET ITEMS (SHARED) =====================
    @classmethod
    def get_items(cls, user_id, kehamilan_id):
        try:
            k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id

            return list(cls.collection.find({
                "kehamilan_id": k_id
            }))

        except Exception as e:
            print(f"❌ Error get_items: {e}")
            return []