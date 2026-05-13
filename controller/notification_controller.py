from datetime import datetime

from bson import ObjectId
from firebase_admin import messaging

users_collection = None
informasi_collection = None

def set_db(database):

    global users_collection, informasi_collection

    users_collection = database["users"]
    informasi_collection = database["informasi"]


def kirim_notif_pendamping(user_id, label, accuracy, kehamilan_id=None):
    user_id_str = str(user_id)

    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id_str
    }))

    if not pendamping_list:
        print("Tidak ada pendamping ditemukan.")
        return

    success = 0
    pesan = f"Ibu hamil menyelesaikan latihan {label} dengan akurasi {accuracy:.1f}%"

    for p in pendamping_list:
        token = p.get("fcmToken") or p.get("tokenFCM") or p.get("token")

        if not token:
            continue

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Latihan Selesai",
                    body=pesan
                ),
                token=token
            )
            messaging.send(message)
            success += 1
            print(f"✅ Notif latihan terkirim ke: {p.get('nama')}")

        except Exception as e:
            print(f"❌ Token mati ditemukan pada {p.get('nama')}, menghapus...")
            users_collection.update_one(
                {"_id": p["_id"]},
                {"$unset": {"fcmToken": "", "tokenFCM": "", "token": ""}}
            )

    # Simpan ke histori informasi
    informasi_collection.insert_one({
        "user_id": user_id_str,
        "kehamilan_id": ObjectId(kehamilan_id) if kehamilan_id and ObjectId.is_valid(kehamilan_id) else None,
        "tipe": "latihan",
        "label": label,
        "accuracy": accuracy,
        "pesan": pesan,
        "tanggal": datetime.utcnow()
    })

def kirim_notif_mood(user_id, pesan, kehamilan_id=None):
    user_id_str = str(user_id)

    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id_str
    }))

    for p in pendamping_list:
        token = p.get("fcmToken") or p.get("tokenFCM") or p.get("token")
        
        if not token:
            continue

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Mood Bunda Hari Ini 🤰",
                    body=pesan
                ),
                token=token
            )
            messaging.send(message)
            print(f"✅ Notif mood terkirim ke: {p.get('nama')}")

        except Exception as e:
            print(f"❌ Token mati pada mood: {p.get('nama')}")
            users_collection.update_one(
                {"_id": p["_id"]},
                {"$unset": {"fcmToken": "", "tokenFCM": "", "token": ""}}
            )

def kirim_notif_relaksasi(user_id, label, durasi, kehamilan_id=None):
    # Pastikan ID dalam format string untuk pencarian partner
    user_id_str = str(user_id)

    # Cari pendamping yang terhubung dengan Ibu ini
    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id_str
    }))

    if not pendamping_list:
        print(f"Tidak ada pendamping ditemukan untuk user_id: {user_id_str}")
        return

    pesan = f"Ibu hamil menyelesaikan latihan {label}"
    success = 0

    for p in pendamping_list:
        # Ambil token dari berbagai kemungkinan field (standarisasi)
        token = p.get("fcmToken") or p.get("tokenFCM") or p.get("token")

        if not token:
            print(f"Skip: Pendamping {p.get('nama')} tidak memiliki token.")
            continue

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Latihan Relaksasi Selesai",
                    body=pesan
                ),
                token=token
            )

            response = messaging.send(message)
            print(f"SUCCESS mengirim ke {p.get('nama')}: {response}")
            success += 1

        except Exception as e:
            # Jika error "Requested entity was not found" atau "invalid token"
            print(f"❌ TOKEN INVALID/EXPIRED untuk {p.get('nama')}: {token}")
            print(f"Detail Error: {e}")

            # BERSIHKAN SEMUA FIELD TOKEN YANG MUNGKIN ADA AGAR TIDAK ERROR LAGI
            users_collection.update_one(
                {"_id": p["_id"]},
                {"$unset": {
                    "fcmToken": "", 
                    "tokenFCM": "", 
                    "token": ""
                }}
            )
            print(f"Database Updated: Token sampah untuk {p.get('nama')} telah dihapus.")

    print(f"Total notifikasi terkirim: {success}")

    # SIMPAN KE HISTORY INFORMASI
    if informasi_collection is not None:
        informasi_collection.insert_one({
            "user_id": user_id_str,
            "kehamilan_id": ObjectId(kehamilan_id) if kehamilan_id and ObjectId.is_valid(kehamilan_id) else None,
            "tipe": "relaksasi",
            "label": label,
            "durasi": durasi,
            "pesan": pesan,
            "tanggal": datetime.utcnow()
        })
        print("Data relaksasi berhasil disimpan ke database.")

