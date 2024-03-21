from datetime import datetime

from src.projector_backend.dto.projekt_dto import ProjektmitarbeiterDTO, ProjektDTO
from src.projector_backend.services.tempclasses import Ma_Identifier_DTO, MaDailyAvgDTO


class PspElementDayForecast(Ma_Identifier_DTO):
    """
    Hält fest, welchen Tagesumsatz und wie welchen Gesamtumsatz eine Person zu einem Stichtag
    vorraussichtlich erwirtschaften wird.
    """
    tag: datetime
    geschaetzter_tagesumsatz: float
    geschatzer_gesamtumsatz: float  # bis zum tag

    def __init__(self, tag: datetime, name: str, personalnummer: str, psp_element: str,
                 geschaetzter_tagesumsatz: float,
                 geschatzer_gesamtumsatz: float) -> None:
        self.geschaetzter_tagesumsatz = geschaetzter_tagesumsatz
        self.tag = tag
        self.geschatzer_gesamtumsatz = geschatzer_gesamtumsatz
        super().__init__(name, personalnummer, psp_element)


class ForecastDayView:
    """
    Hält fest, wie viel Umsatz an einem bestimmten Tag vorraussichtlich gemacht wird.

    """
    tag: datetime
    personen: [PspElementDayForecast]
    _summe: float

    def __init__(self, tag: datetime, personen: [PspElementDayForecast]) -> None:
        self.tag = tag
        self.personen = personen
        self._summe = 0
        p: PspElementDayForecast
        for p in personen:
            self._summe = self.summe + p.geschatzer_gesamtumsatz

    @property
    def summe(self):
        return self._summe


class PspForecastDTO:
    projekt: ProjektDTO

    tage: [ForecastDayView]
    missing: [ProjektmitarbeiterDTO]

    avg_tagesumsaetze: [MaDailyAvgDTO]

    fc_psp_enddate_umsatz: float
    fc_psp_enddate_restbudget: float
    fc_enddate: str
    fc_enddate_umsatz: float
    fc_enddate_restbudget: float

    def __init__(self, projekt: ProjektDTO, tage: [ForecastDayView], missing: [ProjektmitarbeiterDTO],
                 avg_tagesumsaetze: [MaDailyAvgDTO] = None) -> None:
        self.projekt = projekt

        self.missing = missing
        self.tage = tage
        self.avg_tagesumsaetze = avg_tagesumsaetze

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
