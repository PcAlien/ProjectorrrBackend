from flask import Blueprint

from src.projector_backend.entities.Base import Base
from src.projector_backend.version import version


def create_init_blueprint(engine, pservice, dbservice, uservice):
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
    # @admin_required()
    def init_app():  # put application's code here
        Base.metadata.create_all(engine)
        create_init_data()
        # pservice.get_latest_bookings_for_psp("11828", True)

        return "OK"

    @init_bp.route('/version')
    def get_version():  # put application's code here
        return version

    def create_init_data():
        dbservice.create_import_settings()
        uservice.create_admin_users()

    return init_bp
