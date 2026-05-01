from bson import ObjectId
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
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

# ==============================
# INDEX
# ==============================
@meditation_bp.route("/admin/meditation")
def index():
    sessions = MeditationSession.find_all()
    return render_template("ruang_napas/index.html", sessions=sessions)

# ==============================
# CREATE
# ==============================
@meditation_bp.route("/admin/meditation/create", methods=["GET","POST"])
def create():
    if request.method == "POST":
        data = {
            "title": request.form["title"],
            "description": request.form["description"],
            "duration": int(request.form.get("duration", 60))
        }
        MeditationSession.create(data)
        return redirect(url_for("meditation_bp.index"))  # ✅ FIX

    return render_template("ruang_napas/create.html")

# ==============================
# EDIT
# ==============================
@meditation_bp.route("/admin/meditation/edit/<id>", methods=["GET","POST"])
def edit(id):
    data = MeditationSession.db["meditation_sessions"].find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        MeditationSession.db["meditation_sessions"].update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "title": request.form["title"],
                "description": request.form["description"],
                "duration": int(request.form.get("duration", 60))
            }}
        )
        return redirect(url_for("meditation_bp.index"))  # ✅ FIX

    data["_id"] = str(data["_id"])
    return render_template("ruang_napas/edit.html", session=data)

# ==============================
# DELETE (Versi Kompatibel dengan Link <a>)
# ==============================
@meditation_bp.route("/admin/meditation/delete/<id>", methods=["GET", "POST"]) # Tambahkan GET di sini
def delete(id):
    MeditationSession.db["meditation_sessions"].delete_one({
        "_id": ObjectId(id)
    })
    
    # Jika permintaan datang dari AJAX/Fetch (seperti SweetAlert)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == "POST":
        return jsonify({"message": "Berhasil dihapus"})
    
    # Jika diakses langsung via link, arahkan kembali ke index
    return redirect(url_for("meditation_bp.index"))