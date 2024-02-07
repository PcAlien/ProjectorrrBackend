import json
from datetime import date


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        return json_data

def serialize(obj):
    try:
        if isinstance(obj, date):
            return obj.strftime('%d.%m.%Y')
        elif isinstance(obj, set):
            return list(obj)
        return obj.__dict__
    except:
        raise TypeError("Object not serializable")