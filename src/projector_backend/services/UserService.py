import json
from typing import Type
import hashlib

from flask_jwt_extended import get_jwt_identity, set_access_cookies
from sqlalchemy.orm import sessionmaker

from src.projector_backend.dto.UserDTO import UserDTO
from src.projector_backend.entities.User import UserRole, User
from src.projector_backend.helpers import data_helper


class UserService:
    _instance = None

    def __new__(cls, engine, auth_service):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance.engine = engine
            cls._instance.auth_service = auth_service
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

    def change_password(self, old_password, new_password) -> bool:
        with self.Session() as session:
            user = session.query(User).filter(User.username==self.auth_service.get_logged_user_name()).first()
            encoded_old = old_password.encode()
            encoded_new = new_password.encode()
            hashed_old_password = hashlib.sha256(encoded_old).hexdigest()
            if user.password != hashed_old_password:
                return False
            else:

                hashed_new_password = hashlib.sha256(encoded_new).hexdigest()
                user.password = hashed_new_password
                session.commit()
                return True

    def create_user (self, username) -> bool:
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()

            if user:
                return False
            else:
                role =session.query(UserRole).filter(UserRole.name == "user").first()
                u1 = User(username, self.hash_password("password"), [role])
                session.add(u1)
                session.commit()
                return True



    def create_demo_users(self):
        # TODO: verbessern
        r1 = UserRole("user")
        r2 = UserRole("admin")
        u1 = User("testuser", self.hash_password("password"), [r2])
        with self.Session() as session:
            session.add(u1)
            session.commit()

    def get_all_users(self):
        with self.Session() as session:
            users = session.query(User)

            for user in users:
                print(user.roles)

    def login(self,username, password) :
        with (self.Session() as session):
            user = session.query(User).filter(User.username == username).filter(User.password == self.hash_password(password)).first()

            if user:
                user_dto = UserDTO.create_from_db(user)
                user_dto.create_access_token()


                #return user_dto, user_dto.access_token
                return json.dumps(user_dto, default=data_helper.serialize), user_dto.access_token
            else:
                return None






