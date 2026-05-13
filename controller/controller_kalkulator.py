import math
from zoneinfo import ZoneInfo

from bson import ObjectId
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

from dateutil.relativedelta import relativedelta

from models.kalkulator_model import KalkulatorModel
# ================= HITUNG DASHBOARD =================
def hitung_dashboard(data):
    total_biaya = data.get("total_biaya", 0)
    pakai_bpjs = data.get("pakai_bpjs", False)
    metode_nabung = data.get("metode_nabung", "bulanan")  # 🔥 NEW

    # =============================
    # 🔥 BPJS
    # =============================
    if pakai_bpjs:
        total_biaya *= 0.3

    total_masuk = data.get("total_masuk", 0)
    total_keluar = data.get("total_keluar", 0)

    saldo = total_masuk - total_keluar
    sisa = max(total_biaya - saldo, 0)

    bulan = 0
    hari = 0
    sisa_bulan = 1

    try:
        now = datetime.now(ZoneInfo("Asia/Jakarta"))

        # =============================
        # 🔥 VALIDASI FORMAT TANGGAL
        # =============================
        def parse_date_safe(date_str):
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")

                # 🚨 validasi tahun
                if dt.year < 2000:
                    return None

                return dt.replace(tzinfo=ZoneInfo("Asia/Jakarta"))
            except:
                return None

        hpl = parse_date_safe(data.get("hpl"))
        hpht = parse_date_safe(data.get("hpht"))

        # =============================
        # 🔥 PRIORITAS: HPL
        # =============================
        if hpl:
            if hpl < now:
                bulan = 0
                hari = 0
            else:
                selisih = hpl - now
                total_hari = selisih.days

                bulan = total_hari // 30
                hari = total_hari % 30

            sisa_bulan = max(bulan, 1)

        # =============================
        # 🔥 FALLBACK: HPHT
        # =============================
        elif hpht:
            usia_kehamilan = (now - hpht).days
            sisa_hari_total = max(280 - usia_kehamilan, 0)

            bulan = sisa_hari_total // 30
            hari = sisa_hari_total % 30

            sisa_bulan = max(bulan, 1)

        else:
            bulan = 0
            hari = 0
            sisa_bulan = 1

    except Exception as e:
        print("ERROR HITUNG DASHBOARD:", e)
        bulan = 0
        hari = 0
        sisa_bulan = 1

    # =============================
    # 🔥 FINANSIAL
    # =============================
    nabung_per_bulan = sisa / sisa_bulan if sisa_bulan > 0 else sisa

    # =============================
    # 🔥 HITUNG MINGGU (NEW)
    # =============================
    total_minggu = max((bulan * 4) + (hari // 7), 1)
    nabung_per_minggu = sisa / total_minggu if total_minggu > 0 else sisa

    # =============================
    # 🔥 PILIH TARGET (NEW)
    # =============================
    if metode_nabung == "mingguan":
        target_nabung = nabung_per_minggu
    else:
        target_nabung = nabung_per_bulan

    progress = (saldo / total_biaya * 100) if total_biaya > 0 else 0

    # =============================
    # 🔥 INSIGHT
    # =============================
    if progress >= 100:
        insight = "Kamu sudah siap secara finansial 🎉"
    elif progress >= 70:
        insight = "Hampir siap, pertahankan tabungan 💪"
    elif progress >= 40:
        insight = "Masih perlu ditingkatkan lagi 📈"
    else:
        insight = "Yuk mulai menabung dari sekarang 🚀"

    return {
        "saldo": saldo,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "total_kebutuhan": total_biaya,
        "sisa": sisa,

        # 🔥 TARGET
        "nabung_per_bulan": nabung_per_bulan,
        "nabung_per_minggu": nabung_per_minggu,
        "target_nabung": target_nabung,
        "metode_nabung": metode_nabung,

        "progress": progress,
        "insight": insight,
        "sisa_bulan": bulan,
        "sisa_hari": hari
    }


# ================= SAVE =================
def save_kalkulator():
    user_id = get_jwt_identity()
    data = request.json

    kehamilan_id = data.get("kehamilan_id")

    if not kehamilan_id:
        return jsonify({
            "status": "error",
            "message": "kehamilan_id wajib"
        }), 400

    try:
        doc_id = KalkulatorModel.save(user_id, data)

        return jsonify({
            "status": "success",
            "message": "Data tersimpan",

            # 🔥 FIX: kirim 2 ID penting
            "kalkulator_id": doc_id,
            "kehamilan_id": kehamilan_id
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
# ================= DASHBOARD =================
def get_dashboard():
    kehamilan_id = request.args.get("kehamilan_id")

    if not kehamilan_id:
        return jsonify({
            "status": "error",
            "message": "kehamilan_id wajib"
        }), 400

    data = KalkulatorModel.get(kehamilan_id)

    if not data:
        return jsonify({
            "status": "success",
            "data": {}
        })

    result = hitung_dashboard(data) or {}

    result["kehamilan_id"] = str(data.get("kehamilan_id"))
    result["kalkulator_id"] = str(data.get("_id"))
    riwayat = data.get("riwayat", [])

    for item in riwayat:
      item["_id"] = str(item.get("_id", ""))

    result["riwayat"] = riwayat

    return jsonify({
        "status": "success",
        "data": result
    })

# ================= TABUNG =================
def tambah_tabungan():
    data = request.json

    kehamilan_id = data.get("kehamilan_id")
    jumlah = float(data.get("jumlah", 0))

    if not kehamilan_id:
        return jsonify({"status": "error", "message": "kehamilan_id wajib"}), 400

    if jumlah <= 0:
        return jsonify({"status": "error", "message": "jumlah tidak valid"}), 400

    KalkulatorModel.add_income(kehamilan_id, jumlah)

    return jsonify({"status": "success"})

# ================= PENGELUARAN =================
def tambah_pengeluaran():
    data = request.json

    kehamilan_id = data.get("kehamilan_id")
    jumlah = float(data.get("jumlah", 0))
    keterangan = data.get("keterangan", "").strip()

    if not kehamilan_id:
        return jsonify({"status": "error", "message": "kehamilan_id wajib"}), 400

    if jumlah <= 0:
        return jsonify({"status": "error", "message": "Jumlah tidak valid"}), 400

    if not keterangan:
        return jsonify({"status": "error", "message": "Keterangan wajib"}), 400

    KalkulatorModel.add_expense(kehamilan_id, jumlah, keterangan)

    return jsonify({"status": "success"})

# ================= EDIT RIWAYAT =================
def edit_riwayat():
    data = request.json

    kehamilan_id = data.get("kehamilan_id")
    riwayat_id = data.get("riwayat_id")

    if not kehamilan_id or not riwayat_id:
        return jsonify({
            "status": "error",
            "message": "kehamilan_id dan riwayat_id wajib",
            "debug": data
        }), 400

    try:
        jumlah = float(data.get("jumlah", 0))
    except:
        return jsonify({
            "status": "error",
            "message": "Jumlah tidak valid"
        }), 400

    if jumlah <= 0:
        return jsonify({
            "status": "error",
            "message": "Jumlah harus > 0"
        }), 400

    try:
        KalkulatorModel.edit_riwayat(
            kehamilan_id,
            riwayat_id,
            jumlah,
            data.get("keterangan", "")
        )

        return jsonify({
            "status": "success",
            "message": "Riwayat berhasil diupdate"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
# ================= DELETE RIWAYAT =================
def delete_riwayat():
    data = request.json

    kehamilan_id = data.get("kehamilan_id")
    riwayat_id = data.get("riwayat_id")

    if not kehamilan_id or not riwayat_id:
        return jsonify({
            "status": "error",
            "message": "kehamilan_id dan riwayat_id wajib",
            "debug": data
        }), 400

    try:
        KalkulatorModel.delete_riwayat(kehamilan_id, riwayat_id)

        return jsonify({
            "status": "success",
            "message": "Riwayat berhasil dihapus"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
def update_kalkulator():
    data = request.json

    kehamilan_id = data.get("kehamilan_id")
    metode_nabung = data.get("metode_nabung")
    total_biaya = data.get("total_biaya")
    pakai_bpjs = data.get("pakai_bpjs")

    if not kehamilan_id:
        return jsonify({"status": "error", "message": "kehamilan_id wajib"}), 400

    try:
        update_data = {}

        if metode_nabung:
            update_data["metode_nabung"] = metode_nabung

        if total_biaya is not None:
            update_data["total_biaya"] = float(total_biaya)

        if pakai_bpjs is not None:
            update_data["pakai_bpjs"] = pakai_bpjs

        # 🔥 UPDATE DATA
        KalkulatorModel.collection.update_one(
            {"kehamilan_id": ObjectId(kehamilan_id)},
            {"$set": update_data}
        )

        # 🔥 OPTIONAL: refresh recalculation (biar langsung update dashboard logic)
        KalkulatorModel.recalculate(kehamilan_id)

        return jsonify({
            "status": "success",
            "message": "Konfigurasi berhasil diupdate"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500