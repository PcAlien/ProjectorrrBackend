from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

# from dto.projekt_dto import ProjektDTO
from entities.Base import Base


class Booking(Base):
    __tablename__ = "buchungen"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("name", String(30))
    personalnummer: Mapped[int] = mapped_column("personalnummer")
    datum: Mapped[datetime] = mapped_column("Datum")
    berechnungsmotiv: Mapped[str] = mapped_column("berechnungsmotiv", String(2))
    bearbeitungsstatus: Mapped[int] = mapped_column("bearbeitungsstatus")
    bezeichnung: Mapped[str] = mapped_column("bezeichnung", String(300))
    psp: Mapped[str] = mapped_column("psp", String(10))
    pspElement: Mapped[str] = mapped_column("pspElement", String(7))
    stunden: Mapped[float] = mapped_column("stunden")
    text: Mapped[str] = mapped_column("text", String(300))
    erstelltAm: Mapped[datetime] = mapped_column("erstelltAm")
    letzteAenderung: Mapped[datetime] = mapped_column("letzteAenderung")
    stundensatz: Mapped[float] = mapped_column("stundensatz")
    umsatz: Mapped[float] = mapped_column("umsatz")
    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")


    def __init__(self, name: str,
                 personalnummer: int,
                 datum: datetime,
                 berechnungsmotiv: str,
                 bearbeitungsstatus: int,
                 bezeichnung: str,
                 psp: str,
                 pspElement: str,
                 stunden: float,
                 text: str,
                 erstelltAm: datetime,
                 letzteAenderung: datetime,
                 stundensatz: float,
                 umsatz: float,
                 uploadDatum: datetime
                 ) -> None:
        self.datum = datum
        self.bearbeitungsstatus = bearbeitungsstatus
        self.stunden = stunden
        self.pspElement = pspElement
        self.erstelltAm = erstelltAm
        self.berechnungsmotiv = berechnungsmotiv
        self.bezeichnung = bezeichnung
        self.letzteAenderung = letzteAenderung
        self.personalnummer = personalnummer
        self.name = name
        self.text = text
        self.psp = psp
        self.stundensatz = stundensatz
        self.umsatz = umsatz
        self.uploadDatum = uploadDatum
