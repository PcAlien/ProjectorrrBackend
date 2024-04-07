# auth.py - Blueprint für Authentifizierung
from flask import Blueprint, current_app,request,abort

from src.projector_backend.services.UserService import UserService


def create_auth_blueprint(engine,jwt):
    auth_bp = Blueprint('auth', __name__)

    blacklist = []

    @auth_bp.route('/login', methods=['POST'])
    def login():
        uservice = UserService(engine)

        username = request.form['email']
        password = request.form['password']
        user_dto = uservice.login(username, password)
        if user_dto:
            return user_dto
        else:
            abort(403)

    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload["jti"]
        return jti in blacklist

    return auth_bp



