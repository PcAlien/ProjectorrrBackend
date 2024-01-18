import json
import logging
from datetime import date, datetime

from flask import Flask, request
from flask_cors import CORS
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename

from dto.booking_dto import BookingDTO
from dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from entities.Base import Base
from excel.eh_projektmeldung import EhProjektmeldung
from helpers.unfertig.employee_summary import EmployeeSummary
from services.booking_service import BookingService
from services.db_service import DBService
from services.projekt_service import ProjektService
from helpers import data_helper

app = Flask(__name__)
CORS(app)

engine = create_engine("sqlite:///datenbank.db", echo=True)
Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

pservice = ProjektService(engine)
bservice = BookingService(engine)
dbservice = DBService(engine)




def convert_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        employee_summary = EmployeeSummary(**json_data)
        return employee_summary


@app.route('/')
def hello_world():  # put application's code here

    #create_init_data()
    #bservice.get_latest_bookings_for_psp("11828", True)

    return "OK"

@app.route('/project_summary', methods=['GET'])
def get_project_summary():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_project_summary(psp, True)
    return back


@app.route('/buchungen',  methods=['GET'])
def gib_buchungen():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_bookings_for_psp(psp, True)
    return back

@app.route('/monatsbuchungen', methods=['GET'])
def gib_monatsbuchungen():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_bookings_for_psp_by_month(psp, True)
    return back

@app.route('/maBookingsSummary', methods=['GET'])
def get_ma_bookings_summary():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_ma_bookings_summary_for_psp(psp, True)
    return back



def _lade_demoprojekte():
    # Schritt 1: kann ein JSON String in ein BookingDTO umgewandelt werden?
    json_data = data_helper.read_json_file("helpers/json_templates/demoprojekte.json")
    projekte: [ProjektDTO] = []

    for pro in json_data:

        pmas: [ProjektmitarbeiterDTO] = []

        for pma in pro["projektmitarbeiter"]:
            pmas.append(
                ProjektmitarbeiterDTO(pma["personalnummer"], pma["name"], pma["psp_bezeichnung"], pma["psp_element"],
                                      pma["stundensatz"], pma["stundenbudget"], pma["laufzeit_von"],
                                      pma["laufzeit_bis"]))

        projekte.append(
            ProjektDTO(pro["projekt_name"], pro["psp"], pro["volumen"], pro["laufzeit_von"], pro["laufzeit_bis"], pmas))

    for p in projekte:
        pservice.create_new_from_dto_and_save(p)


def _lade_demobuchungen() -> str:
    # Schritt 1:
    json_data = data_helper.read_json_file("helpers/json_templates/examples/bookings.json")
    uploadDatum = datetime.now()

    for booking in json_data:
        dto = BookingDTO(booking["name"],
                         booking["personalnummer"],
                         booking["datum"],
                         booking["berechnungsmotiv"],
                         booking["bearbeitungsstatus"],
                         booking["bezeichnung"],
                         booking["psp"],
                         booking["pspElement"],
                         booking["stunden"],
                         booking["text"],
                         booking["erstelltAm"],
                         booking["letzteAenderung"],
                         uploaddatum=uploadDatum)
        bservice.create_new_from_dto_and_save(dto)


@app.route('/projektupload', methods=["POST"])
def projektupload():  # put application's code here
    # Überprüfe, ob die POST-Anfrage eine Datei enthält
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    json_projektdaten = json.loads(request.form['basis'])
    print(json_projektdaten)

    # Überprüfe, ob eine Datei ausgewählt wurde
    if file.filename == '':
        return 'No selected file', 400
    # file.stream

    # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
    filename = secure_filename(file.filename)

    # Speichere die Datei im Upload-Ordner
    file.save("./uploads/" + filename)

    eh = EhProjektmeldung()
    pmas = eh.create_pms_from_export("./uploads/" + filename)

    dto = ProjektDTO(**json_projektdaten)
    dto.projektmitarbeiter = pmas

    neuesDTO = pservice.create_new_from_dto_and_save(dto)

    neues_json = json.dumps(neuesDTO, default=data_helper.serialize)

    return {'status': 200,
            'answer': "File uploaded successfully",
            'Antwort': neues_json}


@app.route('/bookingsupload', methods=["POST"])
def bookings_upload():
    # Überprüfe, ob die POST-Anfrage eine Datei enthält
    if 'bookings_file' not in request.files:
        return 'No file part', 400

    file = request.files['bookings_file']

    json_buchungsdaten = json.loads(request.form['base_data_booking'])

    # Überprüfe, ob eine Datei ausgewählt wurde
    if file.filename == '':
        return 'No selected file', 400

    # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
    filename = secure_filename(file.filename)

    # Speichere die Datei im Upload-Ordner
    file.save("./uploads/" + filename)

    bservice.convert_bookings_from_excel_export(filename, 1)

    # todo

    return {'status': 200,
            'answer': "File uploaded successfully",
            'Antwort': "Alles paletti"}


def create_init_data():
    dbservice.create_import_settings()
    _lade_demoprojekte()
    _lade_demobuchungen()


if __name__ == '__main__':
    app.run()
