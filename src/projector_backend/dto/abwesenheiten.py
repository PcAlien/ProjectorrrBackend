from src.projector_backend.entities.abwesenheit_db import Employee, AbwesenheitDetails


class EmployeeDTO:
    name: str
    personalnummer: int

    def __init__(self, name: str, personalnummer: int,) -> None:
        self.name = name
        self.personalnummer = personalnummer

    @classmethod
    def create_from_db(cls, employee: Employee):
        return cls(employee.name, employee.personalnummer)


class AbwesenheitDetailsDTO:
    datum: str
    typ: str

    def __init__(self, datum: str, typ: str) -> None:
        self.datum = datum
        self.typ = typ


class AbwesenheitDTO:

    employee: EmployeeDTO
    abwesenheitDetails: [AbwesenheitDetailsDTO]

    def __init__(self, employee,  abwesenheitDetails: [AbwesenheitDetailsDTO]) -> None:
        self.abwesenheitDetails: [AbwesenheitDetailsDTO] = abwesenheitDetails
        self.employee = employee


    @classmethod
    def create_from_db(cls, employee: Employee, abwesenheiten: [AbwesenheitDetails] ):
        abwesenheitDetailsDTOs: [AbwesenheitDetailsDTO] = []
        abd: AbwesenheitDetailsDTO
        for abd in abwesenheiten:
            abwesenheitDetailsDTOs.append(
                AbwesenheitDetailsDTO(abd.datum, abd.typ)
            )

        edto = EmployeeDTO(employee.name, employee.personalnummer)

        return cls(edto, abwesenheitDetailsDTOs)

class AbwesenheitsRangeDTO:
    # TODO: echt?
    personalnummer: int
    abwStart: str
    abwEnde: str
    abwType: str

    def __init__(self, personalnummer, abwStart, abwEnde, abwType):
        self.personalnummer = personalnummer
        self.abwStart = abwStart
        self.abwEnde = abwEnde
        self.abwType = abwType




