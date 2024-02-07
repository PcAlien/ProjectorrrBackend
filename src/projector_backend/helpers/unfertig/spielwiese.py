import json
import logging

from sqlalchemy import create_engine

from dto.forecast_dto import PspForecastDTO
from entities.Base import Base
from src.projector_backend.services.booking_service import BookingService
from services.calender_service import CalendarService
from services.db_service import DBService
from services.projekt_service import ProjektService

#
# abds: [AbwesenheitDetailsDTO] = []
# abds.append(AbwesenheitDetailsDTO("31.12.2023", "u"))
# abds.append(AbwesenheitDetailsDTO("31.12.2023", "a"))
# abds.append(AbwesenheitDetailsDTO("31.12.2023", "x"))
#
# abw: AbwesenheitDTO = AbwesenheitDTO("meinName", "123", "Tester", abds)

# jsonstting = json.dumps(abw, default=data_helper.serialize)
# print(jsonstting)

engine = create_engine("sqlite:///../../datenbank.db", echo=True)
Base.metadata.create_all(engine)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

pservice = ProjektService(engine)
bservice = BookingService(engine)
cservice = CalendarService(engine)
dbservice = DBService(engine)

dto: PspForecastDTO= bservice.mach_forecast(11828, True)
print(dto)
