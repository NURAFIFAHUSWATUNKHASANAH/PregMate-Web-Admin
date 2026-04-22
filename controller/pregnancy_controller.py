from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bson import ObjectId

from models.datauser_model import User
from models.data_kehamilan_model import DataKehamilan
from models.kalkulator_model import KalkulatorModel

def format_ddmmyyyy(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d-%m-%Y")
    except:
        return date_str

def hitung_hpl(hpht):
    hpht_date = datetime.strptime(hpht, "%Y-%m-%d")
    hpl = hpht_date + timedelta(days=280)
    return hpl.strftime("%Y-%m-%d")


def hitung_usia_kehamilan(hpht):
    hpht_date = datetime.strptime(hpht, "%Y-%m-%d")
    today = datetime.today()

    selisih = today - hpht_date
    minggu = selisih.days // 7
    hari = selisih.days % 7

    return minggu, hari


def hitung_trimester(minggu):

    if minggu <= 12:
        return 1
    elif minggu <= 27:
        return 2
    else:
        return 3


# ===============================
# DATA PERKEMBANGAN JANIN
# ===============================

perkembangan_janin = {

    8: {
        "ukuran": "sebesar raspberry",
        "perkembangan": "organ vital mulai terbentuk",
        "tips": "konsumsi asam folat dan cukup istirahat"
    },

    12: {
        "ukuran": "sebesar jeruk nipis",
        "perkembangan": "detak jantung sudah bisa didengar",
        "tips": "mulai olahraga ringan seperti jalan kaki"
    },

    18: {
        "ukuran": "sebesar alpukat",
        "perkembangan": "janin mulai bisa mendengar suara",
        "tips": "ajak bayi berbicara untuk stimulasi"
    },

    24: {
        "ukuran": "sebesar jagung",
        "perkembangan": "paru-paru mulai berkembang",
        "tips": "perbanyak minum air dan makan sayur"
    },

    30: {
        "ukuran": "sebesar kubis",
        "perkembangan": "otak bayi berkembang pesat",
        "tips": "konsumsi protein dan omega 3"
    },

    36: {
        "ukuran": "sebesar pepaya",
        "perkembangan": "bayi mulai masuk posisi lahir",
        "tips": "persiapkan persalinan"
    }

}


# ===============================
# SIMPAN DATA KEHAMILAN
# ===============================

@jwt_required()
def submit_validasi_kehamilan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        hpht = data.get("hpht")
        tinggi_badan = data.get("tinggi_badan")
        berat_badan = data.get("berat_badan")

        if not hpht:
            return jsonify({"message": "HPHT wajib diisi"}), 400

        # 🔥 Cek apakah masih ada kehamilan aktif
        existing = DataKehamilan.db["data_kehamilan"].find_one({
            "user_id": ObjectId(user_id),
            "status": "active"
        })

        if existing:
            return jsonify({"message": "Masih ada kehamilan aktif"}), 400

        # 🔥 Tentukan index kehamilan
        last = DataKehamilan.db["data_kehamilan"].find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("kehamilan_ke", -1)]
        )

        kehamilan_ke = 1 if not last else last["kehamilan_ke"] + 1

        hpl = hitung_hpl(hpht)

        data_kehamilan = {
            "user_id": ObjectId(user_id),
            "kehamilan_ke": kehamilan_ke,
            "hpht": hpht,
            "hpl": hpl,
            "tinggi_badan": tinggi_badan,
            "berat_badan": berat_badan,
            "status": "active",
            "start_date": datetime.utcnow()
        }

        DataKehamilan.create(data_kehamilan)

        User.update_fields(user_id, {"is_validated": True})

        return jsonify({
            "message": "Data kehamilan berhasil disimpan",
            "kehamilan_ke": kehamilan_ke,
            "hpl": hpl
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Terjadi kesalahan"}), 500

# ===============================
# DASHBOARD KEHAMILAN
# ===============================

@jwt_required()
def dashboard_kehamilan():

    try:

        user_id = get_jwt_identity()

        data = DataKehamilan.db["data_kehamilan"].find_one({
    "user_id": ObjectId(user_id),
    "status": "active"
})

        if not data:

            return jsonify({
                "message": "Data kehamilan belum tersedia"
            }), 404

        hpht = data["hpht"]

        minggu, hari = hitung_usia_kehamilan(hpht)

        trimester = hitung_trimester(minggu)

        perkembangan = perkembangan_janin.get(
            minggu,
            {
                "ukuran": "belum tersedia",
                "perkembangan": "data belum tersedia",
                "tips": "tetap jaga kesehatan ibu"
            }
        )

        return jsonify({
            "kehamilan_id": str(data["_id"]),
            "usia_kehamilan_minggu": minggu,
            "usia_kehamilan_hari": hari,
            "trimester": trimester,
            "hpl": format_ddmmyyyy(data.get("hpl")),
            
            "hpht": data.get("hpht"),
            "tinggi_badan": data.get("tinggi_badan"),
            "berat_badan": data.get("berat_badan"),

            "ukuran_janin": perkembangan["ukuran"],
            "perkembangan_janin": perkembangan["perkembangan"],
            "tips_kesehatan": perkembangan["tips"],
            "status": data.get("status", "active")

        })

    except Exception as e:

        print(e)

        return jsonify({
            "message": "Terjadi kesalahan"
        }), 500
    
@jwt_required()
def pregnancy_history():
    try:
        user_id = get_jwt_identity()

        # 🔥 AMBIL DATA USER
        user = User.find_by_id(user_id)

        if not user:
            return jsonify({
                "status": "error",
                "message": "User tidak ditemukan"
            }), 404

        # 🔥 CEK ROLE
        if user.get("role") == "pendamping":
            pasangan_id = user.get("partner_id")

            if not pasangan_id:
                return jsonify({
                    "status": "error",
                    "message": "Belum ada pasangan"
                }), 400

            user_id_to_query = pasangan_id
        else:
            user_id_to_query = user_id

        # 🔥 QUERY DATA KEHAMILAN (SUDAH FIX)
        data = list(
            DataKehamilan.db["data_kehamilan"]
            .find({"user_id": ObjectId(user_id_to_query)})
            .sort("kehamilan_ke", -1)
        )

        result = []

        for d in data:
            result.append({
                "id": str(d["_id"]),
                "kehamilan_ke": d.get("kehamilan_ke", 0),
                "hpht": d.get("hpht"),
                "hpl": format_ddmmyyyy(d.get("hpl")),
                "status": d.get("status", "active"),
                "start_date": d.get("start_date").isoformat() if d.get("start_date") else None,
                "end_date": d.get("end_date").isoformat() if d.get("end_date") else None,
            })

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:
        print("Error pregnancy history:", e)
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil data"
        }), 500
    
