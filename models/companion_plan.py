from datetime import datetime
from bson import ObjectId

class CompanionPlan:
    db = None

    @classmethod
    def set_db(cls, database):
        cls.db = database

    @classmethod
    def find_by_date(cls, user_id, date_str):
        user_id = ObjectId(str(user_id))
        start_date = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")

        return cls.db["companion_plans"].find_one({
            "user_id": user_id,
            "tanggal_jurnal": {"$gte": start_date, "$lte": end_date}
        })
    
    @classmethod
    def upsert_plan(cls, user_id, kehamilan_id, data):
        user_id = ObjectId(str(user_id))
        kehamilan_id = ObjectId(str(kehamilan_id)) if kehamilan_id and str(kehamilan_id) != "null" else None

        date_str = data.get("tanggal", datetime.utcnow().strftime("%Y-%m-%d"))
        start_date = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")

        query = {"user_id": user_id, "tanggal_jurnal": {"$gte": start_date, "$lte": end_date}}
        old_doc = cls.db["companion_plans"].find_one(query)

        doc_update = {
            "user_id": user_id,
            "kehamilan_id": kehamilan_id or (old_doc.get("kehamilan_id") if old_doc else None),
            "tanggal_jurnal": old_doc.get("tanggal_jurnal") if old_doc else start_date,
            "updated_at": datetime.utcnow(),
            "current_phase": data.get("current_phase", old_doc.get("current_phase", 1) if old_doc else 1),
            "analisis": data.get("analisis", old_doc.get("analisis", "Pendampingan Standar")),
            "skor_kepatuhan": data.get("skor_kepatuhan", old_doc.get("skor_kepatuhan", 0))
        }

        # 1. Sync data checkin
        if "checkin_data" in data: doc_update["checkin_data"] = data["checkin_data"]
        
        # 2. Sync agenda
        agenda_baru = data.get("agenda", old_doc.get("agenda", []) if old_doc else [])
        doc_update["agenda"] = agenda_baru

        # --- LOGIKA PERHITUNGAN PROGRES OTOMATIS ---
        total_aktivitas = len(agenda_baru)
        if total_aktivitas > 0:
            jumlah_selesai = sum(1 for item in agenda_baru if item.get("done", False))
            p_pct = (jumlah_selesai / total_aktivitas) * 100
            p_dsp = f"{jumlah_selesai} dari {total_aktivitas} aktivitas selesai"
        else:
            p_pct = 0.0
            p_dsp = "0 dari 0 aktivitas selesai"

        doc_update["progress"] = {
            "percentage": float(p_pct),
            "display": str(p_dsp)
        }
        # -------------------------------------------

        # 3. Sync rekomendasi
        if "rekomendasi" in data: doc_update["rekomendasi"] = data["rekomendasi"]
        elif old_doc and "rekomendasi" in old_doc: doc_update["rekomendasi"] = old_doc["rekomendasi"]

        # 5. Sync Evaluasi Malam
        catatan_baru = data.get("catatan_malam", old_doc.get("evaluasi_malam", {}).get("catatan_malam", "") if old_doc else "")
        doc_update["evaluasi_malam"] = {
            "catatan_malam": str(catatan_baru),
            "updated_at": datetime.utcnow()
        }

        return cls.db["companion_plans"].update_one(query, {"$set": doc_update}, upsert=True)
    
    @classmethod
    def generate_static_plan(cls, user_id, kehamilan_id, date_str):
        user_id = ObjectId(str(user_id))
        valid_kehamilan_id = ObjectId(str(kehamilan_id)) if kehamilan_id and str(kehamilan_id) != "null" else None
        start_date = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        
        query = {"user_id": user_id, "tanggal_jurnal": {"$gte": start_date, "$lte": datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")}}
        
        existing = cls.db["companion_plans"].find_one(query)
        if existing: return existing

        agenda_statis = [
            {"id": "act_1", "tugas": "Sarapan Nutrisi Seimbang", "done": False, "jam": "07:00", "type": "dialog"},
            {"id": "act_8", "tugas": "Review Kepatuhan Jurnal Malam", "done": False, "jam": "21:00", "type": "page_fitur"}
        ]

        document = {
            "user_id": user_id,
            "kehamilan_id": valid_kehamilan_id,
            "tanggal_jurnal": start_date,

            "current_phase": 1,

            "checkin_data": {},
            "analisis": "Pendampingan Standar",
            "agenda": cls.get_default_agenda(),
            "progress": {
                "percentage": 0.0,
                "display": "0 dari 11 aktivitas selesai"
            },
            "evaluasi_malam": {
                "catatan_malam": ""
            },
            "updated_at": datetime.utcnow()
        }

        cls.db["companion_plans"].update_one(query, {"$set": document}, upsert=True)
        return cls.db["companion_plans"].find_one(query)

    # Konfigurasi Rule dengan Prioritas
    RULES_CONFIG = {
        "Perdarahan": {"prioritas": 1, "kategori": "Darurat"},
        "Nyeri Perut Hebat": {"prioritas": 1, "kategori": "Darurat"},
        "Demam": {"prioritas": 2, "kategori": "Tinggi"},
        "Kontraksi": {"prioritas": 2, "kategori": "Tinggi"},
        "Gerakan Janin": {"prioritas": 2, "kategori": "Tinggi"},
        "Mual dan Muntah": {"prioritas": 3, "kategori": "Sedang"},
        "Hidrasi": {"prioritas": 3, "kategori": "Sedang"},
        "Nutrisi": {"prioritas": 3, "kategori": "Sedang"},
        "Kepatuhan Suplemen": {"prioritas": 3, "kategori": "Sedang"},
        "Pusing": {"prioritas": 3, "kategori": "Sedang"},
        "Kondisi Fisik": {"prioritas": 4, "kategori": "Rendah"},
        "Kualitas Tidur": {"prioritas": 4, "kategori": "Rendah"},
        "Kesehatan Emosional": {"prioritas": 4, "kategori": "Rendah"},
        "Kram Otot": {"prioritas": 4, "kategori": "Rendah"},
        "Pembengkakan": {"prioritas": 4, "kategori": "Rendah"},
        "Persiapan Persalinan": {"prioritas": 4, "kategori": "Rendah"}
    }

    @staticmethod
    def analyze_checkin(checkin_data):
        # 1. Inisialisasi Skor
        area_scores = {area: 0 for area in CompanionPlan.RULES_CONFIG.keys()}
        
        # Mapping Dasar
        fisik_map = {"Sangat Baik": 0, "Baik": 0, "Cukup": 1, "Kurang Baik": 3}
        aktivitas_map = {"Sangat Ringan (Banyak duduk)": 0, "Ringan": 0, "Sedang": 1, "Berat": 2}
        mood_map = {"Sangat Senang": 0, "Ceria": 0, "Biasa Saja": 1, "Sedih/Cemas": 3}
        tidur_map = {"Sangat Baik": 0, "Baik": 0, "Cukup": 1, "Kurang": 2}
        kelelahan_map = {"Tidak Lelah": 0, "Ringan": 1, "Sedang": 2, "Berat": 3}
        
        # Proses Skor Umum
        area_scores["Kondisi Fisik"] += fisik_map.get(checkin_data.get("kondisi_fisik"), 0)
        area_scores["Kondisi Fisik"] += aktivitas_map.get(checkin_data.get("aktivitas_harian"), 0)
        area_scores["Kondisi Fisik"] += kelelahan_map.get(checkin_data.get("kelelahan"), 0)
        area_scores["Kesehatan Emosional"] += mood_map.get(checkin_data.get("suasana_hati"), 0)
        area_scores["Kualitas Tidur"] += tidur_map.get(checkin_data.get("kualitas_tidur"), 0)
        
        # Hidrasi & Nutrisi
        if checkin_data.get("hidrasi") in ["0–3 Gelas", "4–5 Gelas"]: area_scores["Hidrasi"] += 2
        if checkin_data.get("status_vitamin") == "Belum": area_scores["Kepatuhan Suplemen"] += 3
        if checkin_data.get("nafsu_makan") in ["Kurang", "Tidak Nafsu"]: area_scores["Nutrisi"] += 3
            
        # Analisis Kondisional & Keluhan
        minggu = checkin_data.get("usia_kehamilan_minggu", 0)
        keluhan = checkin_data.get("keluhan", [])
        
        if minggu >= 24 and checkin_data.get("gerakan_janin") == "Belum": area_scores["Gerakan Janin"] += 5
        if checkin_data.get("kontraksi") == "Ya": area_scores["Kontraksi"] += 5
            
        mual = checkin_data.get("tingkat_mual")
        if mual == "Ringan": area_scores["Mual dan Muntah"] += 1
        elif mual == "Sedang": area_scores["Mual dan Muntah"] += 2
        elif mual == "Berat": area_scores["Mual dan Muntah"] += 4

        if checkin_data.get("kram_kaki_tangan") == "Ya": area_scores["Kram Otot"] += 3
        if checkin_data.get("bengkak_t2") == "Ya": area_scores["Pembengkakan"] += 3
        if checkin_data.get("tas_persalinan") in ["Belum", "Sebagian"]: area_scores["Persiapan Persalinan"] += 3

        # Pengecekan keluhan individu dengan substring
        for item in keluhan:
            if "Perdarahan" in item: area_scores["Perdarahan"] += 100
            elif "Nyeri" in item: area_scores["Nyeri Perut Hebat"] += 100
            elif "Demam" in item: area_scores["Demam"] += 50
            elif "Pusing" in item: area_scores["Pusing"] += 20
            elif "Muntah" in item: area_scores["Mual dan Muntah"] += 20

        # 3. RULE KOMBINASI (Diperbarui dengan any() untuk fleksibilitas label)
        if checkin_data.get("status_vitamin") == "Belum" and checkin_data.get("nafsu_makan") in ["Kurang", "Tidak Nafsu"]:
            area_scores["Nutrisi"] += 3; area_scores["Kepatuhan Suplemen"] += 2
        
        if checkin_data.get("kualitas_tidur") == "Kurang" and checkin_data.get("suasana_hati") == "Sedih/Cemas":
            area_scores["Kesehatan Emosional"] += 4
        
        if checkin_data.get("hidrasi") in ["0–3 Gelas", "4–5 Gelas"] and any("Pusing" in k for k in keluhan):
            area_scores["Hidrasi"] += 3; area_scores["Pusing"] += 2
        
        if checkin_data.get("aktivitas_harian") == "Berat" and checkin_data.get("kelelahan") == "Berat":
            area_scores["Kondisi Fisik"] += 4
        
        if checkin_data.get("tingkat_mual") == "Berat" and checkin_data.get("nafsu_makan") == "Tidak Nafsu":
            area_scores["Mual dan Muntah"] += 3; area_scores["Nutrisi"] += 3
        
        if checkin_data.get("bengkak_t2") == "Ya" and any("Pusing" in k for k in keluhan):
            area_scores["Pembengkakan"] += 2; area_scores["Pusing"] += 2
        
        if checkin_data.get("kontraksi") == "Ya" and any("Nyeri" in k for k in keluhan):
            area_scores["Kontraksi"] += 5; area_scores["Nyeri Perut Hebat"] += 5
        
        if any("Demam" in k for k in keluhan) and any("Muntah" in k for k in keluhan):
            area_scores["Demam"] += 4; area_scores["Mual dan Muntah"] += 3
        
        if checkin_data.get("kondisi_fisik") == "Kurang Baik" and checkin_data.get("kualitas_tidur") == "Kurang":
            area_scores["Kondisi Fisik"] += 2; area_scores["Kualitas Tidur"] += 2
        
        if checkin_data.get("suasana_hati") == "Sedih/Cemas" and checkin_data.get("kelelahan") == "Berat":
            area_scores["Kesehatan Emosional"] += 4
        
        if checkin_data.get("hidrasi") in ["0–3 Gelas", "4–5 Gelas"] and checkin_data.get("kram_kaki_tangan") == "Ya":
            area_scores["Hidrasi"] += 2; area_scores["Kram Otot"] += 2
        
        if checkin_data.get("status_vitamin") == "Belum" and checkin_data.get("kelelahan") == "Berat":
            area_scores["Kepatuhan Suplemen"] += 3; area_scores["Kondisi Fisik"] += 2
        
        if minggu >= 36 and checkin_data.get("tas_persalinan") == "Belum":
            area_scores["Persiapan Persalinan"] += 5
        
        if checkin_data.get("aktivitas_harian") == "Berat" and checkin_data.get("kontraksi") == "Ya":
            area_scores["Kontraksi"] += 5; area_scores["Kondisi Fisik"] += 3

        # Filter & Urutkan
        unique_areas = [area for area, score in area_scores.items() if score > 0]
        unique_areas.sort(
            key=lambda area: (
                CompanionPlan.RULES_CONFIG.get(area, {}).get("prioritas", 99),
                -area_scores[area]
            )
        )
        
        return unique_areas
    
    @staticmethod
    def generate_recommendation(area_perhatian):
        rekomendasi = []
        for area in area_perhatian:
            config = CompanionPlan.RULES_CONFIG.get(area, {})
            rekomendasi.append({
                "kategori": area,
                "prioritas": config.get("kategori", "Rendah"),
                "aksi": CompanionPlan._get_aksi_by_area(area)
            })
        return rekomendasi

    @staticmethod
    def _get_aksi_by_area(area):
        aksi_map = {
            "Hidrasi": ["Minum minimal 8 gelas air", "Bawa botol minum ke mana pun"],
            "Mual dan Muntah": ["Makan sedikit tapi sering", "Konsumsi jahe hangat", "Hindari bau menyengat"],
            "Perdarahan": ["Segera ke fasilitas kesehatan terdekat!"],
            "Nyeri Perut Hebat": ["Istirahat total", "Hubungi dokter jika nyeri menetap"],
            "Kualitas Tidur": ["Relaksasi napas sebelum tidur", "Matikan HP 30 menit sebelum tidur"],
            "Nutrisi": ["Pilih makanan bernutrisi tinggi", "Konsultasi dengan ahli gizi"],
            "Kepatuhan Suplemen": ["Jangan lupa minum vitamin kehamilan"],
            "Kondisi Fisik": ["Perbanyak istirahat", "Hindari aktivitas berat"],
            "Persiapan Persalinan": ["Lengkapi isi tas persalinan Bunda"],
            "Kesehatan Emosional": [
                "Temani Bunda berbicara", 
                "Lakukan relaksasi bersama"
            ],
            "Kram Otot": [
                "Lakukan peregangan ringan", 
                "Istirahat sejenak"
            ],
            "Pembengkakan": [
                "Tinggikan posisi kaki", 
                "Kurangi berdiri terlalu lama"
            ],
            "Gerakan Janin": [
                "Hitung gerakan janin", 
                "Segera ke dokter bila tetap berkurang"
            ],
            "Kontraksi": [
                "Pantau frekuensi kontraksi", 
                "Segera ke fasilitas kesehatan bila teratur"
            ],
            "Demam": [
                "Periksa suhu tubuh", 
                "Hubungi tenaga kesehatan"
            ],
            "Pusing": [
                "Duduk atau berbaring", 
                "Minum air putih"
            ]
        }
        return aksi_map.get(area, ["Pantau kondisi Bunda secara berkala"])
    
    @staticmethod
    def get_default_agenda():
        return [
            {"id": "base_1", "kategori": "Hidrasi", "tugas": "Waktunya minum air putih", "deskripsi": "Awali hari dengan segelas air putih untuk menjaga hidrasi tubuh Bunda ya 💧", "jam": "07:00", "type": "dialog", "done": False},
            {"id": "base_2", "kategori": "Nutrisi", "tugas": "Waktunya sarapan!", "deskripsi": "Pilihlah menu kaya protein seperti telur rebus atau olahan susu agar energi Bunda terjaga optimal 🍳", "jam": "07:30", "type": "dialog", "done": False},
            {"id": "base_3", "kategori": "Edukasi", "tugas": "Edukasi kehamilan hari ini", "deskripsi": "Luangkan sejenak waktu untuk membaca edukasi kehamilan agar Bunda semakin siap menjalani hari 📖", "jam": "09:00", "type": "page_fitur","target": "artikel", "done": False},
            {"id": "base_4", "kategori": "Hidrasi", "tugas": "Saatnya minum air putih", "deskripsi": "Jangan lupa minum segelas air putih agar kebutuhan cairan harian tetap tercukupi 💧", "jam": "10:30", "type": "dialog", "done": False},
            {"id": "base_5", "kategori": "Nutrisi", "tugas": "Makan siang telah tiba", "deskripsi": "Pastikan menu Bunda mengandung zat besi seperti daging merah, ikan, atau bayam ya 🍛", "jam": "12:30", "type": "dialog", "done": False},
            {"id": "base_6", "kategori": "Nutrisi", "tugas": "Camilan sehat Bunda", "deskripsi": "Saatnya camilan sehat untuk menjaga stamina, misalnya buah alpukat atau kacang almond 🍎", "jam": "16:00", "type": "dialog", "done": False},
            {"id": "base_7", "kategori": "Hidrasi", "tugas": "Saatnya minum air putih", "deskripsi": "Yuk, minum segelas air putih lagi agar tubuh tetap terhidrasi dengan baik 💧", "jam": "17:00", "type": "dialog", "done": False},
            {"id": "base_8", "kategori": "Nutrisi", "tugas": "Waktunya makan malam", "deskripsi": "Yuk, nikmati makan malam bergizi yang mudah dicerna, seperti sup ayam atau tumis sayuran 🍲", "jam": "18:30", "type": "dialog", "done": False},
            {"id": "base_9", "kategori": "Kualitas Tidur", "tugas": "Persiapan tidur", "deskripsi": "Tubuh butuh istirahat untuk pemulihan. Yuk, mulai persiapkan diri untuk tidur lebih awal malam ini 🌙", "jam": "20:00", "type": "dialog", "done": False},
        ]

    @staticmethod
    def generate_dynamic_agenda(rekomendasi_list):
        # Mengambil agenda dasar yang sudah diperbarui
        agenda = CompanionPlan.get_default_agenda()
        
        # Mapping tugas dengan field "tugas" (notif) dan "deskripsi" (detail)
        tugas_map = {
            "Hidrasi": {
                "id": "dyn_hidrasi",
                "kategori": "Hidrasi",
                "tugas": "Minum air putih",
                "deskripsi": "Pastikan Bunda tetap terhidrasi dengan minum air putih tambahan 2-3 gelas ya 💧",
                "jam": "10:00",
                "type": "dialog",
                "done": False
            },

            "Nutrisi": {
                "id": "dyn_nutrisi",
                "kategori": "Nutrisi",
                "tugas": "Camilan bernutrisi",
                "deskripsi": "Coba konsumsi buah atau kacang-kacangan untuk tambahan energi yang sehat 🍎",
                "jam": "11:00",
                "type": "dialog",
                "done": False
            },

            "Kepatuhan Suplemen": {
                "id": "dyn_suplemen",
                "kategori": "Kepatuhan Suplemen",
                "tugas": "Minum Vitamin",
                "deskripsi": "Jangan lupa konsumsi vitamin kehamilan agar tumbuh kembang janin optimal 💊",
                "jam": "08:00",
                "type": "dialog",
                "done": False
            },

            "Kualitas Tidur": {
                "id": "dyn_tidur",
                "kategori": "Kualitas Tidur",
                "tugas": "Relaksasi Sebelum Tidur",
                "deskripsi": "Lakukan latihan pernapasan melalui fitur Ruang Napas agar tubuh lebih rileks dan kualitas tidur menjadi lebih baik. 😴",
                "jam": "20:30",
                "type": "page_fitur",
                "target": "ruang_napas",
                "done": False
            },

            "Kondisi Fisik": {
                "id": "dyn_fisik",
                "kategori": "Kondisi Fisik",
                "tugas": "Senam Ibu Hamil",
                "deskripsi": "Lakukan senam ibu hamil sesuai usia kehamilan untuk membantu menjaga kebugaran tubuh dan mengurangi rasa pegal. 🤰",
                "jam": "14:00",
                "type": "page_fitur",
                "target": "senam",
                "done": False
            },

            "Persiapan Persalinan": {
                "id": "dyn_persalinan",
                "kategori": "Persiapan Persalinan",
                "tugas": "Periksa Tas Persalinan",
                "deskripsi": "Yuk, cek kembali perlengkapan tas persalinan agar semua kebutuhan Bunda dan bayi sudah siap. 🎒",
                "jam": "17:00",
                "type": "page_fitur",
                "target": "tas_persalinan",
                "done": False
            },

            "Mual dan Muntah": {
                "id": "dyn_mual",
                "kategori": "Mual dan Muntah",
                "tugas": "Kelola Mual",
                "deskripsi": "Coba konsumsi jahe hangat atau biskuit untuk membantu meredakan mual Bunda ☕",
                "jam": "09:30",
                "type": "dialog",
                "done": False
            },

            "Kesehatan Emosional": {
                "id": "dyn_emosi",
                "kategori": "Kesehatan Emosional",
                "tugas": "Lakukan Relaksasi",
                "deskripsi": "Saat ini Bunda tampak membutuhkan relaksasi. Yuk lakukan latihan pernapasan melalui fitur Ruang Napas agar tubuh dan pikiran lebih tenang. 🌿",
                "jam": "19:00",
                "type": "page_fitur",
                "target": "ruang_napas",
                "done": False
            },

            "Kram Otot": {
                "id": "dyn_kram",
                "kategori": "Kram Otot",
                "tugas": "Peregangan Ringan",
                "deskripsi": "Lakukan peregangan melalui fitur Senam untuk membantu mengurangi kram otot dan membuat tubuh lebih nyaman. 👣",
                "jam": "15:00",
                "type": "page_fitur",
                "target": "senam",
                "done": False
            },

            "Pembengkakan": {
                "id": "dyn_bengkak",
                "kategori": "Pembengkakan",
                "tugas": "Senam Ringan",
                "deskripsi": "Lakukan gerakan ringan melalui fitur Senam untuk membantu melancarkan sirkulasi darah dan mengurangi pembengkakan. 🦶",
                "jam": "16:00",
                "type": "page_fitur",
                "target": "senam",
                "done": False
            },

            "Gerakan Janin": {
                "id": "dyn_janin",
                "kategori": "Gerakan Janin",
                "tugas": "Pantau Gerakan Janin",
                "deskripsi": "Hitung gerakan janin (Counting Kicks) untuk memastikan Si Kecil tetap aktif dan sehat. 👶",
                "jam": "13:00",
                "type": "dialog",
                "done": False
            },

            "Kontraksi": {
                "id": "dyn_kontraksi",
                "kategori": "Kontraksi",
                "tugas": "Pantau Kontraksi",
                "deskripsi": "Pantau frekuensi kontraksi. Jika kontraksi teratur atau semakin kuat, segera hubungi tenaga kesehatan. ⏰",
                "jam": "18:00",
                "type": "dialog",
                "done": False
            },

            "Pusing": {
                "id": "dyn_pusing",
                "kategori": "Pusing",
                "tugas": "Atasi Pusing",
                "deskripsi": "Duduk atau berbaring di posisi nyaman, lalu minum air putih agar pusing berkurang. ☁️",
                "jam": "12:00",
                "type": "dialog",
                "done": False
            }
        }
        
        # Iterasi berdasarkan rekomendasi
        for rec in rekomendasi_list:
            kat = rec if isinstance(rec, str) else rec.get("kategori")
            
            if kat in tugas_map:
                if not any(a['id'] == tugas_map[kat]['id'] for a in agenda):
                    agenda.append(tugas_map[kat])
        
        # Sort agenda berdasarkan jam agar urutan tampil secara kronologis
        agenda.sort(key=lambda x: x.get("jam", "23:59"))
        
        return agenda
    

    @staticmethod
    def get_evaluasi_questions(area_perhatian, agenda_hari_ini):
        questions = []
        
        # Langsung periksa apakah ada tugas yang belum selesai (done: False)
        # Tidak perlu mengecualikan "Evaluasi" karena base_8 sudah tidak ada
        for area in area_perhatian:
            tugas_belum_selesai = [a for a in agenda_hari_ini if a.get("kategori") == area and not a.get("done")]
            
            if tugas_belum_selesai:
                questions.append({
                    "kategori": area,
                    "id": f"eval_{area.lower()}",
                    "text": f"Aktivitas '{tugas_belum_selesai[0]['tugas']}' belum sempat dilakukan. Apa kendalanya?",
                    "options": ["Lupa", "Tidak sempat", "Bunda menolak", "Kondisi tidak memungkinkan"]
                })
        
        # Jika tidak ada yang belum selesai (tugas_belum_selesai kosong), 
        # kembalikan pesan Apresiasi seperti yang kita bahas sebelumnya
        if not questions:
            return [{
                "kategori": "Apresiasi",
                "id": "eval_success",
                "text": "Luar biasa! Semua agenda hari ini telah Bunda selesaikan dengan baik. ✨",
                "options": []
            }]
            
        return questions
    
    @staticmethod
    def get_feedback_by_kendala(kategori, alasan):
        # Pola dasar solusi untuk setiap kategori
        solusi_map = {
            "Hidrasi": {
                "Lupa": "Bunda bisa pasang alarm atau gunakan stiker pengingat di botol minum ya. ✨",
                "Tidak sempat": "Siapkan botol minum di dekat Bunda, jadikan minum sebagai ritual kecil sebelum beraktivitas.",
                "Bunda menolak": "Coba air mineral dengan irisan lemon atau buah agar lebih segar, Bun."
            },
            "Nutrisi": {
                "Lupa": "Alarm 5 menit sebelum jam makan sangat membantu nutrisi dedek bayi.",
                "Tidak sempat": "Coba siapkan porsi praktis di wadah atau lakukan 'Meal Prep' sederhana di malam hari agar Bunda tetap bisa makan tepat waktu.",
                "Bunda menolak": "Makan dalam porsi kecil tapi sering jauh lebih baik daripada tidak makan sama sekali."
            },
            "Kualitas Tidur": {
                "Lupa": "Coba buat ritual santai: matikan HP 30 menit sebelum tidur.",
                "Tidak sempat": "Usahakan untuk memprioritaskan istirahat, Bun. Tubuh Bunda butuh itu.",
                "Bunda menolak": "Relaksasi napas pelan-pelan sebelum tidur bisa membantu tubuh lebih rileks."
            },
            "Kepatuhan Suplemen": {
                "Lupa": "Letakkan vitamin di dekat tempat Bunda biasa sarapan agar mudah terlihat.",
                "Tidak sempat": "Sediakan kotak obat kecil di dalam tas Bunda agar bisa diminum kapan saja.",
                "Bunda menolak": "Vitamin ini penting untuk mendukung perkembangan dedek bayi, Bun. Semangat ya!"
            },
            "Kondisi Fisik": {
                "Lupa": "Jadwalkan istirahat singkat di kalender Bunda.",
                "Tidak sempat": "Bunda, kesehatan Bunda adalah nomor satu. Coba ambil waktu 5 menit untuk duduk tenang.",
                "Kondisi tidak memungkinkan": "Jangan memaksakan diri ya, Bun. Istirahat total adalah pilihan terbaik saat ini."
            },
            "Kesehatan Emosional": {
                "Lupa": "Luangkan waktu sejenak untuk mendengarkan musik favorit atau curhat dengan pasangan.",
                "Tidak sempat": "Ambil napas dalam-dalam sejenak, Bunda hebat sudah bertahan sejauh ini.",
                "Bunda menolak": "Boleh kok merasa lelah, coba sampaikan apa yang Bunda rasakan ke pasangan ya."
            },
            "Kram Otot": {
                "Lupa": "Jangan lupa lakukan peregangan kaki sebelum tidur ya, Bun.",
                "Tidak sempat": "Coba lakukan peregangan ringan saat sedang duduk bekerja atau menonton.",
                "Kondisi tidak memungkinkan": "Kompres hangat atau pijatan lembut bisa membantu meredakan kram."
            },
            "Gerakan Janin": {
                "Lupa": "Coba lebih peka terhadap gerakan dedek, mungkin bisa sambil diajak bicara.",
                "Tidak sempat": "Luangkan 10 menit tenang untuk fokus merasakan gerakan dedek bayi ya.",
                "Bunda menolak": "Memantau gerakan dedek adalah cara terbaik menjaga bonding Bunda dan si kecil."
            },
            "Kontraksi": {
                "Lupa": "Catat waktu kontraksi agar Bunda bisa lebih tenang memantaunya.",
                "Tidak sempat": "Segera ambil posisi nyaman dan pantau apakah kontraksi semakin teratur.",
                "Kondisi tidak memungkinkan": "Jika nyeri hebat, jangan ragu untuk langsung ke fasilitas kesehatan ya, Bun."
            },
            "Pusing": {
                "Lupa": "Jangan lewatkan waktu makan dan minum air putih agar Bunda tidak pusing.",
                "Tidak sempat": "Segera duduk atau berbaring jika merasa pusing, jangan dipaksa beraktivitas.",
                "Kondisi tidak memungkinkan": "Bunda butuh istirahat total, segera hubungi dokter jika pusing tidak hilang."
            }
        }
        
        # Menangani kategori lain dengan tips umum
        default_tips = f"Tetap semangat Bunda! '{alasan}' adalah hal yang wajar. Besok kita coba lagi dengan perlahan ya. ✨"
        
        # Ambil kategori, jika tidak ada, gunakan default_tips
        kategori_tips = solusi_map.get(kategori, {})
        return kategori_tips.get(alasan, default_tips)