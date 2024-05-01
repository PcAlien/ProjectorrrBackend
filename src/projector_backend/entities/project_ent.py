from datetime import datetime
from typing import List

from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.projector_backend.entities.Base import Base
from src.projector_backend.entities.abwesenheit_db import Employee


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)

    projekt_original_name: Mapped[str] = mapped_column("project_name", String(30))
    created_at: Mapped[datetime] = mapped_column("createdAt")
    created_by: Mapped[str] = mapped_column("createdBy", String(30))

    psp: Mapped[str] = mapped_column("psp", String(10))

    project_datas: Mapped[List["ProjectData"]] = relationship(back_populates="project", lazy=False, cascade="all")

    def __init__(self, projekt_original_name: str, psp: str, created_by: str) -> None:
        self.projekt_original_name = projekt_original_name
        self.psp = psp
        self.created_at = datetime.now()
        self.created_by = created_by


class ProjectEmployee(Base):
    __tablename__ = "project_employees"
    id: Mapped[int] = mapped_column(primary_key=True)

    employee: Mapped["Employee"] = relationship(back_populates="project_employees" ,lazy=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    psp_bezeichnung: Mapped[str] = mapped_column("psp_bezeichnung", String(200))
    psp_element: Mapped[str] = mapped_column("psp_element", String(30))
    stundensatz: Mapped[float] = mapped_column("stundensatz", )
    stundenbudget: Mapped[float] = mapped_column("stundenbudget", )
    laufzeit_von: Mapped[str] = mapped_column("laufzeit_von", String(30))
    laufzeit_bis: Mapped[str] = mapped_column("laufzeit_bis", String(30))

    projectsData_id = Column(Integer, ForeignKey("projects_data.id"))
    project = relationship("ProjectData", back_populates="projektmitarbeiter", lazy=False)

    def __init__(self,
                 employee: Employee,
                 psp_bezeichnung: str,
                 psp_element: str,
                 stundensatz: int,
                 stundenbudget: int,
                 laufzeit_von: str,
                 laufzeit_bis: str) -> None:
        self.employee = employee
        self.stundenbudget = stundenbudget
        self.psp_element = psp_element
        self.laufzeit_bis = laufzeit_bis
        self.psp_bezeichnung = psp_bezeichnung
        self.laufzeit_von = laufzeit_von
        self.stundensatz = stundensatz


class ProjectData(Base):
    __tablename__ = "projects_data"
    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="project_datas", lazy=False)

    predecessor_id: Mapped[int] = mapped_column("predecessorId")

    projekt_name: Mapped[str] = mapped_column("projekt_name", String(30))
    volumen: Mapped[int] = mapped_column("volumen")
    laufzeit_von: Mapped[str] = mapped_column("laufzeit_von", String(30))
    laufzeit_bis: Mapped[str] = mapped_column("laufzeit_bis", String(30))

    projektmitarbeiter = relationship("ProjectEmployee", back_populates="project", lazy=False, cascade="all")
    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")
    changed_by: Mapped[str] = mapped_column("changed_by", String(30))

    def __init__(self, project_id: int, volumen: int, projekt_name: str, laufzeit_von: str, laufzeit_bis: str,

                 projektmitarbeiter: [ProjectEmployee], changed_by, predecessor_id=0) -> None:
        self.project_id = project_id
        self.predecessor_id = predecessor_id
        self.volumen = volumen
        self.projekt_name = projekt_name
        self.laufzeit_bis = laufzeit_bis
        self.projektmitarbeiter = projektmitarbeiter
        self.laufzeit_von = laufzeit_von
        self.uploadDatum = datetime.now()
        self.changed_by = changed_by

