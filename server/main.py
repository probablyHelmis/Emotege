import json
import logging
import os
import re
from _operator import itemgetter
import requests

logging.basicConfig(filename="dailyrun.log",
                    format='%(levelname)s - %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.INFO)

sheets_key = (os.environ['SHEETS_KEY'])

url_regex = r"^https\:\/\/(?:(?:static\-cdn\.jtvnw\.net\/emoticons\/v2\/\d+\/static\/light\/3\.0)|(?:static\-cdn\.jtvnw\.net\/emoticons\/v2\/emotesv2\_[\w\d]+\/static\/light\/3\.0)|(?:cdn\.betterttv\.net\/emote\/[\w\d]+\/3x\.webp)|(?:cdn\.frankerfacez\.com\/emoticon\/\d+\/4)|(?:cdn\.7tv\.app\/emote\/[\w\d]+\/4x\.webp))$"


def get_data():
    url = "https://sheets.googleapis.com/v4/spreadsheets/1zjY3c1dZs3x4IO5_65GXLE2lIzYey49FywSaP_v81WU/?key=" + sheets_key + "&includeGridData=true"

    response = json.loads(requests.get(url).text)

    column_numbers = {
        "id": None,
        "group": None,
        "link": None,
        "from": None,
        "to": None
    }

    row_data = []
    for sheet in response['sheets']:
        if sheet['properties']['title'] == "Data":
            row_data = sheet['data'][0]['rowData']

    # LOCAL DATA TESTING
    # with open('raw.json') as f:
    #     row_data = json.loads(f.read())
    # f.close()

    if len(row_data) == 0:
        logger.critical("Data sheet not found!")
        return

    title_row = row_data[0]['values']
    for cell in title_row:
        if "formattedValue" in cell:
            match cell['formattedValue']:
                case "Emote":
                    column_numbers['id'] = title_row.index(cell)
                case "URL":
                    column_numbers['link'] = title_row.index(cell)
                case "Group":
                    column_numbers['group'] = title_row.index(cell)
                case "Connection Parent":
                    column_numbers['from'] = title_row.index(cell)
                case "Connection Child":
                    column_numbers['to'] = title_row.index(cell)
                case _:
                    continue

    for column in column_numbers:
        if column_numbers[column] is None:
            logger.critical("Aborting - Missing column:", column)
            return

    emote_array = get_emotes(row_data, column_numbers)
    connection_array = get_connections(row_data, column_numbers)

    with open("hryGlyphics.json", 'w') as f:
        json.dump(emote_array, f, indent=4)
    f.close()

    with open("rosetta.json", 'w') as f:
        json.dump(connection_array, f, indent=4)
    f.close()


def get_emotes(row_data, column_numbers):
    logger.info("------ Starting Emote parsing ------")
    emote_array = {'emotes': []}
    for row in row_data:
        if row_data.index(row) == 0 or len(row['values']) < max(column_numbers.values()):
            continue

        emote_object = {
            'id': None,
            'group': None,
            'link': None,
        }

        for column in column_numbers:
            column_number = column_numbers[column]
            if 'formattedValue' in row['values'][column_number] and column in emote_object:
                emote_object[column] = row['values'][column_number]['formattedValue']


        missing_value = False
        some_value = False
        for key in emote_object:
            if emote_object[key] is None:
                missing_value = True
            else:
                some_value = True

        if missing_value:
            if some_value:
                logger.warning("Missing value in object: " + str(emote_object))
            continue

        link = emote_object['link']

        if not re.search(url_regex, link):
            logger.warning("Emote \"" + emote_object['id'] + "\" has a malformed URL: " + emote_object['link'])
            continue

        emote_array['emotes'].append(emote_object)

    return {'emotes': sorted(emote_array['emotes'], key=itemgetter("id"))}


def get_connections(row_data, column_numbers):
    logger.info("------ Starting Edge parsing -------")
    connection_array = {'edges': []}
    for row in row_data:
        if row_data.index(row) == 0 or len(row['values']) < max(column_numbers.values()):
            continue

        connection_object = {
            'from': None,
            'to': None
        }

        for column in column_numbers:
            column_number = column_numbers[column]
            if 'formattedValue' in row['values'][column_number] and column in connection_object:
                connection_object[column] = row['values'][column_number]['formattedValue']


        missing_value = False
        some_value = False
        for key in connection_object:
            if connection_object[key] is None:
                missing_value = True
            else:
                some_value = True

        if missing_value:
            if some_value:
                logger.warning("Missing value in object: " + str(connection_object))
            continue

        connection_array['edges'].append(connection_object)

    return {'edges': sorted(connection_array['edges'], key=itemgetter("from"))}


get_data()