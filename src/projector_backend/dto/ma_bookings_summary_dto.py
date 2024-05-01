from src.projector_backend.dto.abwesenheiten import EmployeeDTO


class MaBookingsSummaryElementDTO:

    employee: EmployeeDTO
    psp: str
    psp_element: str
    stundensatz: float
    stunden: float
    umsatz: float

    def __init__(self, employee: EmployeeDTO, psp: str, psp_element: str, stundensatz: float, stunden: float,
                 umsatz: float) -> None:
        self.stunden = stunden
        self.umsatz = umsatz
        self.psp_element = psp_element
        self.employee = employee
        self.psp = psp
        self.stundensatz = stundensatz


class MaBookingsSummaryDTO:
    sum: int
    psp: str
    bookings: [MaBookingsSummaryElementDTO]

    def __init__(self, bookings: [MaBookingsSummaryElementDTO], sum: int) -> None:
        self.sum = sum
        self.bookings = bookings

    @classmethod
    def create_from_db_result(cls, test):
        pass

