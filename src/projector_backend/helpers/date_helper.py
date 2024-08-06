from datetime import datetime


def from_string_to_date_without_time(date: str):
    # Das Format des Datums in deinem String
    datum_format = "%d.%m.%Y"

    # String in ein datetime-Objekt umwandeln
    datum_objekt = datetime.strptime(date, datum_format)

    # Das datetime-Objekt ohne Zeitinformationen extrahieren

    return datum_objekt.date()


def from_dw_date_string_to_date_without_time(date: str):
    # Das Format des Datums in deinem String
    datum_format = "%Y%m%d"

    # String in ein datetime-Objekt umwandeln
    datum_objekt = datetime.strptime(date, datum_format)

    # Das datetime-Objekt ohne Zeitinformationen extrahieren

    return datum_objekt.date()


def from_date_to_string(date: datetime) -> str:
    return date.strftime("%d.%m.%Y")


def from_date_to_string_extended(date: datetime) -> str:
    return date.strftime("%d.%m.%Y - %H:%M:%S Uhr")
