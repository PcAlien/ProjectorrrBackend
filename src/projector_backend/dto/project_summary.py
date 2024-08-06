from src.projector_backend.dto.PspPackageDTO import PspPackageSummaryDTO
from src.projector_backend.dto.erfassungsnachweise import ErfassungsnachweisDTO
from src.projector_backend.dto.monatsaufteilung_dto import MonatsaufteilungSummaryDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO


class UmsatzDTO:
    monat: str
    umsatz: float

    def __init__(self, monat: str, umsatz: float) -> None:
        self.umsatz = umsatz
        self.monat = monat


class ProjectSummaryDTO:
    project: ProjektDTO
    spent: float = 0
    restbudget: float = 0
    umsaetze: [UmsatzDTO]
    last_updated: str

    monatsaufteilungen: [MonatsaufteilungSummaryDTO] = []
    erfassungsnachweise: [ErfassungsnachweisDTO] = []
    package_summaries: [PspPackageSummaryDTO] = ()
    missing_psp_elements: str = ""

    def __init__(self, project: ProjektDTO, umsaetze: [UmsatzDTO], monatsaufteilungen: [MonatsaufteilungSummaryDTO],
                 erfassungsnachweise: [ErfassungsnachweisDTO], package_summaries: [PspPackageSummaryDTO],
                 package_summaries_archived: [PspPackageSummaryDTO], missing_psp_elements,
                 last_updated: str) -> None:
        self.project = project
        self.umsaetze = umsaetze
        self._calculate_spent_and_rest()
        self.monatsaufteilungen = monatsaufteilungen
        self.erfassungsnachweise = erfassungsnachweise
        self.package_summaries = package_summaries
        self.package_summaries_archived = package_summaries_archived
        self.missing_psp_elements = missing_psp_elements
        self.last_updated = last_updated

    def _calculate_spent_and_rest(self):
        umsatz: UmsatzDTO
        for umsatz in self.umsaetze:
            self.spent += umsatz.umsatz

        self.restbudget = self.project.volumen - self.spent
