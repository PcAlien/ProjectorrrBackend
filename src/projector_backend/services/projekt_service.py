import json
from types import NoneType
from typing import Type, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.projector_backend.dto.PspPackageDTO import PspPackageDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.bundle_dtos import ProjectBundleCreateDTO, ProjectBundleDTO
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.entities.PspPackage import PspPackage
from src.projector_backend.entities.bundles import ProjectBundle, ProjectBundlePSPElement
from src.projector_backend.entities.projekt import ProjektMitarbeiter, Projekt
from src.projector_backend.helpers import data_helper
from src.projector_backend.services.booking_service import BookingService


class ProjektService :
    _instance = None
    booking_service : BookingService

    def __new__(cls, engine, ):
        if cls._instance is None:
            cls._instance = super(ProjektService, cls).__new__(cls)
            cls._instance.engine = engine
            #cls._instance.booking_service = bookingService
        return cls._instance

    def set_engine(self, engine):
        self.engine = engine

    @classmethod
    def getInstance(cls: Type['ProjektService']) -> 'ProjektService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def set_booking_service(self, booking_service):
        self.booking_service = booking_service

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

        pspPs: [PspPackage] = []
        pspp_dto: PspPackageDTO
        for pspp_dto in projektDTO.psp_packages:
            dto = PspPackage(pspp_dto.psp, pspp_dto.package_name, pspp_dto.package_description, pspp_dto.volume,
                             pspp_dto.tickets_identifier)
            pspPs.append(dto)

        projekt = Projekt(projektDTO.volumen, projektDTO.projekt_name, projektDTO.laufzeit_bis, projektDTO.psp,
                          projektDTO.laufzeit_von, projektmitarbeiter, pspPs)

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
                session.query(Projekt)
                .filter(Projekt.uploadDatum.in_(subquery))
                # .join(subquery, Projekt.uploadDatum == subquery.c.uploadDatum)
            )

            for p in projekte:
                projektDTOs.append(ProjektDTO.create_from_db(p))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs

    def get_active_projects(self, json_format: bool) -> [ProjektDTO] or str:
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
                # .join(subquery, Projekt.uploadDatum == subquery.c.uploadDatum)
            )

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
                session.query(Projekt).where(Projekt.archiviert == True)
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
        return {"status": "ok"}

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

    def add_psp_package(self, dto: PspPackageDTO):
        projekt_dto: ProjektDTO
        projekt_dto = self.get_project_by_psp(dto.psp, False)

        # pdto = ProjektDTO("bla","jlj",2434,"n", "m", None, [] )
        # pdto.psp_packages.append(dto)

        projekt_dto.psp_packages.append(dto)

        return self.save_update_project(projekt_dto, True)

    def update_psp_package(self, dto: PspPackageDTO):
        projekt_dto: ProjektDTO
        projekt_dto = self.get_project_by_psp(dto.psp, False)

        p: PspPackageDTO
        for p in projekt_dto.psp_packages:
            if p.package_identifier == dto.package_identifier:
                projekt_dto.psp_packages.remove(p)
                break

        projekt_dto.psp_packages.append(dto)
        return self.save_update_project(projekt_dto, True)

    def delete_psp_package(self, dto: PspPackageDTO):
        projekt_dto: ProjektDTO
        projekt_dto = self.get_project_by_psp(dto.psp, False)

        p: PspPackageDTO
        for p in projekt_dto.psp_packages:
            if p.package_identifier == dto.package_identifier:
                projekt_dto.psp_packages.remove(p)
                break

        return self.save_update_project(projekt_dto, True)

    def get_psp_package(self, identifier: str, json_format: bool):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            package = (
                session.query(PspPackage).where(PspPackage.package_identifier == identifier).first()
            )
        dto = PspPackageDTO.create_from_db(package)

        if (json_format):
            return json.dumps(dto, default=data_helper.serialize)
        else:
            return dto

    # def get_psp_package_summary(self, identifier: str, json_format: bool):
    #     pspp_dto = self.get_psp_package(identifier,False)
    #     project_dto: ProjektDTO
    #     project_dto = self.get_project_by_psp(pspp_dto.psp,False)
    #     # TODO

    def create_project_bundle(self, dto: ProjectBundleCreateDTO):
        psps = []

        for psp in dto.psp_list:
            psps.append(ProjectBundlePSPElement(psp["psp"]))

        bundle = ProjectBundle(dto.bundle_name, dto.bundle_descripton, psps)

        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            try:
                session.add(bundle)
                session.commit()



            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result

        return DbResult(True, "Bundle has been created")

    def get_project_bundles(self, json_format: bool = True) -> [ProjectBundleDTO] or str:
        pb_dtos: [ProjectBundleDTO] = []
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            subquery = (
                session.query(func.max(ProjectBundle.uploadDatum))
                .group_by(ProjectBundle.identifier)
                .subquery()
            )

            project_bundles = (
                session.query(ProjectBundle)
                .filter(ProjectBundle.uploadDatum.in_(subquery))
            )

            pb: ProjectBundle
            for pb in project_bundles:
                project_summary_dtos = []
                psp_booking_summaries_dto: [MaBookingsSummaryDTO] = []
                el: ProjectBundlePSPElement
                bs: BookingService = self.booking_service

                for el in pb.bundled_psps:
                    sum_dto = bs.get_project_summary(el.psp,False)
                    project_summary_dtos.append(sum_dto)
                    psp_bookings_summary: MaBookingsSummaryDTO = self.booking_service.get_ma_bookings_summary_for_psp(
                        el.psp, False)
                    psp_booking_summaries_dto.append(psp_bookings_summary)


                dto = ProjectBundleDTO(pb.name, pb.description,project_summary_dtos, identifier=pb.identifier, monthly_umsaetze=psp_booking_summaries_dto)

                pb_dtos.append(dto)

        if (json_format):
            return json.dumps(pb_dtos, default=data_helper.serialize)
        else:
            return dto

    def get_project_bundle(self,identifier: str, json_format: bool = True) -> ProjectBundleDTO or str:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            subquery = (
                session.query(func.max(ProjectBundle.uploadDatum))
                .group_by(ProjectBundle.identifier)
                .subquery()
            )

            project_bundle: ProjectBundle or None
            project_bundle = (
                session.query(ProjectBundle).where(ProjectBundle.identifier == identifier)
                .filter(ProjectBundle.uploadDatum.in_(subquery)).first()
            )

            project_summary_dtos = []
            psp_booking_summaries_dto : [MaBookingsSummaryDTO] = []
            for el in project_bundle.bundled_psps:
                sum_dto = self.booking_service.get_project_summary(el.psp, False)
                project_summary_dtos.append(sum_dto)

                psp_bookings_summary : MaBookingsSummaryDTO= self.booking_service.get_ma_bookings_summary_for_psp(el.psp,False)
                psp_booking_summaries_dto.append(psp_bookings_summary)

            pb_dto = ProjectBundleDTO(project_bundle.name, project_bundle.description, project_summary_dtos, project_bundle.identifier, psp_booking_summaries_dto)

            if (json_format):
                return json.dumps(pb_dto, default=data_helper.serialize)
            else:
                return pb_dto

