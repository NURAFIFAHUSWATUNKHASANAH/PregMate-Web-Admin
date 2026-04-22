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
    schedules = db.schedules.find({"dikirim": {"$ne": True}})  # hanya yang belum dikirim

    for schedule in schedules:
        try:
            tanggal = schedule["tanggal"]
            jam = schedule["jam"]
            pesan = schedule["pesan"]
            user_id = schedule["user_id"]

            # Gabungkan tanggal dan jam menjadi datetime
            waktu_jadwal = datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")

            # Jika waktu sekarang >= jadwal dan belum dikirim
            if now >= waktu_jadwal:
                user = db.users.find_one({"_id": ObjectId(user_id)})
                if user and "token" in user:
                    token = user["token"]
                    send_push_notification(token, "Pengingat Terapi", pesan)

                    # Update agar tidak dikirim dua kali
                    db.schedules.update_one({"_id": schedule["_id"]}, {"$set": {"dikirim": True}})
                else:
                    print(f"⚠️ Token tidak ditemukan untuk user {user_id}")
        except Exception as e:
            print(f"❌ Error memproses jadwal: {e}")

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