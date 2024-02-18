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

    def __init__(self, project: ProjektDTO, umsaetze: [UmsatzDTO]) -> None:
        self.project = project
        self.umsaetze = umsaetze
        self._calculate_spent_and_rest()

    def _calculate_spent_and_rest(self):
        umsatz: UmsatzDTO
        for umsatz in self.umsaetze:
            self.spent += umsatz.umsatz

        self.restbudget = self.project.volumen - self.spent
