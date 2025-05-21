from flask import Flask, jsonify, request
import json
import os
import mysqlDB as msq
import time
import datetime
from bin.config_utils import allowed_API_KEYS
from MindForge import addNewUser, get_next_template,\
    json_string_to_dict, validate_response_structure,\
        template_managment, dict_to_json_string,\
            resumeJson_structure, get_prompt_by_level_task
import sendEmailBySmtp
import saver_ver
import requests

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
        valSomethingOther = f"'{valSomethingOther}'"
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID} AND {nameSomething} = {valSomething} AND {nameSomethingOther} = {valSomethingOther};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def checkLentoAction_before_errors(task_id):
    try:
        return msq.connect_to_database(f'SELECT status FROM ogloszenia_lento WHERE id_zadania="{task_id}";')[0][0]
    except IndexError:
        return None

def checkFacebookAction_before_errors(task_id):
    try:
        return msq.connect_to_database(f'SELECT status FROM ogloszenia_facebook WHERE id_zadania="{task_id}";')[0][0]
    except IndexError:
        return None

def checkAdresowoAction_before_errors(task_id):
    try:
        return msq.connect_to_database(f'SELECT status FROM ogloszenia_adresowo WHERE id_zadania="{task_id}";')[0][0]
    except IndexError:
        return None

def checkAllegroAction_before_errors(task_id):
    try:
        return msq.connect_to_database(f'SELECT status FROM ogloszenia_allegrolokalnie WHERE id_zadania="{task_id}";')[0][0]
    except IndexError:
        return None

def checkOtodomAction_before_errors(task_id):
    try:
        return msq.connect_to_database(f'SELECT status FROM ogloszenia_otodom WHERE id_zadania="{task_id}";')[0][0]
    except IndexError:
        return None

def add_aifaLog(message: str, systemInfoFilePath='/home/johndoe/app/newsletterdemon/logs/logsForAifa.json') -> None:
    # Utwórz plik JSON, jeśli nie istnieje
    if not os.path.exists(systemInfoFilePath):
        with open(systemInfoFilePath, 'w') as file:
            json.dump({"logs": []}, file)
    
    # Dodaj nowy log do pliku
    with open(systemInfoFilePath, 'r+', encoding='utf-8') as file:
        data = json.load(file)
        data["logs"].append({"message": message, "oddany": False})  # dodaj nowy log jako nieoddany
        file.seek(0)  # wróć na początek pliku
        json.dump(data, file, indent=4)  # zapisz zmiany
        file.truncate()  # obetnij zawartość do nowej długości

def addDataLogs(message: str, category: str, file_name_json: str = "/home/johndoe/app/newsletterdemon/logs/dataLogsAifa.json"):
    # Wczytaj istniejące logi lub utwórz pustą listę
    try:
        with open(file_name_json, "r") as file:
            data_json = json.load(file)
    except FileNotFoundError:
        data_json = []

    # Tworzenie nowego logu
    new_log = {
        "id": len(data_json) + 1,  # Generowanie unikalnego ID
        "message": message,
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "category": category,
        "issued": []
    }

    # Dodanie nowego logu do listy i zapisanie do pliku
    data_json.append(new_log)
    with open(file_name_json, "w") as file:
        json.dump(data_json, file, indent=4)

def decode_task_data(task_data: str) -> list:
    """
    Dekoduje zapisane stringi w kolumnie `dane_wykonawcze` na listę krotek.
    Sprawdza, czy id i status dają się skonwertować na int. 
    W przypadku błędu zwraca pustą krotkę dla danego elementu.
    """
    decoded_data = []
    for item in task_data.split(';'):
        parts = item.split('|')
        if len(parts) == 3:
            try:
                record_id = int(parts[0])  # Konwersja id na int
                ogloszenie_id = parts[1]  # Pozostawiamy jako string
                status = int(parts[2])    # Konwersja statusu na int
                decoded_data.append({"record_id": record_id, "ogloszenie_id": ogloszenie_id, "status": status})
            except ValueError:
                # Jeśli id lub status nie da się przekonwertować
                print('id lub status nie da się przekonwertować')
    
    return decoded_data

