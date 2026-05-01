from apscheduler.schedulers.background import BackgroundScheduler
from firebase_admin import messaging
from datetime import datetime
from bson import ObjectId
from zoneinfo import ZoneInfo

from controller.notification_controller import (
    cek_latihan_harian,
    cek_notif_kalkulator
)


def send_push_notification(token, title, body):
    message = messaging.Message(
        token=token,
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                channel_id='default_channel',  # WAJIB match dengan channel di Flutter
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound='default')
            )
        ),
    )
    try:
        response = messaging.send(message)
        print("✅ Notifikasi dikirim:", response)
    except Exception as e:
        print("❌ Gagal mengirim notifikasi:", e)

def check_schedule(db):
    now = datetime.now()
    # Ambil jadwal yang belum dikirim
    schedules = db.schedules.find({"dikirim": {"$ne": True}})

    for schedule in schedules:
        try:
            tanggal = schedule["tanggal"]   # format dari Flutter: 01-05-2026
            jam = schedule["jam"]           # format dari Flutter: 15:58 atau 03:58 PM
            pesan = schedule["pesan"]
            user_id = schedule["user_id"]

            # 🔥 FIX: Sesuaikan format string dengan data yang masuk
            try:
                # Coba format 24 jam (misal: 15:58)
                # Gunakan %d-%m-%Y karena Flutter mengirim dd-MM-yyyy
                waktu_jadwal = datetime.strptime(
                    f"{tanggal} {jam}", 
                    "%d-%m-%Y %H:%M"
                )
            except ValueError:
                # Jika gagal, coba format 12 jam (misal: 03:58 PM)
                waktu_jadwal = datetime.strptime(
                    f"{tanggal} {jam}", 
                    "%d-%m-%Y %I:%M %p"
                )

            # Cek apakah sudah waktunya (atau sudah lewat)
            if now >= waktu_jadwal:
                user = db.users.find_one({"_id": ObjectId(user_id)})
                
                if not user:
                    continue

                token = get_token(user)
                if token:
                    send_push_notification(token, "Pengingat Jadwal", pesan)
                    
                    # Tandai sudah dikirim agar tidak looping terus
                    db.schedules.update_one(
                        {"_id": schedule["_id"]},
                        {"$set": {"dikirim": True}}
                    )
                    print(f"✅ Notifikasi berhasil dikirim ke {user.get('nama')}")

        except Exception as e:
            print(f"❌ Error memproses jadwal ID {schedule.get('_id')}: {e}")

def get_token(user):
    return user.get("fcmToken") or user.get("tokenFCM") or user.get("token")

from apscheduler.schedulers.background import BackgroundScheduler

from controller.notification_controller import (
    cek_latihan_harian,
    cek_notif_kalkulator
)


def start_scheduler(db):
    scheduler = BackgroundScheduler()

    # =============================
    # 🔥 1. NOTIF LATIHAN HARIAN
    # =============================
    scheduler.add_job(
        cek_latihan_harian,
        "cron",
        hour=17,
        minute=10,
        args=[db]
    )

    # =============================
    # 🔥 2. NOTIF KALKULATOR (TARGET TABUNGAN)
    # =============================
    scheduler.add_job(
        lambda: cek_notif_kalkulator(db),
        "cron",
        hour=17,
        minute=50
    )

    # =============================
    # 🔥 3. JADWAL CUSTOM USER (TERAPI DLL)
    # =============================
    scheduler.add_job(
        lambda: check_schedule(db),
        "interval",
        minutes=1
    )

    scheduler.start()

    print("✅ Semua scheduler aktif:")
    print(" - Latihan harian (17:10)")
    print(" - Notif kalkulator (17:50)")
    print(" - Jadwal user (tiap 1 menit)")