import logging
import os
import threading
import time
from datetime import timedelta, datetime

import schedule
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from sqlalchemy import create_engine, Engine

from src.projector_backend.endpoints.bp_absence import create_absence_blueprint
from src.projector_backend.endpoints.bp_bookings import create_bookings_blueprint
from src.projector_backend.endpoints.bp_bundles import create_bundles_blueprint
from src.projector_backend.endpoints.bp_forecast import create_forecast_blueprint
from src.projector_backend.endpoints.bp_init import create_init_blueprint
from src.projector_backend.endpoints.bp_logging import create_auth_blueprint
from src.projector_backend.endpoints.bp_package import create_package_blueprint
from src.projector_backend.endpoints.bp_project import create_project_blueprint
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.helpers import date_helper
from src.projector_backend.helpers.decorators import admin_required
from src.projector_backend.services.DWService import DWService
from src.projector_backend.services.UserService import UserService
from src.projector_backend.services.auth_service import AuthService
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.db_service import DBService
from src.projector_backend.services.projekt_service import ProjektService

app = Flask(__name__)
origin = os.environ.get("ORIGIN")
api_url = os.environ.get("API_URL")
api_user = os.environ.get("API_USER")
api_password = os.environ.get("API_PW")

# Security settings
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
app.config['JWT_BLACKLIST_ENABLED'] = False

app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Optional, wenn du CSRF-Schutz für Cookies deaktivieren möchtest
# app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies", "json", "query_string"]
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

jwt = JWTManager(app)

blocklist = []


# Benutzerdefinierte Callback-Funktion für das Token-Refresh
@jwt.token_in_blocklist_loader
def token_in_blocklist_loader(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blocklist


# Base.metadata.create_all(engine)
# logging.basicConfig()
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%d/%b/%Y %H:%M:%S')

logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# Replace with your MySQL credentials
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
host = os.environ.get("DB_HOST")
database = os.environ.get("DB_DB")

# DB-Settings
engine: Engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}?sql_mode=", pool_size=20,
                               max_overflow=0)


# Init Services
authService = AuthService()
dbservice = DBService(engine)
dwservice = DWService()
pservice = ProjektService(engine, authService)
cservice = CalendarService(engine)
uservice = UserService(engine, authService)
excelhelper = EhBuchungen()

# Register blueprints
login_bp = create_auth_blueprint(jwt, uservice)
bundle_bp = create_bundles_blueprint(pservice)
init_bp = create_init_blueprint(engine, pservice, dbservice, uservice)
project_bp = create_project_blueprint(pservice)
package_bp = create_package_blueprint(pservice)
absence_bp = create_absence_blueprint(cservice)
bookings_bp = create_bookings_blueprint(pservice, excelhelper)
forecast_bp = create_forecast_blueprint(pservice)

app.register_blueprint(login_bp)
app.register_blueprint(bundle_bp)
app.register_blueprint(init_bp)
app.register_blueprint(project_bp)
app.register_blueprint(package_bp)
app.register_blueprint(absence_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(forecast_bp)


@app.route('/')
def hello_world():
    return jsonify(message="Hi - this is Projectorrr backend.!")


# @app.route('/origin')
# def origin():
#     print("ORIGIN-CALL: " + request.headers.get('Origin'))
#     return jsonify(message=request.headers.get('Origin'))


@app.route('/callAPI', methods=['GET'])
@jwt_required()
@admin_required()
def restme():
    return _callAPI()


def _callAPI():
    uploadDatum = datetime.now()

    psp_infos = pservice.get_watched_psp_numbers()
    logger.info("Der automatische API-Buchungsupload wurde um " + date_helper.from_date_to_string_extended(
        uploadDatum) + " Uhr ausgefuehrt.")

    for pro in psp_infos:

        month = pro[1][3:5]
        year = pro[1][6:]
        search_start = year + month

        aktuelles_jahr = datetime.now().year
        such_start_jahr = int(year)

        call_old_data_from_db = False

        if such_start_jahr < aktuelles_jahr:
            search_start = str(aktuelles_jahr) + "01"
            call_old_data_from_db = True

        logger.info(f"Rufe Daten fuer PSP {pro[0]} ab (Start: {search_start})")
        booking_dtos, connection_state = dwservice.call_bookings_from_data_warehouse(api_url, api_user, api_password,
                                                                                     uploadDatum, pro[0], search_start)

        if connection_state == "success":
            if call_old_data_from_db:
                all_booking_dtos = pservice.get_bookings_for_psp(pro[0], False)

                # Objekte mit Uploaddatum im aktuellen Jahr entfernen
                all_booking_dtos = [buchung for buchung in all_booking_dtos if buchung.datum.year != aktuelles_jahr]

                for b in all_booking_dtos:
                    b.uploaddatum = uploadDatum

                if booking_dtos:
                    booking_dtos = booking_dtos + all_booking_dtos
                else:
                    booking_dtos = all_booking_dtos

            if booking_dtos:
                missing_psp_elements_list, dbResult = pservice.create_new_bookings_from_dtos_and_save(booking_dtos)
                if dbResult.complete:
                    # Alte issues löschen
                    pservice.delete_issues(pro[0])

                    if len(missing_psp_elements_list) > 0:
                        logger.info(f"Folgende PSP-Elemente fehlen fuer das PSP {pro[0]}:")
                        for mpe in missing_psp_elements_list:
                            logger.info("\t" + mpe)
                            pservice.save_issue(pro[0], "mpspe", mpe)

                else:
                    logger.info(f"Der Upload für PSP {pro[0]} war nicht erfolgreich! Fehler:")
                    logger.info(dbResult.message)
            else:
                logger.info(f"Fuer PSP {pro[0]} gibt es keine Buchungen.")
        elif connection_state == "wc":
            logger.info(f"Die Zugangsdaten werden nicht akzeptiert. ({pro[0]})")

        else:
            logger.info(
                "Der Upload war nicht erfolgreich! Fehler: es konnte keine Verbindung zum DataWarehouse hergestellt werden.")

    return jsonify(message="Done.")
