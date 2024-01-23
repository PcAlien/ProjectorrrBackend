import json
from typing import Type

from sqlalchemy.orm import sessionmaker

from dto.abwesenheiten import AbwesenheitDTO
from dto.calendar_data import CalenderData
from entities.abwesenheit_db import Abwesenheit, AbwesenheitDetails
from helpers import data_helper


class CalendarService:
    _instance = None

    def __new__(cls, engine):
        if cls._instance is None:
            cls._instance = super(CalendarService, cls).__new__(cls)
            cls._instance.engine = engine
        return cls._instance

    @classmethod
    def getInstance(cls: Type['CalendarService']) -> 'CalendarService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance

    def get_calender_data(self, json_format: bool = True) -> CalenderData or str:
        abwesenheitenDTOs: [AbwesenheitDTO] = self._get_all_abwesenheiten(False)
        cd = CalenderData(abwesenheitenDTOs)

        if (json_format):
            return json.dumps(cd, default=data_helper.serialize)
        else:
            return cd




    def _get_all_abwesenheiten(self, json_format: bool = True):
        Session = sessionmaker(bind=self.engine)
        abwesenheitenDTOs: [AbwesenheitDTO] = []
        with Session() as session:
            abwesenheiten = session.query(Abwesenheit).all()

            for a in abwesenheiten:
                abwesenheitenDTOs.append(AbwesenheitDTO.create_from_db(a))

        if (json_format):
            return json.dumps(abwesenheitenDTOs, default=data_helper.serialize)
        else:
            return abwesenheitenDTOs

    def proceed_demodaten(self,abwesenheiten: [Abwesenheit] ):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            session.query(Abwesenheit).delete()
            session.query(AbwesenheitDetails).delete()
            session.commit()

            for abw in abwesenheiten:
                session.add(abw)
            session.commit()
