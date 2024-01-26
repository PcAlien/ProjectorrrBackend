from datetime import datetime

from dto.forecast_dto import PspElementDayForecast


# 0. temporäre Hilfsklassen definieren.
class Ma_Zwischenspeicher():
    name: str
    personalnummer: str
    stunden: float
    tage: int
    pspElement: str
    stundensatz: float

    def __init__(self, name, personalnummer, pspElement, stundensatz) -> None:
        self.name = name
        self.personalnummer = personalnummer
        self.pspElement = pspElement
        self.stundensatz = stundensatz
        self.stunden = 0
        self.tage = 0

