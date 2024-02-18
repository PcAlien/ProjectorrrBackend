from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

# from dto.projekt_dto import ProjektDTO
from src.projector_backend.entities.Base import Base


class AbwesenheitDetails(Base):
    __tablename__ = "abwesenheitDetails"
    id: Mapped[int] = mapped_column(primary_key=True)

    datum: Mapped[str] = mapped_column("datum", String(30))
    typ: Mapped[str] = mapped_column("typ", String(30))

    abwesenheit_id: Mapped[int] = mapped_column(ForeignKey("abwesenheiten.id"))
    abwesenheit: Mapped["Abwesenheit"] = relationship(back_populates="abwesenheiten", lazy=False)

    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self, datum: str, typ: str, uploadDatum: datetime = datetime.now()):
        self.datum = datum
        self.typ = typ
        self.uploadDatum = uploadDatum


class Abwesenheit(Base):
    __tablename__ = "abwesenheiten"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column("name", String(30))
    personalnummer: Mapped[int] = mapped_column("personalnummer")
    rolle: Mapped[str] = mapped_column("rolle", String(30))

    abwesenheiten = relationship("AbwesenheitDetails", back_populates="abwesenheit", lazy=False,
                                 cascade="all, delete-orphan")

    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self, name: str, personalnummer: int, rolle: str, abwesenheiten: [AbwesenheitDetails],
                 uploadDatum: datetime = datetime.now()):
        self.name = name
        self.personalnummer = personalnummer
        self.rolle = rolle
        self.abwesenheiten = abwesenheiten
        self.uploadDatum = uploadDatum
