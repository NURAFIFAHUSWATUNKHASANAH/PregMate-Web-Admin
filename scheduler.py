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
    schedules = db.schedules.find({"dikirim": {"$ne": True}})

    for schedule in schedules:
        try:
            tanggal = schedule["tanggal"]
            jam = schedule["jam"]
            pesan = schedule["pesan"]
            user_id = schedule["user_id"]

            waktu_jadwal = datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")

            if now >= waktu_jadwal:

                user = db.users.find_one({"_id": ObjectId(user_id)})

                if not user:
                    print(f"❌ User tidak ditemukan: {user_id}")
                    continue

                token = get_token(user)

                if not token:
                    print(f"⚠️ Token kosong untuk user {user_id}")
                    continue

                send_push_notification(token, "Pengingat", pesan)

                db.schedules.update_one(
                    {"_id": schedule["_id"]},
                    {"$set": {"dikirim": True}}
                )

        except Exception as e:
            print(f"❌ Error memproses jadwal: {e}")

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