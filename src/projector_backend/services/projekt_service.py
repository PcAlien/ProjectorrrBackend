import json
from types import NoneType
from typing import Type, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.entities.projekt import ProjektMitarbeiter, Projekt
from src.projector_backend.helpers import data_helper


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

    def save_update_project(self, projektDTO: ProjektDTO, update=False) -> Tuple[ProjektDTO, DbResult]:

        if update:
            if not projektDTO.projektmitarbeiter:
                project_dto: ProjektDTO = self.get_project_by_psp(projektDTO.psp, False)
                projektDTO.projektmitarbeiter = project_dto.projektmitarbeiter

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
            try:

                if not update:
                    pro = session.query(Projekt).filter(Projekt.psp == projekt.psp).first()
                    if pro:
                        result = DbResult(False,
                                          "Ein Projekt mit der gleichen PSP Nummer ist bereits in der Datenbank vorhanden.")
                        return None, result

                session.add(projekt)
                session.commit()
                session.refresh(projekt)


            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return None, result

        if update:
            return ProjektDTO.create_from_db(projekt), DbResult(True, "Project has been updated")
        else:
            return ProjektDTO.create_from_db(projekt), DbResult(True, "A new project has been created")

    def get_project_by_psp(self, psp: str, json_format: bool) -> ProjektDTO or str:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            subquery = (
                session.query(func.max(Projekt.uploadDatum))
                .filter(Projekt.psp == psp)
                .subquery()
            )

            pro = (
                session.query(Projekt)
                .filter(Projekt.psp == psp)
                .filter(Projekt.uploadDatum.in_(subquery)).first()
            )

        dto = ProjektDTO.create_from_db(pro)
        if json_format:
            return json.dumps(dto, default=data_helper.serialize)
        else:
            return dto


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

            subquery = (
                session.query(func.max(Projekt.uploadDatum))
                .group_by(Projekt.psp)
                .subquery()
            )

            projekte = (
                session.query(Projekt).where(Projekt.archiviert == False)
                .filter(Projekt.uploadDatum.in_(subquery))
                #.join(subquery, Projekt.uploadDatum == subquery.c.uploadDatum)
            )
            # subquery = (
            #     session.query(func.max(Projekt.uploadDatum))
            #     .subquery()
            # )
            #
            # projekte = (
            #     session.query(Projekt)
            #     .filter(Projekt.uploadDatum.in_(subquery))
            # )
            #projekte = session.query(Projekt).all()

            for p in projekte:
                projektDTOs.append(ProjektDTO.create_from_db(p))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs


    def get_archived_projects(self, json_format: bool) -> [ProjektDTO] or str:
        Session = sessionmaker(bind=self.engine)
        projektDTOs: [ProjektDTO] = []
        with Session() as session:

            subquery = (
                session.query(func.max(Projekt.uploadDatum))
                .group_by(Projekt.psp)
                .subquery()
            )

            projekte = (
                session.query(Projekt).where(Projekt.archiviert==True)
                .filter(Projekt.uploadDatum.in_(subquery))

            )

            for p in projekte:
                projektDTOs.append(ProjektDTO.create_from_db(p))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs


    def toogle_archive_project(self, psp):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            subquery = (
                session.query(func.max(Projekt.uploadDatum))
                .filter(Projekt.psp == psp)
                .subquery()
            )

            pro = (
                session.query(Projekt)
                .filter(Projekt.psp == psp)
                .filter(Projekt.uploadDatum.in_(subquery)).first()
            )

            pro.archiviert = not pro.archiviert

            session.commit()
        return {"status":"ok"}


    def get_missing_project_psp_for_bookings(self, bookings: [BookingDTO]) -> {}:
        projekte: [Projekt] = self.get_all_projects(False)
        missing_psps: {str} = set()
        psps: [str] = []
        pro: Projekt
        for pro in projekte:
            psps.append(pro.psp)

        b: BookingDTO
        for b in bookings:
            if b.psp not in psps:
                missing_psps.add(b.psp)

        return missing_psps
