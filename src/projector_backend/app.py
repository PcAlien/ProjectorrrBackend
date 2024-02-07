import json
import logging
import os
from datetime import datetime

from flask import Flask, request, send_file
from flask_cors import CORS
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename

from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.forecast_dto import PspForecastDTO, MaDurchschnittsarbeitszeitDTO
from src.projector_backend.entities.Base import Base
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.excel.eh_projektmeldung import EhProjektmeldung
from src.projector_backend.helpers import data_helper
from src.projector_backend.helpers.unfertig import demo_calender_data_importer
from src.projector_backend.helpers.unfertig.employee_summary import EmployeeSummary
from src.projector_backend.services.booking_service import BookingService
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.db_service import DBService
from src.projector_backend.services.projekt_service import ProjektService

app = Flask(__name__)
CORS(app)

engine = create_engine("sqlite:///db/datenbank.db", echo=True)
Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

pservice = ProjektService(engine)
bservice = BookingService(engine)
cservice = CalendarService(engine)
dbservice = DBService(engine)


def convert_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        employee_summary = EmployeeSummary(**json_data)
        return employee_summary


@app.route('/init')
def init_app():  # put application's code here

    create_init_data()
    # bservice.get_latest_bookings_for_psp("11828", True)

    return "OK"


@app.route('/')
def hello_world():  # put application's code here
    return "OK"


@app.route('/buchungen', methods=['GET'])
def gib_buchungen():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_bookings_for_psp(psp, True)
    return back


@app.route('/monatsbuchungen', methods=['GET'])
def gib_monatsbuchungen():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_bookings_summary_for_psp_by_month(psp, True)
    return back


@app.route('/maBookingsSummary', methods=['GET'])
def get_ma_bookings_summary():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_ma_bookings_summary_for_psp(psp, True)
    return back


@app.route('/projects', methods=['GET'])
def get_projects():  # put application's code here
    back = pservice.get_all_projects(True)
    return back



@app.route('/archivedProjects', methods=['GET'])
def get_archived_projects():  # put application's code here
    back = pservice.get_archived_projects(True)
    return back

@app.route('/project', methods=['GET'])
def get_project():  # put application's code here
    psp = request.args.get('psp')
    back = pservice.get_project_by_psp(psp, True)
    return back


@app.route('/project_summary', methods=['GET'])
def get_project_summary():  # put application's code here
    psp = request.args.get('psp')
    back = bservice.get_project_summary(psp, True)
    return back


@app.route('/project_summaries', methods=['GET'])
def get_project_summaries():  # put application's code here
    # psp = request.args.get('psp')
    back = bservice.get_project_summaries(True)
    return back

@app.route('/archived_project_summaries', methods=['GET'])
def get_archived_project_summaries():  # put application's code here
    # psp = request.args.get('psp')
    back = bservice.get_project_summaries(True, archiviert=True)
    return back

@app.route('/toggle_archived', methods=['GET'])
def toggle_archived():  # put application's code here
    psp = request.args.get('psp')
    back = pservice.toogle_archive_project(psp)
    return back



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

    neuesDTO, dbResult = pservice.save_update_project(dto)

    if dbResult.complete:
        project_json = json.dumps(neuesDTO, default=data_helper.serialize)
        return {'status': "Success", 'project': project_json}
    else:
        return {'status': "Error", 'error': dbResult.message}


@app.route('/editProject', methods=["POST"])
def edit_project():  # put application's code here

    json_projektdaten = json.loads(request.form['basis'])

    dto = ProjektDTO(**json_projektdaten)

    if 'file' in request.files:
        file = request.files['file']
        if file.filename != "":
            # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
            filename = secure_filename(file.filename)

            # Speichere die Datei im Upload-Ordner
            file.save("./uploads/" + filename)

            eh = EhProjektmeldung()
            pmas = eh.create_pms_from_export("./uploads/" + filename)
            dto.projektmitarbeiter = pmas



    neuesDTO, dbResult = pservice.save_update_project(dto, True)

    if dbResult.complete:
        project_json = json.dumps(neuesDTO, default=data_helper.serialize)
        return {'status': "Success", 'project': project_json}
    else:
        return {'status': "Error", 'error': dbResult.message}


