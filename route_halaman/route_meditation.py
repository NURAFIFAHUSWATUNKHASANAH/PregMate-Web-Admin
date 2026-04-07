from flask import Blueprint, jsonify
from models.meditation_model import MeditationSession

meditation_bp = Blueprint("meditation_bp", __name__)

def set_db(database):
    MeditationSession.set_db(database)


# ==============================
# GET SEMUA SESI MEDITASI
# ==============================

@meditation_bp.route("/meditation_sessions", methods=["GET"])
def get_meditation_sessions():

    try:

        data = MeditationSession.find_all()

        result = []

        for d in data:

            result.append({
                "id": str(d["_id"]),
                "title": d.get("title"),
                "description": d.get("description"),
                "duration": d.get("duration", 60)
            })

        return jsonify(result)

    except Exception as e:

        print(e)

        return jsonify({
            "message": "Terjadi kesalahan"
        }), 500