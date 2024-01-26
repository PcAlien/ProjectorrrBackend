from datetime import datetime

from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from entities.Base import Base


class ProjektMitarbeiter(Base):
    __tablename__ = "projektmitarbeiter"
    id: Mapped[int] = mapped_column(primary_key=True)
    personalnummer: Mapped[int] = mapped_column("personalnummer")
    name: Mapped[str] = mapped_column("name", String(30))
    psp_bezeichnung: Mapped[str] = mapped_column("psp_bezeichnung", String(30))
    psp_element: Mapped[str] = mapped_column("psp_element", String(30))
    stundensatz: Mapped[float] = mapped_column("stundensatz", )
    stundenbudget: Mapped[float] = mapped_column("stundenbudget", )
    laufzeit_von: Mapped[str] = mapped_column("laufzeit_von", String(30))
    laufzeit_bis: Mapped[str] = mapped_column("laufzeit_bis", String(30))

    projekt_id = Column(Integer, ForeignKey("projekte.id"))
    projekt = relationship("Projekt", back_populates="projektmitarbeiter", lazy=False)
    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self,
                 personalnummer: int,
                 name: str,
                 psp_bezeichnung: str,
                 psp_element: str,
                 stundensatz: int,
                 stundenbudget: int,
                 laufzeit_von: str,
                 laufzeit_bis: str) -> None:
        self.personalnummer = personalnummer
        self.stundenbudget = stundenbudget
        self.psp_element = psp_element
        self.laufzeit_bis = laufzeit_bis
        self.name = name
        self.psp_bezeichnung = psp_bezeichnung
        self.laufzeit_von = laufzeit_von
        self.stundensatz = stundensatz
        self.uploadDatum = datetime.now()


class Projekt(Base):
    __tablename__ = "projekte"
    id: Mapped[int] = mapped_column(primary_key=True)
    volumen: Mapped[int] = mapped_column("volumen")
    projekt_name: Mapped[str] = mapped_column("projekt_name", String(30))
    laufzeit_von: Mapped[str] = mapped_column("laufzeit_von", String(30))
    laufzeit_bis: Mapped[str] = mapped_column("laufzeit_bis", String(30))
    psp: Mapped[str] = mapped_column("psp")

    projektmitarbeiter = relationship("ProjektMitarbeiter", back_populates="projekt", lazy=False)
    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self, volumen: int, projekt_name: str, laufzeit_bis: str, psp: str, laufzeit_von: str,
                 projektmitarbeiter: [ProjektMitarbeiter]) -> None:
        self.volumen = volumen
        self.projekt_name = projekt_name
        self.laufzeit_bis = laufzeit_bis
        self.projektmitarbeiter = projektmitarbeiter
        self.psp = psp
        self.laufzeit_von = laufzeit_von
        self.uploadDatum = datetime.now()



    # @classmethod
    # def create_from_dto(cls,dto: ProjektDTO):
    #     projektmitarbeiter : [ProjektMitarbeiter] = []
    #     pma: ProjektMitarbeiter
    #     for pma in dto.projektmitarbeiter:
    #         projektmitarbeiter.append(ProjektMitarbeiter(None, pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element, pma.stundensatz, pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis))
    #     return cls(dto.volumen, dto.projekt_name, dto.laufzeit_bis, dto.psp, dto.laufzeit_von, projektmitarbeiter)
