from flask_jwt_extended import create_access_token

from src.projector_backend.entities.User import User


class UserDTO:
    username:str
    password:str
    roles:[str]
    access_token:str

    def __init__(self, username, roles, password="") -> None:
        self.username = username
        self.roles = roles
        self.password = password

    @classmethod
    def create_from_db(cls, user: User):
        tmp_roles =  []
        for role in user.roles:
            tmp_roles.append(role.name)
        return cls(user.username,tmp_roles)

    def create_access_token(self):
        claims = {}
        claims["user"] = True
        if "admin" in self.roles:
            claims["admin"] = True

        self.access_token = create_access_token(identity=self.username, additional_claims=claims)