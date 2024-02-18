from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO


class MonatsaufteilungSummaryDTO:
    monat: str
    maBookingsSummary: MaBookingsSummaryDTO

    def __init__(self, monat: str, maBookingsSummary: MaBookingsSummaryDTO) -> None:
        self.monat = monat
        self.maBookingsSummary = maBookingsSummary


class MonatsaufteilungDTO:
    monat: str
    bookings: [BookingDTO]

    def __init__(self, monat, bookings) -> None:
        self.monat = monat
        self.bookings = bookings
