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
# SIMPAN DATA KEHAMILAN (VERSI LENGKAP)
# ===============================
@jwt_required()
def submit_validasi_kehamilan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Data Fisik
        hpht = data.get("hpht")
        tinggi_badan = data.get("tinggi_badan")
        berat_badan = data.get("berat_badan")
        lila = data.get("lila")
        tekanan_darah = data.get("tekanan_darah")
        
        # Data Riwayat (B) & Checklist (C)
        is_kehamilan_pertama = data.get("is_kehamilan_pertama")
        jumlah_kehamilan = data.get("jumlah_kehamilan")
        jumlah_persalinan = data.get("jumlah_persalinan")
        riwayat_keguguran = data.get("riwayat_keguguran")
        skor_risiko = data.get("skor_risiko", 0)
        
        # Flags
        riwayat_sc = data.get("riwayat_sc", False)
        riwayat_hipertensi = data.get("riwayat_hipertensi", False)
        riwayat_preeklamsia = data.get("riwayat_preeklamsia", False)
        riwayat_perdarahan = data.get("riwayat_perdarahan", False)
        
        riwayat_penyakit = data.get("riwayat_penyakit", [])
        riwayat_kehamilan_checklist = data.get("riwayat_kehamilan_checklist", [])

        if not hpht:
            return jsonify({"message": "HPHT wajib diisi"}), 400

        # Cek kehamilan aktif
        existing = DataKehamilan.db["data_kehamilan"].find_one({"user_id": ObjectId(user_id), "status": "active"})
        if existing:
            return jsonify({"message": "Masih ada kehamilan aktif"}), 400

        # Tentukan index kehamilan (kehamilan ke-berapa)
        last = DataKehamilan.db["data_kehamilan"].find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("kehamilan_ke", -1)]
        )
        kehamilan_ke = 1 if not last else last["kehamilan_ke"] + 1

        hpl = hitung_hpl(hpht)
        
        data_kehamilan = {
            "user_id": ObjectId(user_id),
            "kehamilan_ke": kehamilan_ke,  # Penting untuk histori
            "hpht": hpht,
            "hpl": hpl,
            "tinggi_badan": tinggi_badan,
            "berat_badan": berat_badan,
            "lila": lila,
            "tekanan_darah": tekanan_darah,
            "is_kehamilan_pertama": is_kehamilan_pertama,
            "jumlah_kehamilan": jumlah_kehamilan,
            "jumlah_persalinan": jumlah_persalinan,
            "riwayat_keguguran": riwayat_keguguran,
            "skor_risiko": skor_risiko,
            "kategori_risiko": "High Risk" if skor_risiko > 2 else "Sedang/Rendah",
            "riwayat_sc": riwayat_sc,
            "riwayat_hipertensi": riwayat_hipertensi,
            "riwayat_preeklamsia": riwayat_preeklamsia,
            "riwayat_perdarahan": riwayat_perdarahan,
            "riwayat_penyakit": riwayat_penyakit,
            "riwayat_kehamilan_checklist": riwayat_kehamilan_checklist,
            "status": "active",
            "start_date": datetime.utcnow()
        }

        # Simpan ke DB
        result = DataKehamilan.create(data_kehamilan)
        
        # Update user status
        User.update_fields(user_id, {"is_validated": True})

        return jsonify({
            "message": "Data kehamilan berhasil disimpan",
            "kehamilan_ke": kehamilan_ke,
            "hpl": hpl
        }), 200

    except Exception as e:
        print(f"Error: {e}") # Log error untuk debugging
        return jsonify({"message": str(e)}), 500
    
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

        # Field yang boleh diupdate
        fields = [
            "tinggi_badan", "berat_badan", "lila", "tekanan_darah", 
            "riwayat_penyakit", "riwayat_kehamilan_checklist",
            "is_kehamilan_pertama", "jumlah_kehamilan", "jumlah_persalinan",
            "riwayat_keguguran", "riwayat_sc", "riwayat_hipertensi", 
            "riwayat_preeklamsia", "riwayat_perdarahan"
        ]
        
        update_data = {"updated_at": datetime.utcnow()}
        
        for field in fields:
            if data.get(field) is not None:
                update_data[field] = data.get(field)

        # Jika ada update HPHT, hitung ulang HPL
        if "hpht" in data:
            update_data["hpht"] = data["hpht"]
            update_data["hpl"] = hitung_hpl(data["hpht"])

        result = DataKehamilan.db["data_kehamilan"].update_one(
            {"user_id": ObjectId(user_id), "status": "active"},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        return jsonify({"message": "Berhasil update"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
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
        # CEK USER LOGIN
        # ======================
        user = User.find_by_id(user_id)

        if not user:
            return jsonify({
                "status": "error",
                "message": "User tidak ditemukan"
            }), 404

        # ======================
        # TENTUKAN USER YANG DICARI
        # ======================
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

        print("==============")
        print("ROLE :", user.get("role"))
        print("LOGIN USER :", user_id)
        print("QUERY USER :", user_id_to_query)
        print("==============")

        # ======================
        # AMBIL DATA KEHAMILAN
        # ======================
        data = list(
            DataKehamilan.db["data_kehamilan"]
            .find({
                "user_id": ObjectId(user_id_to_query)
            })
            .sort("kehamilan_ke", -1)
        )

        print("TOTAL KEHAMILAN :", len(data))

        result = []

        for d in data:

            kehamilan_id = str(d["_id"])

            # ======================
            # RIWAYAT BERAT BADAN
            # ======================
            bb_data = list(
                DataKehamilan.db["berat_badan"]
                .find({
                    "user_id": ObjectId(user_id_to_query),
                    "kehamilan_id": ObjectId(kehamilan_id)
                })
                .sort("tanggal", -1)
            )

            riwayat_bb = []

            for b in bb_data:

                riwayat_bb.append({
                    "id": str(b["_id"]),
                    "berat_badan": float(
                        b.get("berat_badan") or 0
                    ),
                    "tanggal":
                        b["tanggal"].strftime("%d-%m-%Y")
                        if b.get("tanggal")
                        else None
                })

            # ======================
            # BUILD RESPONSE
            # ======================
            result.append({
                "id": kehamilan_id,
                "kehamilan_ke": d.get("kehamilan_ke", 0),

                "hpht": d.get("hpht"),

                "hpl": format_ddmmyyyy(
                    d.get("hpl")
                ),

                "status": d.get(
                    "status",
                    "active"
                ),

                "start_date":
                    d.get("start_date").isoformat()
                    if d.get("start_date")
                    else None,

                "end_date":
                    d.get("end_date").isoformat()
                    if d.get("end_date")
                    else None,

                "riwayat_bb": riwayat_bb
            })

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:

        print("================================")
        print("ERROR pregnancy_history_with_detail")
        print(e)
        print("================================")

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500