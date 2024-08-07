import json
import os

from flask import Blueprint, current_app, request, abort, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from src.projector_backend.dto.abwesenheiten import AbwesenheitsRangeDTO


def create_absence_blueprint(cservice):
    absence_bp = Blueprint('absence', __name__)

    @absence_bp.route('/abwesenheitsUpload', methods=["POST"])
    @jwt_required()
    def abwesenheits_upload():
        # Überprüfe, ob die POST-Anfrage eine Datei enthält
        if 'abwesenheits_file' not in request.files:
            return 'No file part', 400

        file = request.files['abwesenheits_file']

        # json_buchungsdaten = json.loads(request.form['base_data_booking'])

        # Überprüfe, ob eine Datei ausgewählt wurde
        if file.filename == '':
            return 'No selected file', 400

        # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
        filename = secure_filename(file.filename)

        # Speichere die Datei im Upload-Ordner
        file.save("./uploads/" + filename)

        dbResult = cservice.prozeed_upload_abwesenheiten(filename)
        os.remove("./uploads/" + filename)
        if (not dbResult.complete):
            return {'status': "Failed",
                    'error': dbResult.message
                    }

        return {'status': "Success",
                }

    @absence_bp.route('/abwesenheiten', methods=["GET"])
    @jwt_required()
    def get_abwesenheiten():
        back = cservice.get_instance().get_calender_data(True)
        return back

    @absence_bp.route('/addAbwesenheit', methods=["POST"])
    @jwt_required()
    def add_abwesenheit():
        abw = request.form.get("abwesenheit")
        cservice.get_instance().add_abwesenheit(abw)

        return {'answer': "Added Abwesenheit!!!"}

    @absence_bp.route('/addAbwesenheiten', methods=["POST"])
    @jwt_required()
    def add_abwesenheiten():
        abw = request.form.get("abwData")
        jload = json.loads(abw)
        abwRange = AbwesenheitsRangeDTO(**jload)
        back = cservice.get_instance().add_abwesenheits_range(abwRange)

        if back:
            return {'status': "Success"}
        else:
            return {'status': "Error",
                    'error': "Das ging wohl irgendwie nicht so wie geplant..."
                    }



    @absence_bp.route('/getEmployees', methods=["GET"])
    @jwt_required()
    def get_employees():
        back = cservice.get_instance().get_employees()
        return back

    return absence_bp
