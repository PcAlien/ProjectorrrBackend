from typing import List, Any

from sqlalchemy import String, Column, Integer, ForeignKey, Table
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.projector_backend.entities.Base import Base
from src.projector_backend.entities.project_ent import Project

userroles = Table(
    "user2roles",
    Base.metadata,
    Column("left_id", ForeignKey("users.id")),
    Column("right_id", ForeignKey("userroles.id")),
)

user2projects = Table(
    "user2projects",
    Base.metadata,
    Column("left_id", ForeignKey("users.id")),
    Column("right_id", ForeignKey("projects.id"))
)

class UserRole(Base):

    __tablename__ = "userroles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("name", String(30))

    def __init__(self, name):
        self.name = name



class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)


    username: Mapped[str] = mapped_column("username", String(30))
    password: Mapped[str] = mapped_column("password", String(64))


    roles:Mapped[List[UserRole]] = relationship(secondary=userroles, lazy=False)

    projects:Mapped[List[Project]] = relationship(secondary=user2projects, lazy= False)

    bundles: Mapped[List["ProjectBundle"]] = relationship(back_populates="owner")

    def __init__(self, username: str, password: str, roles: [UserRole]) -> None:
        self.roles = roles
        self.password = password
        self.username = username