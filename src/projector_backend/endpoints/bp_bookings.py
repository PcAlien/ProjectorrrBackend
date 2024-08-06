import os

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from src.projector_backend.dto.booking_dto import BookingDTO


def create_bookings_blueprint(pservice, eh):
    bookings_bp = Blueprint('bookings', __name__)

    @bookings_bp.route('/buchungen', methods=['GET'])
    @jwt_required()
    def gib_buchungen():  # put application's code here
        psp = request.args.get('psp')
        back = pservice.get_bookings_for_psp(psp, True)
        return back

    @bookings_bp.route('/maBookingsSummary', methods=['GET'])
    @jwt_required()
    def get_ma_bookings_summary():  # put application's code here
        psp = request.args.get('psp')
        back = pservice.get_ma_bookings_summary_for_psp(psp, True)
        return back

    @bookings_bp.route('/bookingsupload', methods=["POST"])
    @jwt_required()
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

        missing_psps, missing_psp_element_list, dbResult = pservice.convert_bookings_from_excel_export(filename)

        mpsp_str = ""
        mpsp_elements_str = ""
        if len(missing_psps) > 0:
            mpsp_str = missing_psps.__str__()

        if len(missing_psp_element_list) > 0:
            mpsp_elements_str = missing_psp_element_list.__str__()

        if dbResult.complete:
            psp_set = set()
            missing_psp_dict: dict = {}
            m: str
            for m in missing_psp_element_list:
                psp_set.add(m.split(".")[0])

            for psp in psp_set:
                pservice.delete_issues(psp)
                missing_psp_dict[psp] = []

            for m in missing_psp_element_list:
                missing_psp_dict[m.split(".")[0]].append(m)

            # Kommaseparierte Listen erstellen und speichern
            for psp,element_list in missing_psp_dict.items():
                for e in element_list:
                    pservice.save_issue(psp, "mpspe", e)



        os.remove("./uploads/" + filename)
        if (not dbResult.complete):
            return {'status': "Failed",
                    'missingPSPs': mpsp_str,
                    'missingPSPElements': mpsp_elements_str,
                    'error': dbResult.message
                    }

        return {'status': "Success",
                'missingPSPs': mpsp_str,
                'missingPSPElements': mpsp_elements_str,
                }

    @bookings_bp.route('/exportBuchungen', methods=["GET"])
    @jwt_required()
    def create_buchungen_export():
        psp = request.args.get('psp')
        filename_buchungen = eh.export_buchungen(psp, pservice.get_bookings_for_psp(psp, False),
                                                 pservice.get_bookings_for_psp_by_month(psp, False))
        file_path_buchungen = os.path.join(os.getcwd(), 'exports', filename_buchungen)
        return send_file(file_path_buchungen, as_attachment=True)

    @bookings_bp.route('/exportUmsaetze', methods=["GET"])
    @jwt_required()
    def create_umsaetze_export():
        psp = request.args.get('psp')
        booking_dtos: [BookingDTO] = pservice.get_bookings_for_psp(psp, False)
        filename_umsaetze = eh.export_umsaetze(psp, pservice.get_ma_bookings_summary_for_psp(psp, False),
                                               pservice.get_bookings_summary_for_psp_by_month(booking_dtos, False),
                                               pservice.get_project_by_psp(psp, False).volumen)
        file_path_umsaetze = os.path.join(os.getcwd(), 'exports', filename_umsaetze)
        return send_file(file_path_umsaetze, as_attachment=True)

    return bookings_bp
