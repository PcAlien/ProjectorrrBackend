from datetime import datetime

from dto.projekt_dto import ProjektmitarbeiterDTO, ProjektDTO


class PspElementDayForecast:
    tag: datetime
    name: str
    personalnummer: int
    psp_element: str
    geschaetzter_tagesumsatz: float
    geschatzer_gesamtumsatz: float  # bis zum tag

    def __init__(self, tag: datetime, name: str, personalnummer: int, psp_element: str,
                 geschaetzter_tagesumsatz: float,
                 geschatzer_gesamtumsatz: float) -> None:
        self.geschaetzter_tagesumsatz = geschaetzter_tagesumsatz
        self.personalnummer = personalnummer
        self.psp_element = psp_element
        self.name = name
        self.tag = tag
        self.geschatzer_gesamtumsatz = geschatzer_gesamtumsatz


class ForecastDayView:
    tag: datetime
    personen: [PspElementDayForecast]
    _summe: float

    def __init__(self, tag: datetime, personen: [PspElementDayForecast]) -> None:
        self.tag = tag
        self.personen = personen
        self._summe = 0
        p: PspElementDayForecast
        for p in personen:
            self._summe += p.geschatzer_gesamtumsatz

    @property
    def summe(self):
        # Hier kannst du die Logik für den Lesezugriff auf das Attribut definieren
        return self._summe


class PspForecastDTO:
    projekt: ProjektDTO

    tage: [ForecastDayView]
    missing: [ProjektmitarbeiterDTO]

    fc_psp_enddate_umsatz: float
    fc_psp_enddate_restbudget: float
    fc_enddate: str
    fc_enddate_umsatz: float
    fc_enddate_restbudget: float

    def __init__(self, projekt: ProjektDTO, tage: [ForecastDayView], missing: [ProjektmitarbeiterDTO]) -> None:
        self.projekt = projekt

        self.missing = missing
        self.tage = tage

        psp_ende = self.projekt.laufzeit_bis
        fdv: ForecastDayView
        datum_format = "%d.%m.%Y"
        found = False
        for fdv in self.tage:
            if fdv.tag.strftime(datum_format) == psp_ende:
                self.fc_psp_enddate_umsatz = fdv.summe
                self.fc_psp_enddate_restbudget = self.projekt.volumen - fdv.summe
                found = True
                break



        letzter_tag_forecast: ForecastDayView = self.tage[-1]
        self.fc_enddate = letzter_tag_forecast.tag.strftime(datum_format)

        self.fc_enddate_umsatz = letzter_tag_forecast.summe
        self.fc_enddate_restbudget = self.projekt.volumen - letzter_tag_forecast.summe

        if not found:
            self.fc_psp_enddate_umsatz = self.fc_enddate_umsatz
            self.fc_psp_enddate_restbudget = self.fc_enddate_restbudget
