import json
import logging
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from sqlalchemy import create_engine

from src.projector_backend.endpoints.bg_absence import create_absence_blueprint
from src.projector_backend.endpoints.bg_bookings import create_bookings_blueprint
from src.projector_backend.endpoints.bg_forecast import create_forecast_blueprint
from src.projector_backend.endpoints.bg_init import create_init_blueprint
from src.projector_backend.endpoints.bg_package import create_package_blueprint
from src.projector_backend.endpoints.bg_project import create_project_blueprint
from src.projector_backend.endpoints.bp_logging import create_auth_blueprint
from src.projector_backend.endpoints.bundles.bg_bundles import create_bundles_blueprint
from src.projector_backend.entities.Base import Base
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.helpers.unfertig.employee_summary import EmployeeSummary
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.db_service import DBService
from src.projector_backend.services.projekt_service import ProjektService

app = Flask(__name__)

origin = os.environ.get("ORIGIN")
CORS(app, origins=["http://" + origin + ":4200"], supports_credentials=True)

ACCESS_EXPIRES = timedelta(hours=1)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")

jwt = JWTManager(app)
blacklist = []

# engine = create_engine("sqlite:///\\\\rtgsrv1file3\\public\\PM\\Datenbank\\Datenbank.db", echo=True)
engine = create_engine("sqlite:///db/datenbank.db", echo=True)
Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

dbservice = DBService(engine)
ProjektService(engine)
pservice = ProjektService.getInstance()
cservice = CalendarService(engine)

eh = EhBuchungen()


# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    return jti in blacklist


def convert_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        employee_summary = EmployeeSummary(**json_data)
        return employee_summary


# Register blueprints
auth_bp = create_auth_blueprint(engine)
bundle_bp = create_bundles_blueprint(pservice)
init_bp = create_init_blueprint(pservice, dbservice)
project_bp = create_project_blueprint(pservice)
package_bp = create_package_blueprint(pservice)
absence_bp = create_absence_blueprint(cservice)
bookings_bp = create_bookings_blueprint(pservice, eh)
forecast_bp = create_forecast_blueprint(pservice)

app.register_blueprint(auth_bp)
app.register_blueprint(bundle_bp)
app.register_blueprint(init_bp)
app.register_blueprint(project_bp)
app.register_blueprint(package_bp)
app.register_blueprint(absence_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(forecast_bp)


@app.route('/')
def hello_world():  # put application's code here
    return "Hi - this is Projectorrr backend."


if __name__ == '__main__':
    app.run()
