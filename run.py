from flask import Flask, jsonify, request
import json
import mysqlDB as msq
import time
import datetime

app = Flask(__name__)

def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_where_ID_AND_somethig(key, table, id_name, ID, nameSomething, valSomething):
    if isinstance(ID, str):
        ID = f"'{ID}'"
    if isinstance(valSomething, str):
        valSomething = f"'{valSomething}'"
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID} AND {nameSomething} = {valSomething};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def getMainResponder():
    new_data_from_rent_lento = take_data_where_ID_AND_somethig('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 4)
    task_data = {
        "create": [],
        "update": [],
        "delete": [],
        "promotion": []
    }

    # LENTO.PL - wynajem - create
    for item in new_data_from_rent_lento:
        zdjecia_string = str(item[19]).split('-@-')
        theme = {
            "task_id": int(time.time()),
            "platform": "LENTO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "details": {
                "tytul_ogloszenia": item[3],
                "liczba_pieter": item[5],
                "pietro": item[6],
                "zabudowa": item[7],
                "przeznaczenie_lokalu": item[8],
                "rodzaj_dzialki": item[9],
                "numer_kw": item[10],
                "dodtkowe_info": item[11],
                "forma_kuchni": item[12],
                "typ_domu": item[13],
                "pow_dzialki": item[14],
                "liczba_pokoi": item[15],
                "powierzchnia": item[16],
                "opis_ogloszenia": item[17],
                "cena": item[18],
                "zdjecia_string": zdjecia_string, # lista stringów
                "miejscowosc": item[20],
                "osoba_kontaktowa": item[21],
                "nr_telefonu": item[22],
                "bez_promowania": item[25],
                "promowanie_lokalne_14_dni": item[26],
                "promowanie_lokalne_30_dni": item[27],
                "promowanie_regionalne_14_dni": item[28],
                "promowanie_regionalne_30_dni": item[29],
                "promowanie_ogolnopolskie_14_dni": item[30],
                "promowanie_ogolnopolskie_30_dni": item[31],
                "top_ogloszenie_7_dni": item[32],
                "top_ogloszenie_14_dni": item[33],
                "etykieta_pilne_7_dni": item[34],
                "etykieta_pilne_14_dni": item[35],
                "codzienne_odswiezenie_7_dni": item[36],
                "codzienne_odswiezenie_14_dni": item[37],
                "wyswietlanie_na_stronie_glownej_14_dni": item[38],
                "wyswietlanie_na_stronie_glownej_30_dni": item[39],
                "super_oferta_7_dni": item[40],
                "super_oferta_14_dni": item[41]                
            }
        }
        task_data["create"].append(theme)
    return task_data
    # try:
    #     # Dane do zwrócenia w formacie JSON
    #     with open(file_name, 'r', encoding=encodingJson) as responder:
    #         data = json.load(responder)
    #     return data
    # except FileNotFoundError:
    #     return {"error": "File not found"}
    # except json.JSONDecodeError:
    #     return {"error": "Error decoding JSON"}


def updateJsonFile(taskID, file_name='responder.json', encodingJson='utf-8'):
    responderFile = getMainResponder(file_name, encodingJson)
    
    for key, val in responderFile.items():
        for idx, task in enumerate(val):
            if task["task_id"] == int(taskID):
                responderFile[key].pop(idx)
    try:
        with open(file_name, 'w+', encoding=encodingJson) as jsonFile:
            json.dump(responderFile, jsonFile, indent=4, ensure_ascii=False)
        return True
    except TypeError: return False
    except KeyError: return False


# Lista dozwolonych kluczy API
allowed_API_KEYS = ["your_api_key_here"]  # Dodaj tutaj swoje dozwolone klucze API

@app.route("/", methods=['GET'])
def index():
    data = getMainResponder()
    api_key = request.headers.get('api_key')  # Pobieranie klucza API z nagłówka
    if api_key and api_key in allowed_API_KEYS:
        if 'action' in request.headers:
            action = request.headers.get('action')
            if action == 'get_json':
                return jsonify(data)
            elif action == 'respond':
                message = request.headers.get('message')
                taskID = request.headers.get('taskID')
                if message == 'Done':
                    print('taskID: ', taskID)
                    if updateJsonFile(taskID):
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})

        if 'error' in request.headers:
            error = request.headers.get('error')
            if error == 'error':
                pass
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Zwrot kodu 401 w przypadku braku autoryzacji

if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
