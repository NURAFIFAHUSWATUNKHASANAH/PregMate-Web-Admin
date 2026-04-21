from datetime import datetime
from bson import ObjectId

class TasBersalinModel:
    collection = None
    master_collection = None

    @classmethod
    def set_db(cls, db):
        cls.collection = db["tas_bersalin"]              # progress user
        cls.master_collection = db["master_tas_bersalin"] # master data

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

            # 🔥 ambil master (semua item)
            master_items = list(cls.master_collection.find({}))

            # 🔥 ambil progress user
            user_items = list(cls.collection.find({
                "kehamilan_id": k_id
            }))

            result = []

            for m in master_items:
                # cari apakah sudah dicentang user
                match = next(
                    (u for u in user_items if u["name"] == m["name"] and u["category"] == m["category"]),
                    None
                )

                result.append({
                    "name": m["name"],
                    "detail": m.get("detail", ""),
                    "category": m["category"],
                    "isChecked": match["isChecked"] if match else False
                })

            return result

        except Exception as e:
            print(f"❌ Error get_items: {e}")
            return []