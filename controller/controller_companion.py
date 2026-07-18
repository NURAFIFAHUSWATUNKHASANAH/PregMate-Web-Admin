from flask import jsonify, request
from bson import ObjectId
from datetime import datetime
import traceback
from controller.pregnancy_controller import hitung_usia_kehamilan
from models.companion_plan import CompanionPlan
from models.data_kehamilan_model import DataKehamilan

db = None

def set_db(database):
    global db
    db = database
    CompanionPlan.set_db(database)

def get_current_companion_plan(user_id):
    """Mengambil plan pendampingan hari ini. Jika tidak ada, buat agenda Level 1 Statis"""
    date_str = request.args.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    try:
        plan = CompanionPlan.find_by_date(user_id, date_str)
        
        if not plan:
            user_doc = db["users"].find_one({"_id": ObjectId(user_id)})
            kehamilan_id = user_doc.get("kehamilan_id") if user_doc else None
            plan = CompanionPlan.generate_static_plan(user_id, kehamilan_id, date_str)
            
        plan["_id"] = str(plan["_id"])
        plan["user_id"] = str(plan["user_id"])
        if plan.get("kehamilan_id"):
            plan["kehamilan_id"] = str(plan["kehamilan_id"])
        if isinstance(plan.get("tanggal_jurnal"), datetime):
            plan["tanggal_jurnal"] = plan["tanggal_jurnal"].isoformat()
        if isinstance(plan.get("updated_at"), datetime):
            plan["updated_at"] = plan["updated_at"].isoformat()
            
        return jsonify({"status": "success", "has_data": True, "data": plan}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def submit_companion_checkin(user_id):
    try:
        data = request.json
        
        profil = DataKehamilan.db["data_kehamilan"].find_one({
            "user_id": ObjectId(user_id),
            "status": "active"
        })

        if not profil:
            return jsonify({"status": "error", "message": "Profil tidak ditemukan"}), 404

        # Menggabungkan data inti, detail_trimester, dan usia kehamilan
        # agar sesuai dengan struktur input yang dibutuhkan oleh CompanionPlan.analyze_checkin
        checkin_payload = {
            **data.get("inti", {}),
            **data.get("detail_trimester", {}).get(f"t{data.get('trimester', 1)}", {}),
            "keluhan": data.get("inti", {}).get("keluhan", []),
            "usia_kehamilan_minggu": data.get("usia_kehamilan_minggu", 0)
        }

        # 1. ANALISIS OTOMATIS BERDASARKAN RULE
        # Fungsi ini sekarang menangani semua logika skor berdasarkan checkin_payload
        unique_areas = CompanionPlan.analyze_checkin(checkin_payload)
        
        # 2. GENERATE REKOMENDASI (Actionable steps)
        rekomendasi_list = CompanionPlan.generate_recommendation(unique_areas)
        
        # 3. GENERATE AGENDA
        agenda_baru = CompanionPlan.generate_dynamic_agenda(rekomendasi_list)

        # 4. ANALISIS RISIKO (Tetap di controller)
        skor = profil.get("skor_risiko", 0)
        status_analisis = "Pendampingan Intensif" if skor > 2 else "Pendampingan Standar"

        # 5. SIMPAN KE DB
        CompanionPlan.upsert_plan(
            user_id,
            data.get("kehamilan_id"),
            {
                "tanggal": data.get("date"),
                "current_phase": 3,
                "agenda": agenda_baru,
                "analisis": status_analisis,
                "checkin_data": data,
                "rekomendasi": rekomendasi_list  # Disimpan agar UI bisa merender rekomendasi yang relevan
            }
        )

        return jsonify({
            "status": "success",
            "agenda": agenda_baru,
            "rekomendasi": rekomendasi_list,
            "analisis": status_analisis
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    
def update_companion_progress(user_id):
    try:
        data = request.json
        date_str = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # 1. Ambil plan yang ada
        existing_plan = CompanionPlan.find_by_date(user_id, date_str)
        if not existing_plan:
            return jsonify({"status": "error", "message": "Plan harian tidak ditemukan"}), 404

        # 2. Ambil agenda dari request, pastikan setiap item memiliki status 'done'
        # Jika client mengirim 'agenda_hari_ini', kita pastikan struktur 'done' terjaga
        agenda_update = data.get("agenda_hari_ini", existing_plan.get("agenda", []))
        
        # Payload untuk update
        payload = {
            "tanggal": date_str,
            "agenda": agenda_update,  # Ini sudah termasuk status 'done' dari Flutter
            "progress_percentage": float(data.get("progress", {}).get("percentage", 0.0)),
            "jumlah_selesai_display": data.get("progress", {}).get("display", "0 dari 0 selesai"),
            "catatan_malam": data.get("catatan_malam", "")
        }

        # 3. Simpan ke database
        # Pastikan upsert_plan menangani update array agenda secara utuh
        CompanionPlan.upsert_plan(user_id, existing_plan.get("kehamilan_id"), payload)
        
        return jsonify({"status": "success", "message": "Progress sinkron dan status agenda tersimpan"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
def generate_daily_static_plan(database):
    """
    Cronjob / Batch Processor untuk otomatisasi pembuatan plan awal harian seluruh user ber-role ibu.
    Menerapkan state awal Level 1 berbasis pencegahan intervensi ANC WHO.
    """
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        users = database["users"].find({"role": "ibu"})
        total_generated = 0

        for user in users:
            try:
                # Menghindari duplikasi penulisan ulang jika user sudah aktif membuka aplikasi di pagi hari
                existing = CompanionPlan.find_by_date(user["_id"], today)
                if existing:
                    continue

                CompanionPlan.generate_static_plan(
                    user_id=user["_id"],
                    kehamilan_id=user.get("kehamilan_id"),
                    date_str=today
                )
                total_generated += 1

            except Exception as user_err:
                print(f"⚠️ Gagal memproses batch plan untuk UID {user['_id']}: {str(user_err)}")

        print(f"✅ Batch processing selesai. Berhasil membuat {total_generated} rencana dasar ANC harian.")
    except Exception as e:
        print(f"❌ Kegagalan fatal pada Cronjob: {str(e)}")
        traceback.print_exc()

def get_evaluasi_data(user_id):
    try:
        profil = db["data_kehamilan"].find_one({
            "user_id": ObjectId(user_id),
            "status": "active"
        })

        if not profil:
            return jsonify({"status": "error", "message": "Profil tidak ditemukan"}), 404

        today = request.args.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        plan = CompanionPlan.find_by_date(user_id, today)
        agenda = plan.get("agenda", []) if plan else []
        
        checkin_data = plan.get("checkin_data", {}) if plan else {}
        keluhan = checkin_data.get("inti", {}).get("keluhan", [])

        belum_selesai = []

        # 1. Logika agenda yang belum selesai (TANPA processed_kategori)
        for item in agenda:
            # Lewati jika kategori adalah "Evaluasi" atau tugas sudah selesai
            if item.get("kategori") == "Evaluasi" or item.get("done", False):
                continue
            
            # Setiap tugas yang belum selesai akan masuk ke list
            belum_selesai.append({
                "id": item["id"], # Pastikan ID ini unik untuk setiap item agenda
                "kategori": item.get("kategori", "Umum"),
                "text": f"Kenapa aktivitas '{item['tugas']}' belum sempat dilakukan?",
                "options": [
                    "Lupa",
                    "Tidak sempat",
                    "Bunda menolak",
                    "Kondisi Bunda tidak memungkinkan"
                ]
            })

        # 2. Logika Pertanyaan Kondisi
        if keluhan:
            belum_selesai.append({
                "id": "eval_kondisi_keluhan",
                "kategori": "Kondisi Bunda",
                "text": f"Bunda tadi mengeluhkan: {', '.join(keluhan)}. Bagaimana kondisi Bunda sekarang?",
                "options": ["Membaik", "Masih sama", "Menurun"]
            })

        # 3. Logika Apresiasi
        if not belum_selesai:
            belum_selesai.append({
                "id": "apresiasi_01",
                "kategori": "Apresiasi",
                "text": "Luar biasa! Semua agenda hari ini telah Bunda selesaikan dengan baik. ✨",
                "options": [] 
            })

        return jsonify({
            "status": "success",
            "data": {
                "context": {
                    "trimester": profil.get("trimester", 1),
                    "usia_kehamilan": profil.get("usia_minggu", 0),
                    "bb_info": f"Berat badan {profil.get('berat_badan_terakhir', 0)} kg"
                },
                "questions": belum_selesai
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
def submit_companion_evaluasi(user_id):
    try:
        data = request.json
        answers = data.get("answers", {})
        today = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        plan = CompanionPlan.find_by_date(user_id, today)
        if not plan:
            return jsonify({"status": "error", "message": "Plan tidak ditemukan"}), 404

        # Buat lookup map dari ID ke Kategori berdasarkan agenda yang ada di plan
        id_to_kategori = {item["id"]: item.get("kategori") for item in plan.get("agenda", [])}

        # 1. Kumpulkan Tips/Feedback berdasarkan semua jawaban kendala (DEDUPLIKASI)
        kumpulan_tips_map = {} 
        
        for id_tugas, alasan in answers.items():
            # Lewati kategori khusus yang bukan merupakan tugas agenda
            if id_tugas in ["eval_kondisi_keluhan", "apresiasi_01"]:
                continue
            
            kategori = id_to_kategori.get(id_tugas)
            
            # Hanya ambil tips jika kategori tersebut belum ada di map
            if kategori and kategori not in kumpulan_tips_map:
                tips = CompanionPlan.get_feedback_by_kendala(kategori, alasan)
                kumpulan_tips_map[kategori] = f"• {kategori}: {tips}"

        # Mengubah dictionary kembali menjadi list string untuk digabungkan
        kumpulan_tips = list(kumpulan_tips_map.values())

        # 2. Logika Feedback untuk Kondisi Bunda
        feedback_saran = ""
        kondisi_bunda = answers.get("eval_kondisi_keluhan")
        if kondisi_bunda == "Membaik":
            feedback_saran = "Syukurlah kondisi Bunda membaik. Pertahankan ya! ✨"
        elif kondisi_bunda == "Masih sama":
            feedback_saran = "Bunda, jika keluhan masih terasa, jangan ragu untuk istirahat lebih awal atau hubungi bidan."
        elif kondisi_bunda == "Menurun":
            feedback_saran = "Mohon maaf mendengar kondisi Bunda menurun. Segera hubungi tenaga medis atau pendamping jika keluhan berat."

        # 3. Simpan ke database
        full_feedback = f"{feedback_saran}\n\nTips untuk Bunda:\n" + "\n".join(kumpulan_tips)
        
        db["companion_plans"].update_one(
            {"_id": plan["_id"]},
            {
                "$set": {
                    "evaluasi_malam.answers": answers,
                    "evaluasi_malam.feedback": full_feedback,
                    "evaluasi_malam.updated_at": datetime.utcnow()
                }
            }
        )

        return jsonify({
            "status": "success",
            "message": "Evaluasi tersimpan",
            "data": {
                "feedback_saran": full_feedback,
                "agenda_baru": [] 
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500