from typing import Type

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from src.projector_backend.entities.ImportFileColumns import ImportFileColumns
from src.projector_backend.helpers import data_helper as dh


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

    def get_by_id(self, type: Type, id: int):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            projekt = session.get(type, id)
            return projekt

    def create_import_settings(self):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            ipf = session.get(ImportFileColumns, 1)
            if (ipf == None):
                import os
                print("PFAD #########################")
                print(os.getcwd())

                json_data = dh.read_json_file("./src/projector_backend/helpers/json_templates/importFileColoums.json")
                # ifcs = IFC_Holder(**json_data)
                for i in json_data:
                    ifc = ImportFileColumns(**i)
                    session.add(ifc)
                session.commit()

    def get_import_settings(self, type=1) -> ImportFileColumns:
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            ipf = session.query(ImportFileColumns).where(ImportFileColumns.type == type).first()
            session.commit()
            session.refresh(ipf)
            return ipf

    def save_new_item(self, item):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            session.add(item)
            session.commit()

    def get_latest_of_any(self, table, filter_by, value):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            subquery = (
                session.query(func.max(table.uploadDatum))
                .filter(getattr(table, filter_by) == value)
                .subquery()
            )

            latest_entry = (
                session.query(table)
                .filter(getattr(table, filter_by) == value)
                .filter(table.uploadDatum.in_(subquery)).first()
            )

            return latest_entry
