# Was spricht denn gegen ein Object: Tag, stunden, abwesenheit`?
from src.projector_backend.dto.abwesenheiten import EmployeeDTO


class ErfassungsNachweisDetailDTO:
    tag: str
    stunden: float
    abwesenheit: str

    def __init__(self, tag, stunden, abwesenheit) -> None:
        self.tag = tag
        self.stunden = stunden
        self.abwesenheit = abwesenheit


class ErfassungsnachweisDTO:
    employee: EmployeeDTO
    avg_work_hours: float
    erfassungs_nachweis_details: [ErfassungsNachweisDetailDTO]

    def __init__(self, employee: EmployeeDTO, erfassungs_nachweis_details, avg_work_hours: float) -> None:
        self.employee = employee
        self.avg_work_hours = avg_work_hours

        self.erfassungs_nachweis_details = erfassungs_nachweis_details
