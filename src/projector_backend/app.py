import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine, Engine

from src.projector_backend.endpoints.bg_absence import create_absence_blueprint
from src.projector_backend.endpoints.bg_bookings import create_bookings_blueprint
from src.projector_backend.endpoints.bg_forecast import create_forecast_blueprint
from src.projector_backend.endpoints.bg_init import create_init_blueprint
from src.projector_backend.endpoints.bg_package import create_package_blueprint
from src.projector_backend.endpoints.bg_project import create_project_blueprint
from src.projector_backend.endpoints.bp_logging import create_auth_blueprint
from src.projector_backend.endpoints.bg_bundles import create_bundles_blueprint
from src.projector_backend.excel.eh_buchungen import EhBuchungen
from src.projector_backend.services.UserService import UserService
from src.projector_backend.services.auth_service import AuthService
from src.projector_backend.services.calender_service import CalendarService
from src.projector_backend.services.db_service import DBService
from src.projector_backend.services.projekt_service import ProjektService


app = Flask(__name__)
origin = os.environ.get("ORIGIN")

# Security settings
CORS(app, origins=["http://" + origin + ":4200"], supports_credentials=True)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")
jwt = JWTManager(app)

#Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

# DB-Settings
#engine = create_engine("sqlite:///db/datenbank.db", echo=True)

# Replace with your MySQL credentials
user = "root"
password = "password"
host = "localhost"  # Or hostname if your MySQL server is remote
database = "projectorrr"

engine :Engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")









# Init Services
authService = AuthService()
dbservice = DBService(engine)
pservice = ProjektService(engine, authService)
cservice = CalendarService(engine)
uservice = UserService(engine)
excelhelper = EhBuchungen()

# Register blueprints
login_bp = create_auth_blueprint(engine, jwt)
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
def hello_world():  # put application's code here
    return "Hi - this is Projectorrr backend."


# if __name__ == '__main__':
#     app.run()
