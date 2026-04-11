from flask import Blueprint
from flask_jwt_extended import jwt_required

from controller.controller_kalkulator import (
    save_kalkulator,
    get_dashboard,
    tambah_tabungan,
    tambah_pengeluaran
)

kalkulator_bp = Blueprint("kalkulator", __name__)

# ================= ROUTES =================

@kalkulator_bp.route("/kalkulator/save", methods=["POST"])
@jwt_required()
def save():
    return save_kalkulator()


@kalkulator_bp.route("/kalkulator/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    return get_dashboard()


@kalkulator_bp.route("/kalkulator/tabung", methods=["POST"])
@jwt_required()
def tabung():
    return tambah_tabungan()


@kalkulator_bp.route("/kalkulator/pengeluaran", methods=["POST"])
@jwt_required()
def pengeluaran():
    return tambah_pengeluaran()