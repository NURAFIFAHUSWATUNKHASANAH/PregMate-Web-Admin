from datetime import datetime
from bson import ObjectId
import pytz

def now_wib():
    tz = pytz.timezone("Asia/Jakarta")
    return datetime.now(tz)


class KalkulatorModel:
    collection = None

    @staticmethod
    def set_db(db):
        KalkulatorModel.collection = db["kalkulator_bersalin"]

    # ================= SAFE OBJECT ID =================
    @staticmethod
    def to_object_id(value):
        try:
            return ObjectId(value)
        except:
            raise Exception("ID tidak valid")

    # ================= SAVE (SHARED) =================
    @staticmethod
    def save(user_id, data):
        kehamilan_id = data.get("kehamilan_id")

        if not kehamilan_id:
            raise Exception("kehamilan_id wajib")

        kehamilan_obj = KalkulatorModel.to_object_id(kehamilan_id)
        user_obj = KalkulatorModel.to_object_id(user_id)

        # 🔥 hanya berdasarkan kehamilan_id (SHARED)
        existing = KalkulatorModel.collection.find_one({
            "kehamilan_id": kehamilan_obj
        })

        payload = {
            "kehamilan_id": kehamilan_obj,

            # 🔥 optional (si pembuat pertama)
            "owner_id": user_obj,

            "hpht": data.get("hpht"),
            "hpl": data.get("hpl"),
            "metode": data.get("metode"),
            "metode_nabung": data.get("metode_nabung", "bulanan"),
            "total_biaya": float(data.get("total_biaya", 0)),
            "pakai_bpjs": data.get("pakai_bpjs", False),

            "updated_at": datetime.utcnow()
        }

        if existing:
            KalkulatorModel.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": payload}
            )
            return str(existing["_id"])
        else:
            payload["created_at"] = datetime.utcnow()
            payload["total_masuk"] = 0
            payload["total_keluar"] = 0
            payload["riwayat"] = []

            result = KalkulatorModel.collection.insert_one(payload)
            return str(result.inserted_id)

    # ================= GET (SHARED) =================
    @staticmethod
    def get(kehamilan_id):
        if not kehamilan_id:
            return None

        try:
            return KalkulatorModel.collection.find_one({
                "kehamilan_id": ObjectId(kehamilan_id)
            })
        except:
            return None


    # ================= TABUNG =================
    @staticmethod
    def add_income(kehamilan_id, jumlah):

        riwayat = {
            "_id": ObjectId(),  # 🔥 WAJIB
            "tipe": "masuk",
            "jumlah": jumlah,
            "tanggal": now_wib().strftime("%d-%m-%Y %H:%M")
        }

        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {
                "$push": {
                    "riwayat": riwayat
                }
            }
        )

        # 🔥 AUTO RECALCULATE
        KalkulatorModel.recalculate(kehamilan_id)

    # ================= PENGELUARAN =================
    @staticmethod
    def add_expense(kehamilan_id, jumlah, keterangan):

        riwayat = {
            "_id": ObjectId(),  # 🔥 WAJIB
            "tipe": "keluar",
            "jumlah": jumlah,
            "keterangan": keterangan,
            "tanggal": now_wib().strftime("%d-%m-%Y %H:%M")
        }

        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {
                "$push": {
                    "riwayat": riwayat
                }
            }
        )

        # 🔥 AUTO RECALCULATE
        KalkulatorModel.recalculate(kehamilan_id)

# ================= RECALCULATE =================
    @staticmethod
    def recalculate(kehamilan_id):
        data = KalkulatorModel.collection.find_one({
            "kehamilan_id": ObjectId(kehamilan_id)
        })

        if not data:
            return

        total_masuk = 0
        total_keluar = 0

        for item in data.get("riwayat", []):
            if item["tipe"] == "masuk":
                total_masuk += float(item["jumlah"])
            else:
                total_keluar += float(item["jumlah"])

        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {
                "$set": {
                    "total_masuk": total_masuk,
                    "total_keluar": total_keluar
                }
            }
        )

 # ================= EDIT RIWAYAT =================
    @staticmethod
    def edit_riwayat(
        kehamilan_id,
        riwayat_id,
        jumlah,
        keterangan=""
    ):

        data = KalkulatorModel.collection.find_one({
            "kehamilan_id": ObjectId(kehamilan_id)
        })

        if not data:
            raise Exception("Data tidak ditemukan")

        riwayat = data.get("riwayat", [])

        for item in riwayat:
            if str(item["_id"]) == riwayat_id:

                item["jumlah"] = jumlah

                if item["tipe"] == "keluar":
                    item["keterangan"] = keterangan

                item["edited_at"] = now_wib().strftime("%d-%m-%Y %H:%M")

        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {
                "$set": {
                    "riwayat": riwayat
                }
            }
        )

        KalkulatorModel.recalculate(kehamilan_id)

    # ================= DELETE RIWAYAT =================
    @staticmethod
    def delete_riwayat(kehamilan_id, riwayat_id):

        data = KalkulatorModel.collection.find_one({
            "kehamilan_id": ObjectId(kehamilan_id)
        })

        if not data:
            raise Exception("Data tidak ditemukan")

        riwayat = data.get("riwayat", [])

        riwayat_baru = [
            item for item in riwayat
            if str(item["_id"]) != str(riwayat_id)
        ]

        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {"$set": {"riwayat": riwayat_baru}}
        )

        KalkulatorModel.recalculate(kehamilan_id)