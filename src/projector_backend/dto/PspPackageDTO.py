import json

from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.entities.PspPackage import PspPackage


class PspPackageDTO:
    package_identifier: str
    psp: str
    package_name: str
    package_description: str
    volume: float
    tickets_identifier: [str]
    archived: bool

    def __init__(self, psp: str, package_name: str, package_link, package_description: str, volume: float,
                 tickets_identifier: [str] or str,
                 package_identifier: str = "00000", archived=False) -> None:
        self.volume = volume
        self.package_name = package_name
        self.package_link = package_link
        self.psp = psp
        self.package_identifier = package_identifier
        self.package_description = package_description
        if type(tickets_identifier) == str:
            self.tickets_identifier = json.loads(tickets_identifier)
        else:
            self.tickets_identifier = tickets_identifier
        self.archived = archived

    @classmethod
    def create_from_db(cls, pspp_dto: PspPackage):
        return cls(pspp_dto.psp, pspp_dto.package_name, pspp_dto.package_link, pspp_dto.package_description,
                   pspp_dto.volumen,
                   pspp_dto.tickets_identifier, pspp_dto.package_identifier, pspp_dto.archived)


class PspPackageUmsatzDTO:
    monat: str
    umsatz: float
    _stunden: float
    pt: float
    bookings: [BookingDTO]

    def __init__(self, monat: str, umsatz: float, stunden: float) -> None:
        self.umsatz = umsatz
        self.monat = monat
        self._stunden = stunden
        self.pt = self._stunden / 8.0
        self.bookings = []

    @property
    def stunden(self):
        return self._stunden

    @stunden.setter
    def stunden(self, value):
        # Fügen Sie hier die gewünschte Logik hinzu, z. B. Validierung
        if value < 0:
            raise ValueError("Wert darf nicht negativ sein")
        self._stunden = value
        self.pt = self.stunden / 8.0


class Package_Identifier_Issues:
    booking_dto: BookingDTO
    identifier: [str]

    def __init__(self, booking_dto: BookingDTO, identifier: [str]) -> None:
        self.booking_dto = booking_dto
        self.identifier = identifier


class PspPackageSummaryDTO:
    package: PspPackageDTO
    spent: float
    rest: float
    sum_umsatz: float
    umsaetze: [PspPackageUmsatzDTO]
    multi_identifier_issues: [Package_Identifier_Issues]

    def __init__(self, package: PspPackageDTO, spent: float, umsaetze: [PspPackageUmsatzDTO],
                 multi_identifier_issues: [Package_Identifier_Issues]) -> None:
        self.package = package
        self.spent = spent
        self.rest = self.package.volume - self.spent
        self.umsaetze = umsaetze
        sum = 0.0
        u: PspPackageUmsatzDTO
        for u in umsaetze:
            sum += u.umsatz
        self.sum_umsatz = sum
        self.multi_identifier_issues = multi_identifier_issues
