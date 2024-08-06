from datetime import timedelta, datetime

from src.projector_backend.dto.abwesenheiten import AbwesenheitDetailsDTO, AbwesenheitDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.calendar_data import CalenderData
from src.projector_backend.dto.forecast_dto import PspForecastDTO,  ForecastDayView, PspElementDayForecast
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.helpers import date_helper
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.tempclasses import Ma_Zwischenspeicher_DTO, MaDailyAvgDTO


class ForecastService:

    def create_forecast_by_alltime_avg(self, psp, booking_dtos: [BookingDTO], projekt_dto: ProjektDTO) -> PspForecastDTO:
        """
        Es wird für jeden Mitarbeiter errechnet, wie viel Stunden er am Tag arbeiten und welchen Umsatz er dabei macht.
        Grundlage sind dabei alle Buchungen von Projektbeginn an.
        Daraus wird ein PspForecastDTO erstellt, welches unter anderem angibt, wann das Budget aufgebraucht sein wird.
        :param projekt_dto:
        :param booking_dtos:
        :param psp: TODO
        :return: TODO
        """

        # 1. Alle Buchungen zu einem PSP beziehen
        b: BookingDTO

        ma_dict: dict = {}
        ma_durchschnitt_dtos: [MaDailyAvgDTO] = []
        mas_without_entries: set = set()

        # 2. Ein Dict erstellen, um alle erfassten Stunden und Tage eines MA aufzuaddieren.
        # Dies dient als Vorbereitung zur Ermittlung des Tagesdurchschnittwerts.

        ma_dict = self._get_ma_dict(booking_dtos)

        v: Ma_Zwischenspeicher_DTO
        for k, v in ma_dict.items():
            # Pro Mitarbeiter bzw. pro PSP Element tägliche Durchschnittswerte ausrechnen
            ma_durchschnitt_dtos.append(
                MaDailyAvgDTO((v.stunden / v.tage),(v.stundensatz * (v.stunden / v.tage))))

        # 3. Errechnen, was je tag verbraucht wird unter Berücksichtigung der Urlaube.
        calender_data: CalenderData = CalendarService.get_instance().get_calender_data(False)

        ein_tag = timedelta(days=1)

        datum_format = "%d.%m.%Y"
        # Datetime-Objekt erstellen und Uhrzeit auf Mitternacht setzen
        # psp_enddatum = datetime.strptime(projektDTO.laufzeit_bis, datum_format).replace(hour=0, minute=0, second=0,
        #                                                                                 microsecond=0)

        forecast_day_views: [ForecastDayView] = []

        '''
        Jeden Tag betrachten und dann Summe ziehen.
        '''
        betrachteter_tag = datetime.now() + ein_tag
        # Uhrzeit auf 0 setzen
        betrachteter_tag = datetime(day=betrachteter_tag.day, month=betrachteter_tag.month,
                                    year=betrachteter_tag.year)
        betrachteter_tag_str = betrachteter_tag.strftime(datum_format)

        psp_element_to_gesamtumsatz_dict: dict = {}

        # TODO: Abbruchbedingung optimieren...
        fertig = False
        while (not fertig):
            psp_element_day_forecasts: [PspElementDayForecast] = []

            # für jeden Projektmitarbeiter
            ma: ProjektmitarbeiterDTO
            for ma in projekt_dto.projektmitarbeiter:

                # Es kann vorkommen, dass Mitarbeiter dem Projekt angehören, aber noch nicht erfasst haben.
                if ma.psp_element in ma_dict.keys():

                    if ma.psp_element not in psp_element_to_gesamtumsatz_dict.keys():
                        psp_element_to_gesamtumsatz_dict[ma.psp_element] = ma_dict[ma.psp_element].stunden * ma_dict[
                            ma.psp_element].stundensatz

                    durchschnitts_tagesarbeitszeit: float = ma_dict[ma.psp_element].stunden / ma_dict[
                        ma.psp_element].tage

                    durchschnitts_tagesumsatz: float = durchschnitts_tagesarbeitszeit * ma_dict[
                        ma.psp_element].stundensatz

                    letzter_gesamtumsatz_ma: float = psp_element_to_gesamtumsatz_dict[ma.psp_element]

                    # Liste aller Abwesenheiten ( beinhaltet Datum, Person, Grund)
                    ma_abwesenheiten: [AbwesenheitDetailsDTO] = []

                    abw: AbwesenheitDTO
                    for abw in calender_data.abwesenheiten:
                        if abw.employee.personalnummer == ma.employee.personalnummer:
                            ma_abwesenheiten = abw.abwesenheitDetails

                    # Datum betrachten: wird es ein WE Tag, ein Urlaubstag, ein Abwesenheitstag sein? Falls ja, kein Umsatz.

                    wochenende = betrachteter_tag.weekday() >= 5

                    abwesenheit_existiert = any(
                        abwesenheitDetails.datum == betrachteter_tag_str for abwesenheitDetails in ma_abwesenheiten)

                    # TODO: MA kommen aus unterschiedlichen Bundesländern und mit unterschiedlichen Feiertagsregelungen
                    feiertag_existiert = any(
                        feiertag.datum == betrachteter_tag_str for feiertag in calender_data.specialDays.feiertage)

                    if wochenende or abwesenheit_existiert or feiertag_existiert:
                        tagesumsatz = 0
                    else:
                        tagesumsatz = durchschnitts_tagesumsatz

                    letzter_gesamtumsatz_ma += tagesumsatz

                    pedf = PspElementDayForecast(betrachteter_tag, ma.employee.name, ma.employee.personalnummer, ma.psp_element,
                                                 tagesumsatz,
                                                 letzter_gesamtumsatz_ma)
                    psp_element_day_forecasts.append(pedf)
                    psp_element_to_gesamtumsatz_dict[ma.psp_element] = letzter_gesamtumsatz_ma

                else:
                    # Mitarbeiter (zu PSP Element) hat noch nichts erfasst.

                    psp_element_to_gesamtumsatz_dict[ma.psp_element] = 0
                    mas_without_entries.add(ma)

                    pedf = PspElementDayForecast(betrachteter_tag, ma.employee.name, ma.employee.personalnummer, ma.psp_element,
                                                 0,
                                                 0)
                    psp_element_day_forecasts.append(pedf)

            # jetzt auf den gesamten Tag betrachten
            fdv = ForecastDayView(betrachteter_tag, psp_element_day_forecasts)
            forecast_day_views.append(fdv)

            if fdv.summe >= projekt_dto.volumen:
                fertig = True
            else:
                betrachteter_tag = betrachteter_tag + ein_tag
                betrachteter_tag_str = betrachteter_tag.strftime(datum_format)

        pfcdto = PspForecastDTO(projekt_dto, forecast_day_views, mas_without_entries)

        return pfcdto

    def create_forecast_by_projektmeldung(self, booking_dtos: [BookingDTO],
                                          projektDTO: ProjektDTO) -> PspForecastDTO:

        # Datenbasis
        ma_dict = self._get_ma_dict(booking_dtos)

        # Zuerst muss für jeden Projektmitarbeiter ausgerechnet werden, wie viele Stunden für ihn pro Tag vorgesehen sind.

        projektmitarbeiter_dtos: [ProjektmitarbeiterDTO] = projektDTO.projektmitarbeiter

        # Projektlaufzeit in Tagen errechnen
        startdatum = date_helper.from_string_to_date_without_time(projektDTO.laufzeit_von)
        enddatum = date_helper.from_string_to_date_without_time(projektDTO.laufzeit_bis)
        tage_im_projekt = (enddatum - startdatum).days

        # Errechnen, wie viele Stunden jeder MA pro Tag im Projekt arbeitet (auf PSP Element Ebene)

        # ma_durchschnitt_dtos: [MaDailyAvgDTO] = []
        # ma_to_avg: dict = {}
        for pm in projektmitarbeiter_dtos:
            ma_stunden_pro_tag = pm.stundenbudget / tage_im_projekt
            maDA = MaDailyAvgDTO(ma_stunden_pro_tag, ma_stunden_pro_tag * pm.stundensatz)
            # ma_durchschnitt_dtos.append(maDA)
            # ma_to_avg[pm.psp_element] = maDA

            if pm.psp_element not in ma_dict.keys():
                ma_dict[pm.psp_element] = Ma_Zwischenspeicher_DTO(pm.name, pm.personalnummer, pm.psp_element,
                                                                  pm.stundensatz, maDA)

            maz: Ma_Zwischenspeicher_DTO = ma_dict[pm.psp_element]
            if maz.calc_values_by_projektmeldung is None:
                maz.calc_values_by_projektmeldung = maDA

        # TODO Zwischenberechnung zur Kontrolle, wieder löschen
        #
        # tagessumme = 0
        # v: MaDailyAvgDTO
        # for k,v in ma_to_avg.items():
        #     tagessumme += v.durchschnitts_tagesumsatz
        #
        # print(tagessumme)

        mas_without_entries: set = set()

        # 3. Errechnen, was je tag verbraucht wird unter Berücksichtigung der Urlaube.
        calender_data: CalenderData = CalendarService.get_instance().get_calender_data(False)

        ein_tag = timedelta(days=1)
        datum_format = "%d.%m.%Y"
        forecast_day_views: [ForecastDayView] = []

        '''
        Jeden Tag betrachten und dann Summe ziehen.
        '''
        betrachteter_tag = datetime.now() + ein_tag
        # Uhrzeit auf 0 setzen
        betrachteter_tag = datetime(day=betrachteter_tag.day, month=betrachteter_tag.month,
                                    year=betrachteter_tag.year)
        betrachteter_tag_str = betrachteter_tag.strftime(datum_format)

        psp_element_to_gesamtumsatz_dict: dict = {}

        # Prüfen: manchmal haben nicht alle PSP Elemente einen Buchungseintrag, aber sie benötigen ja trotzdem
        # einen Durchschnittstageswert
        # ma_dict anpassen

        fertig = False
        while not fertig:
            psp_element_day_forecasts: [PspElementDayForecast] = []

            # für jeden Projektmitarbeiter bzw. jedes PSP-Element!
            ma: ProjektmitarbeiterDTO
            for ma in projektDTO.projektmitarbeiter:

                # if ma.psp_element in ma_dict.keys():
                # Das 'psp_element_to_gesamtumsatz_dict' speichert zu jeden PSP Element, den jeweils geplanten
                # erwirtschafteten Umsatz bis zum gerade betrachteten Datum.
                # Wird das PSP-Element zum ersten mal hier aufgerufen, ist die Berechnungsgrundlage natürlich
                # die bisher erbrachten Umsätze.
                if ma.psp_element not in psp_element_to_gesamtumsatz_dict.keys():
                    psp_element_to_gesamtumsatz_dict[ma.psp_element] = ma_dict[ma.psp_element].stunden * ma_dict[
                        ma.psp_element].stundensatz
                letzter_gesamtumsatz_ma: float = psp_element_to_gesamtumsatz_dict[ma.psp_element]

                # Liste aller Abwesenheiten ( beinhaltet Datum, Person, Grund)
                ma_abwesenheiten: [AbwesenheitDetailsDTO] = []

                # TODO: Muss das eigentlich immer wieder gemacht werden? Kann das nicht auserhalb der Schleife passieren?
                abw: AbwesenheitDTO
                for abw in calender_data.abwesenheiten:
                    if abw.employee.personalnummer == ma.employee.personalnummer:
                        ma_abwesenheiten = abw.abwesenheitDetails

                # Datum betrachten: wird es ein WE Tag, ein Urlaubstag, ein Abwesenheitstag sein? Falls ja, kein Umsatz.

                wochenende = betrachteter_tag.weekday() >= 5

                abwesenheit_existiert = any(
                    abwesenheitDetails.datum == betrachteter_tag_str for abwesenheitDetails in ma_abwesenheiten)

                # TODO: MA kommen aus unterschiedlichen Bundesländern und mit unterschiedlichen Feiertagsregelungen
                feiertag_existiert = any(
                    feiertag.datum == betrachteter_tag_str for feiertag in calender_data.specialDays.feiertage)

                if wochenende or abwesenheit_existiert or feiertag_existiert:
                    tagesumsatz = 0
                else:
                    tagesumsatz = ma_dict[ma.psp_element].calc_values_by_projektmeldung.durchschnitts_tagesumsatz

                letzter_gesamtumsatz_ma += tagesumsatz

                pedf = PspElementDayForecast(betrachteter_tag, ma.employee.name, ma.employee.personalnummer, ma.psp_element,
                                             tagesumsatz,
                                             letzter_gesamtumsatz_ma)
                psp_element_day_forecasts.append(pedf)
                psp_element_to_gesamtumsatz_dict[ma.psp_element] = letzter_gesamtumsatz_ma
            # else:
            #     # TODO: hier werden keine Abwesenheiten berücksichtigt
            #     if ma.psp_element not in psp_element_to_gesamtumsatz_dict.keys():
            #         # Alle bisher dato gesammelten Umsätze anlegen
            #         psp_element_to_gesamtumsatz_dict[ma.psp_element] = 0
            #     avg: MaDailyAvgDTO = ma_to_avg[ma.psp_element]
            #     durchschnitts_tagesumsatz = avg.durchschnitts_tagesumsatz
            #     psp_element_to_gesamtumsatz_dict[ma.psp_element] += durchschnitts_tagesumsatz
            #     mas_without_entries.add(ma)
            #
            #     pedf = PspElementDayForecast(betrachteter_tag, ma.name, ma.personalnummer, ma.psp_element,
            #                                  durchschnitts_tagesumsatz,
            #                                  psp_element_to_gesamtumsatz_dict[ma.psp_element])
            #     psp_element_day_forecasts.append(pedf)

            # jetzt auf den gesamten Tag betrachten
            fdv = ForecastDayView(betrachteter_tag, psp_element_day_forecasts)
            forecast_day_views.append(fdv)

            # print(fdv.tag, fdv.summe)
            if fdv.summe >= projektDTO.volumen:
                fertig = True
            else:
                betrachteter_tag = betrachteter_tag + ein_tag
                betrachteter_tag_str = betrachteter_tag.strftime(datum_format)

        pfcdto = PspForecastDTO(projektDTO, forecast_day_views, mas_without_entries)
        #pfcdto = PspForecastDTO(projektDTO, forecast_day_views, mas_without_entries, ma_durchschnitt_dtos)

        # for fdvv in forecast_day_views:
        #     if fdvv.tag == datetime(day=22, month=3, year=2024):
        #         fc: [PspElementDayForecast] = fdvv.personen
        #         for bla in fc:
        #             print(bla.tag, bla.name, bla.psp_element, bla.geschaetzter_tagesumsatz)

        return pfcdto

    def _get_ma_dict(self, booking_dtos):
        ma_dict: dict = {}
        for b in booking_dtos:
            if b.pspElement not in ma_dict.keys():
                ma_dict[b.pspElement] = Ma_Zwischenspeicher_DTO(b.name, b.personalnummer, b.pspElement, b.stundensatz)

            maz: Ma_Zwischenspeicher_DTO = ma_dict[b.pspElement]
            # TODO: Ausgehend davon, dass ein MA pro Tag nur eine Buchung macht.
            maz.add_stunden(b.stunden)

        return ma_dict
