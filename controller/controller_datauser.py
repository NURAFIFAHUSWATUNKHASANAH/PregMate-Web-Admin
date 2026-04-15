from flask import request, jsonify, url_for
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from models.datauser_model import User
from models.userlog_model import UserLog
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import os
import hashlib
from werkzeug.security import generate_password_hash

UPLOAD_FOLDER = os.path.join('static', 'images', 'Profile')
UPLOAD_URL_PATH = 'static/images/Profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def set_db(database):
    global db
    db = database

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@jwt_required()
def users():
    all_users = User.find_all()
    for user in all_users:
        user["_id"] = str(user["_id"])
    return jsonify(all_users), 200

@jwt_required()
def user_detail(id):
    user = User.find_by_id(id)
    if user:
        user["_id"] = str(user["_id"])
        return jsonify(user), 200
    return jsonify({"message": "User not found"}), 404

@jwt_required()
def user_create():
    data = request.get_json()
    nama = data.get("nama")
    email = data.get("email")
    password = data.get("password")
    foto = data.get("foto")

    if not nama or not email or not password:
        return jsonify({"message": "Data tidak lengkap"}), 400

    user_id = User.create(nama, email, password, foto)
    return jsonify({"message": "User created", "user_id": str(user_id)}), 201

@jwt_required()
def user_delete(id):
    user = User.find_by_id(id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    User.delete_user(id)
    return jsonify({"message": "User deleted"}), 200

# ======================= UPDATE PROFILE =======================
@jwt_required()
def update_user_profile(user_id):
    current_user_id = get_jwt_identity()
    if str(current_user_id) != str(user_id):
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    nama = data.get("nama") if data else None
    phone = data.get("phone") if data else None
    password = data.get("password") if data else None

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # VALIDASI PASSWORD
    if password and len(password) < 6:
        return jsonify({"message": "Password minimal 6 karakter"}), 400

    # DEFAULT VALUE
    updated_nama = nama if nama else user.get("nama")
    updated_phone = phone if phone is not None else user.get('phone')
    updated_password = user["password"]

    if password:
        updated_password = generate_password_hash(password)

    updated_foto = user.get("foto")

    # UPLOAD FOTO (optional)
    foto_diganti = False
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            updated_foto = f"{UPLOAD_URL_PATH}/{filename}"
            foto_diganti = True

    # UPDATE DB
    updated_user = User.update(
        user_id,
        updated_nama,
        updated_phone,
        updated_password,
        updated_foto
    )

    if not updated_user:
        return jsonify({"message": "Update failed"}), 500

    # LOGGING
    logger = UserLog(db)
    changes = []

    if nama and nama != user.get("nama"):
        changes.append("nama")

    if phone and phone != user.get("phone"):
        changes.append("phone")   # ✅ FIXED

    if password:
        changes.append("password")

    if foto_diganti:
        changes.append("foto")

    logger.log_activity(
        user_id,
        action="update_profile",
        status="success",
        keterangan=f"Update: {', '.join(changes) if changes else 'tidak ada perubahan'}"
    )

    user_updated = User.find_by_id(user_id)
    user_updated["_id"] = str(user_updated["_id"])

    return jsonify(user_updated), 200

# ======================= UPLOAD FOTO PROFILE =======================
@jwt_required()
def upload_profile_picture(user_id):
    current_user_id = get_jwt_identity()
    if str(current_user_id) != str(user_id):
        return jsonify({"message": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # save file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{secure_filename(file.filename)}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    updated_foto = f"{UPLOAD_URL_PATH}/{filename}"

    # ✅ FIX INI PENTING (JANGAN PAKAI email)
    updated_user = User.update(
        user_id,
        user.get("nama"),
        user.get("phone"),        # ✅ bukan email
        user.get("password"),
        updated_foto
    )

    if not updated_user:
        return jsonify({"message": "Failed update profile picture"}), 500

    # log
    logger = UserLog(db)
    logger.log_activity(
        user_id,
        action="update_profile_picture",
        status="success",
        keterangan=f"Foto profil diperbarui: {filename}"
    )

    return jsonify({
        "message": "Profile picture updated",
        "foto": updated_foto
    }), 200

def update_token():
    data = request.get_json()
    user_id = data.get('user_id')
    token = data.get('token')

    if not user_id or not token:
        return jsonify({'message': 'User ID atau token kosong'}), 400

    try:
        from app import db
        users_collection = db['users']
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'message': 'User tidak ditemukan'}), 404

        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'tokenFCM': token}})
        return jsonify({'message': 'Token berhasil diperbarui'}), 200
    except Exception as e:
        return jsonify({'message': f'Gagal memperbarui token: {str(e)}'}), 500
