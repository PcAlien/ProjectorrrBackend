from src.projector_backend.entities.abwesenheit_db import Abwesenheit


class AbwesenheitDetailsDTO:
    datum: str
    typ: str

    def __init__(self, datum: str, typ: str) -> None:
        self.datum = datum
        self.typ = typ


class AbwesenheitDTO:
    name: str
    personalnummer: int
    abwesenheitDetails: [AbwesenheitDetailsDTO]

    def __init__(self, name: str, personalnummer: int,  abwesenheitDetails: [AbwesenheitDetailsDTO]) -> None:
        self.abwesenheitDetails: [AbwesenheitDetailsDTO] = abwesenheitDetails
        self.name = name
        self.personalnummer = personalnummer

    @classmethod
    def create_from_db(cls, abwesenheit: Abwesenheit):
        abwesenheitDetailsDTOs: [AbwesenheitDetailsDTO] = []
        abd: AbwesenheitDetailsDTO
        for abd in abwesenheit.abwesenheiten:
            abwesenheitDetailsDTOs.append(
                AbwesenheitDetailsDTO(abd.datum, abd.typ)
            )

        return cls(abwesenheit.name, abwesenheit.personalnummer, abwesenheitDetailsDTOs)
