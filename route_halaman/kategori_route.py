from flask import Blueprint

from controller.controller_kategori import create, delete, edit, index


kategori_bp = Blueprint('kategori_bp', __name__)

kategori_bp.route("/admin/kategori/index")(index)
kategori_bp.route("/admin/kategori/create", methods=["POST","GET"])(create)
kategori_bp.route("/admin/kategori/edit", methods=["POST","GET"])(edit)
kategori_bp.route("/admin/kategori/delete")(delete)