def getMainResponder():
    task_data = {
        "create": [],
        "update": [],
        "delete": [],
        "hold": [],
        "resume": [],
        "promotion": []
    }

    new_data_from_logs = msq.connect_to_database(f'SELECT * FROM system_logs_monitor WHERE status = 4 AND active_task = 0;')
    # CHAT - botlogs
    for i, item in enumerate(new_data_from_logs):

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "BOT-LOGS",
            "id": item[0],
            "log_prompt": item[1]
        }

        action_taks = f'''
            UPDATE system_logs_monitor
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], theme["id"])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_chat = msq.connect_to_database(f'SELECT * FROM chat_task WHERE status = 4 AND active_task = 0;')
    # CHAT - create
    for i, item in enumerate(new_data_from_chat):

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "CHARACTER",
            "id": item[0],
            "question": item[1]

        }

        action_taks = f'''
            UPDATE chat_task
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], theme["id"])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data
    
    new_data_from_chat_openai = msq.connect_to_database(f'SELECT * FROM chat_task WHERE status = 5 AND active_task = 0;')
    # CHAT - Open AI
    for i, item in enumerate(new_data_from_chat_openai):

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OPEN-AI",
            "id": item[0],
            "question": item[1]

        }

        action_taks = f'''
            UPDATE chat_task
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], theme["id"])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_career_fbgropus = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_fbgroups', 'sekcja_ogloszenia', 'career', 'status', 4, 'active_task', 0)
    # Career - FB GROUPS - create
    for i, item in enumerate(new_data_from_career_fbgropus):

        if item[8] is not None:
            linkigrup_string = str(item[8]).split('-@-')
        else: 
            linkigrup_string = []
        
        if item[9] is not None:
            zdjecia_string = str(item[9]).split('-@-')
        else: 
            zdjecia_string = []

        theme = {
            "task_id": int(item[10]),
            "platform": "FB-GROUPS",
            "waiting_list_id": int(item[2]),
            "kategoria_ogloszenia": item[3],
            "id_ogloszenia": item[1],
            "sekcja_ogloszenia": item[4],
            'poziom_harmonogramu': item[7],
            'created_by': item[16],
            "details": {
                "tresc_ogloszenia": item[5],
                "styl_ogloszenia": int(item[6]),
                "linkigrup_string": linkigrup_string, # lista stringów
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_fbgroups
            SET 
                active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_estateAdsRent_fbgropus = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_fbgroups', 'sekcja_ogloszenia', 'estateAdsRent', 'status', 4, 'active_task', 0)
    # Estate - FB GROUPS - Rent
    for i, item in enumerate(new_data_from_estateAdsRent_fbgropus):

        if item[8] is not None:
            linkigrup_string = str(item[8]).split('-@-')
        else: 
            linkigrup_string = []
        
        if item[9] is not None:
            zdjecia_string = str(item[9]).split('-@-')
        else: 
            zdjecia_string = []

        theme = {
            "task_id": int(item[10]),
            "platform": "FB-GROUPS",
            "waiting_list_id": int(item[2]),
            "kategoria_ogloszenia": item[3],
            "id_ogloszenia": item[1],
            "sekcja_ogloszenia": item[4],
            'poziom_harmonogramu': item[7],
            'created_by': item[16],
            "details": {
                "tresc_ogloszenia": item[5],
                "styl_ogloszenia": int(item[6]),
                "linkigrup_string": linkigrup_string, # lista stringów
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_fbgroups
            SET 
                active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data
        
    new_data_from_estateAdsSell_fbgropus = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_fbgroups', 'sekcja_ogloszenia', 'estateAdsSell', 'status', 4, 'active_task', 0)
    # Estate - FB GROUPS - Sell
    for i, item in enumerate(new_data_from_estateAdsSell_fbgropus):

        if item[8] is not None:
            linkigrup_string = str(item[8]).split('-@-')
        else: 
            linkigrup_string = []
        
        if item[9] is not None:
            zdjecia_string = str(item[9]).split('-@-')
        else: 
            zdjecia_string = []

        theme = {
            "task_id": int(item[10]),
            "platform": "FB-GROUPS",
            "waiting_list_id": int(item[2]),
            "kategoria_ogloszenia": item[3],
            "id_ogloszenia": item[1],
            "sekcja_ogloszenia": item[4],
            'poziom_harmonogramu': item[7],
            'created_by': item[16],
            "details": {
                "tresc_ogloszenia": item[5],
                "styl_ogloszenia": int(item[6]),
                "linkigrup_string": linkigrup_string, # lista stringów
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_fbgroups
            SET 
                active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data
    
    new_data_from_estateAdsRent_fbgropus = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_fbgroups', 'sekcja_ogloszenia', 'estateAdsRent', 'status', 4, 'active_task', 0)
    # Estate - FB GROUPS - Rent
    for i, item in enumerate(new_data_from_estateAdsRent_fbgropus):

        if item[8] is not None:
            linkigrup_string = str(item[8]).split('-@-')
        else: 
            linkigrup_string = []
        
        if item[9] is not None:
            zdjecia_string = str(item[9]).split('-@-')
        else: 
            zdjecia_string = []

        theme = {
            "task_id": int(item[10]),
            "platform": "FB-GROUPS",
            "waiting_list_id": int(item[2]),
            "kategoria_ogloszenia": item[3],
            "id_ogloszenia": item[1],
            "sekcja_ogloszenia": item[4],
            'poziom_harmonogramu': item[7],
            'created_by': item[16],
            "details": {
                "tresc_ogloszenia": item[5],
                "styl_ogloszenia": int(item[6]),
                "linkigrup_string": linkigrup_string, # lista stringów
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_fbgroups
            SET 
                active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data
        
    new_data_from_hidden_fbgropus = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_fbgroups', 'sekcja_ogloszenia', 'hiddeCampaigns', 'status', 4, 'active_task', 0)
    # hiddeCampaigns - FB GROUPS
    for i, item in enumerate(new_data_from_hidden_fbgropus):

        if item[8] is not None:
            linkigrup_string = str(item[8]).split('-@-')
        else: 
            linkigrup_string = []
        
        if item[9] is not None:
            zdjecia_string = str(item[9]).split('-@-')
        else: 
            zdjecia_string = []

        theme = {
            "task_id": int(item[10]),
            "platform": "FB-GROUPS",
            "waiting_list_id": int(item[2]),
            "kategoria_ogloszenia": item[3],
            "id_ogloszenia": item[1],
            "sekcja_ogloszenia": item[4],
            'poziom_harmonogramu': item[7],
            'created_by': item[16],
            "details": {
                "tresc_ogloszenia": item[5],
                "styl_ogloszenia": int(item[6]),
                "linkigrup_string": linkigrup_string, # lista stringów
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_fbgroups
            SET 
                active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_rent_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 'r', 'status', 4, 'active_task', 0)
    # Otodom - wynajem - create
    for i, item in enumerate(new_data_from_rent_otodom):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[31]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_otodom": item[33],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],


                "opis_ogloszenia": item[7],
                "liczba_pieter": item[8],
                "liczba_pokoi": item[9],
                "poziom": item[10],

                "powierzchnia": item[11],
                "konstrukcja": item[12],
                "stan_wykonczenia": item[13],

                "pow_dzialki": item[14],
                "typ_dzialki": item[15],

                "rodzaj_zabudowy": item[16],
                "rynek": item[17],
                "rok_budowy": item[18],

                "promo": item[19],
                "auto_refresh": item[20],
                "extra_top": item[21],
                "extra_home": item[22],
                "export_olx": item[23],
                "extra_raise": item[24],
                "mega_raise": item[25],

                "pakiet_olx_mini": item[26],
                "pakiet_olx_midi": item[27],
                "pakiet_olx_maxi": item[28],

                "pick_olx": item[29],
                "auto_refresh_olx": item[30],

                "zdjecia_string": zdjecia_string, # lista stringów

            }
        }

        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_sell_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 's', 'status', 4, 'active_task', 0)
    # Otodom - sell - create
    for i, item in enumerate(new_data_from_sell_otodom):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[31]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_otodom": item[33],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],


                "opis_ogloszenia": item[7],
                "liczba_pieter": item[8],
                "liczba_pokoi": item[9],
                "poziom": item[10],

                "powierzchnia": item[11],
                "konstrukcja": item[12],
                "stan_wykonczenia": item[13],

                "pow_dzialki": item[14],
                "typ_dzialki": item[15],

                "rodzaj_zabudowy": item[16],
                "rynek": item[17],
                "rok_budowy": item[18],

                "promo": item[19],
                "auto_refresh": item[20],
                "extra_top": item[21],
                "extra_home": item[22],
                "export_olx": item[23],
                "extra_raise": item[24],
                "mega_raise": item[25],

                "pakiet_olx_mini": item[26],
                "pakiet_olx_midi": item[27],
                "pakiet_olx_maxi": item[28],

                "pick_olx": item[29],
                "auto_refresh_olx": item[30],

                "zdjecia_string": zdjecia_string, # lista stringów

            }
        }

        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_rent_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 'r', 'status', 4, 'active_task', 0)
    # Allegro - wynajem - create
    for i, item in enumerate(new_data_from_rent_allegro):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[24]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_allegro": item[29],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[8],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "kod_pocztowy": item[6],
                "ulica": item[7],


                "opis_ogloszenia": item[9],
                "liczba_pieter": item[10],
                "liczba_pokoi": item[11],
                "poziom": item[12],

                "powierzchnia": item[13],
                "pow_dzialki": item[14],

                "typ_budynku": item[15],
                "typ_komercyjny": item[16],
                "typ_dzialki": item[17],
                "typ_kuchni": item[18],
                "rodzaj_zabudowy": item[19],

                "rynek": item[20],

                "pakiet": item[21],
                "extra_wyroznienie": item[22],
                "extra_wznawianie": item[23],

                "zdjecia_string": zdjecia_string, # lista stringów

                "osoba_kontaktowa": item[25],
                "nr_telefonu": item[26],
                "adres_email": item[27]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_sell_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 's', 'status', 4, 'active_task', 0)
    # Allegro - sell - create
    for i, item in enumerate(new_data_from_sell_allegro):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[24]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_allegro": item[29],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[8],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "kod_pocztowy": item[6],
                "ulica": item[7],


                "opis_ogloszenia": item[9],
                "liczba_pieter": item[10],
                "liczba_pokoi": item[11],
                "poziom": item[12],

                "powierzchnia": item[13],
                "pow_dzialki": item[14],

                "typ_budynku": item[15],
                "typ_komercyjny": item[16],
                "typ_dzialki": item[17],
                "typ_kuchni": item[18],
                "rodzaj_zabudowy": item[19],

                "rynek": item[20],

                "pakiet": item[21],
                "extra_wyroznienie": item[22],
                "extra_wznawianie": item[23],

                "zdjecia_string": zdjecia_string, # lista stringów

                "osoba_kontaktowa": item[25],
                "nr_telefonu": item[26],
                "adres_email": item[27]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_rent_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 'r', 'status', 4, 'active_task', 0)
    # ADRESOWO - wynajem - create
    for i, item in enumerate(new_data_from_rent_adresowo):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[22]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "ulica": item[12],

                "umeblowanie": item[7],
                "opis_ogloszenia": item[8],
                "liczba_pieter": item[9],
                "liczba_pokoi": item[10],
                "poziom": item[11],
                "winda": item[13],
                "powierzchnia": item[14],
                "pow_dzialki": item[15],
                "rok_budowy": item[16],
                "stan": item[17],
                "typ_budynku": item[18],
                "rodzaj_dzialki": item[19],
                "przeznaczenie_lokalu": item[20],
                "forma_wlasnosci": item[21],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[23],
                "nr_telefonu": item[24]         
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_sell_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 's', 'status', 4, 'active_task', 0)
    # ADRESOWO - sell - create
    for i, item in enumerate(new_data_from_sell_adresowo):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[22]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "ulica": item[12],

                "umeblowanie": item[7],
                "opis_ogloszenia": item[8],
                "liczba_pieter": item[9],
                "liczba_pokoi": item[10],
                "poziom": item[11],
                "winda": item[13],
                "powierzchnia": item[14],
                "pow_dzialki": item[15],
                "rok_budowy": item[16],
                "stan": item[17],
                "typ_budynku": item[18],
                "rodzaj_dzialki": item[19],
                "przeznaczenie_lokalu": item[20],
                "forma_wlasnosci": item[21],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[23],
                "nr_telefonu": item[24],
                "rynek": item[32]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_rent_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 'r', 'status', 4, 'active_task', 0)
    # FACEBOOK - wynajem - create
    for i, item in enumerate(new_data_from_rent_facebook):
        znaczniki = str(item[8]).split('-@-')
        zdjecia_string = str(item[10]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
            "details": {
                "tytul_ogloszenia": item[3],
                "opis_ogloszenia": item[4],
                "cena": item[5],
                "stan_nieruchomosci": item[6],
                "miejscowosc": item[7],
                "znaczniki": znaczniki, # lista znaczników
                "promowanie": item[9],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[11],
                "nr_telefonu": item[12]               
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    new_data_from_sell_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 's', 'status', 4, 'active_task', 0)
    # FACEBOOK - sprzedaż - create
    for i, item in enumerate(new_data_from_sell_facebook):
        znaczniki = str(item[8]).split('-@-')
        zdjecia_string = str(item[10]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
            "details": {
                "tytul_ogloszenia": item[3],
                "opis_ogloszenia": item[4],
                "cena": item[5],
                "stan_nieruchomosci": item[6],
                "miejscowosc": item[7],
                "znaczniki": znaczniki, # lista znaczników
                "promowanie": item[9],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[11],
                "nr_telefonu": item[12]               
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data
    
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
            return task_data
    
    new_data_from_sell_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 's', 'status', 4, 'active_task', 0)
    # LENTO.PL - sprzedaż - create
    for i, item in enumerate(new_data_from_sell_lento):
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
                "rynek": item[11],
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
            return task_data



    edit_data_from_rent_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # OTODOM - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_otodom):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[31]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_otodom": item[33],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],


                "opis_ogloszenia": item[7],
                "liczba_pieter": item[8],
                "liczba_pokoi": item[9],
                "poziom": item[10],

                "powierzchnia": item[11],
                "konstrukcja": item[12],
                "stan_wykonczenia": item[13],

                "pow_dzialki": item[14],
                "typ_dzialki": item[15],

                "rodzaj_zabudowy": item[16],
                "rynek": item[17],
                "rok_budowy": item[18],

                "promo": item[19],
                "auto_refresh": item[20],
                "extra_top": item[21],
                "extra_home": item[22],
                "export_olx": item[23],
                "extra_raise": item[24],
                "mega_raise": item[25],

                "pakiet_olx_mini": item[26],
                "pakiet_olx_midi": item[27],
                "pakiet_olx_maxi": item[28],

                "pick_olx": item[29],
                "auto_refresh_olx": item[30],

                "zdjecia_string": zdjecia_string, # lista stringów

            }
        }

        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_sell_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 's', 'status', 5, 'active_task', 0)
    # OTODOM - sell - edit
    for i, item in enumerate(edit_data_from_sell_otodom):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[31]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_otodom": item[33],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],


                "opis_ogloszenia": item[7],
                "liczba_pieter": item[8],
                "liczba_pokoi": item[9],
                "poziom": item[10],

                "powierzchnia": item[11],
                "konstrukcja": item[12],
                "stan_wykonczenia": item[13],

                "pow_dzialki": item[14],
                "typ_dzialki": item[15],

                "rodzaj_zabudowy": item[16],
                "rynek": item[17],
                "rok_budowy": item[18],

                "promo": item[19],
                "auto_refresh": item[20],
                "extra_top": item[21],
                "extra_home": item[22],
                "export_olx": item[23],
                "extra_raise": item[24],
                "mega_raise": item[25],

                "pakiet_olx_mini": item[26],
                "pakiet_olx_midi": item[27],
                "pakiet_olx_maxi": item[28],

                "pick_olx": item[29],
                "auto_refresh_olx": item[30],

                "zdjecia_string": zdjecia_string, # lista stringów

            }
        }

        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_rent_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # ALLEGRO - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_allegro):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[24]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_allegro": item[29],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[8],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "kod_pocztowy": item[6],
                "ulica": item[7],


                "opis_ogloszenia": item[9],
                "liczba_pieter": item[10],
                "liczba_pokoi": item[11],
                "poziom": item[12],

                "powierzchnia": item[13],
                "pow_dzialki": item[14],

                "typ_budynku": item[15],
                "typ_komercyjny": item[16],
                "typ_dzialki": item[17],
                "typ_kuchni": item[18],
                "rodzaj_zabudowy": item[19],

                "rynek": item[20],

                "pakiet": item[21],
                "extra_wyroznienie": item[22],
                "extra_wznawianie": item[23],

                "zdjecia_string": zdjecia_string, # lista stringów

                "osoba_kontaktowa": item[25],
                "nr_telefonu": item[26],
                "adres_email": item[27]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_sell_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 's', 'status', 5, 'active_task', 0)
    # ALLEGRO - sell - edit
    for i, item in enumerate(edit_data_from_sell_allegro):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[24]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_allegro": item[29],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[8],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "kod_pocztowy": item[6],
                "ulica": item[7],


                "opis_ogloszenia": item[9],
                "liczba_pieter": item[10],
                "liczba_pokoi": item[11],
                "poziom": item[12],

                "powierzchnia": item[13],
                "pow_dzialki": item[14],

                "typ_budynku": item[15],
                "typ_komercyjny": item[16],
                "typ_dzialki": item[17],
                "typ_kuchni": item[18],
                "rodzaj_zabudowy": item[19],

                "rynek": item[20],

                "pakiet": item[21],
                "extra_wyroznienie": item[22],
                "extra_wznawianie": item[23],

                "zdjecia_string": zdjecia_string, # lista stringów

                "osoba_kontaktowa": item[25],
                "nr_telefonu": item[26],
                "adres_email": item[27]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_rent_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # ADRESOWO - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_adresowo):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[22]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_adresowo": item[26],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "ulica": item[12],

                "umeblowanie": item[7],
                "opis_ogloszenia": item[8],
                "liczba_pieter": item[9],
                "liczba_pokoi": item[10],
                "poziom": item[11],
                "winda": item[13],
                "powierzchnia": item[14],
                "pow_dzialki": item[15],
                "rok_budowy": item[16],
                "stan": item[17],
                "typ_budynku": item[18],
                "rodzaj_dzialki": item[19],
                "przeznaczenie_lokalu": item[20],
                "forma_wlasnosci": item[21],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[23],
                "nr_telefonu": item[24]         
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_sell_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 's', 'status', 5, 'active_task', 0)
    # ADRESOWO - sell - edit
    for i, item in enumerate(edit_data_from_sell_adresowo):
        # mazowieckie / warszawski zachodni / Izabelin / Izabelin / Brak /
        region = tuple(str(item[5])[:-2].split(' / '))

        zdjecia_string = str(item[22]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_adresowo": item[26],
            "details": {
                "tytul_ogloszenia": item[3],
                "cena": item[6],

                "wojewodztwo": region[0],
                "powiat": region[1],
                "gmina": region[2],
                "miejscowosc": region[3],
                "dzielnica": region[4],

                "ulica": item[12],

                "umeblowanie": item[7],
                "opis_ogloszenia": item[8],
                "liczba_pieter": item[9],
                "liczba_pokoi": item[10],
                "poziom": item[11],
                "winda": item[13],
                "powierzchnia": item[14],
                "pow_dzialki": item[15],
                "rok_budowy": item[16],
                "stan": item[17],
                "typ_budynku": item[18],
                "rodzaj_dzialki": item[19],
                "przeznaczenie_lokalu": item[20],
                "forma_wlasnosci": item[21],
                "zdjecia_string": zdjecia_string, # lista stringów
                "osoba_kontaktowa": item[23],
                "nr_telefonu": item[24],
                "rynek": item[32]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_rent_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # FACEBOOK - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_facebook):
        zdjecia_string = str(item[19]).split('-@-')
        znaczniki = str(item[8]).split('-@-')
        zdjecia_string = str(item[10]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
            "details": {
                "tytul_ogloszenia": item[3],
                "opis_ogloszenia": item[4],
                "cena": item[5],
                "stan_nieruchomosci": item[6],
                "miejscowosc": item[7],
                "znaczniki": znaczniki, # lista znaczników
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data
        
    edit_data_from_sell_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 's', 'status', 5, 'active_task', 0)
    # FACEBOOK - sprzedaż - edit
    for i, item in enumerate(edit_data_from_sell_facebook):
        zdjecia_string = str(item[19]).split('-@-')
        znaczniki = str(item[8]).split('-@-')
        zdjecia_string = str(item[10]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
            "details": {
                "tytul_ogloszenia": item[3],
                "opis_ogloszenia": item[4],
                "cena": item[5],
                "stan_nieruchomosci": item[6],
                "miejscowosc": item[7],
                "znaczniki": znaczniki, # lista znaczników
                "zdjecia_string": zdjecia_string # lista stringów
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    add_ads_fb_profil = msq.connect_to_database(f'SELECT * FROM ogloszenia_socialsync WHERE status = 4 AND active_task = 0;')
    # FACEBOOK - sprzedaż - edit
    for i, item in enumerate(add_ads_fb_profil):
        zdjecia_string = str(item[8]).split('-@-')

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "SOCIALSYNC",
            "id": item[0],
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia": item[2],
            "details": {
                "tresc_ogloszenia": item[5],
                "zdjecia_string": zdjecia_string, # lista stringów
                "created_by": item[15]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_socialsync
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["create"].append(theme)
            return task_data

    generate_description_fb_profil = msq.connect_to_database(f'SELECT * FROM ogloszenia_socialsync WHERE status = 5 AND active_task = 0;')
    # FACEBOOK - sprzedaż - edit
    for i, item in enumerate(generate_description_fb_profil):

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "SOCIALSYNC-DESCRIPTION",
            "id": item[0],
            "id_ogloszenia": item[2],
            "details": {
                "tresc_ogloszenia": item[5],
                "polecenie_ai": item[7]
            }
        }

        action_taks = f'''
            UPDATE ogloszenia_socialsync
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    edit_data_from_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 5, 'active_task', 0)
    # LENTO.PL - wynajem - edit
    for i, item in enumerate(edit_data_from_rent_lento):
        zdjecia_string = str(item[19]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "LENTO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_lento": item[24],
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
                "nr_telefonu": item[22]         
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
            return task_data
    
    edit_data_from_sell_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 's', 'status', 5, 'active_task', 0)
    # LENTO.PL - sprzedaż - edit
    for i, item in enumerate(edit_data_from_sell_lento):
        zdjecia_string = str(item[19]).split('-@-')
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "LENTO",
            "rodzaj_ogloszenia": item[1],
            "kategoria_ogloszenia": item[4],
            "id_ogloszenia_na_lento": item[24],
            "details": {
                "tytul_ogloszenia": item[3],
                "liczba_pieter": item[5],
                "pietro": item[6],
                "zabudowa": item[7],
                "przeznaczenie_lokalu": item[8],
                "rodzaj_dzialki": item[9],
                "numer_kw": item[10],
                "rynek": item[11],
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
                "nr_telefonu": item[22]         
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
            return task_data




    delete_rent_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 'r', 'status', 6, 'active_task', 0)
    # OTODOM - rent - del    
    for i, item in enumerate(delete_rent_otodom):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_otodom": item[33]
        }
        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_sell_otodom = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_otodom', 'rodzaj_ogloszenia', 's', 'status', 6, 'active_task', 0)
    # OTODOM - sell - del    
    for i, item in enumerate(delete_sell_otodom):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "OTODOM",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_otodom": item[33]
        }
        action_taks = f'''
            UPDATE ogloszenia_otodom
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_rent_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 'r', 'status', 6, 'active_task', 0)
    # ALLEGRO - rent - del    
    for i, item in enumerate(delete_rent_allegro):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_sell_allegro = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_allegrolokalnie', 'rodzaj_ogloszenia', 's', 'status', 6, 'active_task', 0)
    # ALLEGRO - sell - del    
    for i, item in enumerate(delete_sell_allegro):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ALLEGRO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_allegrolokalnie
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_rent_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 'r', 'status', 6, 'active_task', 0)
    # ADRESOWO - rent - del    
    for i, item in enumerate(delete_rent_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_sell_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 's', 'status', 6, 'active_task', 0)
    # ADRESOWO - sell - del    
    for i, item in enumerate(delete_sell_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_rent_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 'r', 'status', 6, 'active_task', 0)
    # FACEBOOK - wynajem - del    
    for i, item in enumerate(delete_rent_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_sell_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 's', 'status', 6, 'active_task', 0)
    # FACEBOOK - sprzedaż - del    
    for i, item in enumerate(delete_sell_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["delete"].append(theme)

    delete_rent_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 'r', 'status', 6, 'active_task', 0)
    # LENTO.PL - wynajem - del    
    for i, item in enumerate(delete_rent_lento):
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
            task_data["delete"].append(theme)

    delete_sell_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 's', 'status', 6, 'active_task', 0)
    # LENTO.PL - wynajem - del    
    for i, item in enumerate(delete_sell_lento):
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
            task_data["delete"].append(theme)
            return task_data




    hold_rent_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 'r', 'status', 7, 'active_task', 0)
    # ADRESOWO - wynajem - hold    
    for i, item in enumerate(hold_rent_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["hold"].append(theme)
            return task_data
        
    hold_sell_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 's', 'status', 7, 'active_task', 0)
    # ADRESOWO - sell - hold    
    for i, item in enumerate(hold_sell_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["hold"].append(theme)
            return task_data

    hold_rent_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 'r', 'status', 7, 'active_task', 0)
    # FACEBOOK - wynajem - hold    
    for i, item in enumerate(hold_rent_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["hold"].append(theme)
            return task_data
        
    hold_sell_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 's', 'status', 7, 'active_task', 0)
    # FACEBOOK - wynajem - hold    
    for i, item in enumerate(hold_sell_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["hold"].append(theme)
            return task_data

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
            return task_data
    
    hold_sell_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 's', 'status', 7, 'active_task', 0)
    # LENTO.PL - sprzdaż - create    
    for i, item in enumerate(hold_sell_lento):
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
            return task_data



    resume_rent_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 'r', 'status', 8, 'active_task', 0)
    # ADRESOWO - wynajem - resume    
    for i, item in enumerate(resume_rent_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["resume"].append(theme)
            return task_data
        
    resume_sell_adresowo = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_adresowo', 'rodzaj_ogloszenia', 's', 'status', 8, 'active_task', 0)
    # ADRESOWO - sell - resume    
    for i, item in enumerate(resume_sell_adresowo):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "ADRESOWO",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_adresowo": item[26],
        }
        action_taks = f'''
            UPDATE ogloszenia_adresowo
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["resume"].append(theme)
            return task_data

    resume_rent_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 'r', 'status', 8, 'active_task', 0)
    # FACEBOOK - wynajem - wznow    
    for i, item in enumerate(resume_rent_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["resume"].append(theme)
            return task_data
        
    resume_sell_facebook = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_facebook', 'rodzaj_ogloszenia', 's', 'status', 8, 'active_task', 0)
    # FACEBOOK - sprzedaż - wznow    
    for i, item in enumerate(resume_sell_facebook):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FACEBOOK",
            "rodzaj_ogloszenia": item[1],
            "id_ogloszenia_na_facebook": item[14],
        }
        action_taks = f'''
            UPDATE ogloszenia_facebook
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["resume"].append(theme)
            return task_data

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
    
    resume_sell_lento = take_data_where_ID_AND_somethig_AND_Something('*', 'ogloszenia_lento', 'rodzaj_ogloszenia', 's', 'status', 8, 'active_task', 0)
    # LENTO.PL - sprzedaz - create    
    for i, item in enumerate(resume_sell_lento):
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
    
    fbgroups_stats_collector = msq.connect_to_database(f'SELECT * FROM fbgroups_stats_monitor WHERE status = 4 AND active_task = 0;')
    # FB GROUPS STATS   
    for i, item in enumerate(fbgroups_stats_collector):
        ready_tuple_list  = []
        groups_object = str(item[1]).split('-@-')
        for string_id_link in groups_object:
            tuple_item = (int(string_id_link.split('-$-')[0]), string_id_link.split('-$-')[1])
            ready_tuple_list.append(tuple_item)

        theme = {
            "task_id": int(time.time()) + i,
            "platform": "FBGROUPS-MONITOR",
            "ready_tuple_list": ready_tuple_list,
            "created_by": item[2]
        }
        action_taks = f'''
            UPDATE fbgroups_stats_monitor
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data
    
    tasks_check_visibility = msq.connect_to_database(f'SELECT * FROM tasks_check_visibility WHERE status = 4 AND active_task = 0;')
    # check visibility    
    for i, item in enumerate(tasks_check_visibility):

        ready_dict_list = decode_task_data(item[3])
        

        theme = {
            'task_id': item[1],
            'portal_nazwa': item[2],
            'dane_wykonawcze': ready_dict_list,
            "platform": f"VISIBILITY-MONITOR"
        }
        action_taks = f'''
            UPDATE tasks_check_visibility
            SET active_task=%s
            WHERE id = %s;
        '''
        values = (1, item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data
    
    mind_forge_si = msq.connect_to_database(f'SELECT * FROM mind_forge_si WHERE status = 5 AND active_task = 0;')
    # FB GROUPS STATS   
    for i, item in enumerate(mind_forge_si):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": "MINDFORGE",
            "task_description": item[2],
            "user_name": item[1]
        }
        action_taks = f'''
            UPDATE mind_forge_si
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data
        
    forms_api_test = msq.connect_to_database(f'SELECT * FROM ogloszenia_formsapitest WHERE status = 4 AND active_task = 0;')
    # FB GROUPS STATS   
    for i, item in enumerate(forms_api_test):
        theme = {
            "task_id": int(time.time()) + i,
            "platform": item[1]
        }
        action_taks = f'''
            UPDATE ogloszenia_formsapitest
            SET 
                active_task=%s,
                id_zadania=%s
            WHERE id = %s;
        '''
        values = (1, theme["task_id"], item[0])
        if msq.insert_to_database(action_taks, values):
            task_data["update"].append(theme)
            return task_data

    return task_data

def generatorKolumn(list_of_strings, sepa=", "):
    export_string = ""
    for string in list_of_strings:
        if not str(string).count(sepa):
            export_string += f"{string}{sepa}"
    
    if export_string:
        export_string = export_string[:-2].strip()
        return export_string
    else:
        return None


def send_emails(user_commnder, emails_list, title_mess, content_mess):
    for EMAIL_COMPANY in emails_list:
        TITLE_MESSAGE = title_mess
        message = content_mess

        effect = sendEmailBySmtp.send_html_email(TITLE_MESSAGE, message, EMAIL_COMPANY)
        if effect == "success":
            addDataLogs(f'Wysłano wiadmość do {EMAIL_COMPANY} w temacie: "{TITLE_MESSAGE}" od @{user_commnder}.', effect)
        else:
            addDataLogs(f'Nie wysłano wiadmość do {EMAIL_COMPANY} w temacie: "{TITLE_MESSAGE}" od @{user_commnder} z powodu błędu: {effect}', 'danger')
    return True

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
    
    api_key = request.headers.get('api_key')  # Pobieranie klucza API z nagłówka
    # print(request.headers)
    if api_key and api_key in allowed_API_KEYS:
        if 'action' in request.headers:
            action = request.headers.get('action')
            if action == 'get_json':
                return jsonify(getMainResponder()) # Pobieranie danych po weryfikacji
            elif action == 'respond':
                message = request.headers.get('message')
                taskID = request.headers.get('taskID')
                success = request.headers.get('success')

                if message == 'Done-chat-add-new': 
                                        
                    action_taks = f'''
                        UPDATE chat_task
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-system-logs': 
                                        
                    action_taks = f'''
                        UPDATE system_logs_monitor
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-career-add-fbgroups': 
                                        
                    action_taks = f'''
                        UPDATE ogloszenia_fbgroups
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        add_aifaLog(f'Emisja kampanii o id:{taskID}, zakończona sukcesem. Poinformuj wszystkich, że nie odpisywałaś bo pracowałaś nad kampanią na grupach Facebooka.')
                        addDataLogs(f'Emisja kampanii o id:{taskID}, zakończona sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
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
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na Lento.pl, zakończone sukcesem. Poinformuj wszystkich, że nie odpisywałaś bo pracowałaś nad ogłoszeniem na lento.')
                        addDataLogs(f'Dodawanie nowego ogłoszenia o id:{taskID} na Lento.pl, zakończone sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-facebook-add-new': 
                    action_taks = f'''
                        UPDATE ogloszenia_facebook
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na facebook, zakończone sukcesem.')
                        addDataLogs(f'Dodawanie nowego ogłoszenia o id:{taskID} na facebook, zakończone sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-adresowo-add-new': 
                    if success!='' and success is not None: 
                        id_adresowo_ads = str(success)
                    else: 
                        return jsonify({"error": 500})
                    
                    action_taks = f'''
                        UPDATE ogloszenia_adresowo
                        SET 
                            active_task=%s,
                            status=%s,
                            id_ogloszenia_na_adresowo=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, id_adresowo_ads, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na adresowo.pl, zakończone sukcesem.')
                        addDataLogs(f'Dodawanie nowego ogłoszenia o id:{taskID} na adresowo.pl, zakończone sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-allegro-add-new': 
                    if success!='' and success is not None: 
                        id_adresowo_ads = str(success)
                    else: 
                        return jsonify({"error": 500})
                    
                    action_taks = f'''
                        UPDATE ogloszenia_allegrolokalnie
                        SET 
                            active_task=%s,
                            status=%s,
                            id_ogloszenia_na_allegro=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, id_adresowo_ads, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na allegrolokalnie.pl, zakończone sukcesem.')
                        addDataLogs(f'Dodawanie nowego ogłoszenia o id:{taskID} na allegrolokalnie.pl, zakończone sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-otodom-add-new': 
                    if success!='' and success is not None: 
                        id_otodom_ads = str(success)
                    else: 
                        return jsonify({"error": 500})
                    
                    action_taks = f'''
                        UPDATE ogloszenia_otodom
                        SET 
                            active_task=%s,
                            status=%s,
                            id_ogloszenia_na_otodom=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, id_otodom_ads, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na otodom.pl, zakończone sukcesem.')
                        addDataLogs(f'Dodawanie nowego ogłoszenia o id:{taskID} na otodom.pl, zakończone sukcesem.', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-lento-delete': 

                    action_taks = f'''
                        DELETE FROM ogloszenia_lento 
                        
                        WHERE id_zadania = %s;
                    '''
                    values = (taskID,)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z lento.pl')
                        addDataLogs(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z lento.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-facebook-delete': 

                    action_taks = f'''
                        DELETE FROM ogloszenia_facebook
                        
                        WHERE id_zadania = %s;
                    '''
                    values = (taskID,)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z facebook.com')
                        addDataLogs(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z facebook.com', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-adresowo-delete': 

                    action_taks = f'''
                        DELETE FROM ogloszenia_adresowo
                        
                        WHERE id_zadania = %s;
                    '''
                    values = (taskID,)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z adresowo.pl')
                        addDataLogs(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z adresowo.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-allegro-delete': 

                    action_taks = f'''
                        DELETE FROM ogloszenia_allegrolokalnie
                        
                        WHERE id_zadania = %s;
                    '''
                    values = (taskID,)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z allegrolokalnie.pl')
                        addDataLogs(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z allegrolokalnie.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-otodom-delete': 

                    action_taks = f'''
                        DELETE FROM ogloszenia_otodom
                        
                        WHERE id_zadania = %s;
                    '''
                    values = (taskID,)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z otodom.pl')
                        addDataLogs(f'Z powodzeniem usunięto ogłoszenie o id:{taskID} z otodom.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
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
                        # add_aifaLog(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na lento.pl')
                        addDataLogs(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na lento.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-facebook-hold': 

                    action_taks = f'''
                        UPDATE ogloszenia_facebook
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 0, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na facebook.com')
                        addDataLogs(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na facebook.com', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-adresowo-hold': 

                    action_taks = f'''
                        UPDATE ogloszenia_adresowo
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 0, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na adresowo.pl')
                        addDataLogs(f'Z powodzeniem wstrzymano ogłoszenie o id:{taskID} na adresowo.com', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
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
                        # add_aifaLog(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na lento.pl')
                        addDataLogs(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na lento.com', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-facebook-resume': 

                    action_taks = f'''
                        UPDATE ogloszenia_facebook
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na facebook.com')
                        addDataLogs(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na facebook.com', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-adresowo-resume': 

                    action_taks = f'''
                        UPDATE ogloszenia_adresowo
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na adresowo.pl')
                        addDataLogs(f'Z powodzeniem wznowiono ogłoszenie o id:{taskID} na adresowo.pl', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
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
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na lento.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Aktualizacja ogłoszenia o id:{taskID} na lento.pl, przebiegła pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-facebook-update': 

                    action_taks = f'''
                        UPDATE ogloszenia_facebook
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na facebook.com, przebiegła pomyślnie!')
                        addDataLogs(f'Aktualizacja ogłoszenia o id:{taskID} na facebook.com, przebiegła pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})

                if message == 'Done-adresowo-update': 

                    action_taks = f'''
                        UPDATE ogloszenia_adresowo
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na adresowo.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Aktualizacja ogłoszenia o id:{taskID} na adresowo.pl, przebiegła pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-allegro-update': 

                    action_taks = f'''
                        UPDATE ogloszenia_allegrolokalnie
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na allegrolokalnie.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Aktualizacja ogłoszenia o id:{taskID} na allegrolokalnie.pl, przebiegła pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-otodom-update': 

                    action_taks = f'''
                        UPDATE ogloszenia_otodom
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-fbmonitor-update': 

                    action_taks = f'''
                        UPDATE fbgroups_stats_monitor
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Monitorowanie grup FB o id-cyklu:{taskID} przebiegło pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-mind-forge': 

                    action_taks = f'''
                        UPDATE mind_forge_si
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Zadania modułu decyzyjnego o id: {taskID} zostało zrealizowane!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})

                if message == 'Done-visibility-check': 

                    action_taks = f'''
                        UPDATE tasks_check_visibility
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Zadania modułu sprawdzania widoczności o id: {taskID} zostało zrealizowane!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-public-socialsync': 

                    action_taks = f'''
                        UPDATE ogloszenia_socialsync
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Publikacja posta w trybie SocialSync o id: {taskID} zostało zrealizowane!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
                if message == 'Done-socialsync-description': 

                    action_taks = f'''
                        UPDATE ogloszenia_socialsync
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 4, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Aktualizacja ogłoszenia o id:{taskID} na otodom.pl, przebiegła pomyślnie!')
                        addDataLogs(f'Generowanie treści posta w trybie SocialSync o id: {taskID} zostało zrealizowane!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
                if message == 'Done-formsAPItest-test': 

                    action_taks = f'''
                        UPDATE ogloszenia_formsapitest
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 1, taskID)
                    
                    if msq.insert_to_database(action_taks, values):
                        add_aifaLog(f'Diagnostyka automatyzacji zakończona pomyślnie. Wszystkie kluczowe komponenty systemu obsługi ogłoszeń nieruchomości działają prawidłowo. Brak błędów krytycznych. Sprawdzone: struktura formularzy, detekcja elementów wizualnych, przepływ danych. Zadanie o id: {taskID} zostało zrealizowane i przebiegło pomyślnie!')
                        addDataLogs(f'Diagnostyka automatyzacji zakończona pomyślnie. Wszystkie kluczowe komponenty systemu obsługi ogłoszeń nieruchomości działają prawidłowo. Brak błędów krytycznych. Sprawdzone: struktura formularzy, detekcja elementów wizualnych, przepływ danych. Zadanie o id: {taskID} zostało zrealizowane!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                
            elif action == 'error':
                taskID = request.headers.get('taskID')
                errorMessage = request.headers.get('error')
                message_flag = request.headers.get('message')
                action_taks = f""
                values = ()
                if message_flag == 'error-lento':
                    oldStatus = checkLentoAction_before_errors(taskID)
                    action_taks = f'''
                        UPDATE ogloszenia_lento
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                            action_before_errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, oldStatus, taskID)

                if message_flag == 'error-facebook':
                    oldStatus = checkFacebookAction_before_errors(taskID)
                    action_taks = f'''
                        UPDATE ogloszenia_facebook
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                            action_before_errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, oldStatus, taskID)
                
                if message_flag == 'error-adresowo':
                    oldStatus = checkAdresowoAction_before_errors(taskID)
                    action_taks = f'''
                        UPDATE ogloszenia_adresowo
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                            action_before_errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, oldStatus, taskID)

                if message_flag == 'error-allegro':
                    oldStatus = checkAllegroAction_before_errors(taskID)
                    action_taks = f'''
                        UPDATE ogloszenia_allegrolokalnie
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                            action_before_errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, oldStatus, taskID)

                if message_flag == 'error-otodom':
                    oldStatus = checkOtodomAction_before_errors(taskID)
                    action_taks = f'''
                        UPDATE ogloszenia_otodom
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                            action_before_errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, oldStatus, taskID)
                
                if message_flag == 'error-chat':
                    action_taks = f'''
                        UPDATE chat_task
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)

                if message_flag == 'error-system-logs':
                    action_taks = f'''
                        UPDATE system_logs_monitor
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)

                if message_flag == 'error-fbmonitor':
                    action_taks = f'''
                        UPDATE fbgroups_stats_monitor
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                if message_flag == 'error-career-fbgroups':
                    action_taks = f'''
                        UPDATE ogloszenia_fbgroups
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                if message_flag == 'error-mind-forge':
                    action_taks = f'''
                        UPDATE mind_forge_si
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)

                if message_flag == 'error-visibility':
                    action_taks = f'''
                        UPDATE tasks_check_visibility
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                if message_flag == 'error-public-socialsync':
                    action_taks = f'''
                        UPDATE ogloszenia_socialsync
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                if message_flag == 'error-socialsync-description':
                    action_taks = f'''
                        UPDATE ogloszenia_socialsync
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                if message_flag == 'error-formsAPItest-test':
                    action_taks = f'''
                        UPDATE ogloszenia_formsapitest
                        SET 
                            active_task=%s,
                            status=%s
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, taskID)

                if action_taks and values:
                    if msq.insert_to_database(action_taks, values):
                        add_aifaLog(f'Uwaga! ALARM! Zaleziono błędy {errorMessage}, o fladze: {message_flag} dla id_Zadania: {taskID}.')
                        addDataLogs(f'Uwaga! Zaleziono błędy {errorMessage}, o fladze: {message_flag} dla idZadania: {taskID}.', 'danger')
                        return jsonify({"message": "The error description has been saved"})
                    else:
                        return jsonify({"error": 500})
                else:
                    addDataLogs(f'Uwaga! Brak danych do zapisu w bazie przez serwer automatyzacji', 'danger')
                    return jsonify({"error": 500})

        if 'error' in request.headers:
            error = request.headers.get('error')
            if error == 'error':
                pass
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Zwrot kodu 401 w przypadku braku autoryzacji

@app.route('/get-data/', methods=['POST'])
def get_data():
    api_key = request.json.get('api_key')  # Pobieranie klucza API 
    if api_key and api_key in allowed_API_KEYS:
        if request.method == 'POST':
            platform = request.json.get('platform')
            """
                    CHARACTER AI
            """
            if platform and platform == 'CHARACTER':
                task_id = request.json.get('task_id')
                question = request.json.get('question')
                data = request.json.get('data')
                
                # Przykładowe przetwarzanie danych
                print(f'task_id: {task_id}')
                print(f'platform: {platform}')
                print(f'question: {question}')
                print(f'Data: {data}')

                action_taks = f'''
                        INSERT INTO Messages
                            (user_name, content, status)
                        VALUES 
                            (%s, %s, %s);
                    '''
                values = ('aifa', data, 2)
                    
                if msq.insert_to_database(action_taks, values):
                    return jsonify({'success': 'Dane zostały zapisane'})
                else:
                    return jsonify({"error": "Bad structure json file!"})
            
            """
                    OPEN AI
            """
            if platform and platform == 'OPEN-AI':
                task_id = request.json.get('task_id')
                question = request.json.get('question')
                data = request.json.get('data')
                
                # Przykładowe przetwarzanie danych
                print(f'task_id: {task_id}')
                print(f'platform: {platform}')
                print(f'question: {question}')
                print(f'Data: {data}')

                action_taks = f'''
                        INSERT INTO Messages
                            (user_name, content, status)
                        VALUES 
                            (%s, %s, %s);
                    '''
                values = ('aifa', data, 2)
                    
                if msq.insert_to_database(action_taks, values):
                    return jsonify({'success': 'Dane zostały zapisane'})
                else:
                    return jsonify({"error": "Bad structure json file!"})
            
            """
                    FB-GROUPS
            """
            if platform and platform == 'FB-GROUPS':
                task_id = request.json.get('task_id')
                waiting_list_id = request.json.get('waiting_list_id')
                poziom_harmonogramu = request.json.get('poziom_harmonogramu')
                status = request.json.get('status')
                errors = request.json.get('errors')
                
                # Przykładowe przetwarzanie danych
                print(f'task_id: {task_id}')
                print(f'platform: {platform}')
                print(f'waiting_list_id: {waiting_list_id}')
                print(f'poziom_harmonogramu: {poziom_harmonogramu}')
                print(f'status: {status}')
                print(f'errors: {errors}')

                action_task = f'''
                    UPDATE waitinglist_fbgroups
                    SET schedule_{poziom_harmonogramu}_status = %s, 
                        schedule_{poziom_harmonogramu}_errors = %s
                    WHERE id = %s;
                '''
                values = (status, errors, waiting_list_id)

                if msq.insert_to_database(action_task, values):
                    return jsonify({'success': 'Dane zostały zapisane'})
                else:
                    return jsonify({"error": "Bad structure json file!"})

            """
                    FBGROUPS-MONITOR
            """
            if platform and platform == 'FBGROUPS-MONITOR':
                group_id = request.json.get('stats', {}).get('group_id', None)
                members = request.json.get('stats', {}).get('members', None)
                my_pending_content = request.json.get('stats', {}).get('my_pending_content', 0)
                my_posted_content = request.json.get('stats', {}).get('my_posted_content', 0)
                my_declined_content = request.json.get('stats', {}).get('my_declined_content', 0)
                my_removed_content = request.json.get('stats', {}).get('my_removed_content', 0)
                if group_id and members:
                    try: old_data = msq.connect_to_database(f"SELECT oczekujace, opublikowane, odrzucone, usuniete FROM facebook_gropus WHERE id={group_id};")[0]
                    except IndexError:
                        return jsonify({"error": "Failed id!"})
                    except Exception as e:
                        return jsonify({"error": f"Database error: {str(e)}"})
                else:
                    return jsonify({"error": "Faild id or members!"})

                old_my_pending_content = old_data[0]
                old_my_posted_content = old_data[1]
                old_my_declined_content = old_data[2]
                old_my_removed_content = old_data[3]


                action_task = f'''
                    UPDATE facebook_gropus
                    SET prev_oczekujace = %s, 
                        oczekujace = %s,
                        prev_opublikowane = %s,
                        opublikowane = %s,
                        prev_odrzucone = %s,
                        odrzucone = %s,
                        prev_usuniete = %s,
                        usuniete = %s,
                        ilosc_czlonkow = %s
                    WHERE id = %s;
                '''
                values = (
                    old_my_pending_content, my_pending_content, 
                    old_my_posted_content, my_posted_content,
                    old_my_declined_content, my_declined_content,
                    old_my_removed_content, my_removed_content,
                    members,
                    group_id
                    )

                if msq.insert_to_database(action_task, values):
                    return jsonify({'success': 'Dane zostały zapisane'})
                else:
                    return jsonify({"error": "Bad structure json file!"})

            """
                VISIBILITY-MONITOR
            """
            if platform and platform == 'VISIBILITY-MONITOR':
                got_data = request.json.get('data', {})
                # print(got_data)
                portal = got_data.get('portal')
                if portal == 'lento':
                    # Pobieranie danych z żądania
                    record_id = got_data.get('record_id')
                    ogloszenie_id = got_data.get('ogloszenie_id')
                    status_systemowy = got_data.get('status_systemowy')
                    status_wyszukiwania_id = got_data.get('status_wyszukiwania_id')
                    poprawnosc_statusu = got_data.get('poprawnosc_statusu')
                    status_w_portalu = got_data.get('status_w_portalu')
                    print((record_id, ogloszenie_id))
                    # Sprawdzanie, czy wszystkie wymagane dane są dostępne
                    if not (record_id and ogloszenie_id):
                        return jsonify({"error": "Brak wymaganych danych!"})

                    # Logika aktualizacji lub usuwania danych
                    if status_wyszukiwania_id:
                        if not poprawnosc_statusu:
                            # Ustalanie nowego statusu
                            if status_w_portalu == 'Aktywne':
                                status_int = 1
                            elif status_w_portalu == 'Wstrzymane':
                                status_int = 0
                            else:
                                status_int = 2

                            if status_int in [1, 0]:
                                # Tworzenie zapytania do aktualizacji statusu
                                action_task = '''
                                    UPDATE ogloszenia_lento
                                    SET status = %s
                                    WHERE id = %s;
                                '''
                                values = (status_int, record_id)
                            else:
                                # --- NOWA LOGIKA DLA BŁĘDÓW SCRAPERA ---
                                action_task = '''
                                    UPDATE ogloszenia_lento
                                    SET status = 2,
                                        action_before_errors = 5,
                                        errors = %s,
                                        active_task = 0
                                    WHERE id = %s;
                                '''
                                error_msg = f"Ogłoszenie ID {ogloszenie_id} błąd Ustalania nowego statusu!"
                                values = (error_msg, record_id)
                        
                        else:
                            return jsonify({'success': 'Dane są poprawne!'})
                    else:
                        # --- NOWA LOGIKA DLA BŁĘDÓW SCRAPERA ---
                        action_task = '''
                            UPDATE ogloszenia_lento
                            SET status = 2,
                                action_before_errors = 5,
                                errors = %s,
                                active_task = 0
                            WHERE id = %s;
                        '''
                        error_msg = f"Ogłoszenie ID {ogloszenie_id} nie znalezione na Lento. Możliwa przyczyna: brak załadowania strony lub zmiana layoutu."
                        values = (error_msg, record_id)

                    # Wykonywanie zapytania do bazy danych
                    if msq.insert_to_database(action_task, values):
                        return jsonify({'success': 'Dane zostały zapisane'})
                    else:
                        return jsonify({"error": "Wystąpił błąd podczas zapisu danych!"})

                if portal == 'adresowo':
                    # Pobieranie danych z żądania
                    record_id = got_data.get('record_id')
                    ogloszenie_id = got_data.get('ogloszenie_id')
                    status_systemowy = got_data.get('status_systemowy')
                    status_wyszukiwania_id = got_data.get('status_wyszukiwania_id')
                    poprawnosc_statusu = got_data.get('poprawnosc_statusu')
                    status_w_portalu = got_data.get('status_w_portalu')
                    print((record_id, ogloszenie_id))
                    # Sprawdzanie, czy wszystkie wymagane dane są dostępne
                    if not (record_id and ogloszenie_id):
                        return jsonify({"error": "Brak wymaganych danych!"})

                    # Logika aktualizacji lub usuwania danych
                    if status_wyszukiwania_id:
                        if not poprawnosc_statusu:
                            # Ustalanie nowego statusu
                            if status_w_portalu == 'Link do ogłoszenia':
                                status_int = 1
                            elif status_w_portalu == 'Oferta wstrzymana':
                                status_int = 0
                            elif status_w_portalu == 'Usunięte: Usunięte samodzielnie przez użytkownika':
                                status_int = 3
                            else:
                                status_int = 2

                            if status_int != 3:
                                # Tworzenie zapytania do aktualizacji statusu
                                action_task = '''
                                    UPDATE ogloszenia_adresowo
                                    SET status = %s
                                    WHERE id = %s;
                                '''
                                values = (status_int, record_id)
                            else:
                                action_task = '''
                                    DELETE FROM ogloszenia_adresowo WHERE id = %s;
                                '''
                                values = (record_id,)
                        else:
                            return jsonify({'success': 'Dane są poprawne!'})
                    else:
                        # Tworzenie zapytania do usunięcia rekordu
                        action_task = '''
                            DELETE FROM ogloszenia_adresowo WHERE id = %s;
                        '''
                        values = (record_id,)

                    # Wykonywanie zapytania do bazy danych
                    if msq.insert_to_database(action_task, values):
                        return jsonify({'success': 'Dane zostały zapisane'})
                    else:
                        return jsonify({"error": "Wystąpił błąd podczas zapisu danych!"})

                if portal == 'otodom':
                    # Pobieranie danych z żądania
                    record_id = got_data.get('record_id')
                    ogloszenie_id = got_data.get('ogloszenie_id')
                    status_systemowy = got_data.get('status_systemowy')
                    status_wyszukiwania_id = got_data.get('status_wyszukiwania_id')
                    poprawnosc_statusu = got_data.get('poprawnosc_statusu')
                    status_w_portalu = got_data.get('status_w_portalu')
                    print((record_id, ogloszenie_id))
                    # Sprawdzanie, czy wszystkie wymagane dane są dostępne
                    if not (record_id and ogloszenie_id):
                        return jsonify({"error": "Brak wymaganych danych!"})

                    # Logika aktualizacji lub usuwania danych
                    if status_wyszukiwania_id:
                        if not poprawnosc_statusu:
                            # Ustalanie nowego statusu
                            if status_w_portalu == 'aktywne':
                                status_int = 1
                            else:
                                status_int = 3

                            if status_int != 3:
                                # Tworzenie zapytania do aktualizacji statusu
                                action_task = '''
                                    UPDATE ogloszenia_otodom
                                    SET status = %s
                                    WHERE id = %s;
                                '''
                                values = (status_int, record_id)
                            else:
                                action_task = '''
                                    DELETE FROM ogloszenia_otodom WHERE id = %s;
                                '''
                                values = (record_id,)
                        else:
                            return jsonify({'success': 'Dane są poprawne!'})
                    else:
                        # Tworzenie zapytania do usunięcia rekordu
                        action_task = '''
                            DELETE FROM ogloszenia_otodom WHERE id = %s;
                        '''
                        values = (record_id,)

                    # Wykonywanie zapytania do bazy danych
                    if msq.insert_to_database(action_task, values):
                        return jsonify({'success': 'Dane zostały zapisane'})
                    else:
                        return jsonify({"error": "Wystąpił błąd podczas zapisu danych!"})

            """
                FORMS-API-TEST
            """
            if platform and platform == 'FORMS-API-TEST':
                task_id = request.json.get('task_id')
                portal = request.json.get('portal')
                data = request.json.get('data')
                
                # Przykładowe przetwarzanie danych
                print(f'task_id: {task_id}')
                print(f'platform: {platform}')
                print(f'portal: {portal}')
                print(f'Data: {data}')
                prepared_message = ""
                for cat, podkategorie in data.items():
                    rodzaj = 'wynajem' if cat == 'r' else 'sprzedaż'
                    for przedmiot, lista in podkategorie.items():
                        if lista:
                            prepared_message += f'{portal}-{rodzaj}-{przedmiot} errors-> [{", ".join(lista)}]\n'
                prepared_message = prepared_message.strip()

                action_taks = f'''
                        INSERT INTO forms_errors_api
                            (verificated, status)
                        VALUES 
                            (%s, %s);
                    '''
                values = (prepared_message, 0)
                    
                if msq.insert_to_database(action_taks, values):
                    
                    return jsonify({'success': 'Dane zostały zapisane'})
                else:
                    return jsonify({"error": "Bad structure json file!"})

            return jsonify({"error": "Bad structure json file!"})
        return jsonify({"error": "Bad POST data!"})
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Zwrot kodu 401 w przypadku braku autoryzacji
    

@app.route('/api/get-template/', methods=['POST'])
def get_template():
    data = request.get_json()
    user = data.get("user")
    api_key = data.get("api_key")

    if api_key and api_key not in allowed_API_KEYS:
        return  jsonify({"data": None, "prompt": None, "level": None, "error": "Unauthorized access"}), 401

    if not user:
        return  jsonify({"data": None, "prompt": None, "level": None, "error": "Brak nazwy użytkownika"})
    
    dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")
    if user not in dane_users_dict:
        if not addNewUser(dane_users_dict, user):
            return jsonify({"data": None, "prompt": None, "level": None, "error": "Nieudana rejestracja nowego użytkownika!"})
        if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
            dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")

    system_level_data = get_next_template(dane_users_dict[user])
    ostatni_level = system_level_data['ostatni_level']
    ostatni_level_int = int(ostatni_level)
    # print(ostatni_level_int)

    return jsonify({"data": system_level_data.get('odpowiedz'), "prompt": system_level_data.get('prompt'), "level": ostatni_level_int}), 200


@app.route('/api/handling-responses/', methods=['POST'])
def handling_responses():
    dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")
    # Pobieramy dane JSON z żądania
    data = request.get_json()
    # Sprawdzamy, czy dane zostały poprawnie przesłane
    if not data:
        return jsonify({"success": False, "error": "Brak danych"}), 400
    
    user_aswer = data.get("primary_key", None)
    user = data.get("user", None)
    api_key = data.get("api_key", None)
    api_url = data.get("api_url", None)

    if not user_aswer or not user or not api_key or not api_url:
        return  jsonify({"success": False, "error": "Niewłaściwe dane zapytania!"}), 200
    
    if api_key and api_key not in allowed_API_KEYS:
        return  jsonify({"success": False, "error": "Unauthorized access"}), 401

    if user not in dane_users_dict:
        dane_users_dict = addNewUser(dane_users_dict, user)
        if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
            dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")

    ostatni_level = get_next_template(dane_users_dict[user])['ostatni_level']
    ostatni_level_int = int(ostatni_level)
    # print(ostatni_level_int)

    template_to_return = get_next_template(dane_users_dict[user])['odpowiedz']
    # print(template_to_return)
    curent_tempalte_process_response = json_string_to_dict(template_to_return)
    if curent_tempalte_process_response['error'] is not None:
        return  jsonify({"success": False, "error": curent_tempalte_process_response["error"]}), 200
    curent_tempalte = curent_tempalte_process_response['json']

    current_procedure_name = dane_users_dict.get(user, {}).get(f"{ostatni_level}", {}).get("dane", {}).get("procedura", None)
    raport_koncowy = ""
    if curent_tempalte:
        
        user_process_response = json_string_to_dict(user_aswer)

        if user_process_response.get('error') is not None and user_process_response.get('json', False):
            return jsonify({"success": False, "error": user_process_response["error"]}), 200
        user_json = user_process_response.get('json')
        # print("curent_tempalte, user_json:", curent_tempalte, user_json)

        validator_dict = validate_response_structure(curent_tempalte, user_json)
        # print("validator_dict:", validator_dict)


        if user_json and validator_dict.get("zgodnosc_struktury")\
            and not validator_dict.get("error") and not validator_dict.get("success")\
                and not validator_dict.get("anuluj_zadanie"):
            if validator_dict.get("rozne_wartosci"):
                if ostatni_level == "0":
                    """
                        POZIOM 0                            POZIOM 0                            POZIOM 0
                    """
                    picket_procedures = [label[1:] for label in validator_dict.get("rozne_wartosci", {}).keys()]
                    current_procedure_name = picket_procedures[0] if picket_procedures else None
                    prompt_level_0 = get_prompt_by_level_task(0)
                    ustaw_dane_poziom_0 = {"prompt": prompt_level_0, "poczekalnia_0": picket_procedures}
                    ustaw_dane_poziom_1 = {}

                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":
                        tabela = "OfertyNajmu"
                        zapyanie = "SELECT"
                        kolumny_lista = ["ID", "Tytul"]
                        kolumny = "ID, Tytul"
                        warunki = "WHERE StatusOferty=1"
                        wartosci = ()
                        prompt_level_1 = get_prompt_by_level_task(1, current_procedure_name)

                        ustaw_dane_poziom_1 = {
                            "procedura": current_procedure_name,
                            "tabela": tabela,
                            "zapyanie": zapyanie,
                            "kolumny_lista": kolumny_lista,
                            "kolumny": kolumny,
                            "warunki": warunki,
                            "wartosci": wartosci,
                            "prompt": prompt_level_1
                        }
                        ustaw_dane_poziom_0["procedura"] = current_procedure_name
                        ustaw_dane_poziom_0["poczekalnia_0"].remove(current_procedure_name)
                    
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                        tabela = "OfertySprzedazy"
                        zapyanie = "SELECT"
                        kolumny_lista = ["ID", "Tytul"]
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = "WHERE StatusOferty=1"
                        wartosci = ()
                        prompt_level_1 = get_prompt_by_level_task(1, current_procedure_name)

                        ustaw_dane_poziom_1 = {
                            "procedura": current_procedure_name,
                            "tabela": tabela,
                            "zapyanie": zapyanie,
                            "kolumny_lista": kolumny_lista,
                            "kolumny": kolumny,
                            "warunki": warunki,
                            "wartosci": wartosci,
                            "prompt": prompt_level_1
                        }
                        ustaw_dane_poziom_0["procedura"] = current_procedure_name
                        ustaw_dane_poziom_0["poczekalnia_0"].remove(current_procedure_name)

                    # ############################################################################
                    # WYSYLANIE_EMAILI
                    # ############################################################################
                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        tabela = "admins"
                        zapyanie = "SELECT"
                        kolumny_lista = ["ID", "ADMIN_NAME", "LOGIN", "EMAIL_ADMIN", "ADMIN_ROLE"]
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = ""
                        wartosci = ()
                        prompt_level_1 = get_prompt_by_level_task(1, current_procedure_name)

                        ustaw_dane_poziom_1 = {
                            "procedura": current_procedure_name,
                            "tabela": tabela,
                            "zapyanie": zapyanie,
                            "kolumny_lista": kolumny_lista,
                            "kolumny": kolumny,
                            "warunki": warunki,
                            "wartosci": wartosci,
                            "prompt": prompt_level_1
                        }
                        ustaw_dane_poziom_0["procedura"] = current_procedure_name
                        ustaw_dane_poziom_0["poczekalnia_0"].remove(current_procedure_name)

                    if ustaw_dane_poziom_0:    
                        dane_users_dict = template_managment(dane_users_dict, user, f"0", ustaw_dane_poziom_0)
                    if ustaw_dane_poziom_1:
                        dane_users_dict = template_managment(dane_users_dict, user, f"1", ustaw_dane_poziom_1)

                    if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                        dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")

                    dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})
                    # print("dane_poziomu_1:", dane_poziomu_1)

                    export_data = ""

                    if dane_poziomu_1:
                        zapyanie_sql = f"""
                            {dane_poziomu_1.get("zapyanie", "")} 
                                {dane_poziomu_1.get("kolumny", "")} 
                            FROM {dane_poziomu_1.get("tabela", "")} 
                            {dane_poziomu_1.get("warunki", "")};
                        """
                        values= dane_poziomu_1.get("wartosci", ())
                        # zapyanie_sql jest pobierane z bazy
                        pobrane_dane_z_bazy = msq.safe_connect_to_database(zapyanie_sql, values)
                        # pobrane_dane_z_bazy = [(1, 'tytuł pozycji1'), (2, 'tytuł pozycji2'), (3, 'tytuł pozycji3')]
                        # ############################################################################
                        # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM
                        # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ
                        # ############################################################################
                        if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM"\
                            or current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                            export_data = "{\n"
                            for row in pobrane_dane_z_bazy:
                                export_data += f'''"'''
                                for e in row:
                                    export_data += f'''[{e}]::'''
                                export_data += f'''[{dane_poziomu_1.get("tabela", "")}]": false,\n'''
                            if export_data != "{\n":
                                export_data = export_data[:-2]
                                export_data += "\n}\n"
                                dane_users_dict[user]["1"]["szablon"] = export_data

                        # ############################################################################
                        # WYSYLANIE_EMAILI
                        # ############################################################################
                        if current_procedure_name == "WYSYLANIE_EMAILI":
                            export_data = "{\n"
                            for row in pobrane_dane_z_bazy:
                                export_data += f'''"'''
                                for e in row:
                                    export_data += f'''[{e}]::'''
                                export_data = export_data[:-2] + f'''": false,\n'''

                            if export_data != "{\n":
                                export_data += f'''"@+[Dodatkowe adresy email]": [],\n'''
                                export_data = export_data[:-2] + "\n}\n"
                                dane_users_dict[user]["1"]["szablon"] = export_data

                    dane_users_dict[user]["0"]["wybor"] = dict_to_json_string(user_json)["json_string"]
                    if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                        dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                    raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"

                if ostatni_level == "1":
                    """
                        POZIOM 1                            POZIOM 1                            POZIOM 1
                    """
                    picket_choice = [label[1:] for label in validator_dict.get("rozne_wartosci", {}).keys()]
                    picket_choice_label_vals = [(label[1:], vals) for label, vals in validator_dict.get("rozne_wartosci", {}).items()]
                    current_choice = picket_choice[0] if picket_choice else None
                    # print(picket_choice_label_vals)
                    # splituje id z wybranej pozycji 
                    def split_id_current_choice(current_choice_string: str):
                        if current_choice_string and current_choice_string.startswith("["):
                            splited_id = int(current_choice_string.split("]::")[0][1:])
                        return splited_id

                    def split_emails_picket_choice(picket_choice_label_vals_list: list):
                        emails_list = []
                        for current_choice_string, current_value in picket_choice_label_vals_list:
                            if current_choice_string and str(current_choice_string).startswith("["):
                                email_adr = str(current_choice_string.split("]::")[3][1:])
                                emails_list.append(email_adr)
                            if current_choice_string and str(current_choice_string).startswith("@+")\
                                and current_value and isinstance(current_value, list):
                                emails_list += current_value
                        return emails_list
                    
                    ustaw_dane_poziom_2 = {}
                    dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":

                        tabela = "OfertyNajmu"
                        zapyanie = "SELECT"
                        kolumny_lista = [
                                    "Opis",
                                    "Cena",
                                    "Metraz",
                                    "Czynsz",
                                    "RokBudowy",
                                    "NumerKW",
                                    "TelefonKontaktowy",
                                    "EmailKontaktowy"
                            ]
                        
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = "WHERE id = %s"
                        wybrane_id = split_id_current_choice(current_choice)
                        wartosci = (wybrane_id,)
                        prompt_level_2 = get_prompt_by_level_task(2, current_procedure_name)


                        ustaw_dane_poziom_2 = {
                            "procedura": current_procedure_name,
                            "tabela": tabela,
                            "zapyanie": zapyanie,
                            "kolumny_lista": kolumny_lista,
                            "kolumny": kolumny,
                            "warunki": warunki,
                            "wybrane_id": wybrane_id,
                            "wartosci": wartosci,
                            "prompt": prompt_level_2
                        }
                      
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":

                        tabela = "OfertySprzedazy"
                        zapyanie = "SELECT"
                        kolumny_lista = [
                                    "Opis",
                                    "Cena",
                                    "Metraz",
                                    "RokBudowy",
                                    "NumerKW",
                                    "TelefonKontaktowy",
                                    "EmailKontaktowy"
                            ]
                        
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = "WHERE id = %s"
                        wybrane_id = split_id_current_choice(current_choice)
                        wartosci = (wybrane_id,)
                        
                        prompt_level_2 = get_prompt_by_level_task(2, current_procedure_name)

                        ustaw_dane_poziom_2 = {
                            "procedura": current_procedure_name,
                            "tabela": tabela,
                            "zapyanie": zapyanie,
                            "kolumny_lista": kolumny_lista,
                            "kolumny": kolumny,
                            "warunki": warunki,
                            "wybrane_id": wybrane_id,
                            "wartosci": wartosci,
                            "prompt": prompt_level_2
                        } 
                        
                    # ############################################################################
                    # WYSYLANIE_EMAILI
                    # ############################################################################
                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        
                        wybrane_emails = split_emails_picket_choice(picket_choice_label_vals) # lista emaili
                        prompt_level_2 = get_prompt_by_level_task(2, current_procedure_name)

                        ustaw_dane_poziom_2 = {
                            "procedura": current_procedure_name,
                            "wybrane_emails": wybrane_emails,
                            "prompt": prompt_level_2
                        }
                    
                    if dane_poziomu_1:
                        ustaw_dane_poziomu_1 = dane_poziomu_1

                        if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM"\
                            or current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                            ustaw_dane_poziomu_1["poczekalnia_1"] = picket_choice
                            ustaw_dane_poziomu_1["wybrano"] = current_choice
                            ustaw_dane_poziomu_1["poczekalnia_1"].remove(current_choice)

                        if current_procedure_name == "WYSYLANIE_EMAILI":
                            
                            ustaw_dane_poziomu_1["poczekalnia_1"] = []

                        dane_users_dict = template_managment(dane_users_dict, user, f"1", ustaw_dane_poziomu_1)

                    if ustaw_dane_poziom_2:
                        dane_users_dict = template_managment(dane_users_dict, user, f"2", ustaw_dane_poziom_2)

                    dane_users_dict[user]["1"]["wybor"] = dict_to_json_string(user_json)["json_string"]

                    if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                        dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

                    dane_poziomu_2 = dane_users_dict.get(user, {}).get(f"2", {}).get("dane", {})
                    # print("dane_poziomu_2:", dane_poziomu_2)

                    if dane_poziomu_2:
                        if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM"\
                            or current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                            zapyanie_sql = f"""
                                {dane_poziomu_2.get("zapyanie", "")} 
                                    {dane_poziomu_2.get("kolumny", "")} 
                                FROM {dane_poziomu_2.get("tabela", "")} 
                                {dane_poziomu_2.get("warunki", "")};
                            """
                            values= dane_poziomu_2.get("wartosci", ())
                            # zapyanie_sql jest pobierane z bazy
                            [{"p":"paragraf"}, {"li":["dynamiczny", "stylowalny"]}]
                            # pobrane_dane_z_bazy = [("tytuł", 'opis', 651450, 89),][0]
                            
                            try: pobrane_dane_z_bazy = msq.safe_connect_to_database(zapyanie_sql, values)[0]
                            except IndexError: return jsonify({"success": False, "error": f"Błąd poziomu {ostatni_level} dla {current_procedure_name}"}), 400
                            [("tytuł", '[{"p":"paragraf 1"}, {"li":["dynamiczny 1", "stylowalny 1"]}]', 651450, 89)][0]
                            def is_json_like_string(text):
                                """Sprawdza, czy string wygląda na strukturę JSON po usunięciu znaku ^."""
                                
                                # Usuwamy wszystkie wystąpienia ^ z tekstu
                                text = text.replace('^', '')

                                # Sprawdzamy, czy tekst zawiera kluczowe znaki JSON
                                json_chars = ['{', '[', ']', ':', '"']
                                contains_json_structure = any(char in text for char in json_chars)
                                
                                # Zwraca True, tylko jeśli są kluczowe znaki JSON po usunięciu ^
                                return contains_json_structure

                            # Zastosowanie warunku do listy pobrane_dane_z_bazy
                            pobrane_dane_z_bazy_escaped = [
                                poz.replace('^', "").replace('"', "^").replace('\n', " ") if isinstance(poz, str) and is_json_like_string(poz) else poz 
                                for poz in pobrane_dane_z_bazy
                            ]
                            export_data = "{\n"
                            try: nazwy_zip= zip(pobrane_dane_z_bazy_escaped, dane_poziomu_2.get("kolumny_lista", []))
                            except: 
                                nazwy_zip= []
                                export_data = None
                            for data, name_kol in nazwy_zip:
                                if isinstance(data, str):
                                    export_data += f'"{name_kol}": "{data}",\n'
                                else:
                                    export_data += f'"{name_kol}": {data},\n'
                            if export_data!="{\n":
                                export_data = export_data[:-2]
                                export_data += "\n}\n"
                                dane_users_dict[user]["2"]["szablon"] = export_data
                            del export_data

                        if current_procedure_name == "WYSYLANIE_EMAILI":
                            export_data = '''{\n"WYBRANE": ['''
                            for email in dane_poziomu_2.get("wybrane_emails", []):
                                if str(email).count("@") == 1 and str(email).count("."):
                                    export_data += f'"{email}", '
                            if export_data != '''{\n"WYBRANE": [''':
                                export_data = export_data[:-2]  # Usunięcie ostatniego przecinka i spacji
                                export_data += "],\n"
                            else:
                                return jsonify({"success": False, "error": f"Błąd poziomu {ostatni_level} dla {current_procedure_name}"}), 400

                            # Dodawanie kolejnych elementów
                            export_data += '''"TYTUL": "",\n'''
                            export_data += '''"WIADOMOSC": ""\n'''
                            export_data += "}\n"

                            dane_users_dict[user]["2"]["szablon"] = export_data

                        if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                        raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"
                """
                    POZIOM 2                            POZIOM 2                            POZIOM 2
                """
                if ostatni_level == "2":
                    ostatni_level_int = int(ostatni_level)
                    vanles_changes = []
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM"\
                        or current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                        kolumny_lista = []
                        kolumny_generator = ""
                        values_list = []
                        for label, changes in validator_dict.get("rozne_wartosci", {}).items():
                            # print(label)
                            if label[1:] in dane_users_dict.get(user, {}).get(f"2", {}).get("dane", {}).get("kolumny_lista", []):
                                preared_data = (label[1:], resumeJson_structure(changes))
                                vanles_changes.append(preared_data)
                                kolumny_lista.append(label[1:])
                                kolumny_generator += f"{label[1:]}=%s, "
                                values_list.append(resumeJson_structure(changes))
                        if kolumny_generator!="": kolumny_generator = kolumny_generator[:-2]

                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        title_message = ""
                        content_message = ""

                        for label, changes in validator_dict.get("rozne_wartosci", {}).items():
                            if label[1:] == "TYTUL":
                                title_message = changes
                            if label[1:] == "WIADOMOSC":
                                content_message = changes

                    ustaw_dane_poziomu_3 = {}
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":
                        if vanles_changes:
                            tabela = "OfertyNajmu"
                            zapyanie = f"UPDATE {tabela} SET"
                            warunki = "WHERE id = %s"
                            wybrane_id = dane_users_dict.get(user, {}).get(f"{ostatni_level}", {}).get("dane", {}).get("wybrane_id", None)
                            wartosci = tuple(values_list + [wybrane_id])

                            prompt_level_3 = get_prompt_by_level_task(3, current_procedure_name)
                            ustaw_dane_poziomu_3 = {
                                "procedura": current_procedure_name,
                                "tabela": tabela,
                                "zapyanie": zapyanie,
                                "kolumny_lista": kolumny_lista,
                                "kolumny": kolumny_generator,
                                "warunki": warunki,
                                "wybrane_id": wybrane_id,
                                "wartosci": wartosci,
                                "aktualizacja": vanles_changes,
                                "prompt": prompt_level_3,
                                "zapytanie_sql": f"""
                                    {zapyanie}
                                    {kolumny_generator}
                                    {warunki};
                                            """

                            }
                                            
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                        if vanles_changes:
                            tabela = "OfertySprzedazy"
                            zapyanie = f"UPDATE {tabela} SET"
                            warunki = "WHERE id = %s"
                            wybrane_id = dane_users_dict.get(user, {}).get(f"{ostatni_level}", {}).get("dane", {}).get("wybrane_id", None)
                            wartosci = tuple(values_list + [wybrane_id])

                            prompt_level_3 = get_prompt_by_level_task(3, current_procedure_name)
                            ustaw_dane_poziomu_3 = {
                                "procedura": current_procedure_name,
                                "tabela": tabela,
                                "zapyanie": zapyanie,
                                "kolumny_lista": kolumny_lista,
                                "kolumny": kolumny_generator,
                                "warunki": warunki,
                                "wybrane_id": wybrane_id,
                                "wartosci": wartosci,
                                "aktualizacja": vanles_changes,
                                "prompt": prompt_level_3,
                                "zapytanie_sql": f"""
                                    {zapyanie}
                                    {kolumny_generator}
                                    {warunki};
                                            """

                            }

                    # ############################################################################
                    # WYSYLANIE_EMAILI
                    # ############################################################################
                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        if title_message!="" and content_message!="":
                            prompt_level_3 = get_prompt_by_level_task(3, current_procedure_name)
                            ustaw_dane_poziomu_3 = {
                                "procedura": current_procedure_name,
                                "prompt": prompt_level_3,
                                "email_list": dane_users_dict.get(user, {}).get(f"{ostatni_level}", {}).get("dane", {}).get("wybrane_emails", []),
                                "title": title_message,
                                "content": content_message
                            }

                    if ustaw_dane_poziomu_3:
                        dane_users_dict = template_managment(dane_users_dict, user, f"3", ustaw_dane_poziomu_3)

                    # print("ustaw_dane_poziomu_3", ustaw_dane_poziomu_3)

                    dane_users_dict[user]["2"]["wybor"] = dict_to_json_string(user_json)["json_string"]

                    if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                        dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                    raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"
                """
                    POZIOM 3                            POZIOM 3                            POZIOM 3
                """
                if ostatni_level == "3":
                    raport_data = None
                    for label, changes in validator_dict.get("rozne_wartosci", {}).items():
                        if label[1:] == "raport" and changes != "":
                            raport_data = changes
                    if raport_data:
                        dane_poziomu_3 = dane_users_dict.get(user, {}).get(f"3", {}).get("dane", {})
                        dane_poziomu_3["raport"] = raport_data

                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ . . . NA_WYNAJEM
                    # to jest kluczowa flaga uruchamiająca procedurę realizacji
                    # ustawienie flagi dyrektywy update_db
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM"\
                        or current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
                        dane_poziomu_3["dyrektywa_wykonawcza"] = "update_db"
                        dane_users_dict = template_managment(dane_users_dict, user, f"3", dane_poziomu_3)

                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        dane_poziomu_3["dyrektywa_wykonawcza"] = "run_function"
                        dane_users_dict = template_managment(dane_users_dict, user, f"3", dane_poziomu_3)

                    dane_users_dict[user]["3"]["wybor"] = dict_to_json_string(user_json)["json_string"]

                    if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):                
                        dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                    raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"
            else:
                # Brak różnic w wartościach
                raport_koncowy += f"Nie przetworzono poziomu {ostatni_level} dla {current_procedure_name}. "
                raport_koncowy += "Brak wykrytych różnic w danych (rozne_wartosci jest puste).\n"
        else:
            # Warunki nie zostały spełnione
            raport_koncowy += f"Przetwarzanie poziomu {ostatni_level} dla {current_procedure_name} nie powiodło się. "
            raport_koncowy += f"Warunki wejścia nie zostały spełnione:\n"
            raport_koncowy += f"zgodnosc_struktury: {validator_dict.get('zgodnosc_struktury')}, "
            raport_koncowy += f"error: {validator_dict.get('error')}, "
            raport_koncowy += f"success: {validator_dict.get('success')}, "
            raport_koncowy += f"anuluj_zadanie: {validator_dict.get('anuluj_zadanie')}\n"
        # ###########################################################################
        #                                                                           #
        #                               Anuluj Zadanie                              #
        #                                                                           #
        # ###########################################################################

        if user_json and validator_dict.get("anuluj_zadanie") and ostatni_level_int:
            raport_cancel = ""
            if "wybor" in dane_users_dict[user][f"{ostatni_level_int -1}"]:
                raport_cancel +=f'usunięto: wybor dla poziomu: {ostatni_level_int -1}\n'
                del dane_users_dict[user][f"{ostatni_level_int -1}"]["wybor"]
            
            if "wybor" in dane_users_dict[user][f"{ostatni_level_int}"]:
                raport_cancel +=f'usunięto: wybor dla poziomu: {ostatni_level_int}\n'
                del dane_users_dict[user][f"{ostatni_level_int}"]["wybor"]
            for lvels_up in range(ostatni_level_int-1, 4):
                if lvels_up == 0:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    if dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("poczekalnia_0", False):
                        del dane_users_dict[user][f"{lvels_up}"]["dane"]["poczekalnia_0"]
                    if dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("procedura", False):
                        del dane_users_dict[user][f"{lvels_up}"]["dane"]["procedura"]
                    
                else:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    prompt_existing = dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("prompt", "")
                    procedure_existing = dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("procedura", "")
                    if prompt_existing and procedure_existing:
                        dane_users_dict[user][f"{lvels_up}"]["dane"] = {"prompt": prompt_existing, "procedura": procedure_existing}
                    else:
                        dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            return jsonify({"success": True, "anuluj_zadanie": raport_cancel}), 200

        # ###########################################################################
        #                                                                           #
        #                       Zakończ tryb Decyzyjny                              #
        #                                                                           #
        # ###########################################################################
        elif user_json and validator_dict.get("anuluj_zadanie") and ostatni_level_int == 0:
            
            del dane_users_dict[user]

            if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            return jsonify({"success": True, "zakoncz": "Moduł decyzyjny został poprawnie zakończony, wszystkie decyzje zostały anulowane."}), 200


        # ###########################################################################
        #                                                                           #
        #   SĄ Różnice w kluczach  (Brak elementu na pozycji)   To nie ten json!    #
        #                                                                           #
        # ###########################################################################

        if user_json and not validator_dict.get("zgodnosc_struktury")\
            and validator_dict.get("error", "").startswith("Brak elementu na pozycji") and not validator_dict.get("success"):
            # print("zgodnosc_struktury")
            raport_zgodnosc = validator_dict.get("error")
            return jsonify({"success": False, "raport_zgodnosc": f"Brak elementu na pozycji. To nie ten json! {raport_zgodnosc}"}), 200

    # ###########################################################################
    #                                                                           #
    #   LEVEL 3 - LEVEL WYKONAWCZY, musi istnieć dyrektywa_wykonawcza           #
    #                                                                           #
    # ###########################################################################
    """
        POZIOM 3                            POZIOM 3                            POZIOM 3
    """
    if ostatni_level == "3" and dane_users_dict.get(user, {}).get(f"{ostatni_level_int}", {}).get("wybor", "")\
        and dane_users_dict.get(user, {}).get(f"{ostatni_level_int}", {}).get("dane", {}).get("dyrektywa_wykonawcza", None):
        dane_do_realizacji = dane_users_dict.get(user, {}).get(f"{ostatni_level}", {}).get("dane", {})
        dyrektywa_wykonawcza = dane_do_realizacji.get("dyrektywa_wykonawcza", None)

        raport_cancel = ""
        # ############################################################################
        # dyrektywa_wykonawcza update_db zapytanie_sql wartosci raport
        # ############################################################################
        if dyrektywa_wykonawcza == "update_db":
        # Realizacja zadania
            
            # główna aktualizacja
            zapyanie_sql = dane_do_realizacji.get("zapytanie_sql", "")
            values = dane_do_realizacji.get("wartosci", "")

            if not msq.insert_to_database(zapyanie_sql, values):
                raport_cancel += "Błąd podczas aktualizacji bazy danych.\n"

        
        # ############################################################################
        # dyrektywa_wykonawcza run_function ... .... raport
        # ############################################################################
        if dyrektywa_wykonawcza == "run_function":
            # Realizacja zadania
            if current_procedure_name == "WYSYLANIE_EMAILI":
                email_list = dane_do_realizacji.get("email_list", [])
                title = dane_do_realizacji.get("title", "")
                content = dane_do_realizacji.get("content", "")
                if send_emails(user, email_list, title, content):
                    raport_cancel += "Wysłano wiadomości według planu!\n"
            
        # dodanie raportu
        raport = dane_do_realizacji.get("raport", "")
        current_procedure_name = dane_do_realizacji.get("procedura", "")
        # Zapytanie SQL do wstawienia raportu
        zapytanie_sql_raport = """
            INSERT INTO mind_forge_register (user_name, procedure_name, raport)
            VALUES (%s, %s, %s)
        """

        # Przygotowanie wartości do zapytania
        values_raport = (user, current_procedure_name, raport)

        # Wstawienie danych do bazy
        if not msq.insert_to_database(zapytanie_sql_raport, values_raport):
            raport_cancel += "Błąd podczas zapisu raportu do bazy danych.\n"

        # procedury przygotowania do kolejnych zadań
        dane_poziomu_0 = dane_users_dict.get(user, {}).get(f"0", {}).get("dane", {})
        dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})

        if dane_poziomu_1.get("poczekalnia_1", []):
            # ############################################################################
            # WYSTARTUJ NASTĘPNY WYBÓR Z LISTY ("poczekalnia_1", []) poziomu 1
            # ############################################################################

            # Pobrać wybór z poziomu 1
            wybor_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("wybor", "")
            # pobrać procedurę z dane_poziomu_1.get("wybrano", None) 
            poziom_1_procedury = dane_poziomu_1.get("wybrano", "")
            if wybor_1 and poziom_1_procedury and poziom_1_procedury in wybor_1:
                # pobrać wybór z poziomu 1 i ustawić false przy "wybrano" poziomu 1
                stara_pozycja_w_wybor_poziom_1 = f'"{poziom_1_procedury}": true'
                nowa_pozycja_w_wybor_poziom_1 = f'"{poziom_1_procedury}": false'
                # ustawić jako user_aswer wyedytowany szablon z odznaczonym zrealizowanym wyborem
                gotowy_wybor_poziom_1 = str(wybor_1).replace(stara_pozycja_w_wybor_poziom_1, nowa_pozycja_w_wybor_poziom_1)
            
            # usunąć niepotrzebne dane i wybory z poziomów 3, 2 oraz wybór z poziomu 1
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2\n'
            del dane_users_dict[user][f"2"]["szablon"]
            raport_cancel +=f'Wykasowano wybór dla poziomu: 1\n'
            del dane_users_dict[user][f"1"]["wybor"]
            for lvels_up in range(2, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    raport_cancel +=f'Wykasowano wybór dla poziomu: {lvels_up}\n'
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}
            
            
            if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            payload_1 = {
                "primary_key": gotowy_wybor_poziom_1,
                "user": user,
                "api_key": api_key,
                "api_url": api_url
            }
            # przekazać do realizacji string json tak aby procedura zaczęła się od poziomu 1 dla kolejnego wyboru z listy poczekalnia_1
            try:
                response = requests.post(api_url, json=payload_1, timeout=10)
                response.raise_for_status()  # Upewnia się, że nie ma błędów
            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500

            return jsonify({"success": True, "procedura_zakonczona": f"System został ustawiony dla użytkownika {user} do realizacji zaplanowanych wyborów z poziomu 1. Zrealizowano {raport_cancel}."}), 200
        
        elif dane_poziomu_0.get("poczekalnia_0", []):
            # ############################################################################
            # WYSTARTUJ NASTĘPNY WYBÓR Z LISTY ("poczekalnia_0", [])
            # ############################################################################

            # Pobrać wybór z poziomu 0
            wybor_0 = dane_users_dict.get(user, {}).get(f"0", {}).get("wybor", "")
            # pobrać procedurę z dane_poziomu_0.get("procedura", None) 
            poziom_0_procedura = dane_poziomu_1.get("procedura", "")
            # pobrać wybór z poziomu 0 i ustawić false przy procedurze poziomu 0
            if wybor_0 and poziom_0_procedura and poziom_0_procedura in wybor_0:
                # pobrać wybór z poziomu 1 i ustawić false przy "wybrano" poziomu 1
                stara_pozycja_w_procedury_poziom_0 = f'"{poziom_0_procedura}": true'
                nowa_pozycja_w_procedury_poziom_0 = f'"{poziom_0_procedura}": false'
                # ustawić jako user_aswer wyedytowany szablon z odznaczonym zrealizowanym wyborem
                gotowy_wybor_poziom_0 = str(wybor_0).replace(stara_pozycja_w_procedury_poziom_0, nowa_pozycja_w_procedury_poziom_0)
            # usunąć niepotrzebne dane i wybory z poziomów 3, 2, 1 oraz wybór z poziomu 0
            raport_cancel +=f'Wykasowano szablon dla poziomu: 1\n'
            del dane_users_dict[user][f"1"]["szablon"]
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2\n'
            del dane_users_dict[user][f"2"]["szablon"]
            raport_cancel +=f'Wykasowano wybór dla poziomu: 0\n'
            del dane_users_dict[user][f"0"]["wybor"]
            for lvels_up in range(1, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    raport_cancel +=f'Wykasowano wybór dla poziomu: {lvels_up}\n'
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            # przekazać do realizacji string json tak aby procedura zaczęła się od poziomu 0 dla kolejnej procedury z listy poczekalnia_0
            payload_0 = {
                "primary_key": gotowy_wybor_poziom_0,
                "user": user,
                "api_key": api_key,
                "api_url": api_url
            }
            try:
                response = requests.post(api_url, json=payload_0, timeout=10)
                response.raise_for_status()  # Upewnia się, że nie ma błędów
            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500
            
            return jsonify({"success": True, "procedura_zakonczona": f"System został ustawiony dla użytkownika {user} do realizacji zaplanowanych procedur z poziomu 0. Zrealizowano {raport_cancel}."}), 200
        else:
            raport_cancel +=f'Wykasowano szablon dla poziomu: 1\n'
            del dane_users_dict[user][f"1"]["szablon"]
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2\n'
            del dane_users_dict[user][f"2"]["szablon"]
            for lvels_up in range(0, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]

                if lvels_up == 0:
                    raport_cancel += f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    del dane_users_dict[user][f"{lvels_up}"]["dane"]["procedura"]
                    
                else:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up}\n'
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            if saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict):
                dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
            return jsonify({"success": True, "procedura_zakonczona": f"System został wyzerowany dla użytkownika {user}, wszystkie zaplanowane procedury zostały zrealizowane. Zrealizowano {raport_cancel}."}), 200
    
    # Zwracamy odpowiedź w formacie JSON
    return jsonify({"success": True, "raport_koncowy": raport_koncowy}), 200

@app.route('/api/generated-socialsync-description/', methods=['POST'])
def generated_socialsync_description():

    # Pobieramy dane JSON z żądania
    data = request.get_json()
    # Sprawdzamy, czy dane zostały poprawnie przesłane
    if not data:
        return jsonify({"success": False, "error": "Brak danych"}), 400
    aswer = data.get("answer", None)
    id_zadania = data.get("id_zadania", None)
    api_key = data.get("api_key", None)

    if not aswer or not api_key or not id_zadania:
        return  jsonify({"success": False, "error": "Niewłaściwe dane zapytania!"}), 200
    
    if api_key and api_key not in allowed_API_KEYS:
        return  jsonify({"success": False, "error": "Unauthorized access"}), 401
    
    curent_tempalte = json_string_to_dict('{"tresc_ogloszenia": ""}').get('json', {})
    answer_json = json_string_to_dict(aswer).get('json', {'error': 'False'})
    validator_dict = validate_response_structure(curent_tempalte, answer_json)
    if not validator_dict.get("zgodnosc_struktury", False):
        return  jsonify({"success": False, "error": validator_dict.get("error", 'Błąd struktury json.')}), 200

    if validator_dict.get("rozne_wartosci", None) and not validator_dict.get("anuluj_zadanie", True)\
        and "tresc_ogloszenia" in answer_json and answer_json.get("tresc_ogloszenia"):
        action_taks = f'''
            UPDATE ogloszenia_socialsync
            SET tresc_ogloszenia=%s
            WHERE id_zadania = %s;
        '''
        values = (answer_json.get("tresc_ogloszenia"), id_zadania)
        if msq.insert_to_database(action_taks, values):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Błąd aktualizacji wygenerowanego opisu!"}), 404
        
if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
