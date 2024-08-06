import json
from datetime import date, datetime


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        return json_data

def serialize(obj):
    try:
        if isinstance(obj, date):
            return obj.strftime('%d.%m.%Y - %H:%M')
        elif isinstance(obj, datetime):
            return obj.strftime('%d.%m.%Y - %H:%M')
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, list):
            return list(obj)
        elif isinstance(obj, dict):
            return {key: serialize(value) for key, value in obj.items()}
        return obj.__dict__
    except:
        raise TypeError("Object not serializable")
