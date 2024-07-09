import datetime
from typing import Type
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
    def getInstance(cls: Type['DWService']) -> 'DWService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def callBookingsFromDataWarehouse(self, url, username, password, uploadDatum, project_info) -> [BookingDTO]:


        month= project_info[1][3:5]
        year= project_info[1][6:]
        search_start = year + month
        search_end = str(datetime.datetime.now().year) + "12"
        url = url.replace("STARTMONTH", search_start)
        url = url.replace("ENDMONTH", search_end)
        url = url.replace("SEARCHPSP", project_info[0])

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

            return bookingDTOs
        except Exception:
            return None
