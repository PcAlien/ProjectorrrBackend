from datetime import datetime

from dto.abwesenheiten import AbwesenheitDTO, AbwesenheitDetailsDTO
from entities.abwesenheit_db import AbwesenheitDetails, Abwesenheit
from helpers import data_helper
from services.calender_service import CalendarService
from services.db_service import DBService


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


