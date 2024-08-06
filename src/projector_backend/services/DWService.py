import datetime
from typing import Type, Tuple
import requests
from requests.auth import HTTPBasicAuth

from src.projector_backend.dto.abwesenheiten import EmployeeDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO
from src.projector_backend.helpers import date_helper


class DWService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DWService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls: Type['DWService']) -> 'DWService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def call_bookings_from_data_warehouse(self, url, username, password, uploadDatum, psp, search_start):

        search_end = str(datetime.datetime.now().year) + "12"
        url = url.replace("STARTMONTH", search_start)
        url = url.replace("ENDMONTH", search_end)
        url = url.replace("SEARCHPSP", psp)

        try:
            response = requests.get(url, auth=HTTPBasicAuth(username, password))
            bookingDTOs = []
            if response.status_code == 200:
                bookings = response.json()

                for booking in bookings:
                    employeeName = booking.get('ENAME')
                    employeePsnr = int(booking.get('PERNR'))
                    workdate = date_helper.from_dw_date_string_to_date_without_time(booking.get('WORKDATE'))
                    berechnungsmotiv = booking.get('BEMOT')
                    bearbeitungsstatus = booking.get('STATUS')
                    bezeichnung = booking.get('CPR_OBJGEXTID')
                    psp = booking.get('CPR_GUID')
                    pspElement = booking.get('POSID')
                    stunden = booking.get('CATSHOURS')  # TODO oder CATSQUANTITY???
                    text = booking.get('TXLINE')
                    ##erstelltAm = booking.get('CPR_OBJGEXTID') #  gibts nicht
                    letzteAenderung = date_helper.from_dw_date_string_to_date_without_time(booking.get('LAEDA'))
                    counter = booking.get('COUNTER')

                    dto = BookingDTO(EmployeeDTO(employeeName, employeePsnr),
                                     workdate,
                                     berechnungsmotiv,
                                     bearbeitungsstatus,
                                     bezeichnung,
                                     psp,
                                     pspElement,
                                     stunden,
                                     text,
                                     None,
                                     letzteAenderung,
                                     counter,
                                     uploaddatum=uploadDatum
                                     )

                    if dto.erstelltAm == None:
                        dto.erstelltAm = dto.letzteAenderung
                    bookingDTOs.append(dto)
                return bookingDTOs, "success"

            else:
                return None, "wc"

        except Exception:
            return None, "nc"
