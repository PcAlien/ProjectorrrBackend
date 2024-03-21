
class MaDailyAvgDTO:
    """
    Datenhalter für AVG-Tagesarbeitszeit und AVG-Tagesumsatz festzuhalten.
    """
    durchschnitts_tages_az: float
    durchschnitts_tagesumsatz: float

    def __init__(self, durchschnitts_tages_az, durchschnitts_tagesumsatz) -> None:
        self.durchschnitts_tages_az = durchschnitts_tages_az
        self.durchschnitts_tagesumsatz = durchschnitts_tagesumsatz

class Ma_Identifier_DTO():
    name: str
    personalnummer: str
    psp_element: str

    def __init__(self, name, personalnummer, psp_element) -> None:
        self.name = name
        self.personalnummer = personalnummer
        self.psp_element = psp_element


class Ma_Zwischenspeicher_DTO(Ma_Identifier_DTO):
    # Alle geleisteten Stunden
    stunden: float
    # Anzahl der Tage, an denen etwas erfasst wurde
    tage: int
    # Spezifischer Stundensatz zum Psp-Element
    stundensatz: float

    # Durschnittliche Stunden pro Tag, gemessen an Umsätzen und erfassten Tagen
    avg_stunden_pro_tag : float

    # Durschnittliche Umsatz pro Tag, gemessen an Umsätzen und erfassten Tagen
    avg_umsatz_pro_tag: float


    calc_values_by_projektmeldung: MaDailyAvgDTO

    def __init__(self, name, personalnummer, psp_element, stundensatz,calc_values_by_projektmeldung:MaDailyAvgDTO =None ) -> None:
        self.stundensatz = stundensatz
        self.stunden = 0
        self.tage = 0
        self.calc_values_by_projektmeldung = calc_values_by_projektmeldung
        super().__init__(name, personalnummer, psp_element)

    def add_stunden(self, stunden):
        self.stunden += stunden
        self.tage += 1
        self.avg_stunden_pro_tag = self.stunden / self.tage



