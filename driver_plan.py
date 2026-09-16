import json


def load_driver_rules():
    with open("data/driver_rules.json", "r") as file:
        return json.load(file)


def calculate_drivers(parcel_count):

    rules = load_driver_rules()["rules"]

    for rule in rules:

        if rule["min"] <= parcel_count <= rule["max"]:
            return rule["drivers"]

    return 5

