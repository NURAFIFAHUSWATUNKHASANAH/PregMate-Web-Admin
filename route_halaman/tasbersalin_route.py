from flask import Blueprint
from controller.controller_tasbersalin import admin_create_tas, admin_delete_tas, admin_edit_tas, admin_index_tas, toggle_tas_bersalin, get_tas_bersalin

tasbersalin_bp = Blueprint("tasbersalin_bp", __name__)

tasbersalin_bp.route("/tasbersalin/toggle", methods=["POST"])(toggle_tas_bersalin)
tasbersalin_bp.route("/tasbersalin", methods=["GET"])(get_tas_bersalin)

# ================= ADMIN =================
tasbersalin_bp.route("/admin/tas", methods=["GET"])(admin_index_tas)
tasbersalin_bp.route("/admin/tas/create", methods=["GET", "POST"])(admin_create_tas)
tasbersalin_bp.route("/admin/tas/edit/<id>", methods=["GET", "POST"])(admin_edit_tas)
tasbersalin_bp.route("/admin/tas/delete/<id>", methods=["GET"])(admin_delete_tas)