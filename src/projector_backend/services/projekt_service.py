import json
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter
from typing import Type, Tuple, List

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.util import NoneType

from src.projector_backend.dto.PspPackageDTO import PspPackageDTO, PspPackageSummaryDTO, PspPackageUmsatzDTO, \
    Package_Identifier_Issues
from src.projector_backend.dto.abwesenheiten import AbwesenheitDTO, AbwesenheitDetailsDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.bundle_dtos import ProjectBundleCreateDTO, ProjectBundleDTO
from src.projector_backend.dto.calendar_data import CalenderData
from src.projector_backend.dto.erfassungsnachweise import ErfassungsnachweisDTO
from src.projector_backend.dto.forecast_dto import PspElementDayForecast, ForecastDayView, PspForecastDTO, \
    MaDurchschnittsarbeitszeitDTO
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO, MaBookingsSummaryElementDTO
from src.projector_backend.dto.monatsaufteilung_dto import MonatsaufteilungSummaryDTO, MonatsaufteilungDTO
from src.projector_backend.dto.project_summary import ProjectSummaryDTO, UmsatzDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.entities.PspPackage import PspPackage
from src.projector_backend.entities.booking import Booking
from src.projector_backend.entities.bundles import ProjectBundlePSPElement, ProjectBundle
from src.projector_backend.entities.projekt import ProjektMitarbeiter, Projekt
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.helpers import data_helper, date_helper
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.tempclasses import Ma_Zwischenspeicher


