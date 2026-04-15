from flask import Blueprint
from controller.controller_tasbersalin import toggle_tas_bersalin, get_tas_bersalin

tasbersalin_bp = Blueprint("tasbersalin_bp", __name__)

tasbersalin_bp.route("/tasbersalin/toggle", methods=["POST"])(toggle_tas_bersalin)
tasbersalin_bp.route("/tasbersalin", methods=["GET"])(get_tas_bersalin)