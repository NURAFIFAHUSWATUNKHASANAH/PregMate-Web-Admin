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

    # 🔥 PASTIKAN user_id selalu string benar
    user_id = str(user_id)

    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id
    }))

    tokens = []

    for p in pendamping_list:
        token = p.get("fcmToken") or p.get("tokenFCM") or p.get("fcm_token")

        print("==== DEBUG PENDAMPING ====")
        print("Nama:", p.get("nama"))
        print("Role:", p.get("role"))
        print("Partner:", p.get("partner_id"))
        print("Token:", token)
        print("===========================")

        if token:
            tokens.append(token)

    if not tokens:
        print("Tidak ada token pendamping")
        return

    success = 0

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Latihan Selesai",
                    body=f"Ibu hamil menyelesaikan latihan {label} dengan akurasi {accuracy:.1f}%"
                ),
                token=token
            )

            messaging.send(message)
            success += 1

        except Exception as e:
            print("Gagal kirim notif:", e)

    print("Notifikasi terkirim:", success)

    # 🔥 FIX PENTING: pastikan user_id yang disimpan benar-benar ibu yang login
    informasi_collection.insert_one({
        "user_id": str(user_id),   # 🔥 FIX DI SINI
        "kehamilan_id": str(kehamilan_id) if kehamilan_id else None,
        "tipe": "latihan",
        "label": label,
        "accuracy": accuracy,
        "pesan": f"Ibu hamil menyelesaikan latihan {label} dengan akurasi {accuracy:.1f}%",
        "tanggal": datetime.utcnow()
    })

def kirim_notif_mood(user_id, pesan, kehamilan_id=None):

    user_id = str(user_id)

    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id
    }))

    tokens = []

    for p in pendamping_list:
        token = p.get("fcmToken")
        if token:
            tokens.append(token)

    if not tokens:
        print("Tidak ada token pendamping")
        return

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Mood Bunda Hari Ini 🤰",
                    body=pesan  # ✅ hanya versi pendek
                ),
                token=token
            )

            messaging.send(message)

        except Exception as e:
            print("Gagal kirim notif:", e)

def kirim_notif_relaksasi(user_id, label, durasi, kehamilan_id=None):

    user_id = str(user_id)

    pendamping_list = list(users_collection.find({
        "role": "pendamping",
        "partner_id": user_id
    }))

    if not pendamping_list:
        print("Tidak ada pendamping")
        return

    success = 0

    for p in pendamping_list:
        token = p.get("fcmToken")

        if not token:
            print("Token kosong untuk:", p.get("nama"))
            continue

        try:
            pesan = f"Ibu hamil menyelesaikan latihan {label} selama {durasi} menit 🤰"

            message = messaging.Message(
                notification=messaging.Notification(
                    title="Latihan Relaksasi Selesai",
                    body=pesan
                ),
                token=token
            )

            response = messaging.send(message)
            print("SUCCESS SEND:", response)
            success += 1

        except Exception as e:
            print("❌ TOKEN INVALID / ERROR:", token)
            print("DETAIL ERROR:", e)

            # 🔥 HAPUS TOKEN YANG SUDAH ERROR (IMPORTANT FIX)
            users_collection.update_one(
                {"_id": p["_id"]},
                {"$unset": {"fcmToken": ""}}
            )

    print("Notifikasi terkirim:", success)

    # SIMPAN KE DB
    informasi_collection.insert_one({
        "user_id": user_id,
        "kehamilan_id": ObjectId(kehamilan_id) if kehamilan_id else None,
        "tipe": "relaksasi",
        "label": label,
        "durasi": durasi,
        "pesan": pesan,
        "tanggal": datetime.utcnow()
    })

    print("MASUK FUNGSI RELAKSASI")

def kirim_notif_pengingat_harian(user):

    user_id = str(user.get("_id")) if user.get("_id") else None
    token = user.get("fcmToken")

    if not token:
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Pengingat Latihan Harian",
                body="Hari ini kamu belum melakukan latihan. Yuk lakukan latihan untuk kesehatan ibu dan bayi 🤰"
            ),
            token=token
        )

        messaging.send(message)

        print("Notif pengingat terkirim ke:", user.get("nama"))

    except Exception as e:
        print("Gagal kirim notif:", e)

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