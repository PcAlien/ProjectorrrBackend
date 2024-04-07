from flask import Blueprint, current_app,request,abort

from src.projector_backend.dto.forecast_dto import PspForecastDTO


def create_forecast_blueprint(pservice):
    forecast_bp = Blueprint('forecast', __name__)

    @forecast_bp.route('/pspForecast', methods=["POST"])
    def get_psp_forecast():
        psp = request.form.get("psp")
        back = pservice.getInstance().create_forecast_by_alltime_avg(psp, True)
        back_projektmeldung: PspForecastDTO = pservice.getInstance().create_forecast_by_projektmeldung(psp, False)

        return back

    @forecast_bp.route('/pspForecastTest', methods=["GET"])
    def get_psp_forecast_test():
        psp = "11828"
        back: PspForecastDTO = pservice.getInstance().create_forecast_by_alltime_avg(psp, False)
        return back

    return forecast_bp