@jwt_required()
def dashboard_kehamilan_pasangan():
    try:
        user_id = get_jwt_identity()

        # 🔥 Ambil data user pendamping
        user = User.find_by_id(user_id)

        if not user:
            return jsonify({
                "message": "User tidak ditemukan"
            }), 404

        pasangan_id = user.get("partner_id")

        if not pasangan_id:
            return jsonify({
                "message": "Pasangan belum terhubung"
            }), 404

        # 🔥 Ambil kehamilan aktif pasangan (PASTIKAN ACTIVE)
        data = DataKehamilan.db["data_kehamilan"].find_one({
            "user_id": ObjectId(pasangan_id),
            "status": "active"
        })

        if not data:
            return jsonify({
                "message": "Data kehamilan belum tersedia"
            }), 404

        hpht = data.get("hpht")

        if not hpht:
            return jsonify({
                "message": "HPHT tidak tersedia"
            }), 400

        # 🔥 HITUNG
        minggu, hari = hitung_usia_kehamilan(hpht)
        trimester = hitung_trimester(minggu)

        perkembangan = perkembangan_janin.get(
            minggu,
            {
                "ukuran": "belum tersedia",
                "perkembangan": "data belum tersedia",
                "tips": "tetap jaga kesehatan ibu"
            }
        )

        # 🔥 RESPONSE LENGKAP (INI YANG PENTING)
        return jsonify({
            "kehamilan_id": str(data["_id"]),
            "usia_kehamilan_minggu": minggu,
            "usia_kehamilan_hari": hari,
            "trimester": trimester,
            "hpl": format_ddmmyyyy(data.get("hpl")),

            # 🔥 WAJIB ADA (BIAR MINGGU KE MUNCUL DI FRONTEND)
            "hpht": hpht,

            # 🔥 TAMBAHAN BIAR KONSISTEN DENGAN DASHBOARD UTAMA
            "tinggi_badan": data.get("tinggi_badan"),
            "berat_badan": data.get("berat_badan"),
            "status": data.get("status", "active"),

            # 🔥 DATA JANIN
            "ukuran_janin": perkembangan["ukuran"],
            "perkembangan_janin": perkembangan["perkembangan"],
            "tips_kesehatan": perkembangan["tips"]
        }), 200

    except Exception as e:
        print("Error dashboard pasangan:", e)

        return jsonify({
            "message": "Terjadi kesalahan"
        }), 500

