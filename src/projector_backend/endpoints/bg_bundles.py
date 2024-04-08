# auth.py - Blueprint für Authentifizierung
import json

from flask import Blueprint, current_app,request,abort
from flask_jwt_extended import jwt_required

from src.projector_backend.dto.bundle_dtos import ProjectBundleCreateDTO


def create_bundles_blueprint(pservice):
    bundles_bp = Blueprint('bundles', __name__)

    @bundles_bp.route('/createBundle', methods=["POST"])
    @jwt_required()
    def create_bundle():
        bundle = request.form.get("bundle")
        json_daten = json.loads(bundle)
        bundle_dto = ProjectBundleCreateDTO(**json_daten)
        back = pservice.create_project_bundle(bundle_dto)
        if (not back.complete):
            return {'status': "Failed",
                    'error': back.message
                    }

        return {'status': "Success",
                }

    @bundles_bp.route('/editBundle', methods=["POST"])
    @jwt_required()
    def edit_bundle():
        bundle = request.form.get("bundle")
        json_daten = json.loads(bundle)
        bundle_dto = ProjectBundleCreateDTO(**json_daten)
        back = pservice.edit_project_bundle(bundle_dto)
        if (not back.complete):
            return {'status': "Failed",
                    'error': back.message
                    }

        return {'status': "Success",
                }

    @bundles_bp.route('/deleteBundle', methods=["POST"])
    @jwt_required()
    def delete_Bundle():  # put application's code here

        identifier = json.loads(request.form['bundle'])

        dbResult = pservice.delete_bundle(identifier)

        if dbResult.complete:

            return {'status': "Success"}
        else:
            return {'status': "Error", 'error': dbResult.message}

    @bundles_bp.route('/getAllBundles', methods=["GET"])
    @jwt_required()
    def get_all_bundles():
        back = pservice.get_project_bundles(True)
        return back

    @bundles_bp.route('/getBundle', methods=["GET"])
    @jwt_required()
    def get_bundle():
        identifier = request.args.get('identifier')
        back = pservice.get_project_bundle(identifier, True)
        return back

    return bundles_bp
