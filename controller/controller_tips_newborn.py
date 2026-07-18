from flask import request, jsonify, render_template, redirect, url_for, current_app
from models.tips_newborn_model import TipsNewbornModel
from werkzeug.utils import secure_filename
import os
from bson import ObjectId


# ================= ADMIN INDEX (WITH SEARCH) =================
def admin_index_tips():
    # 1. Ambil parameter search dari URL
    search_query = request.args.get('search', '').strip()
    
    # 2. Kondisikan query MongoDB (Mencari berdasarkan Judul atau Deskripsi)
    query_filter = {}
    if search_query:
        query_filter = {
            "$or": [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"desc": {"$regex": search_query, "$options": "i"}}
            ]
        }
        
    # Jika model Anda mendukung parameter filter, masukkan query_filter ke dalamnya.
    # Jika tidak, Anda bisa memanggil: TipsNewbornModel.collection.find(query_filter)
    # Di sini diasumsikan model Anda fleksibel atau Anda memanggil collection langsung:
    try:
        collection = TipsNewbornModel.collection
        data = list(collection.find(query_filter))
    except AttributeError:
        # Fallback menggunakan method bawaan model jika find global sudah di-override
        data = TipsNewbornModel.get_all() # Sesuaikan jika get_all bisa menerima filter

    tips = []
    for d in data:
        video = d.get("video")
        tips.append({
            "id": str(d["_id"]),
            "title": d.get("title", ""),
            "desc": d.get("desc", ""),
            "video_url": f"/static/videos/{video}" if video else None
        })

    return render_template("tips_newborn/index.html", tips=tips, search_query=search_query)

# ================= CREATE =================
def admin_create_tips():
    if request.method == "POST":

        video_file = request.files.get("video")

        if not video_file:
            return "Video wajib diupload", 400

        filename = secure_filename(video_file.filename)

        upload_folder = current_app.config["UPLOAD_VIDEO"]

        # 🔥 FIX: auto create folder biar tidak error
        os.makedirs(upload_folder, exist_ok=True)

        upload_path = os.path.join(upload_folder, filename)
        try:
            video_file.save(upload_path)
        except Exception as e:
            return f"Upload error: {str(e)}", 500

        steps = request.form.getlist("steps[]")

        TipsNewbornModel.create({
            "title": request.form["title"],
            "desc": request.form["desc"],
            "video": filename,
            "steps": steps
        })

        return redirect(url_for("tips_bp.admin_index_tips"))

    return render_template("tips_newborn/create.html")


# ================= EDIT =================
def admin_edit_tips(id):
    item = TipsNewbornModel.get_by_id(id)

    if request.method == "POST":

        video_file = request.files.get("video")

        # default pakai video lama
        filename = item.get("video")

        upload_folder = current_app.config["UPLOAD_VIDEO"]
        os.makedirs(upload_folder, exist_ok=True)

        # kalau upload video baru
        if video_file and video_file.filename != "":
            filename = secure_filename(video_file.filename)
            video_file.save(os.path.join(upload_folder, filename))

        # ================= FIX STEPS =================
        # ambil dari textarea (string panjang)
        steps_raw = request.form.get("steps[]", "")

        # pecah jadi array berdasarkan enter
        steps = [s.strip() for s in steps_raw.split("\n") if s.strip()]
        # =================================================

        TipsNewbornModel.update(id, {
            "title": request.form["title"],
            "desc": request.form["desc"],
            "video": filename,
            "steps": steps
        })

        return redirect(url_for("tips_bp.admin_index_tips"))

    return render_template("tips_newborn/edit.html", item=item)

# ================= DELETE =================
def admin_delete_tips(id):
    TipsNewbornModel.delete(id)
    return redirect(url_for("tips_bp.admin_index_tips"))


# ================= API =================
from flask import request

def api_get_tips():
    data = TipsNewbornModel.get_all()

    base_url = request.host_url.rstrip("/")

    result = []
    for d in data:
        result.append({
            "id": str(d["_id"]),
            "title": d["title"],
            "desc": d["desc"],
            "video_url": f"{base_url}/static/videos/{d['video']}",
            "steps": d.get("steps", [])
        })

    return jsonify(result)