from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.projector_backend.dto.projekt_dto import ProjektmitarbeiterDTO
from src.projector_backend.entities.project_ent import ProjectEmployee
from src.projector_backend.excel.excelhelper import ExcelHelper


class EhProjektmeldung(ExcelHelper):

    def create_pms_from_export(self, source) -> [ProjektmitarbeiterDTO]:

        #### ACHTUNG: bezieht sich auf den Excel-Export der "PSP ELement eintragen" Ansicht!!!!
        ### TODO: Abfangen, wenn es andere Dateien sind.

        wb: Workbook = self.load_workbook(source)

        ws: Worksheet = wb.active
        pmas: [ProjectEmployee] = []

        for row in ws.iter_rows(values_only=True, min_row=2):
            if row[1] != None:
                mitarbeiter_und_id = row[0]
                id = int(mitarbeiter_und_id[:5])
                name = mitarbeiter_und_id[8:]
                stundensatz = row[1]
                stundenbudet = row[3]
                psp_element = row[4]
                bezeichnung = row[5]
                laufzeit_von = row[6]
                laufzeit_bis = row[7]

                pma = ProjektmitarbeiterDTO(id, name, bezeichnung, psp_element, stundensatz, stundenbudet, laufzeit_von,
                                            laufzeit_bis)
                pmas.append(pma)

        return pmas
