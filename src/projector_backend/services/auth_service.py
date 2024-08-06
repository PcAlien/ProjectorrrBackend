from typing import Type

from flask_jwt_extended import get_jwt_identity
from src.projector_backend.entities.User import User


class AuthService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def getInstance(cls: Type['AuthService']) -> 'AuthService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def get_logged_user(self, session) -> User:
        current_username = get_jwt_identity()
        return session.query(User).filter(User.username == current_username).first()

    def get_logged_user_name(self) -> str:
        return get_jwt_identity()
