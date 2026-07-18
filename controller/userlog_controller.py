from flask import jsonify, render_template, request
from models.userlog_model import UserLog
from bson import ObjectId
from flask import redirect, url_for
userlog_model = None
db = None  # simpan juga db di sini

def set_db(database):
    global userlog_model, db
    db = database
    userlog_model = UserLog(database)

def get_all_user_logs():
    # 1. Tangkap parameter pencarian dari input text web
    search_query = request.args.get('search', '').strip()
    
    # 2. Bangun filter kondisi untuk MongoDB
    query_filter = {}
    if search_query:
        query_filter = {
            "$or": [
                {"action": {"$regex": search_query, "$options": "i"}},
                {"status": {"$regex": search_query, "$options": "i"}},
                {"keterangan": {"$regex": search_query, "$options": "i"}},
                {"user_id": {"$regex": search_query, "$options": "i"}}
            ]
        }

    # 3. Ambil data logs berdasarkan filter (urutkan dari yang terbaru)
    logs = list(userlog_model.collection.find(query_filter).sort("timestamp", -1))
    
    # 4. Ambil nama user dari koleksi users berdasarkan user_id
    for log in logs:
        user_id = log.get("user_id")
        if user_id:
            try:
                user = db["users"].find_one({"_id": ObjectId(user_id)})
                if user:
                    log["user_name"] = f"{user.get('nama', '')} {user.get('nama_belakang', '')}".strip()
                else:
                    log["user_name"] = "Tidak Diketahui"
            except Exception:
                log["user_name"] = "Tidak Diketahui"
        else:
            log["user_name"] = "Tidak Diketahui"
            
        # Skenario tambahan jika admin mencari berdasarkan Nama User yang dicatatkan di database lain
        # Jika nama user tidak cocok dengan pencarian teks, namun query_filter aktif, kita bisa biarkan mengalir.
    
    return render_template("histori_user.html", logs=logs, search_query=search_query)


def delete_log_by_id(log_id):
    try:
        userlog_model.collection.delete_one({"_id": ObjectId(log_id)})
    except Exception as e:
        print(f"Error deleting log: {e}")
    return redirect(url_for("histori_user_bp.histori_user_page"))