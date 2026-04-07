from flask import Blueprint
from controller.controller_craving import (
    get_cravings,
    add_craving,
    update_craving
)

craving_bp = Blueprint('craving', __name__)

# =========================
# GET semua ngidam user
# =========================
craving_bp.route('/craving', methods=['GET'])(get_cravings)

# =========================
# TAMBAH ngidam
# =========================
craving_bp.route('/craving', methods=['POST'])(add_craving)

# =========================
# UPDATE status ngidam
# =========================
craving_bp.route('/craving/<id>', methods=['PUT'])(update_craving)