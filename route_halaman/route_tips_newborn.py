from flask import Blueprint
from controller.controller_tips_newborn import (
    admin_index_tips,
    admin_create_tips,
    admin_edit_tips,
    admin_delete_tips,
    api_get_tips
)

tips_bp = Blueprint("tips_bp", __name__)

# ================= API =================
tips_bp.route("/tips-newborn", methods=["GET"])(api_get_tips)

# ================= ADMIN =================
tips_bp.route("/admin/tips-newborn", methods=["GET"])(admin_index_tips)
tips_bp.route("/admin/tips-newborn/create", methods=["GET", "POST"])(admin_create_tips)
tips_bp.route("/admin/tips-newborn/edit/<id>", methods=["GET", "POST"])(admin_edit_tips)
tips_bp.route("/admin/tips-newborn/delete/<id>", methods=["GET"])(admin_delete_tips)