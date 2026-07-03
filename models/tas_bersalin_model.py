from datetime import datetime
from bson import ObjectId

class TasBersalinModel:
    collection = None        # Ini akan diarahkan ke user_progress_tas
    master_collection = None # Master data

    @classmethod
    def set_db(cls, db):
        cls.collection = db["user_progress_tas"]      # Sesuai permintaan Anda
        cls.master_collection = db["master_tas_bersalin"]

    # ===================== TOGGLE ITEM =====================
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
                        "created_at": datetime.utcnow(),
                        "is_custom": False # Item toggle bawaan bukan custom
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"❌ Error toggle_item: {e}")
            return None

# ===================== ADD CUSTOM ITEM (DIPERBARUI) =====================
    @classmethod
    def add_custom_item(cls, user_id, kehamilan_id, name, category, type, detail=""):
        try:
            return cls.collection.insert_one({
                "kehamilan_id": ObjectId(kehamilan_id),
                "name": name,
                "category": category,
                "type": type,
                "detail": detail,  # <-- SEKARANG MENYIMPAN FIELD DETAIL
                "isChecked": False,
                "is_custom": True, 
                "created_at": datetime.utcnow()
            })
        except Exception as e:
            print(f"❌ Error add_custom_item: {e}")
            return None

    # ===================== UPDATE CUSTOM ITEM (FITUR BARU) =====================
    @classmethod
    def update_custom_item(cls, item_id, name, category, type, detail):
        try:
            return cls.collection.update_one(
                {"_id": ObjectId(item_id)},
                {
                    "$set": {
                        "name": name,
                        "category": category,
                        "type": type,
                        "detail": detail,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"❌ Error update_custom_item: {e}")
            return None

    # ===================== DELETE CUSTOM ITEM =====================
    @classmethod
    def delete_custom_item(cls, item_id):
        try:
            return cls.collection.delete_one({"_id": ObjectId(item_id)})
        except Exception as e:
            print(f"❌ Error delete_custom_item: {e}")
            return None

    # ===================== HIDE ITEM =====================
    @classmethod
    def hide_item(cls, kehamilan_id, name):
        return cls.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id), "name": name},
            {"$set": {"is_hidden": True}},
            upsert=True
        )

    # ===================== GET ITEMS (Master + User Progress) =====================
    @classmethod
    def get_items(cls, user_id, kehamilan_id):
        try:
            k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id

            master_items = list(cls.master_collection.find({"is_hidden": {"$ne": True}}))
            user_items = list(cls.collection.find({"kehamilan_id": k_id, "is_hidden": {"$ne": True}}))

            result = []

            # 1. Olah Master Items
            for m in master_items:
                match = next((u for u in user_items if u["name"] == m["name"] and u["category"] == m["category"]), None)
                result.append({
                    "id": str(match["_id"]) if match else str(m["_id"]),
                    "name": m["name"],
                    "detail": m.get("detail", ""),
                    "category": m["category"],
                    "type": m.get("type", "Disarankan"),
                    "isChecked": match["isChecked"] if match else False,
                    "isCustom": False
                })

            # 2. Olah User Custom Items
            for u in user_items:
                if u.get("is_custom") == True:
                    result.append({
                        "id": str(u["_id"]),
                        "name": u["name"],
                        "detail": u.get("detail", ""),
                        "category": u["category"],
                        "type": u.get("type", "Pribadi"),
                        "isChecked": u.get("isChecked", False),
                        "isCustom": True
                    })

            return result

        except Exception as e:
            print(f"❌ Error get_items: {e}")
            return []
        
# ===================== HIDE ITEM FOR SPECIFIC USER =====================
    @classmethod
    def hide_item_for_user(cls, kehamilan_id, name, category):
        try:
            # Lakukan upsert: jika data progress belum ada, buat baru dengan status is_hidden=True
            return cls.collection.update_one(
                {
                    "kehamilan_id": kehamilan_id,
                    "category": category,
                    "name": name
                },
                {
                    "$set": {
                        "is_hidden": True,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"❌ Error hide_item_for_user: {e}")
            return None