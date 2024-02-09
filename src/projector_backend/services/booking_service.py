import json
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter
from typing import Type, Tuple, List

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.projector_backend.dto.abwesenheiten import AbwesenheitDTO, AbwesenheitDetailsDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.calendar_data import CalenderData
from src.projector_backend.dto.erfassungsnachweise import ErfassungsnachweisDTO
from src.projector_backend.dto.forecast_dto import PspElementDayForecast, ForecastDayView, PspForecastDTO, MaDurchschnittsarbeitszeitDTO
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO, MaBookingsSummaryElementDTO
from src.projector_backend.dto.monatsaufteilung_dto import MonatsaufteilungSummaryDTO, MonatsaufteilungDTO
from src.projector_backend.dto.project_summary import ProjectSummaryDTO, UmsatzDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.entities.booking import Booking
from src.projector_backend.entities.projekt import Projekt
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.helpers import data_helper, date_helper
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.db_service import DBService
from src.projector_backend.services.projekt_service import ProjektService
from src.projector_backend.services.tempclasses import Ma_Zwischenspeicher


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

    def create_new_from_dtos_and_save(self, bookingDTOs: [BookingDTO]) -> DbResult:
        """
        Erstellt einen neuen Buchungseintrag in der DB .
        :param bookingDTOs: die DTOs elches in die DB übertragen werden sollen
        :return: Ergebnis des Datenbankaufrufs.
        """

        ps = ProjektService.getInstance()
        project_dtos: [ProjektDTO] = ps.get_all_projects(False)

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

            pmaDTO = ps.get_pma_for_psp_element(bookingDTO.pspElement)
            bookingDTO.stundensatz = pmaDTO.stundensatz
            bookingDTO.umsatz = bookingDTO.stundensatz * bookingDTO.stunden

            buchung = Booking(bookingDTO.name, bookingDTO.personalnummer, bookingDTO.datum, bookingDTO.berechnungsmotiv,
                              bookingDTO.bearbeitungsstatus, bookingDTO.bezeichnung, bookingDTO.psp,
                              bookingDTO.pspElement,
                              bookingDTO.stunden, bookingDTO.text, bookingDTO.erstelltAm, bookingDTO.letzteAenderung,
                              bookingDTO.stundensatz, bookingDTO.umsatz, bookingDTO.uploaddatum)
            buchungen.append(buchung)

        session = sessionmaker(bind=self.engine)

        with session() as session:
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

        ps = ProjektService.getInstance()
        project_dtos: [ProjektDTO] = ps.get_all_projects(False)

        pro: ProjektDTO

        found = False
        for pro in project_dtos:
            if pro.psp == bookingDTO.psp:
                found = True
                break

        if not found:
            return bookingDTO.psp

        pmaDTO = ps.get_pma_for_psp_element(bookingDTO.pspElement)
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


    def get_bookings_for_psp_by_month(self,psp:str, json_format:bool) -> [MonatsaufteilungDTO] or str:
        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)

        monatsaufteilung_dtos: [MonatsaufteilungDTO] = []

        dto: BookingDTO
        for dto in booking_dtos:
            monat_jahr_str = f"{dto.datum.month}.{dto.datum.year}"
            gesuchtes_dto = next((element for element in monatsaufteilung_dtos if element.monat == monat_jahr_str), None)
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

    def get_project_summary(self, psp: str, json_format: bool) -> ProjectSummaryDTO or str:
        monatsaufteilung_dtos: [MonatsaufteilungSummaryDTO] = self.get_bookings_summary_for_psp_by_month(psp, False)
        # restbudget
        project_dto: ProjektDTO = ProjektService.getInstance().get_project_by_psp(psp, False)

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

    def get_project_summaries(self, json_format: bool, archiviert = False) -> [ProjectSummaryDTO]:
        if archiviert:
            projekte = ProjektService.getInstance().get_archived_projects(False)
        else:
            projekte = ProjektService.getInstance().get_active_projects(False)
        ps_dtos = []
        for pro in projekte:
            ps_dtos.append(self.get_project_summary(pro.psp, False))

        if json_format:
            return json.dumps(ps_dtos, default=data_helper.serialize)
        else:
            return ps_dtos




    def convert_bookings_from_excel_export(self, filename: str) -> Tuple[List[str], DbResult]:
        bookingDTOs: [BookingDTO] = self.helper.create_bookings_from_export("uploads/" + filename)
        dto: BookingDTO

        missing_psps: {str} = ProjektService.getInstance().get_missing_project_psp_for_bookings(bookingDTOs)

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

        projektDTO: ProjektDTO = ProjektService.getInstance().get_project_by_psp(psp, False)
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

    def erstelle_erfassungsauswertung(self, psp, json_format: bool) -> ErfassungsnachweisDTO or str:
        projekt_dto: ProjektDTO = ProjektService.getInstance().get_project_by_psp(psp, False)

        laufzeit_date = date_helper.from_string_to_date_without_time(projekt_dto.laufzeit_von)
        anzahl_tage_seit_projektstart = (datetime.now().date() - laufzeit_date).days

        booking_dtos: [BookingDTO] = self.get_bookings_for_psp(psp, False)

        # vorfiltern --> Datum
        jetzt = datetime.now()
        jetzt_um_null_uhr = datetime(year=jetzt.year, month=jetzt.month, day=jetzt.day, minute=0, hour=0, second=0)

        sechs_tage = timedelta(days=6)

        suchzeit = jetzt - timedelta(days=10)
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
            if b.datum >= suchzeit:
                filtered_booking_dtos.append(b)

        # grouped_booking_by_personalnummer = {key: list(group) for key, group in groupby(filtered_booking_dtos, key=lambda x: x.personalnummer)}
        #
        # for psnr, group in grouped_booking_by_personalnummer.items():
        #     bo:BookingDTO
        #     for bo in group:
        #         grouped_booking_by_date = {key: list(group) for key, group in groupby(filtered_booking_dtos, key=lambda x: x.datum)}
        #         for datum, g2 in grouped_booking_by_date:
        #             bo2:BookingDTO
        #             sum = 0
        #             for bo2 in g2:
        #                 sum += bo2.stunden

        # personr / tag

        # alle Personalnummern rausholen:
        nachweise: [ErfassungsnachweisDTO] = []

        # vorher filtern

        pmas = dict()
        for pma in projekt_dto.projektmitarbeiter:
            pmas[pma.personalnummer] = pma.name

        CalendarService.getInstance().get_calender_data()

        for pnummer, name in pmas.items():
            stunden: [float or str] = []

            abwesenheiten: [AbwesenheitDTO] = CalendarService.getInstance().get_abwesenheiten_for_psnr(pnummer, False)
            for gesuchtesDatum in suchtage:
                found = False
                for abw in abwesenheiten:
                    if abw.personalnummer == pnummer:
                        for x in abw.abwesenheitDetails:
                            d = date_helper.from_date_to_string(gesuchtesDatum)
                            if x.datum == d:
                                stunden.append(x.typ)
                                found = True
                                break

                if not found:
                    gesammelte_stunden = 0.0
                    for b in filtered_booking_dtos:
                        if b.personalnummer == pnummer and b.datum == gesuchtesDatum:
                            gesammelte_stunden += b.stunden
                    stunden.append(gesammelte_stunden)

            edto = ErfassungsnachweisDTO(name, pnummer, suchtage, stunden)
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
