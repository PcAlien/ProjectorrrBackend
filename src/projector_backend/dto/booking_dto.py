from datetime import datetime

from src.projector_backend.entities.booking import Booking
from src.projector_backend.helpers import date_helper as dh


class BookingDTO:
    name: str
    personalnummer: int
    datum: datetime
    berechnungsmotiv: str
    bearbeitungsstatus: int
    bezeichnung: str
    psp: str
    pspElement: str
    stunden: float
    text: str
    erstelltAm: datetime
    letzteAenderung: datetime
    id: int
    stundensatz: float
    umsatz: float

    def __init__(self, name: str,
                 personalnummer: int,
                 datum: str | datetime,
                 berechnungsmotiv: str,
                 bearbeitungsstatus: int,
                 bezeichnung: str,
                 psp: int,
                 pspElement: str,
                 stunden: float,
                 text: str,
                 erstelltAm: str | datetime,
                 letzteAenderung: str | datetime,
                 id=0,
                 stundensatz=0,
                 umsatz=0,
                 uploaddatum=datetime.today()
                 ) -> None:

        if (type(datum) == str):
            self.datum = dh.from_string_to_date_without_time(datum)
        else:
            self.datum = datum
        self.bearbeitungsstatus = bearbeitungsstatus
        self.stunden = stunden
        self.pspElement = pspElement
        if (type(erstelltAm) == str):
            self.erstelltAm = dh.from_string_to_date_without_time(erstelltAm)
        else:
            self.erstelltAm = erstelltAm

        self.berechnungsmotiv = berechnungsmotiv
        self.bezeichnung = bezeichnung
        if (type(letzteAenderung) == str):
            self.letzteAenderung = dh.from_string_to_date_without_time(letzteAenderung)
        else:
            self.letzteAenderung = letzteAenderung

        self.personalnummer = personalnummer
        self.name = name
        self.text = text
        self.psp = psp
        self.id = id
        self.umsatz = umsatz
        self.stundensatz = stundensatz
        self.uploaddatum = uploaddatum

    @classmethod
    def create_from_db(cls, buchung: Booking):
        return cls(buchung.name, buchung.personalnummer, buchung.datum, buchung.berechnungsmotiv,
                   buchung.bearbeitungsstatus, buchung.bezeichnung, buchung.psp, buchung.pspElement, buchung.stunden,
                   buchung.text, buchung.erstelltAm, buchung.letzteAenderung, buchung.id, umsatz=buchung.umsatz,
                   stundensatz=buchung.stundensatz)
