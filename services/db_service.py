from typing import Type

from sqlalchemy.orm import sessionmaker

from entities.ImportFileColumns import ImportFileColumns
from helpers import data_helper as dh


class DBService:
    _instance = None

    def __new__(cls, engine):
        if cls._instance is None:
            cls._instance = super(DBService, cls).__new__(cls)
            cls._instance.engine = engine
        return cls._instance

    @classmethod
    def getInstance(cls: Type['DBService']) -> 'DBService':
        if cls._instance is None:
            raise ValueError("Die Singleton-Instanz wurde noch nicht erstellt.")
        return cls._instance


    def get_by_id(self,type: Type, id:int):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            projekt = session.get(type, id)
            return projekt


    def create_import_settings(self):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            ipf = session.get(ImportFileColumns, 1)
            if (ipf == None):
                json_data = dh.read_json_file("helpers/json_templates/importFileColoums.json")
                ifc = ImportFileColumns(**json_data)
                session.add(ifc)
                session.commit()

    def get_import_settings(self,type = 1) -> ImportFileColumns:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            ipf = session.query(ImportFileColumns).where(ImportFileColumns.type == type).first()
            session.commit()
            session.refresh(ipf)
            return ipf