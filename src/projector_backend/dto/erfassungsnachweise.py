from datetime import datetime


class ErfassungsnachweisDTO:
    name: str
    personalnummer: int
    tage: [datetime]
    stunden: [float]

    def __init__(self, name: str, personalnummer: int, tage: [datetime], stunden: [float], ) -> None:
        self.stunden = stunden
        self.tage = tage
        self.name = name
        self.personalnummer = personalnummer
