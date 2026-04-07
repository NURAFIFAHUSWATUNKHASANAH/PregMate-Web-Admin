from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bson import ObjectId

from models.datauser_model import User
from models.data_kehamilan_model import DataKehamilan


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

        hpl = hitung_hpl(hpht)

        data_kehamilan = {

            "user_id": ObjectId(user_id),
            "hpht": hpht,
            "hpl": hpl,
            "tinggi_badan": tinggi_badan,
            "berat_badan": berat_badan,
            "created_at": datetime.utcnow()

        }

        DataKehamilan.create(data_kehamilan)

        User.update_fields(user_id, {"is_validated": True})

        return jsonify({
            "message": "Data kehamilan berhasil disimpan",
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

        data = DataKehamilan.find_by_user(user_id)

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

            "usia_kehamilan_minggu": minggu,
            "usia_kehamilan_hari": hari,
            "trimester": trimester,
            "hpl": data["hpl"],
            
            "hpht": data.get("hpht"),
            "tinggi_badan": data.get("tinggi_badan"),
            "berat_badan": data.get("berat_badan"),

            "ukuran_janin": perkembangan["ukuran"],
            "perkembangan_janin": perkembangan["perkembangan"],
            "tips_kesehatan": perkembangan["tips"]

        })

    except Exception as e:

        print(e)

        return jsonify({
            "message": "Terjadi kesalahan"
        }), 500
    
@jwt_required()
def dashboard_kehamilan_pasangan():

    try:

        user_id = get_jwt_identity()

        # cari user pendamping
        user = User.find_by_id(user_id)

        pasangan_id = user.get("partner_id")

        if not pasangan_id:
            return jsonify({
                "message": "Pasangan belum terhubung"
            }), 404

        # ambil data kehamilan pasangan
        data = DataKehamilan.find_by_user(pasangan_id)

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

            "usia_kehamilan_minggu": minggu,
            "usia_kehamilan_hari": hari,
            "trimester": trimester,
            "hpl": data["hpl"],

            "ukuran_janin": perkembangan["ukuran"],
            "perkembangan_janin": perkembangan["perkembangan"],
            "tips_kesehatan": perkembangan["tips"]

        })

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

        result = DataKehamilan.db["data_kehamilan"].update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": update_data}
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