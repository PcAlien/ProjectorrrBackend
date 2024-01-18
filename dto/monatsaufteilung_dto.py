from dto.ma_bookings_summary_dto import MaBookingsSummaryDTO


class MonatsaufteilungDTO:
    monat: str
    maBookingsSummary: MaBookingsSummaryDTO

    def __init__(self, monat: str, maBookingsSummary: MaBookingsSummaryDTO) -> None:
        self.monat = monat
        self.maBookingsSummary = maBookingsSummary
