# auth.py - Blueprint für Authentifizierung
import json

from flask import Blueprint, current_app, request, abort, jsonify, make_response
from flask_jwt_extended import jwt_required, set_access_cookies, create_access_token

from src.projector_backend.services.UserService import UserService


def create_auth_blueprint(jwt, userService):
    auth_bp = Blueprint('auth', __name__)

    blacklist = []

    @auth_bp.route('/login', methods=['POST'])
    def login():
        username = request.form['email']
        password = request.form['password']
        user_dto, at = userService.login(username, password)


        response = make_response(user_dto)
        #response.set_cookie('access_token_cookie', at, httponly=True)


        if user_dto:
            return response
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

    @auth_bp.route('/createUser', methods=['POST'])
    @jwt_required()
    def create_user():
        credits = json.loads(request.form['credits'])
        result = userService.create_user(credits['username'])
        if result:
            return {'status': "success"}
        else:
            return {'status': "error"}




    return auth_bp
