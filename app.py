# ============================== IMPORT DAN SETUP DASAR ==============================

from datetime import datetime

from flask import Flask, redirect, url_for, session, flash, jsonify, Blueprint, render_template, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from flask.json.provider import DefaultJSONProvider
from pymongo import MongoClient
from bson import ObjectId
import secrets
import os
from ai_recommendation import generate_recommendation
import config

# Firebase & Scheduler (aktifkan jika kamu pakai)
from controller import controller_admin_user
from controller.pregnancy_controller import dashboard_kehamilan, dashboard_kehamilan_pasangan, submit_validasi_kehamilan, update_kehamilan
from firebase_init import init_firebase
from models.craving_model import Craving
from models.data_kehamilan_model import DataKehamilan
from scheduler import start_scheduler
from route_halaman.route_meditation import meditation_bp, set_db as set_meditation_db
from ai_babyname import generate_baby_name
# ============================== KONVERSI ObjectId AGAR BISA DI JSONIFY ==============================

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# ============================== FLASK APP SETUP ==============================

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.secret_key = secrets.token_hex(16)
app.json = CustomJSONProvider(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# JWT Configuration
app.config['JWT_SECRET_KEY'] = '12345'
jwt = JWTManager(app)

# ============================== DATABASE SETUP ==============================

client = MongoClient("mongodb://localhost:27017/")
db = client["capstone"]
users_collection = db["users"]
schedule_collection = db["schedules"]
data_kehamilan_collection = db["data_kehamilan"]
babyname_collection = db["favorite_babynames"]
mood_ibu_hamil_collection = db["mood_ibu_hamil"]
cravings_collection = db["cravings"]

# ============================== IMPORT MODEL & CONTROLLER ==============================

# Models
from models.admin_model import Admin
from models.datauser_model import User

# Controllers
import controller.controller_keluhan as controller_keluhan
import controller.controller_register as controller_register
import controller.controller_login as controller_login
import controller.controller_terapi as controller_terapi
import controller.controller_datauser as controller_datauser
import controller.controller_artikel as controller_artikel
from controller.controller_jadwal import jadwal_bp, set_db as set_jadwal_db
from route_halaman.route_histori import histori_bp, set_db as set_histori_db
from controller.userlog_controller import set_db as set_userlog_db
from route_halaman.route_diskusi import diskusi_bp
from controller.controller_diskusi import set_db as set_diskusi_db
from route_halaman.route_beratbadan import berat_badan_bp, set_db as set_berat_db
from route_halaman.route_informasi import informasi_bp, set_db as set_informasi_db
from controller.notification_controller import kirim_notif_mood, kirim_notif_pendamping, kirim_notif_relaksasi, set_db as set_notif_db
from route_halaman.route_admin_user import admin_user
from models.craving_model import Craving
from route_halaman.route_kalkulator import kalkulator_bp
from models.kalkulator_model import KalkulatorModel


set_userlog_db(db)
# Set DB di controller dan model
User.set_db(db)
Admin.set_db(db)
controller_artikel.set_db(db)
controller_keluhan.set_db(db)
controller_register.set_db(db)
controller_login.set_db(db)
controller_terapi.set_db(db)
controller_datauser.set_db(db)
controller_admin_user.set_db(db)
set_histori_db(db)
set_jadwal_db(db)
set_diskusi_db(db)
DataKehamilan.set_db(db)
set_berat_db(db)
set_meditation_db(db)
set_informasi_db(db)
set_notif_db(db)
Craving.set_db(db)
KalkulatorModel.set_db(db)

# ============================== BLUEPRINT REGISTRASI ==============================

def register_blueprints():
    from route_halaman.route_admin import admin_bp
    from route_halaman.route_keluhan import keluhan_bp
    from route_halaman.route_register import register_bp
    from route_halaman.route_login import login_bp
    from route_halaman.route_histori import histori_bp
    from route_halaman.route_terapi import terapi_bp
    from route_halaman.route_datauser import datauser_bp
    from route_halaman.route_artikel import artikel_bp
    from route_halaman.forgot_password_route import forgot_password_bp
    from route_halaman.histori_user_route import histori_user_bp
    from route_halaman.route_dashboard import dashboard_bp
    from route_halaman.route_informasi import informasi_bp
    from route_halaman.craving_route import craving_bp
    app.register_blueprint(histori_user_bp)

    app.register_blueprint(forgot_password_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(artikel_bp, url_prefix='/api')
    app.register_blueprint(keluhan_bp)
    app.register_blueprint(register_bp, url_prefix='/auth')
    app.register_blueprint(login_bp, url_prefix='/auth')
    app.register_blueprint(terapi_bp)
    app.register_blueprint(datauser_bp,)
    app.register_blueprint(jadwal_bp)
    app.register_blueprint(histori_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(diskusi_bp)
    app.register_blueprint(berat_badan_bp, url_prefix="/berat_badan")
    app.register_blueprint(meditation_bp)
    app.register_blueprint(informasi_bp)
    app.register_blueprint(admin_user)
    app.register_blueprint(craving_bp, url_prefix="/api")
    app.register_blueprint(kalkulator_bp)
    
register_blueprints()

# ============================== ROUTES UTAMA ==============================

@app.route('/')
def home():
    return render_template('landingpage.html')

@app.route('/keluhan')
def index_keluhan():
    return controller_keluhan.index_keluhan()

@app.route("/ai/recommendation", methods=["POST"])
def ai_recommendation():
    data = request.json

    user_id = data.get("user_id")

    energi = data.get("energy")
    mual = data.get("nausea")
    nyeri = data.get("pain")
    tidur = data.get("sleep")
    nafsu_makan = data.get("appetite")

    try:
        # ================= AI RECOMMENDATION =================
        result = generate_recommendation(
            energi,
            mual,
            nyeri,
            tidur,
            nafsu_makan
        )

        # ================= SIMPAN KE DATABASE =================
        record = {
            "user_id": ObjectId(user_id) if user_id else None,
            "energi": energi,
            "mual": mual,
            "nyeri": nyeri,
            "tidur": tidur,
            "nafsu_makan": nafsu_makan,
            "recommendation": result,
            "created_at": datetime.utcnow()
        }

        mood_ibu_hamil_collection.insert_one(record)

        # ================= KIRIM NOTIF =================
        try:
            if user_id:
                # 🔥 Ringkas hasil AI (biar tidak kepanjangan)
                short_recommendation = (
                    result[:200] + "..."
                    if len(result) > 200 else result
                )

                pesan = (
                    f"Energi {energi}/10 | Mual {mual}/10 | Nyeri {nyeri}/10\n\n"
                    f"Analisis:\n{short_recommendation}"
                )

                kirim_notif_mood(user_id, pesan)

        except Exception as notif_error:
            print("Notif gagal:", notif_error)

        # ================= RESPONSE =================
        return jsonify({
            "status": "success",
            "recommendation": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
    
@app.route('/pregnancy/validate', methods=['POST'])
def validate():
    return submit_validasi_kehamilan()

@app.route('/pregnancy/dashboard', methods=['GET'])
def dashboard():
    return dashboard_kehamilan()

@app.route('/pregnancy/dashboard/pasangan', methods=['GET'])
@jwt_required()
def dashboard_pasangan():
    return dashboard_kehamilan_pasangan()

@app.route('/pregnancy/update', methods=['PUT'])
@jwt_required()
def updatedatahamil():
    return update_kehamilan()

@app.route("/ai/babyname", methods=["POST"])
def ai_babyname():

    data = request.json

    keyword = data.get("keyword")
    category = data.get("category")
    gender = data.get("gender")

    try:

        result = generate_baby_name(keyword, category, gender)

        return jsonify({
            "status": "success",
            "names": result
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })
    
@app.route("/babyname/favorite", methods=["POST"])
@jwt_required()
def save_favorite_babyname():

    user_id = get_jwt_identity()
    data = request.json

    name = data.get("name", "").strip()

    # 🔥 ambil user
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    # ✅ FIX: pastikan owner_id selalu ObjectId
    partner_id = user.get("partner_id") if user else None

    if partner_id:
        owner_id = ObjectId(partner_id)
    else:
        owner_id = ObjectId(user_id)

    # cek existing
    existing = babyname_collection.find_one({
        "user_id": owner_id,
        "name": name
    })

    if existing:
        return jsonify({
            "status": "error",
            "message": "Nama sudah ada di favorit"
        }), 400

    babyname_collection.insert_one({
        "user_id": owner_id,              # 🔥 FIX CONSISTENT OBJECTID
        "created_by": ObjectId(user_id),  # siapa yang menyimpan
        "name": name,
        "meaning": data.get("meaning"),
        "category": data.get("category"),
        "gender": data.get("gender"),
        "created_at": datetime.utcnow()
    })

    return jsonify({
        "status": "success",
        "message": "Nama bayi berhasil disimpan"
    })

@app.route("/babyname/favorite", methods=["GET"])
@jwt_required()
def get_babyname_favorites():
    current_user_id = get_jwt_identity()  # user_id dari token

    # Ambil pasangan jika ada (misal disimpan di users_collection)
    user_doc = users_collection.find_one({"_id": ObjectId(current_user_id)})
    pasangan_id = user_doc.get("partner_id") if user_doc else None

    query_filter = {
        "$or": [
            {"user_id": ObjectId(current_user_id)},          # Favorit milik sendiri
            {"created_by": ObjectId(current_user_id)},       # Favorit yang dibuat untuk user
        ]
    }

    # Jika ada pasangan, ambil juga favorit pasangan
    if pasangan_id:
        query_filter["$or"].extend([
            {"user_id": ObjectId(pasangan_id)},
            {"created_by": ObjectId(pasangan_id)},
        ])

    favorites = list(babyname_collection.find(query_filter).sort("created_at", -1))

    # Format response
    result = []
    for fav in favorites:
        result.append({
            "id": str(fav["_id"]),
            "name": fav["name"],
            "meaning": fav["meaning"],
            "category": fav.get("category"),
            "gender": fav.get("gender"),
            "created_by": str(fav.get("created_by")),
            "user_id": str(fav.get("user_id")),
            "created_at": fav.get("created_at").isoformat() if fav.get("created_at") else None
        })

    return jsonify({"status": "success", "data": result})

@app.route("/babyname/favorite/<name>", methods=["DELETE"])
@jwt_required()
def delete_favorite_babyname(name):

    user_id = get_jwt_identity()
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    partner_id = user.get("partner_id") if user else None

    filter_query = {
        "$or": [
            {"user_id": ObjectId(user_id)},
            {"created_by": ObjectId(user_id)}
        ]
    }

    if partner_id:
        filter_query["$or"].extend([
            {"user_id": ObjectId(partner_id)},
            {"created_by": ObjectId(partner_id)}
        ])

    # Cari dokumen yang cocok berdasarkan nama (case-insensitive)
    result = babyname_collection.delete_one({
        **filter_query,
        "name": {"$regex": f"^{name.strip()}$", "$options": "i"}
    })

    if result.deleted_count == 0:
        return jsonify({
            "status": "error",
            "message": "Nama tidak ditemukan"
        }), 404

    return jsonify({
        "status": "success",
        "message": "Berhasil dihapus"
    })

@app.route("/save-fcm-token", methods=["POST"])
@jwt_required()
def save_fcm_token():

    user_id = get_jwt_identity()
    data = request.get_json()

    token = data.get("token")

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"fcmToken": token}}
    )

    return jsonify({
        "status": "success",
        "message": "FCM token saved"
    })

@app.route('/kirim_notif_relaksasi', methods=['POST'])
def api_kirim_notif_relaksasi():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        label = data.get("label")
        durasi = data.get("durasi")

        kirim_notif_relaksasi(user_id, label, durasi)

        return jsonify({
            "status": "success",
            "message": "Notif relaksasi berhasil dikirim"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# ============================== RUN APLIKASI ==============================

if __name__ == '__main__':
    init_firebase()        # aktifkan jika kamu gunakan Firebase Admin SDK
    start_scheduler(db)    # aktifkan jika kamu gunakan fitur penjadwalan
    app.run(host='0.0.0.0', port=5000, debug=True)
