from flask import Blueprint, render_template
from models.datauser_model import User
from controller.controller_artikel import artikel_collection
from models.tips_newborn_model import TipsNewbornModel
from models.userlog_model import UserLog

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():

    # =====================
    # TOTAL USER
    # =====================
    total_user = len(User.find_all())

    # =====================
    # TOTAL ARTIKEL
    # =====================
    total_artikel = artikel_collection.count_documents({})

    # =====================
    # TOTAL TIPS NEWBORN
    # =====================
    total_tips = TipsNewbornModel.collection.count_documents({})

    # =====================
    # AKTIVITAS TERAKHIR (USER LOG)
    # =====================
    log_model = UserLog(User.db)
    logs_raw = log_model.get_all_logs()[:5]  # ambil 5 terbaru

    activities = []

    for log in logs_raw:
        user = User.db["users"].find_one({"_id": log.get("user_id")})

        activities.append({
            "user": user.get("nama") if user else "Unknown",
            "avatar": f"https://ui-avatars.com/api/?name={user.get('nama') if user else 'User'}&background=random",
            "action": log.get("action"),
            "status": log.get("status"),
            "tanggal": log.get("timestamp").strftime("%d %b %Y") if log.get("timestamp") else "-"
        })

    stats = {
        "total_user": total_user,
        "total_artikel": total_artikel,
        "total_tips": total_tips
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        activities=activities
    )