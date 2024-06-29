from datetime import datetime

from src.projector_backend.dto.abwesenheiten import EmployeeDTO
from src.projector_backend.entities.booking_etc import Booking
from src.projector_backend.helpers import date_helper as dh


class BookingDTO:
    employee: EmployeeDTO
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
    counter: int

    def __init__(self, employee: EmployeeDTO,
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
                 counter: int,
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

        self.employee = employee
        self.text = text
        self.psp = psp
        self.id = id
        self.umsatz = umsatz
        self.stundensatz = stundensatz
        self.counter = counter
        self.uploaddatum = uploaddatum

    @classmethod
    def create_from_db(cls, buchung: Booking):
        edto = EmployeeDTO.create_from_db(buchung.employee)
        return cls(edto, buchung.datum, buchung.berechnungsmotiv,
                   buchung.bearbeitungsstatus, buchung.bezeichnung, buchung.psp, buchung.pspElement, buchung.stunden,
                   buchung.text, buchung.erstelltAm, buchung.letzteAenderung, buchung.counter, buchung.id,
                   umsatz=buchung.umsatz,
                   stundensatz=buchung.stundensatz, uploaddatum=buchung.uploadDatum)


class BookingDTOProxy:
    def __init__(self, booking: BookingDTO) -> None:
        self.booking = booking
        self.checked = False

    def __eq__(self, other):
        if isinstance(other, BookingDTOProxy):
            return (self.booking.text == other.booking.text and
                    self.booking.datum == other.booking.datum and
                    self.booking.stunden == other.booking.stunden and
                    self.booking.counter == other.booking.counter
                    )
        return False

    def __hash__(self):
        return hash((self.booking.text, self.booking.datum, self.booking.stunden, self.booking.counter))
