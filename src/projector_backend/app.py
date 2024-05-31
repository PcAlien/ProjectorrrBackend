import logging
import os
from datetime import timedelta

from flask import Flask, request, jsonify, after_this_request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, create_access_token, verify_jwt_in_request, \
    get_current_user, jwt_required, get_jwt
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
#CORS(app, supports_credentials=True)
CORS(app)
# CORS(app, origins=["http://" + origin + ":4200","http://127.0.0.1:4200", "http://localhost:4200", "http://rtgsrv1pmgmt1:4200", "http://" + origin + ":80","http://127.0.0.1:80", "http://localhost:80", "http://rtgsrv1pmgmt1:80" ])
app.secret_key = os.environ.get("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
app.config['JWT_BLACKLIST_ENABLED'] = False

app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Optional, wenn du CSRF-Schutz für Cookies deaktivieren möchtest
#app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies", "json", "query_string"]
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

jwt = JWTManager(app)


blocklist = []


# Benutzerdefinierte Callback-Funktion für das Token-Refresh
@jwt.token_in_blocklist_loader
def token_in_blocklist_loader(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blocklist



# Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

# Replace with your MySQL credentials
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
host = os.environ.get("DB_HOST")
database = os.environ.get("DB_DB")

# DB-Settings
# engine = create_engine("sqlite:///db/datenbank.db", echo=True)
engine: Engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}?sql_mode=", pool_size=20, max_overflow=0)
# engine.connect().execute("SET sql_mode = ''")


# Init Services
authService = AuthService()
dbservice = DBService(engine)
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
def hello_world():  # put application's code here
    return "Hi - this is Projectorrr backend."


@app.route('/origin')
def origin():  # put application's code here
    print("ORIGIN-CALL: " + request.headers.get('Origin'))
    return jsonify(message=request.headers.get('Origin'))

# if __name__ == '__main__':
#     app.run()
