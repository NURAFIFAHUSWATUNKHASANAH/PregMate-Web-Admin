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

    # ================= SIMPAN / UPDATE =================
    @staticmethod
    def save(user_id, data):
        existing = KalkulatorModel.collection.find_one({
            "user_id": ObjectId(user_id)
        })

        payload = {
            "hpht": data.get("hpht"),
            "hpl": data.get("hpl"),
            "metode": data.get("metode"),
            "total_biaya": float(data.get("total_biaya", 0)),
            "pakai_bpjs": data.get("pakai_bpjs", False),
            "updated_at": datetime.utcnow()
        }

        if existing:
            KalkulatorModel.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": payload}
            )
        else:
            payload["user_id"] = ObjectId(user_id)
            payload["created_at"] = datetime.utcnow()
            KalkulatorModel.collection.insert_one(payload)

    # ================= AMBIL DATA =================
    @staticmethod
    def get(user_id):
        return KalkulatorModel.collection.find_one({
            "user_id": ObjectId(user_id)
        })

    # ================= TABUNG =================
    @staticmethod
    def add_income(user_id, jumlah):
        KalkulatorModel.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$inc": {"total_masuk": jumlah},
                "$push": {
                    "riwayat": {
                        "tipe": "masuk",
                        "jumlah": jumlah,
                        "tanggal": now_wib().strftime("%d-%m-%Y %H:%M")
                    }
                }
            }
        )

    # ================= PENGELUARAN =================
    @staticmethod
    def add_expense(user_id, jumlah, keterangan):
        KalkulatorModel.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$inc": {"total_keluar": jumlah},
                "$push": {
                    "riwayat": {
                        "tipe": "keluar",
                        "jumlah": jumlah,
                        "keterangan": keterangan,  # 🔥 TAMBAHAN
                        "tanggal": now_wib().strftime("%d-%m-%Y %H:%M")
                    }
                }
            }
        )