@jwt_required()
def update_kehamilan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        hpht = data.get("hpht")

        if not hpht:
            return jsonify({"message": "HPHT wajib diisi"}), 400

        hpl = hitung_hpl(hpht)

        update_data = {
            "hpht": hpht,
            "hpl": hpl,
            "updated_at": datetime.utcnow()
        }

        if data.get("tinggi_badan") is not None:
            update_data["tinggi_badan"] = data.get("tinggi_badan")

        if data.get("berat_badan") is not None:
            update_data["berat_badan"] = data.get("berat_badan")

        # ✅ UPDATE DATA KEHAMILAN
        result = DataKehamilan.db["data_kehamilan"].update_one(
            {"user_id": ObjectId(user_id), "status": "active"},
            {"$set": update_data}
        )

        # 🔥 SYNC KE KALKULATOR (FIX DI SINI)
        KalkulatorModel.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$set": {
                    "hpht": hpht,
                    "hpl": hpl,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        return jsonify({
            "message": "Berhasil update",
            "hpl": hpl
        }), 200

    except Exception as e:
        print("Error update:", e)
        return jsonify({"message": "Terjadi kesalahan"}), 500
    
@jwt_required()
def end_pregnancy():
    try:
        user_id = get_jwt_identity()

        result = DataKehamilan.db["data_kehamilan"].update_one(
            {"user_id": ObjectId(user_id), "status": "active"},
            {
                "$set": {
                    "status": "finished",
                    "end_date": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            return jsonify({"message": "Tidak ada kehamilan aktif"}), 400

        return jsonify({"message": "Kehamilan diakhiri"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Gagal mengakhiri"}), 500
    
@jwt_required()
def pregnancy_history_with_detail():
    try:
        user_id = get_jwt_identity()

        # ======================
        # AMBIL DATA KEHAMILAN
        # ======================
        data = list(
            DataKehamilan.db["data_kehamilan"]
            .find({"user_id": ObjectId(user_id)})
            .sort("kehamilan_ke", -1)
        )

        result = []

        for d in data:

            kehamilan_id = str(d["_id"])

            # ======================
            # AMBIL RIWAYAT BERAT BADAN
            # ======================
            bb_data = list(
                DataKehamilan.db["berat_badan"].find({
                    "user_id": ObjectId(user_id),
                    "kehamilan_id": ObjectId(kehamilan_id)
                }).sort("tanggal", -1)
            )

            riwayat_bb = []

            for b in bb_data:
                riwayat_bb.append({
                    "id": str(b["_id"]),
                    "berat_badan": float(b.get("berat_badan") or 0),
                    "tanggal": b["tanggal"].strftime("%d-%m-%Y") if b.get("tanggal") else None
                })

            # ======================
            # BUILD RESPONSE
            # ======================
            result.append({
                "id": kehamilan_id,
                "kehamilan_ke": d.get("kehamilan_ke", 0),
                "hpht": d.get("hpht"),

                # 🔥 HPL FORMAT DD-MM-YYYY
                "hpl": format_ddmmyyyy(d.get("hpl")),

                "status": d.get("status", "active"),
                "start_date": d.get("start_date").isoformat() if d.get("start_date") else None,
                "end_date": d.get("end_date").isoformat() if d.get("end_date") else None,

                # 🔥 RIWAYAT BERAT BADAN
                "riwayat_bb": riwayat_bb
            })

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:
        print("ERROR pregnancy_history_with_detail:", e)
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil data"
        }), 500