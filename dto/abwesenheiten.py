from entities.abwesenheit_db import Abwesenheit


class AbwesenheitDetailsDTO:
    datum: str
    typ: str

    def __init__(self, datum: str, typ: str) -> None:
        self.datum = datum
        self.typ = typ


class AbwesenheitDTO:
    name: str
    personalnummer: int
    rolle: str
    abwesenheitDetail: [AbwesenheitDetailsDTO]

    def __init__(self, name: str, personalnummer: int, rolle: str, abwesenheit_detail: [AbwesenheitDetailsDTO]) -> None:
        self.abwesenheitDetail = abwesenheit_detail
        self.name = name
        self.personalnummer = personalnummer
        self.rolle = rolle

    @classmethod
    def create_from_db(cls, abwesenheit: Abwesenheit):
        abwesenheitDetailsDTOs: [AbwesenheitDetailsDTO] = []
        abd: AbwesenheitDetailsDTO
        for abd in abwesenheit.abwesenheiten:
            abwesenheitDetailsDTOs.append(
                AbwesenheitDetailsDTO(abd.datum, abd.typ)
            )

        return cls(abwesenheit.name, abwesenheit.personalnummer, abwesenheit.rolle, abwesenheitDetailsDTOs)
