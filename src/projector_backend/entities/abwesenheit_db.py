from datetime import datetime
from typing import List

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

    employee: Mapped["Employee"] = relationship(back_populates="abwesenheit_details", lazy=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self,employee, datum: str, typ: str, uploadDatum: datetime = datetime.now()):
        self.employee = employee
        self.datum = datum
        self.typ = typ
        self.uploadDatum = uploadDatum


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column("name", String(30))
    personalnummer: Mapped[int] = mapped_column("personalnummer")

    project_employees: Mapped[List["ProjectEmployee"]] = relationship(back_populates="employee", lazy=True)
    bookings: Mapped[List["Booking"]] = relationship(back_populates="employee", lazy=True)
    abwesenheit_details: Mapped[List["AbwesenheitDetails"]] = relationship(back_populates="employee", lazy=True)


    # abwesenheiten = relationship("AbwesenheitDetails", back_populates="abwesenheit", lazy=False,
    #                              cascade="all, delete-orphan")

    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")


    def __init__(self, name: str, personalnummer: int,  uploadDatum = datetime.now()):
        self.name = name
        self.personalnummer = personalnummer

        self.uploadDatum = uploadDatum
