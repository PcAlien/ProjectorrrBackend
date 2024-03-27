from datetime import datetime

from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.projector_backend.entities.Base import Base


class ProjektMaster(Base):
    __tablename__ = "projectmaster"
    id: Mapped[int] = mapped_column(primary_key=True)

    projekt_original_name: Mapped[str] = mapped_column("project_name", String(30))
    # projektmitarbeiter = relationship("ProjektMitarbeiter", back_populates="projekt", lazy=False)
    created_at: Mapped[datetime] = mapped_column("createdAt")
    created_by: Mapped[str] = mapped_column("createdBy")

    def __init__(self, projekt_original_name: str, created_by: str) -> None:
        self.projekt_original_name = projekt_original_name
        # self.projektmitarbeiter = projektmitarbeiter
        self.created_at = datetime.now()
        self.created_by = created_by

