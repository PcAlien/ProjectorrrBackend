import json
import os

from flask import Blueprint, current_app, request, abort, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from src.projector_backend.dto.projekt_dto import ProjektDTO
from src.projector_backend.dto.returners import DbResult
from src.projector_backend.excel.eh_projektmeldung import EhProjektmeldung
from src.projector_backend.helpers import data_helper
from src.projector_backend.helpers.decorators import admin_required
from src.projector_backend.services.UserService import UserService


def create_project_blueprint(pservice):
    project_bp = Blueprint('project', __name__)

    @project_bp.route('/project', methods=['GET'])
    @jwt_required()
    def get_project():  # put application's code here
        psp = request.args.get('psp')
        back = pservice.get_project_by_psp(psp, True)
        return back

    @project_bp.route('/projects', methods=['GET'])
    @jwt_required()
    def get_projects():  # put application's code here
        back = pservice.get_active_projects(True)
        return back

    @project_bp.route('/allProjects', methods=['GET'])
    @jwt_required()
    def get_all_projects():  # put application's code here
        back = pservice.get_all_projects_basics()
        return back

    @project_bp.route('/projektupload', methods=["POST"])
    @jwt_required()
    def projektupload():  # put application's code here
        # Überprüfe, ob die POST-Anfrage eine Datei enthält
        if 'file' not in request.files:
            return 'No file part', 400

        file = request.files['file']
        json_projektdaten = json.loads(request.form['basis'])

        # Überprüfe, ob eine Datei ausgewählt wurde
        if file.filename == '':
            return 'No selected file', 400
        # file.stream

        # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
        filename = secure_filename(file.filename)

        # Speichere die Datei im Upload-Ordner
        file.save("./uploads/" + filename)

        eh = EhProjektmeldung()
        pmas, upload_errors, upload_warnings  = eh.create_pms_from_export("./uploads/" + filename, json_projektdaten['psp'])

        if upload_errors:
            dbResult = DbResult(False, upload_errors)
        else:

            dto = ProjektDTO(**json_projektdaten)
            dto.projektmitarbeiter = pmas
            neuesDTO, dbResult = pservice.save_update_project(dto)





        os.remove("./uploads/" + filename)
        if dbResult.complete:
            project_json = json.dumps(neuesDTO, default=data_helper.serialize)
            return {'status': "Success", 'project': project_json}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @project_bp.route('/editProject', methods=["POST"])
    @jwt_required()
    def edit_project():  # put application's code here

        json_projektdaten = json.loads(request.form['basis'])

        dto = ProjektDTO(**json_projektdaten)
        file_found = False
        upload_errors = None
        upload_warnings = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != "":
                # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
                filename = secure_filename(file.filename)

                # Speichere die Datei im Upload-Ordner
                file.save("./uploads/" + filename)
                file_found = True

                eh = EhProjektmeldung()
                pmas, upload_errors, upload_warnings = eh.create_pms_from_export("./uploads/" + filename, dto.psp)
                dto.projektmitarbeiter = pmas

        if not upload_errors:
            neuesDTO, dbResult = pservice.save_update_project(dto, True)
        else:
            dbResult = DbResult(False, upload_errors)

        if file_found:
            os.remove("./uploads/" + filename)

        if dbResult.complete:
            project_json = json.dumps(neuesDTO, default=data_helper.serialize)
            return {'status': "Success", 'project': project_json, 'warnings': json.dumps(upload_warnings)}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @project_bp.route('/project_summary', methods=['GET'])
    @jwt_required()
    def get_project_summary():  # put application's code here
        psp = request.args.get('psp')
        back = pservice.get_project_summary(psp, True)
        return back

    @project_bp.route('/project_summaries', methods=['GET'])
    @jwt_required()
    def get_project_summaries():  # put application's code here
        # psp = request.args.get('psp')
        back = pservice.get_project_summaries(True)
        return back

    @project_bp.route('/toggleUserProject', methods=['GET'])
    @jwt_required()
    def toggle_user_project():  # put application's code here
        pmaster_id = request.args.get('pid')
        back = pservice.toggle_user_project(pmaster_id)
        return back

    @project_bp.route('/deleteProject', methods=['GET'])
    @admin_required()
    def delete_project():  # put application's code here
        psp = request.args.get('psp')

        back = pservice.delete_project(psp)
        return jsonify(back)

    return project_bp


