import json
import os

from flask import Blueprint, current_app, request, abort
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from src.projector_backend.dto.projekt_dto import ProjektDTO
from src.projector_backend.excel.eh_projektmeldung import EhProjektmeldung
from src.projector_backend.helpers import data_helper
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

    @project_bp.route('/archivedProjects', methods=['GET'])
    @jwt_required()
    def get_archived_projects():  # put application's code here
        back = pservice.get_archived_projects(True)
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
        pmas = eh.create_pms_from_export("./uploads/" + filename)

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
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != "":
                # Sichere den Dateinamen, um böswillige Dateinamen zu verhindern
                filename = secure_filename(file.filename)

                # Speichere die Datei im Upload-Ordner
                file.save("./uploads/" + filename)
                file_found = True

                eh = EhProjektmeldung()
                pmas = eh.create_pms_from_export("./uploads/" + filename)
                dto.projektmitarbeiter = pmas

        neuesDTO, dbResult = pservice.save_update_project(dto, True)

        if file_found:
            os.remove("./uploads/" + filename)

        if dbResult.complete:
            project_json = json.dumps(neuesDTO, default=data_helper.serialize)
            return {'status': "Success", 'project': project_json}
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
        pmaster_id = request.args.get('pmaster_id')
        back = pservice.toggle_user_project(pmaster_id)
        return back

    # @project_bp.route('/archived_project_summaries', methods=['GET'])
    # @jwt_required()
    # def get_archived_project_summaries():  # put application's code here
    #     # psp = request.args.get('psp')
    #     back = pservice.get_project_summaries(True, archiviert=True)
    #     return back

    @project_bp.route('/toggle_archived', methods=['GET'])
    @jwt_required()
    def toggle_archived():  # put application's code here
        psp = request.args.get('psp')
        back = pservice.toogle_archive_project(psp)
        return back

    return project_bp
