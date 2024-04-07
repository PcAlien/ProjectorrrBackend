from datetime import datetime

from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.projector_backend.entities.Base import Base


class UserProject(Base):
    __tablename__ = "userProjects"
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column("username")
    project_id: Mapped[int] = mapped_column("projectId")
    archived: Mapped[bool] = mapped_column("archived")


    def __init__(self, username: str, project_master_id: int, archived: bool = False) -> None:
        self.username = username
        self.project_id = project_master_id
        self.archived = archived

