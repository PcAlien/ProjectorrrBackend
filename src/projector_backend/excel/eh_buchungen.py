import datetime
from types import NoneType

from openpyxl.cell import Cell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.entities.ImportFileColumns import ImportFileColumns
from src.projector_backend.excel.excelhelper import ExcelHelper


class EhBuchungen(ExcelHelper):

    def create_bookings_from_export(self, source_file_path: str, ifc: ImportFileColumns) -> [BookingDTO]:

        wb: Workbook = self.load_workbook(source_file_path)

        ws: Worksheet = wb.active
        bookingDTOs: [BookingDTO] = []

        if ifc.delete_empty_lines:
            self._delete_summary_rows(ws)

        uploadDatum = datetime.datetime.now()

        for row in ws.iter_rows(values_only=True, min_row=2):
            dto = BookingDTO(
                row[ifc.name],
                row[ifc.personalnummer],
                row[ifc.leistungsdatum],
                row[ifc.fakturierbar],
                row[ifc.status],
                row[ifc.bezeichnung],
                row[ifc.psp],
                row[ifc.psp_element],
                row[ifc.stunden],
                row[ifc.text],
                row[ifc.erfasst_am],
                row[ifc.letzte_aenderung],
                uploaddatum=uploadDatum
            )
            bookingDTOs.append(dto)

        return bookingDTOs









    def _delete_summary_rows(self, sheet: Worksheet):
        toDelete = []
        for i, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            cell: Cell
            if type(row[1]) is NoneType:
                toDelete.append(i)
            else:
                if row[1].isspace() or row[1] == "":
                    toDelete.append(i)

        # delete useless rows
        for counter, rowNumber in enumerate(toDelete):
            sheet.delete_rows(rowNumber - counter)
            counter += 1

        # TODO: lässt sich das kürzen?
