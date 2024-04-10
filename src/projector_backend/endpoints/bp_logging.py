# auth.py - Blueprint für Authentifizierung
import json

from flask import Blueprint, current_app, request, abort
from flask_jwt_extended import jwt_required

from src.projector_backend.services.UserService import UserService


def create_auth_blueprint(jwt, userService):
    auth_bp = Blueprint('auth', __name__)

    blacklist = []

    @auth_bp.route('/login', methods=['POST'])
    def login():
        username = request.form['email']
        password = request.form['password']
        user_dto = userService.login(username, password)
        if user_dto:
            return user_dto
        else:
            abort(403)

    @auth_bp.route('/changepw', methods=['POST'])
    @jwt_required()
    def change_pw():
        credits = json.loads(request.form['credits'])
        result = userService.change_password(credits['old_password'], credits['new_password'])
        if result:
            return {'status': "success"}
        else:
            return {'status': "error"}


    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload["jti"]
        return jti in blacklist

    return auth_bp
