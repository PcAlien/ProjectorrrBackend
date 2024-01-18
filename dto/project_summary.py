class UmsatzDTO:
    monat: str
    umsatz: float

    def __init__(self,  monat: str, umsatz: float) -> None:
        self.umsatz = umsatz
        self.monat = monat


class ProjectSummaryDTO:
    restbudget: float
    umsaetze: [UmsatzDTO]
    psp: int
    budget: float
    spent : float

    def __init__(self,  psp: int, budget: float, spent: float,restbudget: float, umsaetze: [UmsatzDTO]) -> None:
        self.psp = psp
        self.budget = budget
        self.spent = spent
        self.restbudget = restbudget
        self.umsaetze = umsaetze