def kirim_notif_pengingat_harian(user):
    # 'user' di sini adalah objek dokumen user dari MongoDB
    token = user.get("fcmToken") or user.get("tokenFCM") or user.get("token")

    if not token:
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Pengingat Latihan Harian",
                body="Hari ini kamu belum melakukan latihan. Yuk latihan sebentar untuk kesehatan ibu dan bayi 🤰"
            ),
            token=token
        )
        messaging.send(message)
        print(f"✅ Notif pengingat terkirim ke: {user.get('nama')}")

    except Exception as e:
        print(f"❌ Gagal kirim pengingat ke {user.get('nama')}, membersihkan token...")
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$unset": {"fcmToken": "", "tokenFCM": "", "token": ""}}
        )

def kirim_notif_jadwal(user_id, pesan, kehamilan_id=None):
    user_id_str = str(user_id)

    # 1. KIRIM KE BUNDA (Diri Sendiri)
    bunda = users_collection.find_one({"_id": ObjectId(user_id)})
    if bunda:
        token_bunda = bunda.get("fcmToken") or bunda.get("tokenFCM") or bunda.get("token")
        if token_bunda:
            try:
                msg_bunda = messaging.Message(
                    notification=messaging.Notification(
                        title="Jadwal Berhasil Dibuat 🗓️",
                        body=pesan
                    ),
                    token=token_bunda
                )
                messaging.send(msg_bunda)
                print(f"✅ Notif terkirim ke Bunda: {bunda.get('nama')}")
            except Exception:
                print("❌ Gagal kirim ke Bunda (Token invalid)")

    # 2. KIRIM KE PENDAMPING (Pasangan)
    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id_str
    }))

    for p in pendamping_list:
        token_p = p.get("fcmToken") or p.get("tokenFCM") or p.get("token")
        if not token_p:
            continue

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Jadwal Baru Bunda 🗓️",
                    body=pesan
                ),
                token=token_p
            )
            messaging.send(message)
            print(f"✅ Notif terkirim ke Pendamping: {p.get('nama')}")
        except Exception as e:
            # Bersihkan token mati
            users_collection.update_one(
                {"_id": p["_id"]},
                {"$unset": {"fcmToken": "", "tokenFCM": "", "token": ""}}
            )
            
def cek_latihan_harian(db):

    users = db["users"]
    histori = db["histori"]

    today = datetime.now().strftime("%Y-%m-%d")

    ibu_list = list(users.find({"role": "ibu"}))

    for ibu in ibu_list:

        user_id = str(ibu["_id"])

        latihan_hari_ini = histori.find_one({
            "user_id": user_id,
            "tanggal": {"$regex": today}
        })

        if not latihan_hari_ini:

            print("Tidak ada latihan hari ini:", ibu["nama"])

            # kirim ke ibu
            kirim_notif_pengingat_harian(ibu)

            # ambil pendamping yang benar-benar pasangan ibu ini
            pendamping = users.find_one({
                "partner_id": user_id,
                "role": "pendamping"
            })

            if pendamping:
                kirim_notif_pengingat_harian(pendamping)

