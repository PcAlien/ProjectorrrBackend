from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

# from dto.projekt_dto import ProjektDTO
from src.projector_backend.entities.Base import Base


class ImportFileColumns(Base):
    __tablename__ = "importFileColumns"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_name: Mapped[str] = mapped_column("importName", String(30))
    type: Mapped[int] = mapped_column("type")

    bezeichnung: Mapped[int] = mapped_column("bezeichnung")
    name: Mapped[int] = mapped_column("name")
    personalnummer: Mapped[int] = mapped_column("personalnummer")
    leistungsdatum: Mapped[int] = mapped_column("leistungsdatum")
    fakturierbar: Mapped[int] = mapped_column("fakturierbar")
    status: Mapped[int] = mapped_column("status")
    psp: Mapped[int] = mapped_column("psp")
    psp_element: Mapped[int] = mapped_column("psp_element")
    stunden: Mapped[int] = mapped_column("stunden")
    erfasst_am: Mapped[int] = mapped_column("erfasst_am")
    text: Mapped[int] = mapped_column("text")
    letzte_aenderung: Mapped[int] = mapped_column("letzte_aenderung")
    worksheet: Mapped[int] = mapped_column("worksheet")
    delete_empty_lines: Mapped[int] = mapped_column("delete_empty_lines")
    counter: Mapped[int] = mapped_column("counter")

    def __init__(self,
                 import_name: str,
                 type: int,

                 bezeichnung: int,
                 name: int,
                 personalnummer: int,
                 leistungsdatum: int,
                 fakturierbar: int,
                 status: int,
                 psp: int,
                 psp_element: int,
                 stunden: int,
                 erfasst_am: int,
                 text: int,
                 letzte_aenderung: int,
                 worksheet: int,
                 delete_empty_lines: int,
                 counter: int
                 ):
        self.import_name = import_name
        self.type = type
        self.bezeichnung = bezeichnung
        self.name = name
        self.personalnummer = personalnummer
        self.leistungsdatum = leistungsdatum
        self.fakturierbar = fakturierbar
        self.status = status
        self.psp = psp
        self.psp_element = psp_element
        self.stunden = stunden
        self.erfasst_am = erfasst_am
        self.text = text
        self.letzte_aenderung = letzte_aenderung
        self.worksheet = worksheet
        self.delete_empty_lines = delete_empty_lines
        self.counter= counter
