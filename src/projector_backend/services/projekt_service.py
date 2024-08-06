import json
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter
from typing import Type, Tuple, List

from sqlalchemy import func, distinct, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.util import NoneType

from src.projector_backend.dto.AllProjects import AllProjectsDTO
from src.projector_backend.dto.PspPackageDTO import PspPackageDTO, PspPackageSummaryDTO, PspPackageUmsatzDTO, \
    Package_Identifier_Issues
from src.projector_backend.dto.abwesenheiten import AbwesenheitDTO, EmployeeDTO
from src.projector_backend.dto.booking_dto import BookingDTO, BookingDTOProxy
from src.projector_backend.dto.bundle_dtos import ProjectBundleCreateDTO, ProjectBundleDTO
from src.projector_backend.dto.erfassungsnachweise import ErfassungsnachweisDTO, ErfassungsNachweisDetailDTO
from src.projector_backend.dto.forecast_dto import PspForecastDTO
from src.projector_backend.dto.history import EditedItem, HistResult
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO, MaBookingsSummaryElementDTO
from src.projector_backend.dto.monatsaufteilung_dto import MonatsaufteilungSummaryDTO, MonatsaufteilungDTO
from src.projector_backend.dto.project_summary import ProjectSummaryDTO, UmsatzDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO, ProjectIssueDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.entities.PspPackage import PspPackage
from src.projector_backend.entities.User import User, user2projects
from src.projector_backend.entities.abwesenheit_db import Employee
from src.projector_backend.entities.booking_etc import Booking
from src.projector_backend.entities.bundles import ProjectBundlePSPElement, ProjectBundle
from src.projector_backend.entities.project_ent import ProjectEmployee, ProjectData, Project, ProjectIssue
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.helpers import data_helper, date_helper
from src.projector_backend.helpers.date_helper import from_date_to_string_extended
from src.projector_backend.helpers.sorter import sortme
from src.projector_backend.services.ForecastService import ForecastService
from src.projector_backend.services.auth_service import AuthService
from src.projector_backend.services.calender_service import CalendarService





