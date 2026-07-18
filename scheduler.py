from apscheduler.schedulers.background import BackgroundScheduler
from firebase_admin import messaging
from datetime import datetime
from bson import ObjectId
from zoneinfo import ZoneInfo

from controller.controller_companion import generate_daily_static_plan
from controller.notification_controller import (
    cek_latihan_harian,
    cek_notif_checkin,
    cek_notif_kalkulator,
    kirim_notif_agenda_statis
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

    now = datetime.now(ZoneInfo("Asia/Jakarta"))

    schedules = db.schedules.find({
        "dikirim": {"$ne": True}
    })

    for schedule in schedules:

        try:

            tanggal = schedule["tanggal"]
            jam = schedule["jam"]
            pesan = schedule["pesan"]
            user_id = schedule["user_id"]

            # ============================
            # PARSE WAKTU
            # ============================

            try:
                waktu_jadwal = datetime.strptime(
                    f"{tanggal} {jam}",
                    "%d-%m-%Y %H:%M"
                )
            except ValueError:
                waktu_jadwal = datetime.strptime(
                    f"{tanggal} {jam}",
                    "%d-%m-%Y %I:%M %p"
                )

            waktu_jadwal = waktu_jadwal.replace(
                tzinfo=ZoneInfo("Asia/Jakarta")
            )

            print("=======================")
            print("NOW :", now)
            print("JADWAL :", waktu_jadwal)
            print("=======================")

            if now >= waktu_jadwal:

                if not ObjectId.is_valid(user_id):
                    print("User ID tidak valid")
                    continue

                user = db.users.find_one({
                    "_id": ObjectId(user_id)
                })

                if not user:
                    print("User tidak ditemukan")
                    continue

                token = (
                    user.get("fcmToken")
                    or user.get("tokenFCM")
                    or user.get("token")
                )

                if not token:
                    print("Token kosong")
                    continue

                send_push_notification(
                    token,
                    "Pengingat Jadwal",
                    pesan
                )

                db.schedules.update_one(
                    {"_id": schedule["_id"]},
                    {
                        "$set": {
                            "dikirim": True
                        }
                    }
                )

                print("✅ Pengingat berhasil dikirim")

        except Exception as e:
            print("ERROR CHECK SCHEDULE :", e)
            
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

    # =============================
    # NOTIF CHECK-IN
    # =============================
    scheduler.add_job(
        lambda: cek_notif_checkin(db),
        "interval",
        minutes=30
    )
    
    scheduler.start()

    print("✅ Semua scheduler aktif:")
    print(" - Latihan harian (17:10)")
    print(" - Notif kalkulator (17:50)")
    print(" - Jadwal user (tiap 1 menit)")

def cek_dan_kirim_fcm_agenda(database):
    try:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_str = now.strftime("%Y-%m-%d")

        start_date = datetime.strptime(f"{today_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(f"{today_str} 23:59:59", "%Y-%m-%d %H:%M:%S")

        # UBAH: dari 'agenda_hari_ini' menjadi 'agenda'
        active_plans = list(database["companion_plans"].find({
            "tanggal_jurnal": {"$gte": start_date, "$lte": end_date},
            "agenda": {
                "$elemMatch": {
                    "jam": current_time_str,
                    "done": False,
                    "notif_sent": {"$ne": True}
                }
            }
        }))

        for plan in active_plans:
            user_doc = database["users"].find_one({"_id": plan["user_id"]})
            if not user_doc: continue

            # UBAH: ambil dari 'agenda'
            updated_agenda = plan["agenda"]
            any_update = False

            for task in updated_agenda:
                if task["jam"] == current_time_str and not task["done"] and not task.get("notif_sent"):
                    notif_ok = kirim_notif_agenda_statis(user_doc, task["tugas"], task["jam"])
                    if notif_ok:
                        task["notif_sent"] = True
                        any_update = True

            if any_update:
                # UBAH: update field 'agenda'
                database["companion_plans"].update_one(
                    {"_id": plan["_id"]},
                    {"$set": {"agenda": updated_agenda, "updated_at": datetime.utcnow()}}
                )
    except Exception as e:
        print(f"Error pada Background Scheduler Agenda: {e}")

def start_companion_scheduler(database):

    scheduler = BackgroundScheduler()


    # Buat agenda umum semua user jam 00:00
    scheduler.add_job(
        func=generate_daily_static_plan,
        trigger="cron",
        hour=0,
        minute=0,
        args=[database],
        id="generate_daily_companion_plan",
        replace_existing=True
    )


    # Cek notif agenda tiap menit
    scheduler.add_job(
        func=cek_dan_kirim_fcm_agenda,
        trigger="interval",
        minutes=1,
        args=[database],
        id="companion_level1_job",
        replace_existing=True
    )


    # Jika backend baru hidup siang hari
    generate_daily_static_plan(database)


    scheduler.start()


    print("====================================")
    print("✅ Companion Scheduler Aktif")
    print("Generate Plan Umum : 00:00")
    print("Cek Agenda FCM     : tiap 1 menit")
    print("====================================")