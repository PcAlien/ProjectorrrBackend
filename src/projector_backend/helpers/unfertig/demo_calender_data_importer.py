from datetime import datetime

from src.projector_backend.entities.abwesenheit_db import AbwesenheitDetails, Abwesenheit
from src.projector_backend.helpers import data_helper
from src.projector_backend.services.calender_service import CalendarService


def run():
    json_data = data_helper.read_json_file("./helpers/json_templates/demodata_abwesenheiten.json")
    uploadDatum = datetime.now()

    abs = []

    for item in json_data:

        personalnummer = item["personalnummer"]
        maName = item["name"]
        urlaube = item["urlaube"]
        abwesenheiten = item["abwesenheiten"]

        abwesenheitenDetailsList: [AbwesenheitDetails] = []
        a: str
        for a in abwesenheiten:
            abd = AbwesenheitDetails(a, "A", uploadDatum)
            abwesenheitenDetailsList.append(abd)

        for a in urlaube:
            abd = AbwesenheitDetails(a, "U", uploadDatum)
            abwesenheitenDetailsList.append(abd)

        ab: Abwesenheit = Abwesenheit(maName, personalnummer,"", abwesenheitenDetailsList, uploadDatum)
        abs.append(ab)

    CalendarService.getInstance().proceed_demodaten(abs)


