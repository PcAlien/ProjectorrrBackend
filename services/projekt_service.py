from typing import Type

from sqlalchemy.orm import sessionmaker

from dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from entities.projekt import ProjektMitarbeiter, Projekt


class ProjektService:
    _instance = None

    def __new__(cls, engine):
        if cls._instance is None:
            cls._instance = super(ProjektService, cls).__new__(cls)
            cls._instance.engine = engine
        return cls._instance

    @classmethod
    def getInstance(cls: Type['ProjektService']) -> 'ProjektService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def create_new_from_dto_and_save(self, projektDTO: ProjektDTO) -> ProjektDTO:
        projektmitarbeiter: [ProjektMitarbeiter] = []
        # pma: ProjektmitarbeiterDTO
        for pma in projektDTO.projektmitarbeiter:
            neuerPMA = ProjektMitarbeiter(pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element,
                                          pma.stundensatz, pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis)
            projektmitarbeiter.append(neuerPMA)

        projekt = Projekt(projektDTO.volumen, projektDTO.projekt_name, projektDTO.laufzeit_bis, projektDTO.psp,
                          projektDTO.laufzeit_von, projektmitarbeiter)

        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            session.add(projekt)
            # Änderungen in die Datenbank schreiben
            # session.flush()
            session.commit()
            session.refresh(projekt)

        return ProjektDTO.create_from_db(projekt)

    # def get_project_by_id(self, id: int):
    #     Session = sessionmaker(bind=self.engine)
    #     with Session() as session:
    #         projekt = session.get(Projekt, id)
    #         return projekt

    def get_project_by_psp(self, psp:str):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            pro = session.query(Projekt).filter(Projekt.psp == psp).first()

            return ProjektDTO.create_from_db(pro)

    def get_pma_for_psp_element(self, psp_element: str) -> ProjektmitarbeiterDTO:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            pma = session.query(ProjektMitarbeiter).filter(ProjektMitarbeiter.psp_element == psp_element).first()

            return ProjektmitarbeiterDTO.create_from_db(pma)

    def get_all_projects(self) :
        Session = sessionmaker(bind=self.engine)
        projektDTOs: [ProjektDTO] = []
        with Session() as session:
            projekte = session.query(Projekt).all()

            for p in projekte:
                projektDTOs.append(ProjektDTO.create_from_db(p))

        return projektDTOs

