from flask import Blueprint, jsonify, request
from app.dbconnect import connection, close_connection

from .auth import auth
from .message import message

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(auth, url_prefix="/auth")
api_bp.register_blueprint(message, url_prefix="/message")