class ProjektService:
    _instance = None

    def __new__(cls, engine, ):
        if cls._instance is None:
            cls._instance = super(ProjektService, cls).__new__(cls)
            cls._instance.engine = engine
            cls._instance.helper = EhBuchungen()
            cls._instance.Session = sessionmaker(bind=cls._instance.engine)
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
                          projektDTO.laufzeit_von, projektmitarbeiter, )

        with self.Session() as session:
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

        with self.Session() as session:
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

            dtos = self.get_psp_packages(psp, False)

        dto = ProjektDTO.create_from_db(pro, dtos)
        if json_format:
            return json.dumps(dto, default=data_helper.serialize)
        else:
            return dto

    def get_pma_for_psp_element(self, psp_element: str) -> ProjektmitarbeiterDTO:

        with self.Session() as session:
            pma = session.query(ProjektMitarbeiter).filter(ProjektMitarbeiter.psp_element == psp_element).first()
            if type(pma) == NoneType:
                print(psp_element)

            return ProjektmitarbeiterDTO.create_from_db(pma)

    def get_all_projects(self, json_format: bool) -> [ProjektDTO] or str:

        projektDTOs: [ProjektDTO] = []
        with self.Session() as session:

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

        projektDTOs: [ProjektDTO] = []
        with self.Session() as session:

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
                dtos = self.get_psp_packages(p.psp, False)
                projektDTOs.append(ProjektDTO.create_from_db(p, dtos))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs

    def get_archived_projects(self, json_format: bool) -> [ProjektDTO] or str:

        projektDTOs: [ProjektDTO] = []
        with self.Session() as session:

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
                dtos = self.get_psp_packages(p.psp, False)
                projektDTOs.append(ProjektDTO.create_from_db(p, dtos))

        if (json_format):
            return json.dumps(projektDTOs, default=data_helper.serialize)
        else:
            return projektDTOs

    def toogle_archive_project(self, psp):

        with self.Session() as session:
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
        with self.Session() as session:
            try:
                package = PspPackage(dto.psp, dto.package_name,dto.package_description,dto.volume, dto.tickets_identifier)
                session.add(package)
                session.commit()



            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return None, result


            return package.package_identifier, DbResult(True, "A new package has been created")



    def update_psp_package(self, dto: PspPackageDTO):
        with self.Session() as session:
            try:
            #package:PspPackage

                package = (
                    session.query(PspPackage)
                    .where(PspPackage.package_identifier == dto.package_identifier).first()
                )

                package.package_name = dto.package_name
                package.package_description = dto.package_description
                package.tickets_identifier = json.dumps(dto.tickets_identifier, default=data_helper.serialize)
                package.volumen = dto.volume

                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return None, result


            return package.package_identifier, DbResult(True, "Package has been updated")



    def delete_psp_package(self, dto: PspPackageDTO):

        with self.Session() as session:
            try:
                # package:PspPackage

                package = (
                    session.query(PspPackage)
                    .where(PspPackage.package_identifier == dto.package_identifier).first()
                )

                session.delete(package)
                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result

            return DbResult(True, "Package has been updated")

    def get_psp_packages(self, psp: str, json_format: bool):

        with self.Session() as session:
            packages = (
                session.query(PspPackage).where(PspPackage.psp == psp)
            )
            package_dtos = []
            for p in packages:
                dto = PspPackageDTO.create_from_db(p)
                package_dtos.append(dto)

        if (json_format):
            return json.dumps(package_dtos, default=data_helper.serialize)
        else:
            return package_dtos

    def get_psp_package(self, identifier: str, json_format: bool):

        with self.Session() as session:
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

        bundle = ProjectBundle(dto.bundle_name, dto.bundle_descripton, psps, None)

        with self.Session() as session:
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

    def edit_project_bundle(self, dto: ProjectBundleCreateDTO):
        psps = []

        for psp in dto.psp_list:
            psps.append(ProjectBundlePSPElement(psp["psp"]))

        bundle = ProjectBundle(dto.bundle_name, dto.bundle_descripton, psps, dto.identifier)

        with self.Session() as session:
            try:
                session.add(bundle)
                session.commit()



            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result

        return DbResult(True, "Bundle has been updated.")

    def delete_bundle(self, identifier: str) -> DbResult:

        with self.Session() as session:
            try:
                obj: [ProjectBundle] = session.query(ProjectBundle).where(ProjectBundle.identifier == identifier)
                for o in obj:
                    for psp in o.bundled_psps:
                        session.delete(psp)
                    session.delete(o)
                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result
            return DbResult(True, "Hat geklappt.")

    def get_project_bundles(self, json_format: bool = True) -> [ProjectBundleDTO] or str:
        pb_dtos: [ProjectBundleDTO] = []

        with self.Session() as session:
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

                for el in pb.bundled_psps:
                    sum_dto = self.get_project_summary(el.psp, False)
                    project_summary_dtos.append(sum_dto)
                    psp_bookings_summary: MaBookingsSummaryDTO = self.get_ma_bookings_summary_for_psp(
                        el.psp, False)
                    psp_booking_summaries_dto.append(psp_bookings_summary)

                # bundle_nachweise = self.get_bundle_nachweise(project_summary_dtos, False)

                dto = ProjectBundleDTO(pb.name, pb.description, project_summary_dtos, identifier=pb.identifier,
                                       monthly_umsaetze=psp_booking_summaries_dto, nachweise=None)

                pb_dtos.append(dto)

        if (json_format):
            return json.dumps(pb_dtos, default=data_helper.serialize)
        else:
            return dto

    def get_project_bundle(self, identifier: str, json_format: bool = True) -> ProjectBundleDTO or str:

        with self.Session() as session:
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
            psp_booking_summaries_dto: [MaBookingsSummaryDTO] = []
            for el in project_bundle.bundled_psps:
                sum_dto = self.get_project_summary(el.psp, False)
                project_summary_dtos.append(sum_dto)

                psp_bookings_summary: MaBookingsSummaryDTO = self.get_ma_bookings_summary_for_psp(el.psp, False)
                psp_booking_summaries_dto.append(psp_bookings_summary)

            bundle_nachweise = self.get_bundle_nachweise(project_summary_dtos, False)

            pb_dto = ProjectBundleDTO(project_bundle.name, project_bundle.description, project_summary_dtos,
                                      project_bundle.identifier, psp_booking_summaries_dto, bundle_nachweise)

            if (json_format):
                return json.dumps(pb_dto, default=data_helper.serialize)
            else:
                return pb_dto

    def get_project_summary(self, psp: str, json_format: bool) -> ProjectSummaryDTO or str:
        monatsaufteilung_dtos: [MonatsaufteilungSummaryDTO] = self.get_bookings_summary_for_psp_by_month(psp, False)
        # restbudget

        project_dto: ProjektDTO = self.get_project_by_psp(psp, False)

        umsaetze_dtos: [UmsatzDTO] = []

        sum_verbraucht = 0
        ma_dto: MonatsaufteilungSummaryDTO
        for ma_dto in monatsaufteilung_dtos:
            umsaetze_dtos.append(UmsatzDTO(ma_dto.monat, ma_dto.maBookingsSummary.sum))
            sum_verbraucht += ma_dto.maBookingsSummary.sum

        ps_dto: ProjectSummaryDTO = ProjectSummaryDTO(project_dto, umsaetze_dtos)

        if json_format:
            return json.dumps(ps_dto, default=data_helper.serialize)
        else:
            return ps_dto

    def get_project_summaries(self, json_format: bool, archiviert=False) -> [ProjectSummaryDTO]:

        if archiviert:
            projekte = self.get_archived_projects(False)
        else:
            projekte = self.get_active_projects(False)
        ps_dtos = []
        for pro in projekte:
            ps_dtos.append(self.get_project_summary(pro.psp, False))

        if json_format:
            return json.dumps(ps_dtos, default=data_helper.serialize)
        else:
            return ps_dtos

    def get_bookings_summary_for_psp_by_month(self, psp: str, json_format: bool) -> [MonatsaufteilungSummaryDTO] or str:
        """
        Liefert alle Buchungen zu einem PSP und teilt diese in Monate auf.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn das Ergebnis im JSON Format zurückgegeben werden soll
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/monatsaufteilung.json".
        """
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        monatsaufteilung_dto: [MonatsaufteilungSummaryDTO] = []

        dto: BookingDTO
        for dto in booking_dtos:
            divider = f"{dto.datum.month}.{dto.datum.year}"
            gesuchtes_dto = next((element for element in monatsaufteilung_dto if element.monat == divider), None)
            if gesuchtes_dto == None:
                gesuchtes_dto = MonatsaufteilungSummaryDTO(divider, MaBookingsSummaryDTO([], 0))
                monatsaufteilung_dto.append(gesuchtes_dto)

            ma_booking_summary_dto: [MaBookingsSummaryDTO] = gesuchtes_dto.maBookingsSummary
            sum: int = ma_booking_summary_dto.sum
            bookings: [MaBookingsSummaryElementDTO] = ma_booking_summary_dto.bookings
            x = MaBookingsSummaryElementDTO(dto.name, dto.personalnummer, dto.psp, dto.pspElement, dto.stundensatz,
                                            dto.stunden, dto.umsatz)
            bookings.append(x)
            sum += x.umsatz

        madtos_compressed: [MonatsaufteilungSummaryDTO] = []

        for madto in monatsaufteilung_dto:
            monat = madto.monat
            ma_booking_summary_dto = madto.maBookingsSummary
            sum_month = ma_booking_summary_dto.sum

            result: [MaBookingsSummaryElementDTO] = self._group_and_sum_by_psp_element(ma_booking_summary_dto.bookings)
            for dto in result:
                sum_month += dto.umsatz

            madtos_compressed.append(MonatsaufteilungSummaryDTO(monat, MaBookingsSummaryDTO(result, sum_month)))

        madtos_compressed = sorted(madtos_compressed, key=self._sort_by_month)

        if (json_format):
            return json.dumps(madtos_compressed, default=data_helper.serialize)
        else:
            return madtos_compressed

    def _sum_stunden_umsatz_for_group(self, group_list):
        # Summen berechnen
        stunden_sum = sum(item.stunden for item in group_list)
        umsatz_sum = sum(item.umsatz for item in group_list)

        return stunden_sum, umsatz_sum

    def _group_and_sum_by_psp_element(self, booking_dtos: [MaBookingsSummaryElementDTO]) -> [
        MaBookingsSummaryElementDTO]:
        # Zuerst sortieren, damit die Gruppen nebeneinander stehen
        sorted_dtos = sorted(booking_dtos, key=attrgetter('psp_element'))

        # Dann nach 'pspElement' gruppieren
        grouped_dtos = groupby(sorted_dtos, key=attrgetter('psp_element'))

        # Ergebnis-Array erstellen
        result: [MaBookingsSummaryElementDTO] = []

        # Für jede Gruppe die Summen berechnen und zum Ergebnis hinzufügen
        for key, group in grouped_dtos:
            group_list = list(group)
            group_list_item: MaBookingsSummaryElementDTO = group_list[0]
            stunden_sum, umsatz_sum = self._sum_stunden_umsatz_for_group(group_list)

            result.append(
                MaBookingsSummaryElementDTO(group_list_item.name, group_list_item.personalnummer, group_list_item.psp,
                                            key, group_list_item.stundensatz, stunden_sum, umsatz_sum))
        return result

    def create_new_from_dtos_and_save(self, bookingDTOs: [BookingDTO]) -> DbResult:
        """
        Erstellt einen neuen Buchungseintrag in der DB .
        :param bookingDTOs: die DTOs elches in die DB übertragen werden sollen
        :return: Ergebnis des Datenbankaufrufs.
        """

        project_dtos: [ProjektDTO] = self.get_all_projects(False)

        pro: ProjektDTO
        buchungen: [Booking] = []

        for bookingDTO in bookingDTOs:

            found = False
            for pro in project_dtos:
                if pro.psp == bookingDTO.psp:
                    found = True
                    break

            if not found:
                return bookingDTO.psp

            pmaDTO = self.get_pma_for_psp_element(bookingDTO.pspElement)
            bookingDTO.stundensatz = pmaDTO.stundensatz
            bookingDTO.umsatz = bookingDTO.stundensatz * bookingDTO.stunden

            buchung = Booking(bookingDTO.name, bookingDTO.personalnummer, bookingDTO.datum, bookingDTO.berechnungsmotiv,
                              bookingDTO.bearbeitungsstatus, bookingDTO.bezeichnung, bookingDTO.psp,
                              bookingDTO.pspElement,
                              bookingDTO.stunden, bookingDTO.text, bookingDTO.erstelltAm, bookingDTO.letzteAenderung,
                              bookingDTO.stundensatz, bookingDTO.umsatz, bookingDTO.uploaddatum)
            buchungen.append(buchung)

        with self.Session() as session:
            try:
                # Füge alle Buchungen hinzu
                session.add_all(buchungen)

                # Führe die Transaktion durch
                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                return DbResult(False, e)

        return DbResult(True, "All bookings have been stored successfully.")

    def create_new_from_dto_and_save(self, bookingDTO: BookingDTO) -> str:
        """
        Erstellt einen neuen Buchungseintrag in der DB und gibt ein entsprechendes DTO zurück.
        :param bookingDTO: das DTO welches in die DB übertragen werden soll
        :return: neues DTO, mit Stundensatz, Umsatz und DB-Id
        """

        project_dtos: [ProjektDTO] = self.get_all_projects(False)

        pro: ProjektDTO

        found = False
        for pro in project_dtos:
            if pro.psp == bookingDTO.psp:
                found = True
                break

        if not found:
            return bookingDTO.psp

        pmaDTO = self.get_pma_for_psp_element(bookingDTO.pspElement)
        bookingDTO.stundensatz = pmaDTO.stundensatz
        bookingDTO.umsatz = bookingDTO.stundensatz * bookingDTO.stunden

        buchung = Booking(bookingDTO.name, bookingDTO.personalnummer, bookingDTO.datum, bookingDTO.berechnungsmotiv,
                          bookingDTO.bearbeitungsstatus, bookingDTO.bezeichnung, bookingDTO.psp, bookingDTO.pspElement,
                          bookingDTO.stunden, bookingDTO.text, bookingDTO.erstelltAm, bookingDTO.letzteAenderung,
                          bookingDTO.stundensatz, bookingDTO.umsatz, bookingDTO.uploaddatum)

        with self.Session() as session:
            session.add(buchung)
            session.commit()
            session.refresh(buchung)

    def get_bookings_for_psp(self, psp: str, json_format: bool) -> [BookingDTO] or str:
        """
        Liefert alle Buchungen zu einem PSP. Berücksichtigt werden dabei nur Buchungen mit dem jüngsten Uploaddatum.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn der Ergebnis im JSON Format zurückgegeben werden soll, ansonsten [BookingDTO]
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/bookings.json".
        """

        with self.Session() as session:
            subquery = (
                session.query(func.max(Booking.uploadDatum))
                .filter(Booking.psp == psp)
                .subquery()
            )

            latest_results = (
                session.query(Booking)
                .filter(Booking.psp == psp)
                .filter(Booking.uploadDatum.in_(subquery))
            )

        booking_dtos: [BookingDTO] = []

        for dto in latest_results:
            booking_dtos.append(BookingDTO.create_from_db(dto))

        if json_format:
            return json.dumps(booking_dtos, default=data_helper.serialize)
        else:
            return booking_dtos

    def get_bookings_for_psp_by_month(self, psp: str, json_format: bool) -> [MonatsaufteilungDTO] or str:
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)

        monatsaufteilung_dtos: [MonatsaufteilungDTO] = []

        dto: BookingDTO
        for dto in booking_dtos:
            monat_jahr_str = f"{dto.datum.month}.{dto.datum.year}"
            gesuchtes_dto = next((element for element in monatsaufteilung_dtos if element.monat == monat_jahr_str),
                                 None)
            if gesuchtes_dto == None:
                gesuchtes_dto = MonatsaufteilungDTO(monat_jahr_str, [])
                monatsaufteilung_dtos.append(gesuchtes_dto)

            gesuchtes_dto.bookings.append(dto)

        if (json_format):
            return json.dumps(monatsaufteilung_dtos, default=data_helper.serialize)
        else:
            return monatsaufteilung_dtos

    def _sort_by_month(self, monatsaufteilung: MonatsaufteilungSummaryDTO):
        return monatsaufteilung.monat

    def get_ma_bookings_summary_for_psp(self, psp: str, json_format: bool) -> MaBookingsSummaryDTO or str:
        """
        Liefert alle Buchung zu einem PSP und gruppiert diese nach den PSP-Elementen.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn das Ergebnis im JSON Format zurückgegeben werden soll.
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/mitarbeiteruebersicht.json".
        """

        with self.Session() as session:

            latest_upload_subquery = (
                session.query(
                    Booking.name,
                    Booking.personalnummer,
                    Booking.psp,
                    Booking.pspElement,
                    Booking.stundensatz,
                    func.max(Booking.uploadDatum).label('LatestUploadDate')
                )
                .where(Booking.psp == psp)
                .group_by(Booking.pspElement)
                .subquery()
            )

            latest_results = (
                session.query(
                    latest_upload_subquery.c.name,
                    latest_upload_subquery.c.personalnummer,
                    latest_upload_subquery.c.psp,
                    latest_upload_subquery.c.pspElement,
                    latest_upload_subquery.c.stundensatz,
                    func.sum(Booking.stunden).label('stunden'),
                    func.sum(Booking.umsatz).label('umsatz')
                )
                .join(
                    Booking,
                    (latest_upload_subquery.c.pspElement == Booking.pspElement) &
                    (latest_upload_subquery.c.LatestUploadDate == Booking.uploadDatum)
                )
                .group_by(latest_upload_subquery.c.pspElement)
                .all()
            )

        ma_bookings_summary_elements: [MaBookingsSummaryElementDTO] = []
        sum_all_bookings = 0
        for row in latest_results:
            ma_booking_summary_element_dto = MaBookingsSummaryElementDTO(row[0], row[1], row[2], row[3], row[4], row[5],
                                                                         row[6])
            ma_bookings_summary_elements.append(ma_booking_summary_element_dto)
            sum_all_bookings += row[6]

        ma_bookings_summary_dto = MaBookingsSummaryDTO(ma_bookings_summary_elements, sum_all_bookings)

        if json_format:
            return json.dumps(ma_bookings_summary_dto, default=data_helper.serialize)
        else:
            return ma_bookings_summary_dto

    def convert_bookings_from_excel_export(self, filename: str) -> Tuple[List[str], DbResult]:
        bookingDTOs: [BookingDTO] = self.helper.create_bookings_from_export("uploads/" + filename)
        dto: BookingDTO

        missing_psps: {str} = self.get_missing_project_psp_for_bookings(bookingDTOs)

        not_missing_psp_bookings: [BookingDTO] = []
        for dto in bookingDTOs:
            if dto.psp not in missing_psps:
                not_missing_psp_bookings.append(dto)

        dbResult = self.create_new_from_dtos_and_save(not_missing_psp_bookings)

        return missing_psps, dbResult

    def mach_forecast(self, psp, json_format: bool) -> PspForecastDTO or str:
        # -----------------------------------------------------------------------

        # 1. Alle Buchungen zu einem PSP beziehen
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        b: BookingDTO

        ma_dict: dict = {}
        ma_tdurchschnitt_dtos: [MaDurchschnittsarbeitszeitDTO] = []
        mas_without_entries: set = set()

        # 2. Ein Dict erstellen, um alle erfassten Stunden und Tage eines MA aufzuaddieren.
        # Dies dient als Vorbereitung zur Ermittlung des Tagesdurchschnittwerts.
        for b in booking_dtos:
            if b.pspElement not in ma_dict.keys():
                ma_dict[b.pspElement] = Ma_Zwischenspeicher(b.name, b.personalnummer, b.pspElement, b.stundensatz)

            ma_dict[b.pspElement].stunden = ma_dict[b.pspElement].stunden + b.stunden
            ma_dict[b.pspElement].tage = ma_dict[b.pspElement].tage + 1

        v: Ma_Zwischenspeicher
        for k, v in ma_dict.items():
            ma_tdurchschnitt_dtos.append(
                MaDurchschnittsarbeitszeitDTO(v.name, v.personalnummer, k, (v.stunden / v.tage),
                                              (v.stundensatz * (v.stunden / v.tage))))

        # 3. Errechnen, was je tag verbraucht wird unter Berücksichtigung der Urlaube.

        calender_data: CalenderData = CalendarService.getInstance().get_calender_data(False)

        ein_tag = timedelta(days=1)

        projektDTO: ProjektDTO = self.get_project_by_psp(psp, False)
        datum_format = "%d.%m.%Y"
        # Datetime-Objekt erstellen und Uhrzeit auf Mitternacht setzen
        # psp_enddatum = datetime.strptime(projektDTO.laufzeit_bis, datum_format).replace(hour=0, minute=0, second=0,
        #                                                                                 microsecond=0)

        forecast_day_views: [ForecastDayView] = []

        # jeden Tag betrachten und dann Summe ziehen.
        betrachteter_tag = datetime.now() + ein_tag
        betrachteter_tag = datetime(day=betrachteter_tag.day, month=betrachteter_tag.month,
                                    year=betrachteter_tag.year)
        betrachteter_tag_str = betrachteter_tag.strftime(datum_format)
        psp_to_gesamtumsatz_dict: dict = {}
        fertig = False
        while (not fertig):
            psp_element_day_forecasts: [PspElementDayForecast] = []

            # für jeden Projektmitarbeiter
            ma: ProjektmitarbeiterDTO
            for ma in projektDTO.projektmitarbeiter:

                if ma.psp_element in ma_dict.keys():

                    if ma.psp_element not in psp_to_gesamtumsatz_dict.keys():
                        psp_to_gesamtumsatz_dict[ma.psp_element] = ma_dict[ma.psp_element].stunden * ma_dict[
                            ma.psp_element].stundensatz

                    durchschnitts_tagesarbeitszeit: float = ma_dict[ma.psp_element].stunden / ma_dict[
                        ma.psp_element].tage

                    durchschnitts_tagesumsatz: float = durchschnitts_tagesarbeitszeit * ma_dict[
                        ma.psp_element].stundensatz

                    letzter_gesamtumsatz_ma: float = psp_to_gesamtumsatz_dict[ma.psp_element]

                    ma_abwesenheiten: [AbwesenheitDetailsDTO] = []

                    abw: AbwesenheitDTO
                    for abw in calender_data.abwesenheiten:
                        if abw.personalnummer == ma.personalnummer:
                            ma_abwesenheiten = abw.abwesenheitDetails

                    tagesumsatz = 0

                    # Datum betrachten: wird es ein WE Tag, ein Urlaubstag, ein Abwesenheitstag sein? Falls ja, kein Umsatz.

                    wochende = betrachteter_tag.weekday() >= 5

                    abwesenheit_existiert = any(
                        abwesenheitDetails.datum == betrachteter_tag_str for abwesenheitDetails in ma_abwesenheiten)
                    feiertag_existiert = any(
                        feiertag.datum == betrachteter_tag_str for feiertag in calender_data.specialDays.feiertage)

                    if wochende or abwesenheit_existiert or feiertag_existiert:
                        tagesumsatz = 0
                    else:
                        tagesumsatz = durchschnitts_tagesumsatz

                    letzter_gesamtumsatz_ma += tagesumsatz

                    pedf = PspElementDayForecast(betrachteter_tag, ma.name, ma.personalnummer, ma.psp_element,
                                                 tagesumsatz,
                                                 letzter_gesamtumsatz_ma)
                    psp_element_day_forecasts.append(pedf)
                    psp_to_gesamtumsatz_dict[ma.psp_element] = letzter_gesamtumsatz_ma

                else:
                    if ma.psp_element not in psp_to_gesamtumsatz_dict.keys():
                        psp_to_gesamtumsatz_dict[ma.psp_element] = 0
                        mas_without_entries.add(ma)

                    pedf = PspElementDayForecast(betrachteter_tag, ma.name, ma.personalnummer, ma.psp_element,
                                                 0,
                                                 0)
                    psp_element_day_forecasts.append(pedf)

            # jetzt auf den gesamten Tag betrachten
            fdv = ForecastDayView(betrachteter_tag, psp_element_day_forecasts)
            forecast_day_views.append(fdv)

            if fdv.summe >= projektDTO.volumen:
                fertig = True
            else:
                betrachteter_tag = betrachteter_tag + ein_tag
                betrachteter_tag_str = betrachteter_tag.strftime(datum_format)

        pfcdto = PspForecastDTO(projektDTO, forecast_day_views, mas_without_entries, ma_tdurchschnitt_dtos)

        if json_format:
            return json.dumps(pfcdto, default=data_helper.serialize)
        else:
            return pfcdto

    def erstelle_erfassungsauswertung(self, psp, json_format: bool) -> [ErfassungsnachweisDTO] or str:

        projekt_dto: ProjektDTO = self.get_project_by_psp(psp, False)

        laufzeit_date = date_helper.from_string_to_date_without_time(projekt_dto.laufzeit_von)
        anzahl_tage_seit_projektstart = (datetime.now().date() - laufzeit_date).days

        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)

        # vorfiltern --> Datum
        jetzt = datetime.now()
        jetzt_um_null_uhr = datetime(year=jetzt.year, month=jetzt.month, day=jetzt.day, minute=0, hour=0, second=0)

        filtered_booking_dtos: [BookingDTO] = []

        suchtage: [datetime] = []
        counter = 0
        abbruchkante = 6
        if anzahl_tage_seit_projektstart < 6:
            abbruchkante = anzahl_tage_seit_projektstart
        done = False
        delta = timedelta(days=1)
        oneDayBack = jetzt_um_null_uhr
        while not done:
            oneDayBack = oneDayBack - delta
            if oneDayBack.weekday() < 5:
                suchtage.append(oneDayBack)
                counter += 1
                if counter == abbruchkante:
                    done = True

        suchtage.reverse()

        b: BookingDTO
        for b in booking_dtos:
            if b.datum >= suchtage[0]:
                filtered_booking_dtos.append(b)

        # alle Personalnummern rausholen:
        nachweise: [ErfassungsnachweisDTO] = []

        # vorher filtern
        # pmas -> {Name:Personalnummer}
        pmas = dict()
        for pma in projekt_dto.projektmitarbeiter:
            pmas[pma.personalnummer] = pma.name

        CalendarService.getInstance().get_calender_data()

        for pnummer, name in pmas.items():
            stunden: [float or str] = []
            tage_zu_stunden: {str: float} = dict()
            tage_zu_abwesenheiten: {str: str} = dict()
            tage: [str] = []

            abwesenheit: AbwesenheitDTO = CalendarService.getInstance().get_abwesenheiten_for_psnr(pnummer, False)
            for gesuchtesDatum in suchtage:
                found = False
                gesuchtes_datum_string = date_helper.from_date_to_string(gesuchtesDatum)
                tage.append(gesuchtes_datum_string)
                if abwesenheit is not None:
                    for x in abwesenheit.abwesenheitDetails:

                        if x.datum == gesuchtes_datum_string:
                            stunden.append(x.typ)
                            tage_zu_abwesenheiten[gesuchtes_datum_string] = x.typ
                            found = True
                            break

                if not found:
                    gesammelte_stunden = 0.0
                    for b in filtered_booking_dtos:
                        if b.personalnummer == pnummer and b.datum == gesuchtesDatum:
                            gesammelte_stunden += b.stunden
                    stunden.append(gesammelte_stunden)
                    tage_zu_stunden[gesuchtes_datum_string] = gesammelte_stunden

            # edto = ErfassungsnachweisDTO(name, pnummer, suchtage, stunden)
            edto = ErfassungsnachweisDTO(name, pnummer, tage, tage_zu_stunden, tage_zu_abwesenheiten)
            nachweise.append(edto)

        # # Personen mit mehreren PSP Elementen erzeugen mehrere Einträge, das muss korrgiert werden
        # nachweise_korrigiert = dict()
        #
        # for edto in nachweise:
        #     if edto.personalnummer not in nachweise_korrigiert.keys():
        #         nachweise_korrigiert[edto.personalnummer] = edto
        #     else:
        #         watched_edto: ErfassungsnachweisDTO = nachweise_korrigiert[edto.personalnummer]
        #         anzahl_tage = len(watched_edto.tage)
        #         for i in range(anzahl_tage):
        #             watched_edto.stunden[i] += edto.stunden[i]
        #
        # nachweise = list(nachweise_korrigiert.values())

        if json_format:
            return json.dumps(nachweise, default=data_helper.serialize)
        else:
            return nachweise

    def get_package_summary(self, identifier: str, json_format: bool) -> PspPackageSummaryDTO or str:

        pspp_dto: PspPackageDTO = self.get_psp_package(identifier, False)
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(pspp_dto.psp, False)

        sum_hours = 0
        sum_umsatz = 0

        # Monate rausfinden
        monate = []
        for b in booking_dtos:
            divider = f"{b.datum.month}.{b.datum.year}"
            if divider not in monate:
                monate.append(divider)

        # UmsatzDTOs vorbereiten
        umsatz_dtos: [PspPackageUmsatzDTO] = []
        for mon in monate:
            umsatz_dtos.append(PspPackageUmsatzDTO(mon, 0, 0))

        b: BookingDTO
        multi_bookings_to_identifiers: {BookingDTO: [str]} = dict()
        for b in booking_dtos:
            local_multi_bookings_to_identifiers: {BookingDTO: [str]} = {b: []}
            found_tis = 0
            for ti in pspp_dto.tickets_identifier:
                if ti in b.text:
                    found_tis += 1

                    local_multi_bookings_to_identifiers[b].append(ti)
                    sum_umsatz += b.umsatz
                    sum_hours += b.stunden

                    # Jetzt in das entsprechende UmsatzDTO schieben
                    divider = f"{b.datum.month}.{b.datum.year}"
                    dto: PspPackageUmsatzDTO
                    for dto in umsatz_dtos:
                        if dto.monat == divider:
                            dto.umsatz += b.umsatz
                            dto.stunden += b.stunden
                            dto.bookings.append(b)
                            break
            if found_tis > 1:
                multi_bookings_to_identifiers.update(local_multi_bookings_to_identifiers)

        # [Package_Identifier_issues]
        piissues = []

        for booking, identifiers in multi_bookings_to_identifiers.items():
            piissues.append(Package_Identifier_Issues(booking, identifiers))

        summary_dto: PspPackageSummaryDTO = PspPackageSummaryDTO(pspp_dto, sum_hours / 8.0, umsatz_dtos, piissues)

        if json_format:
            return json.dumps(summary_dto, default=data_helper.serialize)
        else:
            return summary_dto

    def get_package_summaries(self, psp: str, json_format: bool) -> [PspPackageSummaryDTO] or str:

        projekt_dto: ProjektDTO

        projekt_dto = self.get_project_by_psp(psp, False)

        summaries: [PspPackageSummaryDTO] = []

        pack: PspPackageDTO
        for pack in projekt_dto.psp_packages:
            identifier = pack.package_identifier
            dto = self.get_package_summary(identifier, False)
            summaries.append(dto)

        if json_format:
            return json.dumps(summaries, default=data_helper.serialize)
        else:
            return summaries

    def get_bundle_nachweise(self, project_summaries: [ProjectSummaryDTO], json_format: bool):

        alle_erfassung_dtos: [ErfassungsnachweisDTO] = []
        ps_dto: ProjectSummaryDTO
        for ps_dto in project_summaries:
            psp = ps_dto.project.psp
            erfassung_dtos: [ErfassungsnachweisDTO] = self.erstelle_erfassungsauswertung(psp, False)
            alle_erfassung_dtos.extend(erfassung_dtos)

        # An dieser Stelle wurde aus jedem PSP die ErfassungsNachweisDTOs geholt und in alle_erfassung_dtos gesammelt
        # Jetzt müssen die Werte kombiniert werden.

        # {psnr: [Erfassungsnachweis]}
        psnr_to_erfassungsnachweise: {str: [ErfassungsnachweisDTO]} = dict()

        ef_dto: ErfassungsnachweisDTO
        for ef_dto in alle_erfassung_dtos:
            if ef_dto.personalnummer not in psnr_to_erfassungsnachweise.keys():
                psnr_to_erfassungsnachweise[ef_dto.personalnummer] = []

            psnr_to_erfassungsnachweise[ef_dto.personalnummer].append(ef_dto)

        neue_erfassungsnachwei_dtos: [ErfassungsnachweisDTO] = []

        for psnr, efdtos in psnr_to_erfassungsnachweise.items():

            tage_zu_stunden = {}
            tage_zu_abwesenheit = {}
            dto: ErfassungsnachweisDTO
            for dto in efdtos:
                for tag in dto.tage:
                    if tag in dto.tage_zu_stunden.keys():
                        if tag not in tage_zu_stunden.keys():
                            tage_zu_stunden[tag] = 0
                        tage_zu_stunden[tag] += dto.tage_zu_stunden[tag]

                    elif tag in dto.tage_zu_abwesenheiten.keys():
                        if tag not in tage_zu_abwesenheit.keys():
                            tage_zu_abwesenheit[tag] = 0
                        tage_zu_abwesenheit[tag] = dto.tage_zu_abwesenheiten[tag]

            sumup = ErfassungsnachweisDTO(efdtos[0].name, efdtos[0].personalnummer, efdtos[0].tage, tage_zu_stunden,
                                          tage_zu_abwesenheit)
            neue_erfassungsnachwei_dtos.append(sumup)

        if json_format:
            return json.dumps(neue_erfassungsnachwei_dtos, default=data_helper.serialize)
        else:
            return neue_erfassungsnachwei_dtos