class ProjektService:
    _instance = None

    def __new__(cls, engine, auth_service: AuthService):
        if cls._instance is None:
            cls._instance = super(ProjektService, cls).__new__(cls)
            cls._instance.engine = engine
            cls._instance.auth_service = auth_service
            cls._instance.helper = EhBuchungen()
            cls._instance.Session = sessionmaker(bind=cls._instance.engine)
            cls._instance._session = None
        return cls._instance

    @classmethod
    def get_instance(cls: Type['ProjektService']) -> 'ProjektService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    @contextmanager
    def session_scope(self):
        if self._session is None:
            self._session = self.Session()
            own_session = True
        else:
            own_session = False

        try:
            yield self._session
            if own_session:
                self._session.commit()
        except Exception:
            if own_session:
                self._session.rollback()
            raise
        finally:
            if own_session:
                self._session.close()
                self._session = None

    def save_update_project(self, projekt_dto: ProjektDTO, update=False) -> Tuple[ProjektDTO, DbResult]:

        with self.session_scope() as session:
            try:

                predecessor_id = 0

                if update:
                    if not projekt_dto.projektmitarbeiter:
                        project_dto: ProjektDTO = self.get_project_by_psp(projekt_dto.psp, False)
                        projekt_dto.projektmitarbeiter = project_dto.projektmitarbeiter
                    predecessor_id = projekt_dto.dbID
                    project_id = projekt_dto.project_master_id
                else:
                    # neues Projekt erstellen
                    project = session.query(Project).filter(Project.psp == projekt_dto.psp).first()
                    if project:
                        result = DbResult(False,
                                          "Ein Projekt mit der gleichen PSP Nummer ist bereits in der "
                                          "Datenbank vorhanden.")
                        return None, result

                    project = Project(projekt_dto.projekt_name, projekt_dto.psp,
                                      self.auth_service.get_logged_user_name())

                    session.add(project)
                    session.commit()
                    session.refresh(project)
                    project_id = project.id

                projektmitarbeiter: [ProjectEmployee] = []

                # pma: ProjektmitarbeiterDTO
                for pma in projekt_dto.projektmitarbeiter:
                    employee = self.get_create_Employee(pma.employee.name, pma.employee.personalnummer)

                    neuerPMA = ProjectEmployee(employee, pma.psp_bezeichnung, pma.psp_element,
                                               pma.stundensatz, pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis)
                    projektmitarbeiter.append(neuerPMA)

                project_data = ProjectData(project_id, projekt_dto.volumen, projekt_dto.projekt_name,
                                           projekt_dto.laufzeit_von,
                                           projekt_dto.laufzeit_bis,
                                           projektmitarbeiter,
                                           self.auth_service.get_logged_user_name(), predecessor_id)

                session.add(project_data)
                session.commit()
                session.refresh(project_data)

                if update:
                    # # Issues überprüfen!
                    issues: ProjectIssue
                    issues = session.query(ProjectIssue).filter(ProjectIssue.psp == projekt_dto.psp).filter(
                        ProjectIssue.type == "mpspe").all()

                    if issues:
                        to_delete_issues = []
                        for i in issues:
                            psp_element = i.issue
                            for p in projektmitarbeiter:
                                if p.psp_element == psp_element:
                                    to_delete_issues.append(i)
                                    break

                        for td in to_delete_issues:
                            session.delete(td)

                        session.commit()

                    return ProjektDTO.create_from_db(project_data, projekt_dto.psp_packages,
                                                     projekt_dto.psp_packages_archived), DbResult(True,
                                                                                                  "Project has been updated")
                else:
                    user = self.auth_service.get_logged_user(session)
                    project = session.query(Project).filter(Project.id == project_id).first()
                    # Project beziehen
                    user.projects.append(project)
                    # session.refresh(user)
                    session.commit()
                    return ProjektDTO.create_from_db(project_data, projekt_dto.psp_packages,
                                                     projekt_dto.psp_packages_archived), DbResult(True,
                                                                                                  "A new project has been created")

            except IntegrityError as e:

                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return None, result

    def get_project_by_psp(self, psp: str, json_format: bool) -> ProjektDTO or str:
        with self.session_scope() as session:

            # Alias für ProjectData.project erstellen
            project_alias = aliased(Project)

            subquery = (
                session.query(func.max(ProjectData.uploadDatum))
                .join(project_alias)
                .filter(project_alias.psp == psp)
                .subquery()
            )

            pro = (
                session.query(ProjectData)
                # .filter(ProjectData.project.psp == psp)
                .filter(ProjectData.uploadDatum.in_(session.query(subquery))).first()
            )

            psp_packages = self.get_psp_packages(psp, False, False)
            psp_packages_archived = self.get_psp_packages(psp, False, True)

            dto = ProjektDTO.create_from_db(pro, psp_packages, psp_packages_archived)
            if json_format:
                return json.dumps(dto, default=data_helper.serialize)
            else:
                return dto

    def get_pma_for_psp_element(self, psp_element: str) -> ProjektmitarbeiterDTO or None:
        with self.session_scope() as session:
            pma = session.query(ProjectEmployee).filter(ProjectEmployee.psp_element == psp_element).first()
            if not pma or type(pma) == NoneType:
                return None

            return ProjektmitarbeiterDTO.create_from_db(pma)

    def get_all_psp_numbers(self):
        with self.session_scope() as session:
            unique_numbers = session.query(distinct(Project.psp)).all()
            unique_numbers_list = [number[0] for number in unique_numbers]
            return unique_numbers_list

    def get_all_projects(self, json_format: bool) -> [ProjektDTO] or str:
        with self.session_scope() as session:
            subquery = (
                session.query(func.max(ProjectData.uploadDatum))
                .group_by(ProjectData.project_id)
                .subquery()
            )

            projekte = (
                session.query(ProjectData).filter(ProjectData.uploadDatum.in_(session.query(subquery)))
            )

            return self._combine_project_dtos(projekte, json_format)

    def get_active_projects(self, json_format: bool) -> [ProjektDTO] or str:
        with self.session_scope() as session:
            # Welche Projekte sind dem User zugeordnet?
            user = self.auth_service.get_logged_user(session)
            pmaster_ids = []
            for userproject in user.projects:
                pmaster_ids.append(userproject.id)

            subquery = (
                session.query(func.max(ProjectData.uploadDatum))
                .group_by(ProjectData.project_id)
                # .group_by(ProjectData.project.psp)
                .subquery()
            )

            projekte = (
                session.query(ProjectData)
                .filter(ProjectData.uploadDatum.in_(session.query(subquery)))
                .filter(ProjectData.project_id.in_(pmaster_ids))
            )

            return self._combine_project_dtos(projekte, json_format)

    def _combine_project_dtos(self, projekte, json_format):
        projekt_dtos: [ProjektDTO] = []
        for p in projekte:
            psp_packages = self.get_psp_packages(p.project.psp, False)
            psp_packages_archived = self.get_psp_packages(p.project.psp, False)
            projekt_dtos.append(ProjektDTO.create_from_db(p, psp_packages, psp_packages_archived))

        if (json_format):
            return json.dumps(projekt_dtos, default=data_helper.serialize)
        else:
            return projekt_dtos

    def get_missing_project_psp_for_bookings(self, bookings: [BookingDTO]) -> {}:
        psp_numbers = self.get_all_psp_numbers()
        missing_psps: {str} = set()
        b: BookingDTO
        for b in bookings:
            if b.psp not in psp_numbers:
                missing_psps.add(b.psp)

        return missing_psps

    def add_psp_package(self, dto: PspPackageDTO):
        with self.session_scope() as session:
            try:
                package = PspPackage(dto.psp, dto.package_name, dto.package_link, dto.package_description, dto.volume,
                                     dto.tickets_identifier)
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
        with self.session_scope() as session:
            try:
                # package:PspPackage

                package = (
                    session.query(PspPackage)
                    .where(PspPackage.package_identifier == dto.package_identifier).first()
                )

                package.package_name = dto.package_name
                package.package_link = dto.package_link
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
        with self.session_scope() as session:
            try:
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

    def get_psp_packages(self, psp: str, json_format: bool, archived=False):
        with self.session_scope() as session:
            packages = (
                session.query(PspPackage).where(PspPackage.psp == psp).filter(PspPackage.archived == archived)
            )
            package_dtos = []
            for p in packages:
                dto = PspPackageDTO.create_from_db(p)
                package_dtos.append(dto)

            if (json_format):
                return json.dumps(package_dtos, default=data_helper.serialize)
            else:
                return package_dtos

    def get_package(self, identifier: str, json_format: bool):
        with self.session_scope() as session:
            package = (
                session.query(PspPackage).where(PspPackage.package_identifier == identifier).first()
            )
            dto = PspPackageDTO.create_from_db(package)

            if json_format:
                return json.dumps(dto, default=data_helper.serialize)
            else:
                return dto

    def create_project_bundle(self, dto: ProjectBundleCreateDTO):
        psps = []

        for psp in dto.psp_list:
            psps.append(ProjectBundlePSPElement(psp["psp"]))

        with self.session_scope() as session:
            try:
                bundle = ProjectBundle(dto.bundle_name, dto.bundle_descripton, psps,
                                       self.auth_service.get_logged_user(session),
                                       None)
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

        with self.session_scope() as session:
            try:

                bundle: ProjectBundle = session.query(ProjectBundle).filter(
                    ProjectBundle.identifier == dto.identifier).first()

                bundle.name = dto.bundle_name
                bundle.description = dto.bundle_descripton

                psp_list_dto = []
                for psp in dto.psp_list:
                    psp_list_dto.append(psp["psp"])

                psp_list_dao = []
                for psp in bundle.bundled_psps:
                    psp_list_dao.append(psp.psp)

                add_elements = []
                remove_elements = []

                current_psp: ProjectBundlePSPElement
                for current_psp in bundle.bundled_psps:
                    if current_psp.psp not in psp_list_dto:
                        remove_elements.append(current_psp)

                current_psp: ProjektDTO
                for current_psp in psp_list_dto:
                    if current_psp not in psp_list_dao:
                        add_elements.append(ProjectBundlePSPElement(current_psp))

                for r in remove_elements:
                    session.delete(r)

                for a in add_elements:
                    bundle.bundled_psps.append(a)

                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result

        return DbResult(True, "Bundle has been updated.")

    def delete_bundle(self, identifier: str) -> DbResult:
        with self.session_scope() as session:
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

        with self.session_scope() as session:

            project_bundles = (
                session.query(ProjectBundle)
                .filter(ProjectBundle.owner == self.auth_service.get_logged_user(session))
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
        with self.session_scope() as session:
            project_bundle: ProjectBundle or None
            project_bundle = (
                session.query(ProjectBundle).where(ProjectBundle.identifier == identifier).filter(
                    ProjectBundle.owner == self.auth_service.get_logged_user(session))
                .first()
            )

            project_summary_dtos = []

            psp_booking_summaries_dto: [MaBookingsSummaryDTO] = []
            el: ProjectBundlePSPElement
            for el in project_bundle.bundled_psps:
                sum_dto: ProjectSummaryDTO = self.get_project_summary(el.psp, False)
                project_summary_dtos.append(sum_dto)

                psp_bookings_summary: MaBookingsSummaryDTO = self.get_ma_bookings_summary_for_psp(el.psp, False)
                psp_bookings_summary.psp = el.psp
                psp_booking_summaries_dto.append(psp_bookings_summary)

            bundle_nachweise = self.get_bundle_nachweise(project_summary_dtos, False)

            pb_dto = ProjectBundleDTO(project_bundle.name, project_bundle.description, project_summary_dtos,
                                      project_bundle.identifier, psp_booking_summaries_dto, bundle_nachweise)

            if json_format:
                return json.dumps(pb_dto, default=data_helper.serialize)
            else:
                return pb_dto

    def get_project_summary(self, psp: str, json_format: bool) -> ProjectSummaryDTO or str:
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        monatsaufteilung_dtos: [MonatsaufteilungSummaryDTO] = self.get_bookings_summary_for_psp_by_month(booking_dtos,
                                                                                                         False)
        # restbudget

        project_dto: ProjektDTO = self.get_project_by_psp(psp, False)
        erfassungs_nachweise: [ErfassungsnachweisDTO] = self.erstelle_erfassungsauswertung(project_dto, booking_dtos,
                                                                                           False)
        package_summaries: list = self.get_package_summaries(project_dto, booking_dtos, False)
        package_summaries_archived: list = self.get_package_summaries(project_dto, booking_dtos, False, True)

        umsaetze_dtos: [UmsatzDTO] = []

        sum_verbraucht = 0
        ma_dto: MonatsaufteilungSummaryDTO
        for ma_dto in monatsaufteilung_dtos:
            umsaetze_dtos.append(UmsatzDTO(ma_dto.monat, ma_dto.maBookingsSummary.sum))
            sum_verbraucht += ma_dto.maBookingsSummary.sum

        if len(booking_dtos) > 0:
            last_updated = booking_dtos[0].uploaddatum
        else:
            last_updated = "-"

        sorted_madtos = sorted(monatsaufteilung_dtos, key=sortme)
        sorted_madtos.reverse()
        sorted_umsaetze = sorted(umsaetze_dtos, key=sortme)

        missing_psp_elements = self.get_issues(psp, False)
        missing_psp_elements_str: str = ""
        for m in missing_psp_elements:
            if m.type == "mpspe":
                missing_psp_elements_str += ", " + m.issue

        if missing_psp_elements_str:
            missing_psp_elements_str = missing_psp_elements_str[2:]

        ps_dto: ProjectSummaryDTO = ProjectSummaryDTO(project_dto, sorted_umsaetze, sorted_madtos,
                                                      erfassungs_nachweise, package_summaries,
                                                      package_summaries_archived, missing_psp_elements_str,
                                                      last_updated)

        if json_format:
            return json.dumps(ps_dto, default=data_helper.serialize)
        else:
            return ps_dto

    def get_project_summaries(self, json_format: bool) -> [ProjectSummaryDTO]:
        projekte = self.get_active_projects(False)
        ps_dtos = []
        for pro in projekte:
            ps_dtos.append(self.get_project_summary(pro.psp, False))

        # Sort by project name
        ps_dtos.sort(key=lambda x: x.project.projekt_name)

        if json_format:
            return json.dumps(ps_dtos, default=data_helper.serialize)
        else:
            return ps_dtos

    def get_all_projects_basics(self):
        all_projects_dtos = self.get_all_projects(False)
        user_active_project_ids = []
        with self.session_scope() as session:
            userprojects = self.auth_service.get_logged_user(session).projects
            for up in userprojects:
                user_active_project_ids.append(up.id)

        back = AllProjectsDTO(all_projects_dtos, user_active_project_ids)
        return json.dumps(back, default=data_helper.serialize)

    def toggle_user_project(self, project_id):
        with (self.session_scope() as session):

            project = session.query(Project).filter_by(id=project_id).first()
            user = self.auth_service.get_logged_user(session)

            if project in user.projects:
                user.projects.remove(project)
            else:
                user.projects.append(project)
            session.commit()

        return self.get_all_projects_basics()

    def toggle_package_archived(self, package_identifier):
        with (self.session_scope() as session):
            psp_package = session.query(PspPackage).filter_by(package_identifier=package_identifier).first()
            psp_package.archived = not psp_package.archived

            session.commit()

        return True

    def get_bookings_summary_for_psp_by_month(self, booking_dtos: [BookingDTO], json_format: bool) -> [
                                                                                                          MonatsaufteilungSummaryDTO] or str:
        """
        Liefert alle Buchungen zu einem PSP und teilt diese in Monate auf.
        :param json_format: True, wenn das Ergebnis im JSON Format zurückgegeben werden soll
        :return: Aktuelle Buchungen zum PSP.
        """
        # booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
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

            x = MaBookingsSummaryElementDTO(dto.employee, dto.psp, dto.pspElement, dto.stundensatz,
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
            stunden_sum, umsatz_sum = _sum_stunden_umsatz_for_group(group_list)

            result.append(
                MaBookingsSummaryElementDTO(group_list_item.employee, group_list_item.psp,
                                            key, group_list_item.stundensatz, stunden_sum, umsatz_sum))
        return result

    def create_new_bookings_from_dtos_and_save(self, bookingDTOs: [BookingDTO]) -> Tuple[List[str], DbResult]:
        """
        Erstellt neue Buchungseinträge in der DB .
        :param bookingDTOs: die DTOs elches in die DB übertragen werden sollen.
        :return: Ergebnis des Datenbankaufrufs.
        """
        with self.session_scope() as session:
            try:

                start = time.time()

                buchungen: [Booking] = []
                employee_dict = dict()
                missing_psp_element_list: [str] = []
                pma_dict = dict()

                for bookingDTO in bookingDTOs:

                    # Es kann vorkommen, dass ein Mitarbeiter noch nicht im System hinterlegt ist.
                    # Falls dies nicht der Fall ist, wird dieser im System automatisch angelegt.
                    # Der Mitarbeiter wird über seine Personalnummer identifiziert - nicht über das PSP Element!

                    if bookingDTO.employee.personalnummer not in employee_dict.keys():
                        employee = self.get_create_Employee(bookingDTO.employee.name,
                                                            bookingDTO.employee.personalnummer)
                        employee_dict[bookingDTO.employee.personalnummer] = employee

                    employee = employee_dict[bookingDTO.employee.personalnummer]

                    if bookingDTO.pspElement not in pma_dict.keys():
                        pma_dict[bookingDTO.pspElement] = self.get_pma_for_psp_element(bookingDTO.pspElement)

                    pmaDTO = pma_dict[bookingDTO.pspElement]

                    if pmaDTO is None:
                        if bookingDTO.pspElement not in missing_psp_element_list:
                            missing_psp_element_list.append(bookingDTO.pspElement)

                    else:
                        bookingDTO.stundensatz = pmaDTO.stundensatz
                        if bookingDTO.berechnungsmotiv.lower() == "f":
                            bookingDTO.umsatz = bookingDTO.stundensatz * bookingDTO.stunden
                        else:
                            bookingDTO.umsatz = 0

                        if not bookingDTO.text:
                            bookingDTO.text = ""

                        buchung = Booking(employee, bookingDTO.datum, bookingDTO.berechnungsmotiv,
                                          bookingDTO.bearbeitungsstatus, bookingDTO.bezeichnung, bookingDTO.psp,
                                          bookingDTO.pspElement,
                                          bookingDTO.stunden, bookingDTO.text, bookingDTO.erstelltAm,
                                          bookingDTO.letzteAenderung,
                                          bookingDTO.stundensatz, bookingDTO.umsatz, bookingDTO.counter,
                                          bookingDTO.uploaddatum)
                        buchungen.append(buchung)

                # Füge alle Buchungen hinzu
                session.add_all(buchungen)

                # Führe die Transaktion durch
                session.commit()


            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                return missing_psp_element_list, DbResult(False, e)

        return missing_psp_element_list, DbResult(True, "All bookings have been stored successfully.")

    def get_upload_date_list_for_psp(self, psp: str):
        with self.session_scope() as session:
            result = session.query(Booking.uploadDatum).filter(Booking.psp == psp).filter(
                Booking.counter > 0).distinct().all()
            unique_datetimes = [row[0] for row in result]

            unique_datetimes.reverse()
            datums_texte = []

            dt: datetime
            counter = 0
            for dt in unique_datetimes:
                counter += 1
                if counter <= 10:
                    datums_texte.append(from_date_to_string_extended(dt))

            # datums_texte.reverse()

            # bla = self._get_upload_date_list_for_psp_with_range(psp,"","")

            return json.dumps(datums_texte, default=data_helper.serialize)

    def _get_upload_date_list_for_psp_in_range(self, psp: str, start: str, end: str):
        with self.session_scope() as session:
            datum_objekt_start = datetime.strptime(start, "%d.%m.%Y - %H:%M:%S Uhr")
            datum_objekt_end = datetime.strptime(end, "%d.%m.%Y - %H:%M:%S Uhr")

            result = session.query(Booking.uploadDatum).filter(Booking.psp == psp).filter(
                Booking.counter > 0).filter(
                Booking.uploadDatum <= datum_objekt_start).filter(
                Booking.uploadDatum >= datum_objekt_end).distinct().all()
            unique_datetimes = [row[0] for row in result]

            return unique_datetimes

    def get_history_for_psp_in_range(self, psp: str, start_upload_date, end_upload_date):

        upload_date_list = self._get_upload_date_list_for_psp_in_range(psp, start_upload_date, end_upload_date)

        upload_date_list.reverse()

        with self.session_scope() as session:

            all_bookings_proxys_in_order = []
            for up in upload_date_list:
                bookings = session.query(Booking).filter(Booking.psp == psp).filter(Booking.uploadDatum == up).all()
                b_dtos = []
                for b in bookings:
                    b_dtos.append(BookingDTO.create_from_db(b))

                set_proxy = {BookingDTOProxy(item) for item in b_dtos}

                all_bookings_proxys_in_order.append(set_proxy)

            anzahl_uploads = len(upload_date_list)

            hiResultList = []

            for i in range(0, anzahl_uploads - 1):
                set_one = all_bookings_proxys_in_order[i]
                set_two = all_bookings_proxys_in_order[i + 1]

                deleted_items = []
                edited_items = []
                new_items = []
                b: BookingDTOProxy

                for item in set_one:
                    item.checked = False
                    # 1. Fall: Werte wurden nicht verändert
                    if item in set_two:
                        item_from_two = [b for b in set_two if b == item]
                        item_from_two[0].checked = True
                        item.checked = True
                    else:
                        # Es gibt keine 1:1 Übereinstimmung - nach Veränderung suchen
                        item_from_two = [b for b in set_two if b.booking.counter == item.booking.counter]
                        if len(item_from_two) > 0:
                            # Das bedeutet, es gab eine Veränderung im Text , des Datums oder der Stundenzahl
                            item_from_two[0].checked = True

                            text_changed = item_from_two[0].booking.text != item.booking.text
                            date_changed = item_from_two[0].booking.datum != item.booking.datum
                            stunden_changed = item_from_two[0].booking.stunden != item.booking.stunden
                            bm_changed = item_from_two[0].booking.berechnungsmotiv != item.booking.berechnungsmotiv

                            budDiff = 0
                            if stunden_changed:
                                budDiff = item.booking.umsatz - item_from_two[0].booking.umsatz
                            # tODO: wo ist bm_changed?
                            ei = EditedItem(item.booking.employee.name, "(" + item.booking.pspElement + ")",
                                            text_changed, stunden_changed, date_changed, bm_changed, budDiff,
                                            item_from_two[0].booking.text, item.booking.text,
                                            item.booking.datum,
                                            item_from_two[0].booking.datum,
                                            item_from_two[0].booking.stunden, item.booking.stunden,
                                            item_from_two[0].booking.berechnungsmotiv, item.booking.berechnungsmotiv
                                            )
                            edited_items.append(ei)

                        else:
                            # Neu hinzugefügt
                            new_items.append(item.booking)

                for item in set_two:
                    if not item.checked:
                        # Das bedeutet, dass dieser Eintrag gelöscht wurde
                        deleted_items.append(item.booking)

                hiResultList.append(
                    HistResult(from_date_to_string_extended(upload_date_list[i]), deleted_items, edited_items,
                               new_items))

            return json.dumps(hiResultList, default=data_helper.serialize)

    # def get_bookings_for_psp(self, psp: str, json_format: bool) -> [BookingDTO] or str:
    def get_bookings_for_psp(self, psp: str, json_format: bool, upload_date: datetime = None) -> [BookingDTO] or str:
        """
        Liefert alle Buchungen zu einem PSP. Berücksichtigt werden dabei nur Buchungen mit dem jüngsten Uploaddatum.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn der Ergebnis im JSON Format zurückgegeben werden soll, ansonsten [BookingDTO]
        :return: Aktuelle Buchungen zum PSP.
        """

        with self.session_scope() as session:

            if upload_date:
                latest_results = (
                    session.query(Booking)
                    .filter(Booking.psp == psp)
                    .filter(Booking.uploadDatum == upload_date)
                )
            else:
                subquery = session.query(func.max(Booking.uploadDatum)).filter(Booking.psp == psp).scalar()
                latest_results = (
                    session.query(Booking)
                    .filter(Booking.psp == psp)
                    .filter(Booking.uploadDatum == subquery)
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
        :return: Aktuelle Buchungen zum PSP.
        """

        with self.session_scope() as session:

            booking_dtos = self.get_bookings_for_psp(psp, False)

            psp_dict = dict()

            maBookingsSummaryElementDTOs = []

            for booking in booking_dtos:
                if booking.pspElement not in psp_dict.keys():
                    psp_dict[booking.pspElement] = []
                psp_dict[booking.pspElement].append(booking)

            for psp_element, bookings in psp_dict.items():
                buchung: BookingDTO
                stunden = 0
                umsatz = 0
                for buchung in bookings:
                    stunden += buchung.stunden
                    umsatz += buchung.umsatz

                maseDTO = MaBookingsSummaryElementDTO(bookings[0].employee, bookings[0].psp, psp_element,
                                                      bookings[0].stundensatz, stunden, umsatz)
                maBookingsSummaryElementDTOs.append(maseDTO)

            sum_all_bookings = 0
            for dto in maBookingsSummaryElementDTOs:
                sum_all_bookings += dto.umsatz

            ma_bookings_summary_dto = MaBookingsSummaryDTO(maBookingsSummaryElementDTOs, sum_all_bookings)

            if json_format:
                return json.dumps(ma_bookings_summary_dto, default=data_helper.serialize)
            else:
                return ma_bookings_summary_dto

    def convert_bookings_from_excel_export(self, filename: str) -> Tuple[List[str], List[str], DbResult]:

        start = time.time()
        bookingDTOs: [BookingDTO] = self.helper.create_booking_dtos_from_export("uploads/" + filename)

        dto: BookingDTO

        missing_psps: {str} = self.get_missing_project_psp_for_bookings(bookingDTOs)

        not_missing_psp_bookings: [BookingDTO] = []
        for dto in bookingDTOs:
            if dto.psp not in missing_psps:
                not_missing_psp_bookings.append(dto)

        missing_psp_elements_list, dbResult = self.create_new_bookings_from_dtos_and_save(not_missing_psp_bookings)
        stop = time.time()
        diff = stop - start

        print("ZEIT fuer den gesamten Buchungsupload: ", diff)

        return missing_psps, missing_psp_elements_list, dbResult

    def create_forecast_by_alltime_avg(self, psp, json_format: bool) -> PspForecastDTO or str:
        """
        Es wird für jeden Mitarbeiter errechnet, wie viel Stunden er am Tag arbeiten und welchen Umsatz er dabei macht.
        Grundlage sind dabei alle Buchungen von Projektbeginn an.
        Daraus wird ein PspForecastDTO erstellt, welches unter anderem angibt, wann das Budget aufgebraucht sein wird.
        :param psp: TODO
        :param json_format: tODO
        :return: TODO
        """

        fcs = ForecastService()

        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        projektDTO: ProjektDTO = self.get_project_by_psp(psp, False)

        pfcdto = fcs.create_forecast_by_alltime_avg(psp, booking_dtos, projektDTO)

        if json_format:
            return json.dumps(pfcdto, default=data_helper.serialize)
        else:
            return pfcdto

    def create_forecast_by_projektmeldung(self, psp, json_format: bool) -> PspForecastDTO or str:
        fcs = ForecastService()

        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        projektDTO: ProjektDTO = self.get_project_by_psp(psp, False)

        pfcdto = fcs.create_forecast_by_projektmeldung(booking_dtos, projektDTO)

        if json_format:
            return json.dumps(pfcdto, default=data_helper.serialize)
        else:
            return pfcdto

    def erstelle_erfassungsauswertung(self, projekt_dto: ProjektDTO, booking_dtos: [BookingDTO], json_format: bool) -> [
                                                                                                                           ErfassungsnachweisDTO] or str:
        laufzeit_von_date = date_helper.from_string_to_date_without_time(projekt_dto.laufzeit_von)
        laufzeit_bis_date = date_helper.from_string_to_date_without_time(projekt_dto.laufzeit_bis)

        anzahl_tage_seit_projektstart = (datetime.now().date() - laufzeit_von_date).days
        nachweise: [ErfassungsnachweisDTO] = []

        if (anzahl_tage_seit_projektstart > 0):

            anzahl_projekttage = (laufzeit_bis_date - laufzeit_von_date).days

            # vorfiltern --> Datum
            jetzt = datetime.now()
            jetzt_um_null_uhr = datetime(year=jetzt.year, month=jetzt.month, day=jetzt.day, minute=0, hour=0, second=0)

            # Es werden nur die Buchungen betrachtet, die in den letzte Tagen vorgenommen wurden.
            filtered_booking_dtos: [BookingDTO] = []

            suchtage: [datetime] = []
            counter = 0
            abbruchkante = 6
            if anzahl_tage_seit_projektstart < 6:
                abbruchkante = anzahl_tage_seit_projektstart

            # Festlegen, welche Tage betrachtet werden (bis zu 6 Tage zurück, ausgenommen Feiertage und Wochenenden)
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

            # Alle Buchungseinträge identifizieren und sammeln, die innerhalb dieser 6 Tage zurück liegen

            b: BookingDTO
            for b in booking_dtos:
                if b.datum >= suchtage[0]:
                    filtered_booking_dtos.append(b)


            # alle Personalnummern rausholen und in dict speichern --> personalnummer : name
            pmas = dict()
            for pma in projekt_dto.projektmitarbeiter:
                avg_work_hours_per_day = pma.stundenbudget / anzahl_projekttage
                pmas[pma.employee.personalnummer] = [pma.employee.name, avg_work_hours_per_day]

            nachweise: [ErfassungsnachweisDTO] = []

            for pnummer, name_and_workhours in pmas.items():

                tage: [str] = []
                erfassungs_nachweis_details_dtos = []

                abwesenheit: AbwesenheitDTO = CalendarService.get_instance().get_abwesenheiten_for_psnr(pnummer, False)
                for gesuchtesDatum in suchtage:

                    en_stunden = 0
                    abw = ""

                    found = False
                    gesuchtes_datum_string = date_helper.from_date_to_string(gesuchtesDatum)
                    tage.append(gesuchtes_datum_string)
                    if abwesenheit is not None:
                        for abwesenheitsDetailDTO in abwesenheit.abwesenheitDetails:
                            if abwesenheitsDetailDTO.datum == gesuchtes_datum_string:
                                abw = abwesenheitsDetailDTO.typ
                                found = True
                                break

                    if not found:
                        gesammelte_stunden = 0.0
                        for b in filtered_booking_dtos:
                            if b.employee.personalnummer == pnummer and b.datum == gesuchtesDatum:
                                gesammelte_stunden += b.stunden
                        en_stunden = gesammelte_stunden

                    end_dto = ErfassungsNachweisDetailDTO(gesuchtes_datum_string, en_stunden, abw)
                    erfassungs_nachweis_details_dtos.append(end_dto)

                # TODO: das geht sicher besser
                edto = ErfassungsnachweisDTO(EmployeeDTO(name_and_workhours[0], pnummer),
                                             erfassungs_nachweis_details_dtos,
                                             name_and_workhours[1])
                nachweise.append(edto)

        if json_format:
            return json.dumps(nachweise, default=data_helper.serialize)
        else:
            return nachweise

    def get_package_summary(self, identifier: str, json_format: bool,
                            booking_dtos: [BookingDTO] = None, archived=False) -> PspPackageSummaryDTO or str:
        pspp_dto: PspPackageDTO = self.get_package(identifier, False)
        pspp_dtos: [PspPackageDTO] = self.get_psp_packages(pspp_dto.psp, False, archived)

        if booking_dtos is None:
            booking_dtos: [BookingDTO] = self.get_bookings_for_psp(pspp_dto.psp, False)

        sum_package_hours = 0
        sum_package_umsatz = 0

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

        # todo:nur ein package betrachtet

        package_identifier_issues: [Package_Identifier_Issues] = []
        booking_to_identifiers = {}

        if isinstance(booking_to_identifiers, list):
            raise ValueError("booking_to_identifiers wurde als Liste definiert, erwartet wurde ein Dictionary.")

        for b in booking_dtos:
            booking_to_identifiers[b] = []
            found_ticket_indentifiers = 0
            ticket_identifier: str

            for ticket_identifier in pspp_dto.tickets_identifier:
                if ticket_identifier.lower() in b.text.lower():

                    # Wenn es sich nicht die Identifizierer des betrachteten Package handelt,

                    found_ticket_indentifiers += 1
                    booking_to_identifiers[b].append(ticket_identifier)

                    sum_package_hours += b.stunden
                    sum_package_umsatz += b.umsatz

                    divider = f"{b.datum.month}.{b.datum.year}"
                    dto: PspPackageUmsatzDTO
                    for dto in umsatz_dtos:
                        if dto.monat == divider:
                            dto.umsatz += b.umsatz
                            dto.stunden += b.stunden
                            dto.bookings.append(b)
                            break

            if found_ticket_indentifiers > 0:
                for other_package_dto in pspp_dtos:
                    if other_package_dto.package_identifier != pspp_dto.package_identifier:
                        for ticket_identifier in other_package_dto.tickets_identifier:
                            if ticket_identifier.lower() in b.text.lower():
                                found_ticket_indentifiers += 1
                                booking_to_identifiers[b].append(ticket_identifier)

            # Was wenn mehr als ein Ticketidentifizierer innerhalb einer Buchung gefunden wurde?
            if found_ticket_indentifiers > 1:
                package_identifier_issues.append(Package_Identifier_Issues(b, booking_to_identifiers[b]))

        sorted_umsaetze = sorted(umsatz_dtos, key=sortme)
        sorted_umsaetze.reverse()

        summary_dto: PspPackageSummaryDTO = PspPackageSummaryDTO(pspp_dto, sum_package_hours / 8.0, sorted_umsaetze,
                                                                 package_identifier_issues)

        if json_format:
            return json.dumps(summary_dto, default=data_helper.serialize)
        else:
            return summary_dto

    def get_package_summaries(self, projekt_dto_or_str: ProjektDTO or str, booking_dtos: [BookingDTO],
                              json_format: bool, archived=False) -> [PspPackageSummaryDTO] or str:
        if type(projekt_dto_or_str) == str:
            projekt_dto = self.get_project_by_psp(projekt_dto_or_str, False)
        elif type(projekt_dto_or_str) == ProjektDTO:
            projekt_dto = projekt_dto_or_str

        summaries: [PspPackageSummaryDTO] = []

        pack: PspPackageDTO

        if not archived:
            for pack in projekt_dto.psp_packages:
                identifier = pack.package_identifier
                dto = self.get_package_summary(identifier, False, booking_dtos=booking_dtos, archived=archived)
                summaries.append(dto)
        else:
            for pack in projekt_dto.psp_packages_archived:
                identifier = pack.package_identifier
                dto = self.get_package_summary(identifier, False, booking_dtos=booking_dtos, archived=archived)
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
            # TODO: bookingDTOs übergeben oder prüfen, ob None auch OK wäre.
            booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
            erfassung_dtos: [ErfassungsnachweisDTO] = self.erstelle_erfassungsauswertung(ps_dto.project, booking_dtos,
                                                                                         False)
            alle_erfassung_dtos.extend(erfassung_dtos)

        # An dieser Stelle wurde aus jedem PSP die ErfassungsNachweisDTOs geholt und in alle_erfassung_dtos gesammelt
        # Jetzt müssen die Werte kombiniert werden.

        # {psnr: [Erfassungsnachweis]}
        psnr_to_erfassungsnachweise: {str: [ErfassungsnachweisDTO]} = dict()

        ef_dto: ErfassungsnachweisDTO
        for ef_dto in alle_erfassung_dtos:
            if ef_dto.employee.personalnummer not in psnr_to_erfassungsnachweise.keys():
                psnr_to_erfassungsnachweise[ef_dto.employee.personalnummer] = []

            psnr_to_erfassungsnachweise[ef_dto.employee.personalnummer].append(ef_dto)

        neue_erfassungsnachwei_dtos: [ErfassungsnachweisDTO] = []

        for psnr, efdtos in psnr_to_erfassungsnachweise.items():

            erfassungs_nachweis_dto: ErfassungsnachweisDTO

            collected_erfassungs_nachweise_dtos: [ErfassungsNachweisDetailDTO] = []

            avg_work_hours_sum = 0

            for erfassungs_nachweis_dto in efdtos:

                end: ErfassungsNachweisDetailDTO
                avg_work_hours_sum += erfassungs_nachweis_dto.avg_work_hours

                for end in erfassungs_nachweis_dto.erfassungs_nachweis_details:
                    # Prüfen, ob es für diesen Tag schon ein detailsDTO gibt.
                    watched_erfassungs_nachweis_dto: ErfassungsNachweisDetailDTO = None
                    cnachweis: ErfassungsNachweisDetailDTO
                    for cnachweis in collected_erfassungs_nachweise_dtos:
                        if cnachweis.tag == end.tag:
                            watched_erfassungs_nachweis_dto = cnachweis
                            break

                    if watched_erfassungs_nachweis_dto is None:
                        watched_erfassungs_nachweis_dto = ErfassungsNachweisDetailDTO(end.tag, 0, "")
                        collected_erfassungs_nachweise_dtos.append(watched_erfassungs_nachweis_dto)

                    if end.abwesenheit == "":
                        watched_erfassungs_nachweis_dto.stunden += end.stunden
                    else:
                        watched_erfassungs_nachweis_dto.abwesenheit = end.abwesenheit
                        continue

            new_endto = ErfassungsnachweisDTO(EmployeeDTO(efdtos[0].employee.name, efdtos[0].employee.personalnummer),
                                              collected_erfassungs_nachweise_dtos,
                                              avg_work_hours_sum)

            neue_erfassungsnachwei_dtos.append(new_endto)

        if json_format:
            return json.dumps(neue_erfassungsnachwei_dtos, default=data_helper.serialize)
        else:
            return neue_erfassungsnachwei_dtos

    def delete_project(self, psp) -> bool:
        with (self.session_scope() as session):
            projectDTO = self.get_project_by_psp(psp, False)

            project: Project = session.query(Project).filter_by(id=projectDTO.project_master_id).first()

            # Alle Verknüpfungen zu Usern manuell aufheben, geht kaskadierend wohl nicht.
            users: [User] = session.query(User).all()

            for user in users:
                if project in user.projects:
                    user.projects.remove(project)
                    session.commit()

            bla: ProjectData
            for bla in project.project_datas:
                session.delete(bla)

            pbundlesElements: [ProjectBundlePSPElement] = session.query(ProjectBundlePSPElement).filter_by(
                psp=psp).all()

            for pel in pbundlesElements:
                session.delete(pel.project_bundle)

            bookings = session.query(Booking).filter_by(psp=psp)
            bookings.delete()

            session.delete(project)
            session.commit()

        return True

    def get_create_Employee(self, name, personalnummer):

        with (self.session_scope() as session):
            employee = session.query(Employee).filter(Employee.personalnummer == personalnummer).first()

            if not employee:
                employee = Employee(name, personalnummer)
                session.add(employee)
                # session.commit()
                # session.refresh(employee)

            return employee

    def get_watched_psp_numbers(self):

        with (self.session_scope() as session):
            stmt_project_ids = select(distinct(user2projects.c.right_id))
            project_ids_result = session.execute(stmt_project_ids).fetchall()

            # Ergebnis verarbeiten und Projekt-IDs extrahieren
            project_ids = [row[0] for row in project_ids_result]

            if project_ids:  # Nur wenn es Projekt-IDs gibt
                projects = session.query(Project).filter(Project.id.in_(project_ids)).all()

                blas = []
                p: Project
                for p in projects:
                    bla = p.psp, p.project_datas[0].laufzeit_von
                    blas.append(bla)

                return blas
            else:
                return None

    def get_issues(self, psp, json_format):
        with (self.session_scope() as session):
            issues = session.query(ProjectIssue).filter(ProjectIssue.psp == psp).all()

            dtos = []
            for i in issues:
                dtos.append(ProjectIssueDTO.create_from_db(i))

            if json_format:
                return json.dumps(dtos, default=data_helper.serialize)
            else:
                return dtos

    def save_issue(self, psp, type, issue):
        with (self.session_scope() as session):
            pi = ProjectIssue(psp, "mpspe", issue)
            session.add(pi)
            session.commit()

    def delete_issues(self, psp):
        with self.session_scope() as session:
            try:
                issuess = session.query(ProjectIssue).filter(ProjectIssue.psp == psp).all()

                for i in issuess:
                    session.delete(i)

                session.commit()

            except IntegrityError as e:
                # Behandle den Fehler speziell für Integritätsverletzungen
                session.rollback()
                print(f"Fehler während der Transaktion: {e}")
                result = DbResult(False, e)
                return result

            return DbResult(True, "Issues have been deleted")

def _sum_stunden_umsatz_for_group(group_list):
    # Summen berechnen
    stunden_sum = sum(item.stunden for item in group_list)
    umsatz_sum = sum(item.umsatz for item in group_list)

    return stunden_sum, umsatz_sum