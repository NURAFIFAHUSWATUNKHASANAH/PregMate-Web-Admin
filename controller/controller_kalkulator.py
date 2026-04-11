import math
from zoneinfo import ZoneInfo

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

from dateutil.relativedelta import relativedelta

from models.kalkulator_model import KalkulatorModel

def hitung_dashboard(data):
    import math
    from datetime import datetime
    from zoneinfo import ZoneInfo

    total_biaya = data.get("total_biaya", 0)
    pakai_bpjs = data.get("pakai_bpjs", False)

    # 🔥 BPJS
    if pakai_bpjs:
        total_biaya *= 0.3

    total_masuk = data.get("total_masuk", 0)
    total_keluar = data.get("total_keluar", 0)

    saldo = total_masuk - total_keluar
    sisa = max(total_biaya - saldo, 0)

    # 🔥 DEFAULT
    bulan = 0
    hari = 0
    sisa_bulan = 1

    try:
        now = datetime.now(ZoneInfo("Asia/Jakarta"))

        # =============================
        # 🔥 PRIORITAS: HPL
        # =============================
        if data.get("hpl"):
            hpl = datetime.strptime(data["hpl"], "%Y-%m-%d")

            # 🔥 FIX TIMEZONE (AMAN)
            if hpl.tzinfo is None:
                hpl = hpl.replace(tzinfo=ZoneInfo("Asia/Jakarta"))

            if hpl < now:
                bulan = 0
                hari = 0
            else:
                # 🔥 HITUNG BERDASARKAN HARI (STABIL)
                selisih_hari = (hpl - now).days

                bulan = max(selisih_hari // 30, 0)
                hari = max(selisih_hari % 30, 0)

            sisa_bulan = max(bulan, 1)

        # =============================
        # 🔥 FALLBACK: HPHT
        # =============================
        elif data.get("hpht"):
            hpht = datetime.strptime(data["hpht"], "%Y-%m-%d")

            if hpht.tzinfo is None:
                hpht = hpht.replace(tzinfo=ZoneInfo("Asia/Jakarta"))

            usia_hari = (now - hpht).days
            sisa_hari = max(280 - usia_hari, 0)

            bulan = max(sisa_hari // 30, 0)
            hari = max(sisa_hari % 30, 0)

            sisa_bulan = max(bulan, 1)

    except Exception as e:
        print("ERROR HITUNG DASHBOARD:", e)
        bulan = 0
        hari = 0
        sisa_bulan = 1

    # =============================
    # 🔥 FINANSIAL
    # =============================
    nabung_per_bulan = sisa / sisa_bulan if sisa_bulan > 0 else sisa
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
        "nabung_per_bulan": nabung_per_bulan,
        "progress": progress,
        "insight": insight,
        "sisa_bulan": bulan,
        "sisa_hari": hari
    }

# ================= SAVE =================
def save_kalkulator():
    user_id = get_jwt_identity()
    data = request.json

    KalkulatorModel.save(user_id, data)

    return jsonify({
        "status": "success",
        "message": "Data tersimpan"
    })


# ================= DASHBOARD =================
def get_dashboard():
    from flask import jsonify
    from flask_jwt_extended import get_jwt_identity
    from models.kalkulator_model import KalkulatorModel

    user_id = get_jwt_identity()

    data = KalkulatorModel.get(user_id)

    # 🔥 kalau belum ada data
    if not data:
        return jsonify({
            "status": "success",
            "data": {}
        })

    try:
        result = hitung_dashboard(data) or {}

        # 🔥 TAMBAH RIWAYAT (AMAN)
        result["riwayat"] = data.get("riwayat", [])

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("ERROR GET DASHBOARD:", e)

        # 🔥 fallback biar ga 500
        return jsonify({
            "status": "error",
            "message": "Gagal memuat dashboard",
            "data": {}
        }), 200

# ================= TABUNG =================
def tambah_tabungan():
    user_id = get_jwt_identity()
    data = request.json

    jumlah = float(data.get("jumlah", 0))

    KalkulatorModel.add_income(user_id, jumlah)

    return jsonify({"status": "success"})


# ================= PENGELUARAN =================
def tambah_pengeluaran():
    user_id = get_jwt_identity()
    data = request.json

    jumlah = float(data.get("jumlah", 0))
    keterangan = data.get("keterangan", "").strip()

    # 🔥 VALIDASI WAJIB
    if jumlah <= 0:
        return jsonify({"status": "error", "message": "Jumlah tidak valid"}), 400

    if not keterangan:
        return jsonify({"status": "error", "message": "Keterangan wajib diisi"}), 400

    KalkulatorModel.add_expense(user_id, jumlah, keterangan)

    return jsonify({"status": "success"})