def _lade_demoprojekte():
    # Schritt 1: kann ein JSON String in ein BookingDTO umgewandelt werden?
    json_data = data_helper.read_json_file("src/projector_backend/helpers/json_templates/demoprojekte.json")
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
        pservice.save_update_project(p)


def _lade_demobuchungen() -> str:
    # Schritt 1:
    json_data = data_helper.read_json_file("src/projector_backend/helpers/json_templates/examples/bookings.json")
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


def _lade_demoabwesenheiten() -> str:
    demo_calender_data_importer.run()


@app.route('/bookingsupload', methods=["POST"])
def bookings_upload():
    # Überprüfe, ob die POST-Anfrage eine Datei enthält
    if 'bookings_file' not in request.files:
        return 'No file part', 400

    file = request.files['bookings_file']

    # json_buchungsdaten = json.loads(request.form['base_data_booking'])

    # Überprüfe, ob eine Datei ausgewählt wurde
    if file.filename == '':
        return 'No selected file', 400

    # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
    filename = secure_filename(file.filename)

    # Speichere die Datei im Upload-Ordner
    file.save("./uploads/" + filename)

    missing_psps, dbResult = bservice.convert_bookings_from_excel_export(filename, 1)

    mpsp_str = ""
    if len(missing_psps) > 0:
        mpsp_str = missing_psps.__str__()
        print("Folgende PSPs fehlen:", mpsp_str)

    if (not dbResult.complete):
        return {'status': "Failed",
                'missingPSPs': mpsp_str,
                'error': dbResult.message
                }

    return {'status': "Success",
            'missingPSPs': mpsp_str,
            }


@app.route('/abwesenheiten', methods=["GET"])
def get_abwesenheiten():
    back = cservice.getInstance().get_calender_data(True)
    return back


@app.route('/addAbwesenheit', methods=["POST"])
def add_abwesenheit():
    abw = request.form.get("abwesenheit")
    cservice.getInstance().add_abwesenheit(abw)

    return {'answer': "Added Abwesenheit!!!"}


@app.route('/pspForecast', methods=["POST"])
def get_psp_forecast():
    psp = request.form.get("psp")
    back = bservice.getInstance().mach_forecast(psp, True)
    return back


@app.route('/pspForecastTest', methods=["GET"])
def get_psp_forecast_test():
    psp = "11828"
    back: PspForecastDTO = bservice.getInstance().mach_forecast(psp, False)

    durchschnitt = 0.0
    s: MaDurchschnittsarbeitszeitDTO
    for s in back.avg_tagesumsaetze:
        durchschnitt += s.durchschnitts_tagesumsatz

        formatted_string = str(s.durchschnitts_tagesumsatz).replace(".", ",")
        print(s.name, formatted_string)

    print(f"AVG Tagesumsatz: {durchschnitt}")

    return back


@app.route('/nachweise', methods=["GET"])
def get_nachweise():
    # psp = request.form.get("psp")
    back = bservice.getInstance().erstelle_erfassungsauswertung("11828", True)
    return back

@app.route('/exportExcel', methods=["GET"])
def create_export():
    psp = request.args.get('psp')

    eh =  EhBuchungen()
    filename = eh.export_buchungen(psp, bservice.get_bookings_for_psp(psp, False), bservice.get_bookings_for_psp_by_month(psp, False))

    file_path = os.path.join(os.getcwd(), 'exports', filename)

    # Verwende send_file, um die Datei als Antwort zu senden
    return send_file(file_path, as_attachment=True)

    # back = bservice.getInstance().erstelle_erfassungsauswertung(psp, True)
    # return back

def create_init_data():
    dbservice.create_import_settings()
    # _lade_demoprojekte()
    # _lade_demobuchungen()
    _lade_demoabwesenheiten()


if __name__ == '__main__':
    app.run()
