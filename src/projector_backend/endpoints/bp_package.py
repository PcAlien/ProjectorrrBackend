import json

from flask import Blueprint, current_app, request, abort
from flask_jwt_extended import jwt_required

from src.projector_backend.dto.PspPackageDTO import PspPackageDTO, PspPackageSummaryDTO
from src.projector_backend.helpers import data_helper


def create_package_blueprint(pservice):
    package_bp = Blueprint('package', __name__)

    @package_bp.route('/addPspPackage', methods=["POST"])
    @jwt_required()
    def add_psp_package():  # put application's code here

        json_projektdaten = json.loads(request.form['package'])
        dto = PspPackageDTO(**json_projektdaten)

        try:
            identifier, dbResult = pservice.add_psp_package(dto)
        except:
            print("Das hat leider so gar nicht geklappt")
            print(dbResult)
            print(identifier)

        if dbResult.complete:
            identifier_json = json.dumps(identifier, default=data_helper.serialize)
            return {'status': "Success", 'identifier': identifier_json}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @package_bp.route('/loadPspPackage', methods=["GET"])
    @jwt_required()
    def load_psp_package():  # put application's code here
        identifier = request.args.get('identifier')
        back = pservice.get_package(identifier, True)
        return back

    @package_bp.route('/updatePspPackage', methods=["POST"])
    @jwt_required()
    def update_psp_package():  # put application's code here

        json_projektdaten = json.loads(request.form['package'])
        dto = PspPackageDTO(**json_projektdaten)

        identifier, dbResult = pservice.update_psp_package(dto)

        if dbResult.complete:
            identifier_json = json.dumps(identifier, default=data_helper.serialize)
            return {'status': "Success", 'identifier': identifier_json}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @package_bp.route('/deletePspPackage', methods=["POST"])
    @jwt_required()
    def delete_psp_package():  # put application's code here

        json_projektdaten = json.loads(request.form['package'])
        dto = PspPackageDTO(**json_projektdaten)

        dbResult = pservice.delete_psp_package(dto)

        if dbResult.complete:

            return {'status': "Success"}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @package_bp.route('/getPackageSummary', methods=["GET"])
    @jwt_required()
    def get_package_summary():  # put application's code here
        identifier = request.args.get('identifier')
        back: PspPackageSummaryDTO = pservice.get_package_summary(identifier, True)

        return back

    @package_bp.route('/getPackageSummaries', methods=["GET"])
    @jwt_required()
    def get_package_summaries():  # put application's code here
        psp = request.args.get('psp')
        back: [PspPackageSummaryDTO] = pservice.get_package_summaries(psp, None, True)
        return back

    return package_bp
