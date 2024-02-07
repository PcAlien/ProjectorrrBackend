import calendar
from datetime import datetime, timedelta

import holidays


class Feiertag:
    datum: str
    bezeichnung: str
    bundeslaender: str

    def __init__(self, datum: str, bezeichnung: str, bundeslaender: str) -> None:
        self.datum = datum
        self.bundeslaender = bundeslaender
        self.bezeichnung = bezeichnung


class Monatstage:
    monat: int
    tage: int

    def __init__(self, monat: int, tage: int) -> None:
        self.monat = monat
        self.tage = tage


class SpecialDays:
    monatstage: [Monatstage]
    feiertage: [Feiertag]
    wochenendtage: [str]

    def __init__(self) -> None:
        self.monatstage = []
        self.feiertage = []
        self.wochenendtage = []

        for date, name in sorted(holidays.Germany(subdiv="BW", years=2024).items()):
            formatted_date = date.strftime("%d.%m.%Y")
            self.feiertage.append(Feiertag(formatted_date, name, ""))

        current_year = datetime.now().year
        for m in range(1,13):
            daycounter = calendar.monthrange(current_year,m)[1]
            self.monatstage.append(Monatstage(m,daycounter))

        # Wochenendtage
        start_date =  datetime(current_year, 1, 1)
        end_date =  datetime(current_year, 12, 31)

        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() == 5 or current_date.weekday() == 6:
                self.wochenendtage.append(current_date.strftime("%d.%m.%Y"))
            current_date += timedelta(days=1)


