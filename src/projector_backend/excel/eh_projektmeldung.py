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

        errors = []
        warnings = []

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

                pma = ProjektmitarbeiterDTO(str(id), name, bezeichnung, psp_element, stundensatz, stundenbudet, laufzeit_von,
                                            laufzeit_bis)

                if not psp_element or psp_element is None:
                    errors.append("Es konnte kein PSP-ELement für "+ name + " gefunden werden.")
                    continue

                if not laufzeit_bis or laufzeit_bis is None:
                    errors.append("Es wurde kein Laufzeit-bis Datum für " +name + " angegeben.")
                    continue

                if not laufzeit_von or laufzeit_von is None:
                    errors.append("Es wurde kein Laufzeit-von Datum für " +name + " angegeben.")
                    continue


                if not bezeichnung or bezeichnung is None:
                    warnings.append("Für das PSP Element " + psp_element + " wurde keine PSP-Bezeichnung hinterlegt.")
                    if stundensatz == 0:
                        pma.psp_bezeichnung = "NF Stunden - " + name
                    else:
                        pma.psp_bezeichnung = "Stundensatz:  " + str(stundensatz) + " € für "+ name


                pmas.append(pma)



        return pmas, errors, warnings
