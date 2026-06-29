from flask import Blueprint
import controller.controller_ukuranjanin as controller_ukuranjanin

# Inisialisasi blueprint untuk ukuran janin
ukuranjanin_bp = Blueprint('ukuranjanin_bp', __name__)

@ukuranjanin_bp.route('/ukuran-janin', methods=['GET'])
def index():
    return controller_ukuranjanin.index()

@ukuranjanin_bp.route('/ukuran-janin/create', methods=['GET', 'POST'])
def create():
    return controller_ukuranjanin.create()

@ukuranjanin_bp.route('/ukuran-janin/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    return controller_ukuranjanin.edit(id)

@ukuranjanin_bp.route('/ukuran-janin/delete/<id>', methods=['GET', 'POST'])
def delete(id):
    return controller_ukuranjanin.delete(id)