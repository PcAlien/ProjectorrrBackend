from src.projector_backend.dto.abwesenheiten import AbwesenheitDTO
from src.projector_backend.dto.special_days import SpecialDays


class CalenderData:
    abwesenheiten: [AbwesenheitDTO]
    specialDays: [SpecialDays]

    def __init__(self, abwesenheiten) -> None:
        self.abwesenheiten = abwesenheiten
        self.specialDays = SpecialDays()

