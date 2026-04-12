# route_halaman/route_histori.py

from flask import Blueprint, request, jsonify
from controller import controller_histori
from flask_jwt_extended import jwt_required, get_jwt_identity

# import notifikasi
from controller.notification_controller import kirim_notif_pendamping

histori_bp = Blueprint('histori', __name__, url_prefix='/histori')


def set_db(database):
    controller_histori.set_db(database)

# =========================
# GET HISTORI PER KEHAMILAN
# =========================
@histori_bp.route('/<user_id>/<kehamilan_id>', methods=['GET'])
@jwt_required()
def get_user_histori(user_id, kehamilan_id):

    jwt_user = get_jwt_identity()

    if jwt_user != user_id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 403

    return controller_histori.get_histori(user_id, kehamilan_id)


# =========================
# GET STATISTIK PER KEHAMILAN
# =========================
@histori_bp.route('/stats/<user_id>/<kehamilan_id>', methods=['GET'])
@jwt_required()
def get_histori_stats(user_id, kehamilan_id):

    jwt_user = get_jwt_identity()

    if jwt_user != user_id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 403

    user_histori = controller_histori.get_histori_by_user(user_id, kehamilan_id)

    total = len(user_histori)

    avg_accuracy = (
        sum(h.get("accuracy", 0) for h in user_histori) / total
        if total > 0 else 0
    )

    return jsonify({
        "status": "success",
        "total": total,
        "avg_accuracy": avg_accuracy
    })



# =========================
# POST HISTORI BARU
# =========================
@histori_bp.route('', methods=['POST'])
@jwt_required()
def create_histori():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Data kosong"
        }), 400

    jwt_user = get_jwt_identity()

    # validasi user
    if jwt_user != data.get("user_id"):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 403

    # wajib ada kehamilan_id
    if not data.get("kehamilan_id"):
        return jsonify({
            "status": "error",
            "message": "kehamilan_id wajib"
        }), 400

    result, status = controller_histori.save_histori(data)

    if status == 201:
        try:
            kirim_notif_pendamping(
                data["user_id"],
                data["label"],
                data["accuracy"],
                data["kehamilan_id"]
            )
        except Exception as e:
            print("Notif gagal:", e)

    return jsonify(result), status

# =========================
# GET HISTORI BY KEHAMILAN (UNTUK FLUTTER)
# =========================
@histori_bp.route('/by-kehamilan/<kehamilan_id>', methods=['GET'])
@jwt_required()
def get_histori_by_kehamilan(kehamilan_id):

    user_id = get_jwt_identity()

    return controller_histori.get_histori(user_id, kehamilan_id)