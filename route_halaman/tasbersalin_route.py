from flask import Blueprint
from controller.controller_tasbersalin import (
    add_custom_item, admin_create_tas, admin_delete_tas, 
    admin_edit_tas, admin_index_tas, toggle_tas_bersalin, 
    get_tas_bersalin, delete_tas_bersalin, update_custom_item # <-- 1. Pastikan fungsi delete ini di-import
)

tasbersalin_bp = Blueprint("tasbersalin_bp", __name__)

tasbersalin_bp.route("/tasbersalin/toggle", methods=["POST"])(toggle_tas_bersalin)
tasbersalin_bp.route("/tasbersalin", methods=["GET"])(get_tas_bersalin)
tasbersalin_bp.route("/tasbersalin/add-custom", methods=["POST"])(add_custom_item)

# ================= USER DELETE / HIDE =================
# 2. TAMBAHKAN RUTE INI AGAR FLUTTER BISA MELAKUKAN DELETE DENGAN METHOD 'DELETE'
tasbersalin_bp.route("/tasbersalin/delete/<id>", methods=["DELETE"])(delete_tas_bersalin)

tasbersalin_bp.route('/tasbersalin/update/<string:item_id>', methods=['PUT'])(update_custom_item)

# ================= ADMIN =================
tasbersalin_bp.route("/admin/tas", methods=["GET"])(admin_index_tas)
tasbersalin_bp.route("/admin/tas/create", methods=["GET", "POST"])(admin_create_tas)
tasbersalin_bp.route("/admin/tas/edit/<id>", methods=["GET", "POST"])(admin_edit_tas)
tasbersalin_bp.route("/admin/tas/delete/<id>", methods=["GET"])(admin_delete_tas)