from zoneinfo import ZoneInfo
from datetime import datetime
from bson import ObjectId
from firebase_admin import messaging

def cek_notif_kalkulator(db):

    kalkulator = db["kalkulator_bersalin"]
    users = db["users"]
    informasi = db["informasi"]

    now = datetime.now(ZoneInfo("Asia/Jakarta"))

    for data in kalkulator.find():

        try:
            user_id = data["user_id"]
            created_at = data.get("created_at")

            if not created_at:
                continue

            # 🔥 Samakan timezone
            created_at = created_at.replace(tzinfo=ZoneInfo("Asia/Jakarta"))

            selisih = now - created_at
            hari_ke = max(selisih.days, 0)

            metode = data.get("metode_nabung", "bulanan")

            total_biaya = data.get("total_biaya", 0)
            total_masuk = data.get("total_masuk", 0)
            total_keluar = data.get("total_keluar", 0)

            saldo = total_masuk - total_keluar
            sisa = max(total_biaya - saldo, 0)

            # 🔥 Ambil user
            if isinstance(user_id, str):
                if not ObjectId.is_valid(user_id):
                    continue
                user_id = ObjectId(user_id)

            user = users.find_one({"_id": user_id})
            if not user:
                continue

            token = user.get("fcmToken") or user.get("tokenFCM") or user.get("token")
            if not token:
                continue

            def rupiah(x):
                return f"Rp {int(x):,}".replace(",", ".")

            title = "Reminder Tabungan 💰"
            body = None
            flag = None

            # =============================
            # BULANAN
            # =============================
            if metode == "bulanan":

                if hari_ke == 10 and not data.get("notif_h10"):
                    body = "Yuk mulai nabung bulan ini 💡"
                    flag = "notif_h10"

                elif hari_ke == 20 and not data.get("notif_h20"):
                    body = f"Kamu masih kurang {rupiah(sisa)} dari target bulan ini 😬"
                    flag = "notif_h20"

                elif hari_ke == 30 and not data.get("notif_h30"):
                    body = f"Hari terakhir! Kurang {rupiah(sisa)} lagi 🎯"
                    flag = "notif_h30"

            # =============================
            # MINGGUAN
            # =============================
            else:
                hari_dalam_minggu = hari_ke % 7

                if hari_dalam_minggu == 3 and not data.get("notif_h3"):
                    body = "Yuk mulai nabung minggu ini 💡"
                    flag = "notif_h3"

                elif hari_dalam_minggu == 5 and not data.get("notif_h5"):
                    body = f"Kamu masih kurang {rupiah(sisa)} minggu ini 😬"
                    flag = "notif_h5"

                elif hari_dalam_minggu == 6 and not data.get("notif_h7"):
                    body = f"Hari terakhir minggu ini! Kurang {rupiah(sisa)} 🎯"
                    flag = "notif_h7"

            # =============================
            # 🔥 KIRIM + SIMPAN
            # =============================
            if body and flag:

                # 🔥 Kirim FCM
                messaging.send(
                    messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body
                        ),
                        token=token
                    )
                )

                print(f"✅ Notif terkirim: {user_id} | hari {hari_ke}")

                # 🔥 SIMPAN KE KOLEKSI INFORMASI (AMAN)
                if informasi is not None:
                    informasi.insert_one({
                        "user_id": str(user_id),
                        "kehamilan_id": ObjectId(data.get("kehamilan_id"))
                            if data.get("kehamilan_id") and ObjectId.is_valid(str(data.get("kehamilan_id")))
                            else None,
                        "tipe": "kalkulator",
                        "label": "tabungan",
                        "title": title,
                        "pesan": body,
                        "tanggal": datetime.utcnow()
                    })

                # 🔥 Set flag agar tidak double kirim
                kalkulator.update_one(
                    {"_id": data["_id"]},
                    {"$set": {flag: True}}
                )

        except Exception as e:
            print("❌ ERROR NOTIF KALKULATOR:", e)