from flask import Flask, jsonify, request
import json
import mysqlDB as msq
import time
import datetime
from bin.config_utils import allowed_API_KEYS

app = Flask(__name__)

def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_where_ID_AND_somethig_AND_Something(key, table, id_name, ID, nameSomething, valSomething, nameSomethingOther, valSomethingOther):
    if isinstance(ID, str):
        ID = f"'{ID}'"
    if isinstance(valSomething, str):
        valSomething = f"'{valSomething}'"
    if isinstance(valSomethingOther, str):
        valSomething = f"'{valSomethingOther}'"
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID} AND {nameSomething} = {valSomething} AND {nameSomethingOther} = {valSomethingOther};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def getMainResponder():
    task_data = {
        "create": [],
        "update": [],
        "delete": [],
        "hold": [],
        "resume": [],
        "promotion": []
    }

    edit_data_from_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # LENTO.PL - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_lento):
        zdjecia_string = str(item[19]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
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
                "id_ogloszenia_na_lento": item[24]           
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_lento
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)

    new_data_from_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 4, 'active_task', 0)
    # LENTO.PL - wynajem - create
    for i, item in enumerate(new_data_from_rent_lento):
        zdjecia_string = str(item[19]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
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

        action_taks = f'''
            UPDATE ogloszenia_lento
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)

    hold_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 7, 'active_task', 0)
    # LENTO.PL - wynajem - create    
    for i, item in enumerate(hold_rent_lento):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "LENTO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_lento": item[24]
        }
        action_taks = f'''
            UPDATE ogloszenia_lento
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["hold"].append(theme)

    resume_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 8, 'active_task', 0)
    # LENTO.PL - wynajem - create    
    for i, item in enumerate(resume_rent_lento):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "LENTO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_lento": item[24]
        }
        action_taks = f'''
            UPDATE ogloszenia_lento
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["resume"].append(theme)
    
    return task_data



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




@app.route("/", methods=['GET'])
def index():
    data = getMainResponder()
    api_key = request.headers.get('api_key')  # Pobieranie klucza API z nagłówka
    if api_key and api_key in allowed_API_KEYS:
        if 'action' in request.headers:
            action = request.headers.get('action')
            if action == 'get_json':
                print(data)
                return jsonify(data)
            elif action == 'respond':
                message = request.headers.get('message')
                taskID = request.headers.get('taskID')
                success = request.headers.get('success')

                if message == 'Done-lento-add-new': 
                    try: 
                        id_lento_ads = int(success)
                    except TypeError:
                        return jsonify({"error": 500})
                    
                    action_taks = f'''
                        UPDATE ogloszenia_lento
                        SET 
                            active_task=%s,
                            status=%s,
                            id_ogloszenia_na_lento=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, id_lento_ads, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})
                    
                if message == 'Done-lento-hold': 

                    action_taks = f'''
                        UPDATE ogloszenia_lento
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 0, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})
                
                if message == 'Done-lento-resume': 

                    action_taks = f'''
                        UPDATE ogloszenia_lento
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})
                    
                if message == 'Done-lento-update': 

                    action_taks = f'''
                        UPDATE ogloszenia_lento
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})

                if message == 'Done':
                    print('taskID: ', taskID)
                    if updateJsonFile(taskID):
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
            elif action == 'error':                
                taskID = request.headers.get('taskID')
                errorMessage = request.headers.get('error')
                action_taks = f'''
                    UPDATE ogloszenia_lento
                    SET 
                        active_task=%s,
                        status=%s,
                        errors=%s
                    WHERE id_zadania = %s;
                '''
                values = (0, 2, errorMessage, taskID)
                
                if msq.insert_to_database(action_taks, values):
                    return jsonify({"message": "The error description has been saved"})

        if 'error' in request.headers:
            error = request.headers.get('error')
            if error == 'error':
                pass
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Zwrot kodu 401 w przypadku braku autoryzacji

if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
