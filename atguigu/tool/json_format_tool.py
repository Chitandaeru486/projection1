import json


def json_format(date):
    return json.dumps(date, indent=4, ensure_ascii=False)