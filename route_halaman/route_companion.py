# E:\9. SKRPSI\SKRIPSI\Project\Backend-PregMateFIX\route_halaman\route_companion.py

from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
import controller.controller_companion as controller_companion

companion_bp = Blueprint('companion', __name__)

@companion_bp.route('/api/companion/plan', methods=['GET'])
@jwt_required()
def get_plan():
    user_id = get_jwt_identity()
    return controller_companion.get_current_companion_plan(user_id)

@companion_bp.route('/api/companion/checkin', methods=['POST'])
@jwt_required()
def post_checkin():
    user_id = get_jwt_identity()
    return controller_companion.submit_companion_checkin(user_id)

@companion_bp.route('/api/companion/progress', methods=['PUT'])
@jwt_required()
def put_progress():
    user_id = get_jwt_identity()
    return controller_companion.update_companion_progress(user_id)

@companion_bp.route('/api/companion/evaluasi', methods=['GET'])
@jwt_required()
def get_evaluasi():
    user_id = get_jwt_identity()
    return controller_companion.get_evaluasi_data(user_id)

@companion_bp.route('/api/companion/evaluasi', methods=['POST'])
@jwt_required()
def post_evaluasi():
    user_id = get_jwt_identity()
    return controller_companion.submit_companion_evaluasi(user_id)