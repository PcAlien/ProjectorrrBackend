import json
from types import NoneType
from typing import Type

from sqlalchemy.orm import sessionmaker

from dto.booking_dto import BookingDTO
from dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from entities.projekt import ProjektMitarbeiter, Projekt
from helpers import data_helper


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

    def get_project_by_psp(self, psp: str):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            pro = session.query(Projekt).filter(Projekt.psp == psp).first()

            return ProjektDTO.create_from_db(pro)

    def get_pma_for_psp_element(self, psp_element: str) -> ProjektmitarbeiterDTO:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            pma = session.query(ProjektMitarbeiter).filter(ProjektMitarbeiter.psp_element == psp_element).first()
            if type(pma) == NoneType:
                print(psp_element)

            return ProjektmitarbeiterDTO.create_from_db(pma)

    def get_all_projects(self, json_format: bool) -> [ProjektDTO] or str:
        Session = sessionmaker(bind=self.engine)
        projektDTOs: [ProjektDTO] = []
        with Session() as session:
            projekte = session.query(Projekt).all()

            for p in projekte:
                projektDTOs.append(ProjektDTO.create_from_db(p))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs

    def get_missing_project_psp_for_bookings(self, bookings: [BookingDTO]) -> {}:
        projekte: [Projekt] = self.get_all_projects(False)
        missing_psps :{str} = set()
        psps: [str] = []
        pro: Projekt
        for pro in projekte:
            psps.append(pro.psp)

        b: BookingDTO
        for b in bookings:
            if b.psp not in psps:
                missing_psps.add(b.psp)

        return missing_psps
