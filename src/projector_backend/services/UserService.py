import json
from typing import Type
import hashlib

from flask_jwt_extended import get_jwt_identity
from sqlalchemy.orm import sessionmaker

from src.projector_backend.dto.UserDTO import UserDTO
from src.projector_backend.entities.User import UserRole, User
from src.projector_backend.helpers import data_helper


class UserService:
    _instance = None

    def __new__(cls, engine, ):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance.engine = engine
            cls._instance.Session = sessionmaker(bind=cls._instance.engine)
        return cls._instance

    @classmethod
    def getInstance(cls: Type['UserService']) -> 'UserService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def hash_password(self,password):
        # Passwort in Bytes umwandeln
        password_bytes = password.encode('utf-8')

        # Passwort hashen mit SHA-256
        hashed_password = hashlib.sha256(password_bytes).hexdigest()

        return hashed_password

    def create_demo_users(self):

        r1 = UserRole("user")
        r2 = UserRole("admin")

        u1 = User("stefan", self.hash_password("password"), [r2])
        u2 = User("robert", self.hash_password("password"), [r1])

        with self.Session() as session:
            session.add(u1)
            session.add(u2)
            session.commit()

    def get_all_users(self):
        with self.Session() as session:
            users = session.query(User)

            for user in users:
                print(user.roles)

    def login(self,username, password) -> str:
        with (self.Session() as session):
            user = session.query(User).filter(User.username == username).filter(User.password == self.hash_password(password)).first()

            if user:
                user_dto = UserDTO.create_from_db(user)
                user_dto.create_access_token()

                return json.dumps(user_dto, default=data_helper.serialize)
            else:
                return None






