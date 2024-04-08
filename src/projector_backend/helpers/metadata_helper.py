from sqlalchemy import MetaData

metadata_obj = None  # Initialisierung der globalen Variablen

def initialize_global_object():
    global metadata_obj
    metadata_obj = MetaData()


# def use_global_object():
#     global metadata_obj
#     # Verwendung des globalen Objekts
#     if metadata_obj is not None:
#         metadata_obj.do_something()

# initialize_global_object()  # Initialisierung aufrufen, um das Objekt zu erstellen
# use_global_object()  # Verwendung des globalen Objekts