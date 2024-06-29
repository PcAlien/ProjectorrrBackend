from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column

# from dto.projekt_dto import ProjektDTO
from src.projector_backend.entities.Base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)


    employee: Mapped["Employee"] = relationship(back_populates="bookings", lazy=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    datum: Mapped[datetime] = mapped_column("Datum")
    berechnungsmotiv: Mapped[str] = mapped_column("berechnungsmotiv", String(2))
    bearbeitungsstatus: Mapped[int] = mapped_column("bearbeitungsstatus")
    bezeichnung: Mapped[str] = mapped_column("bezeichnung", String(300))
    psp: Mapped[str] = mapped_column("psp", String(10))
    pspElement: Mapped[str] = mapped_column("pspElement", String(20))
    stunden: Mapped[float] = mapped_column("stunden")
    text: Mapped[str] = mapped_column("text", String(300))
    erstelltAm: Mapped[datetime] = mapped_column("erstelltAm")
    letzteAenderung: Mapped[datetime] = mapped_column("letzteAenderung")
    stundensatz: Mapped[float] = mapped_column("stundensatz")
    umsatz: Mapped[float] = mapped_column("umsatz")
    counter: Mapped[int] = mapped_column("counter")
    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")

    def __init__(self,
                 employee: employee,
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
                 counter: int,
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
        self.employee = employee
        self.text = text
        self.psp = psp
        self.stundensatz = stundensatz
        self.umsatz = umsatz
        self.counter = counter
        self.uploadDatum = uploadDatum
