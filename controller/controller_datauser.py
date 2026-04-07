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

    # Ambil data JSON
    data = request.get_json()

    nama = data.get("nama") if data else None
    email = data.get("email") if data else None
    password = data.get("password") if data else None

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Validasi password minimal 6 karakter jika diisi
    if password and len(password) < 6:
        return jsonify({"message": "Password minimal 6 karakter"}), 400

    # Gunakan data lama jika field kosong
    updated_nama = nama if nama else user['nama']
    updated_email = email if email else user['email']
    updated_password = generate_password_hash(password) if password else user['password']
    updated_foto = user.get('foto', None)

    foto_diganti = False

    # Jika ada upload file foto
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            updated_foto = f"{UPLOAD_URL_PATH}/{filename}"
            foto_diganti = True

    # Update ke database
    updated_user = User.update(
        user_id,
        updated_nama,
        updated_email,
        updated_password,
        updated_foto
    )

    if not updated_user:
        return jsonify({"message": "Update failed"}), 500

    # Logging perubahan
    logger = UserLog(db)
    changes = []

    if nama and nama != user['nama']:
        changes.append("nama")

    if email and email != user['email']:
        changes.append("email")

    if password:
        changes.append("password")

    if foto_diganti:
        changes.append("foto")

    action_detail = ", ".join(changes) if changes else "tidak ada perubahan"

    logger.log_activity(
        user_id,
        action="update_profile",
        status="success",
        keterangan=f"Update: {action_detail}"
    )

    user_updated = User.find_by_id(user_id)
    user_updated["_id"] = str(user_updated["_id"])

    return jsonify(user_updated), 200
# ======================= UPLOAD FOTO PROFILE =======================
@jwt_required()
def upload_profile_picture(user_id):
    print("Headers:", request.headers)
    print("JWT Identity:", get_jwt_identity())
    print("JWT Payload:", get_jwt())
    current_user_id = get_jwt_identity()
    if str(current_user_id) != str(user_id):
        return jsonify({"message": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']  # pastikan nama field 'file'
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # update field foto di DB
        updated_foto = f"{UPLOAD_URL_PATH}/{filename}"
        updated_user = User.update(user_id, user['nama'], user['email'], user['password'], updated_foto)
        if not updated_user:
            return jsonify({"message": "Failed to update user profile picture"}), 500

        # Logging
        logger = UserLog(db)
        logger.log_activity(user_id, action="update_profile_picture", status="success", keterangan=f"Foto profil diperbarui: {filename}")

        return jsonify({"message": "Profile picture updated", "filename": filename, "foto": updated_foto}), 200

    return jsonify({'message': 'File type not allowed'}), 400
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
