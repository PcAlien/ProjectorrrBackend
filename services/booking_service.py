import json
from itertools import groupby
from operator import attrgetter
from typing import Type

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from dto.booking_dto import BookingDTO
from dto.ma_bookings_summary_dto import MaBookingsSummaryDTO, MaBookingsSummaryElementDTO
from dto.monatsaufteilung_dto import MonatsaufteilungDTO
from dto.project_summary import ProjectSummaryDTO, UmsatzDTO
from dto.projekt_dto import ProjektDTO
from entities.booking import Booking
from excel.eh_buchungen import EhBuchungen
from helpers import data_helper
from services.db_service import DBService
from services.projekt_service import ProjektService


class BookingService:
    _instance = None

    def __new__(cls, engine):
        if cls._instance is None:
            cls._instance = super(BookingService, cls).__new__(cls)
            cls._instance.engine = engine
            cls._instance.helper = EhBuchungen()
        return cls._instance

    @classmethod
    def getInstance(cls: Type['BookingService']) -> 'BookingService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

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

    def create_new_from_dto_and_save(self, bookingDTO: BookingDTO) -> BookingDTO:
        """
        Erstellt einen neuen Buchungseintrag in der DB und gibt ein entsprechendes DTO zurück.
        :param bookingDTO: das DTO welches in die DB übertragen werden soll
        :return: neues DTO, mit Stundensatz, Umsatz und DB-Id
        """
        pmaDTO = ProjektService.getInstance().get_pma_for_psp_element(bookingDTO.pspElement)
        bookingDTO.stundensatz = pmaDTO.stundensatz
        bookingDTO.umsatz = bookingDTO.stundensatz * bookingDTO.stunden

        buchung = Booking(bookingDTO.name, bookingDTO.personalnummer, bookingDTO.datum, bookingDTO.berechnungsmotiv,
                          bookingDTO.bearbeitungsstatus, bookingDTO.bezeichnung, bookingDTO.psp, bookingDTO.pspElement,
                          bookingDTO.stunden, bookingDTO.text, bookingDTO.erstelltAm, bookingDTO.letzteAenderung,
                          bookingDTO.stundensatz, bookingDTO.umsatz, bookingDTO.uploaddatum)

        session = sessionmaker(bind=self.engine)

        with session() as session:
            session.add(buchung)
            session.commit()
            session.refresh(buchung)

        return BookingDTO.create_from_db(buchung)

    # def get_all_bookings_ever(self) -> [BookingDTO]:
    #     Session = sessionmaker(bind=self.engine)
    #     buchungenDTOs: [BookingDTO] = []
    #
    #     with Session() as session:
    #         buchungen = session.query(Booking).all()
    #         for buchung in buchungen:
    #             pma = ProjektService.getInstance().get_pma_for_psp_element(buchung.pspElement)
    #             buchungDTO = BookingDTO.create_from_db(buchung)
    #             buchungDTO.stundensatz = pma.stundensatz
    #             buchungDTO.umsatz = pma.stundensatz * buchung.stunden
    #             buchungenDTOs.append(buchungDTO)
    #
    #         return buchungenDTOs

    def get_bookings_for_psp(self, psp: str, json_format: bool) -> [BookingDTO] or str:
        """
        Liefert alle Buchungen zu einem PSP. Berücksichtigt werden dabei nur Buchungen mit dem jüngsten Uploaddatum.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn der Ergebnis im JSON Format zurückgegeben werden soll, ansonsten [BookingDTO]
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/bookings.json".
        """

        session = sessionmaker(bind=self.engine)

        with session() as session:
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
        """
        Liefert alle Buchungen zu einem PSP und teilt diese in Monate auf.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn das Ergebnis im JSON Format zurückgegeben werden soll
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/monatsaufteilung.json".
        """
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)
        monatsaufteilung_dto: [MonatsaufteilungDTO] = []

        dto: BookingDTO
        for dto in booking_dtos:
            divider = f"{dto.datum.month}.{dto.datum.year}"
            gesuchtes_dto = next((element for element in monatsaufteilung_dto if element.monat == divider), None)
            if gesuchtes_dto == None:
                gesuchtes_dto = MonatsaufteilungDTO(divider, MaBookingsSummaryDTO([], 0))
                monatsaufteilung_dto.append(gesuchtes_dto)

            ma_booking_summary_dto: [MaBookingsSummaryDTO] = gesuchtes_dto.maBookingsSummary
            sum: int = ma_booking_summary_dto.sum
            bookings: [MaBookingsSummaryElementDTO] = ma_booking_summary_dto.bookings
            x = MaBookingsSummaryElementDTO(dto.name, dto.personalnummer, dto.psp, dto.pspElement, dto.stundensatz,
                                            dto.stunden, dto.umsatz)
            bookings.append(x)
            sum += x.umsatz

        madtos_compressed: [MonatsaufteilungDTO] = []

        for madto in monatsaufteilung_dto:
            monat = madto.monat
            ma_booking_summary_dto = madto.maBookingsSummary
            sum_month = ma_booking_summary_dto.sum

            result: [MaBookingsSummaryElementDTO] = self._group_and_sum_by_psp_element(ma_booking_summary_dto.bookings)
            for dto in result:
                sum_month += dto.umsatz

            madtos_compressed.append(MonatsaufteilungDTO(monat, MaBookingsSummaryDTO(result, sum_month)))
        if (json_format):
            return json.dumps(madtos_compressed, default=data_helper.serialize)
        else:
            return madtos_compressed

    def get_ma_bookings_summary_for_psp(self, psp: str, json_format: bool) -> [BookingDTO] or str:
        """
        Liefert alle Buchung zu einem PSP und gruppiert diese nach den PSP-Elementen.
        :param psp: Das PSP, für das die Buchungen ausgegeben werden sollen.
        :param json_format: True, wenn das Ergebnis im JSON Format zurückgegeben werden soll.
        :return: Aktuelle Buchungen zum PSP. Der JSON String entspricht dabei "helpers/json_templates/mitarbeiteruebersicht.json".
        """

        session = sessionmaker(bind=self.engine)

        with session() as session:

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

    def get_project_summary(self, psp: str, json_format=bool) ->  ProjectSummaryDTO or str:
        monatsaufteilung_dtos: [MonatsaufteilungDTO] = self.get_bookings_for_psp_by_month(psp, False)
        # restbudget
        project_dto: ProjektDTO = ProjektService.getInstance().get_project_by_psp(psp)

        ps_dto: ProjectSummaryDTO = ProjectSummaryDTO(psp, project_dto.volumen, 0, project_dto.volumen, [])
        restbudget = ps_dto.restbudget
        sum_verbraucht = 0
        umsaetze_dtos: [UmsatzDTO] = ps_dto.umsaetze

        ma_dto: MonatsaufteilungDTO
        for ma_dto in monatsaufteilung_dtos:
            umsaetze_dtos.append(UmsatzDTO(ma_dto.monat, ma_dto.maBookingsSummary.sum))
            sum_verbraucht += ma_dto.maBookingsSummary.sum

        restbudget -= sum_verbraucht
        ps_dto.spent = sum_verbraucht
        ps_dto.restbudget = restbudget


        if json_format:
            return json.dumps(ps_dto, default=data_helper.serialize)
        else:
            return ps_dto




    def convert_bookings_from_excel_export(self, filename: str, export_type: int):
        """
        TODO: Export type noch berücksichtigen
        :param filename:
        :param export_type:
        :return:
        """
        ifc = DBService.getInstance().get_import_settings(1)
        bookingDTOs: [BookingDTO] = self.helper.create_bookings_from_export("uploads/" + filename, ifc)
        dto: BookingDTO
        for dto in bookingDTOs:
            self.create_new_from_dto_and_save(dto)
