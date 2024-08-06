from sqlalchemy import MetaData

metadata_obj = None  # Initialisierung der globalen Variablen

def initialize_global_object():
    global metadata_obj
    metadata_obj = MetaData()
