# auth.py - Blueprint für Authentifizierung
from flask import Blueprint, current_app,request,abort

from src.projector_backend.services.UserService import UserService


def create_auth_blueprint(db):
    auth_bp = Blueprint('auth', __name__)

    @auth_bp.route('/login', methods=['POST'])
    def login():
        engine = db  # Verwenden Sie das übergebene Objekt
        uservice = UserService(engine)

        username = request.form['email']
        password = request.form['password']
        user_dto = uservice.login(username, password)
        if user_dto:
            return user_dto
        else:
            abort(403)

    return auth_bp
