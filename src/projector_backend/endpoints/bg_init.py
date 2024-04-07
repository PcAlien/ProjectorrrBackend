from datetime import datetime

from flask import Blueprint, current_app,request,abort

from src.projector_backend.dto.booking_dto import BookingDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO, ProjektmitarbeiterDTO
from src.projector_backend.helpers import data_helper
from src.projector_backend.helpers.decorators import admin_required
from src.projector_backend.helpers.unfertig import demo_calender_data_importer


def create_init_blueprint(pservice, dbservice):
    init_bp = Blueprint('init', __name__)

    # @project_bp.route('/login', methods=['POST'])
    # def login():
    #     engine = db  # Verwenden Sie das übergebene Objekt
    #     uservice = UserService(engine)
    #
    #     username = request.form['email']
    #     password = request.form['password']
    #     user_dto = uservice.login(username, password)
    #     if user_dto:
    #         return user_dto
    #     else:
    #         abort(403)

    @init_bp.route('/init')
    @admin_required()
    def init_app():  # put application's code here

        create_init_data()
        # pservice.get_latest_bookings_for_psp("11828", True)

        return "OK"

    def create_init_data():
        dbservice.create_import_settings()
        # uservice.create_demo_users()
        # _lade_demoprojekte()
        # _lade_demobuchungen()
        # _lade_demoabwesenheiten()

    def _lade_demoprojekte():
        # Schritt 1: kann ein JSON String in ein BookingDTO umgewandelt werden?
        json_data = data_helper.read_json_file("src/projector_backend/helpers/json_templates/demoprojekte.json")
        projekte: [ProjektDTO] = []

        for pro in json_data:

            pmas: [ProjektmitarbeiterDTO] = []

            for pma in pro["projektmitarbeiter"]:
                pmas.append(
                    ProjektmitarbeiterDTO(pma["personalnummer"], pma["name"], pma["psp_bezeichnung"],
                                          pma["psp_element"],
                                          pma["stundensatz"], pma["stundenbudget"], pma["laufzeit_von"],
                                          pma["laufzeit_bis"]))

            projekte.append(
                ProjektDTO(pro["projekt_name"], pro["psp"], pro["volumen"], pro["laufzeit_von"], pro["laufzeit_bis"],
                           pmas))

        for p in projekte:
            pservice.save_update_project(p)

    def _lade_demobuchungen():
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
            pservice.create_new_from_dto_and_save(dto)

    def _lade_demoabwesenheiten():
        demo_calender_data_importer.run()

    return init_bp