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
            resumeJson_structure
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


def send_emails(procedur, emails, title_mess, content_mess):
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
                        # add_aifaLog(f'Emisja kampanii o id:{taskID}, zakończona sukcesem.')
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
                        # add_aifaLog(f'Dodawanie nowego ogłoszenia o id:{taskID} na Lento.pl, zakończone sukcesem.')
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

                if action_taks and values:
                    if msq.insert_to_database(action_taks, values):
                        # add_aifaLog(f'Uwaga! Zaleziono błędy {errorMessage}, o fladze: {message_flag} dla idZadania: {taskID}.')
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
        saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
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
        saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
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

        if user_process_response['error'] is not None:
            return jsonify({"success": False, "error": user_process_response["error"]}), 200
        user_json = user_process_response['json']

        validator_dict = validate_response_structure(curent_tempalte, user_json)

        if user_json and validator_dict.get("zgodnosc_struktury")\
            and not validator_dict.get("error") and not validator_dict.get("success")\
                and not validator_dict.get("anuluj_zadanie"):
            if validator_dict.get("rozne_wartosci"):
                """
                    POZIOM 0                            POZIOM 0                            POZIOM 0
                """
                if ostatni_level == "0":
                    picket_procedures = [label[1:] for label in validator_dict.get("rozne_wartosci", {}).keys()]
                    current_procedure_name = picket_procedures[0] if picket_procedures else None
                    prompt_level_0 = "Wybierz potrzebne narzędzia, aktualizując wartość true przy wybranych opcjach.\nJeśli odeślesz niezmieniony obiekt, model decyzyjny zostanie dezaktywowany."
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
                        warunki = ""
                        wartosci = ()
                        prompt_level_1 = "Wybierz ogłoszenie, aktualizując wartość true przy wybranej opcji.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

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
                        warunki = ""
                        wartosci = ()
                        prompt_level_1 = "Wybierz ogłoszenie, aktualizując wartość true przy wybranej opcji.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

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
                        prompt_level_1 = "Wybierz osoby do których chcesz napisać wiadomość email, aktualizując wartość true przy wybranej osobie.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

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

                    saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
                    dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")

                    dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})
                    # print(dane_poziomu)
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
                                export_data += export_data[:-2] + "\n}\n"
                                dane_users_dict[user]["1"]["szablon"] = export_data

                    dane_users_dict[user]["0"]["wybor"] = dict_to_json_string(user_json)["json_string"]
                    saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
                    dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                    raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"

                """
                    POZIOM 1                            POZIOM 1                            POZIOM 1
                """
                if ostatni_level == "1":
                    picket_choice = [label[1:] for label in validator_dict.get("rozne_wartosci", {}).keys()]
                    current_choice = picket_choice[0] if picket_choice else None

                    # splituje id z wybranej pozycji 
                    def split_id_current_choice(current_choice_string: str):
                        if current_choice_string and current_choice_string.startswith("["):
                            splited_id = int(current_choice_string.split("]::")[0][1:])
                        return splited_id

                    def split_emails_picket_choice(picket_choice_list: list):
                        emails_list = []
                        for current_choice_string in picket_choice_list:
                            if current_choice_string and str(current_choice_string).startswith("["):
                                email_adr = str(current_choice_string.split("]::")[3][1:])
                                emails_list.append(email_adr)
                        return emails_list
                    
                    ustaw_dane_poziom_2 = {}
                    ustaw_dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})
                    # ############################################################################
                    # AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM
                    # ############################################################################
                    if current_procedure_name == "AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":

                        tabela = "OfertyNajmu"
                        zapyanie = "SELECT"
                        kolumny_lista = [
                                            "Opis",
                                            "Cena",
                                            "Kaucja",
                                            "Lokalizacja",
                                            "LiczbaPokoi",
                                            "Metraz",
                                            "RodzajZabudowy",
                                            "Czynsz",
                                            "Umeblowanie",
                                            "LiczbaPieter",
                                            "PowierzchniaDzialki",
                                            "TechBudowy",
                                            "FormaKuchni",
                                            "TypDomu",
                                            "StanWykonczenia",
                                            "RokBudowy",
                                            "NumerKW",
                                            "InformacjeDodatkowe",
                                            "TelefonKontaktowy",
                                            "EmailKontaktowy",
                                            "StatusOferty",
                            ]
                        
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = "WHERE id = %s"
                        wybrane_id = split_id_current_choice(current_choice)
                        wartosci = (wybrane_id,)
                        prompt_level_2 = "Przejrzyj szczegóły oferty i dokonaj niezbędnych zmian, aktualizując wartości odpowiednich parametrów. Jeżeli w treści są karaty (^) użyj ich ponieważ są to znaczniki stylowania zastępujące cudzysłowy więc zachowaj obecną strukturę. To ważne!\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

                        ustaw_dane_poziom_2 = {
                            "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
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
                                    "TypNieruchomosci",
                                    "Tytul",
                                    "Rodzaj",
                                    "Opis",
                                    "Cena",
                                    "Lokalizacja",
                                    "LiczbaPokoi",
                                    "Metraz",
                                    'RodzajZabudowy',
                                    'Rynek',
                                    'LiczbaPieter',
                                    'PrzeznaczenieLokalu',
                                    'Poziom',
                                    'TechBudowy',
                                    'FormaKuchni',
                                    'TypDomu',
                                    'StanWykonczenia',
                                    'RokBudowy',
                                    'NumerKW',
                                    'InformacjeDodatkowe',
                                    'TelefonKontaktowy',
                                    'EmailKontaktowy',
                                    'StatusOferty'
                            ]
                        
                        kolumny = generatorKolumn(kolumny_lista)
                        warunki = "WHERE id = %s"
                        wybrane_id = split_id_current_choice(current_choice)
                        wartosci = (wybrane_id,)
                        prompt_level_2 = "Przejrzyj szczegóły oferty i dokonaj niezbędnych zmian, aktualizując wartości odpowiednich parametrów. Jeżeli w treści są karaty (^) użyj ich ponieważ są to znaczniki stylowania zastępujące cudzysłowy więc zachowaj obecną strukturę. To ważne!\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

                        ustaw_dane_poziom_2 = {
                            "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
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
                        
                        wybrane_emails = split_emails_picket_choice(picket_choice) # lista emaili
                        prompt_level_2 = "Sprawdź wybrane emaile i uzupełnij tytuł i treści wiadomości, aktualizując wartości przy danym kluczu.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej."

                        ustaw_dane_poziom_2 = {
                            "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
                            "wybrane_emails": wybrane_emails,
                            "prompt": prompt_level_2
                        }
                    
                    if ustaw_dane_poziomu_1:
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

                    saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
                    dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

                    dane_poziomu_2 = dane_users_dict.get(user, {}).get(f"2", {}).get("dane", {})
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
                                poz.replace('^', "").replace('"', "^") if isinstance(poz, str) and is_json_like_string(poz) else poz 
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
                                    export_data += f'"{email}",\n'
                            if export_data!='''{\n"WYBRANE": [''':
                                export_data = export_data[:-2]
                                export_data += "],\n"
                            else: return jsonify({"success": False, "error": f"Błąd poziomu {ostatni_level} dla {current_procedure_name}"}), 400
                            export_data = '''"TYTUL": "",\n'''
                            export_data = '''"WIADOMOSC": "",\n'''
                            export_data = export_data[:-2]
                            export_data += "\n}\n"
                            dane_users_dict[user]["2"]["szablon"] = export_data

                        saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
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
                        kolumny_generator = "("
                        values_list = []
                        for label, changes in validator_dict.get("rozne_wartosci", {}).items():
                            # print(label)
                            if label[1:] in dane_users_dict.get(user, {}).get(f"2", {}).get("dane", {}).get("kolumny_lista", []):
                                preared_data = (label[1:], resumeJson_structure(changes))
                                vanles_changes.append(preared_data)
                                kolumny_lista.append(label[1:])
                                kolumny_generator += f"{label[1:]}=%s, "
                                values_list.append(resumeJson_structure(changes))
                        if kolumny_generator!="(": kolumny_generator = kolumny_generator[:-2] + ")"

                    if current_procedure_name == "WYSYLANIE_EMAILI":
                        final_email_list = []
                        title_message = ""
                        content_message = ""

                        for label, changes in validator_dict.get("rozne_wartosci", {}).items():
                            # print(label)
                            if label[1:] == "WYBRANE":
                                final_email_list = changes
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
                            wybrane_id = dane_users_dict[user][f"{ostatni_level}"]["dane"]["wybrane_id"]
                            wartosci = tuple(values_list + [wybrane_id])

                            prompt_level_3 = "Zmiany zostaną wprowadzone po wysłaniu raportu. Wypełnij pole raportu, aby zakończyć proces aktualizacji.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej a zmiany nie zostaną wprowadzone."
                            ustaw_dane_poziomu_3 = {
                                "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
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
                            wybrane_id = dane_users_dict[user][f"{ostatni_level}"]["dane"]["wybrane_id"]
                            wartosci = tuple(values_list + [wybrane_id])

                            prompt_level_3 = "Zmiany zostaną wprowadzone po wysłaniu raportu. Wypełnij pole raportu, aby zakończyć proces aktualizacji.\nJeśli odeślesz niezmieniony obiekt, wrócisz do poprzedniej opcji decyzyjnej a zmiany nie zostaną wprowadzone."
                            ustaw_dane_poziomu_3 = {
                                "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
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
                            ustaw_dane_poziomu_3 = {
                                "procedura": dane_users_dict[user][f"{ostatni_level}"]["dane"]["procedura"],
                                "email_list": final_email_list,
                                "title": title_message,
                                "content": content_message
                            }

                    if ustaw_dane_poziomu_3:
                        dane_users_dict = template_managment(dane_users_dict, user, f"3", ustaw_dane_poziomu_3)

                    dane_users_dict[user]["2"]["wybor"] = dict_to_json_string(user_json)["json_string"]
                    saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
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

                    saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
                    dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
                    raport_koncowy += f"Udane przetworzenie poziomu {ostatni_level} dla {current_procedure_name}"

        # ###########################################################################
        #                                                                           #
        #                               Anuluj Zadanie                              #
        #                                                                           #
        # ###########################################################################

        if user_json and validator_dict.get("anuluj_zadanie") and ostatni_level_int:
            # print("anuluj_zadanie")
            raport_cancel = ""
            if "wybor" in dane_users_dict[user][f"{ostatni_level_int -1}"]:
                raport_cancel +=f'usunięto: wybor dla poziomu: {ostatni_level_int -1} | '
                del dane_users_dict[user][f"{ostatni_level_int -1}"]["wybor"]
            
            if "wybor" in dane_users_dict[user][f"{ostatni_level_int}"]:
                raport_cancel +=f'usunięto: wybor dla poziomu: {ostatni_level_int} | '
                del dane_users_dict[user][f"{ostatni_level_int}"]["wybor"]
            for lvels_up in range(ostatni_level_int -1, 4):
                if lvels_up == 0:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    if dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("poczekalnia_0", True):
                        del dane_users_dict[user][f"{lvels_up}"]["dane"]["poczekalnia_0"]
                    if dane_users_dict.get(user, {}).get(f"{lvels_up}", {}).get("dane", {}).get("procedura", True):
                        del dane_users_dict[user][f"{lvels_up}"]["dane"]["procedura"]
                    
                else:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            return jsonify({"success": True, "anuluj_zadanie": raport_cancel}), 200

        # ###########################################################################
        #                                                                           #
        #                       Zakończ tryb Decyzyjny                              #
        #                                                                           #
        # ###########################################################################
        elif user_json and validator_dict.get("anuluj_zadanie") and ostatni_level_int == 0:
            
            del dane_users_dict[user]

            saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            return jsonify({"success": True, "zakoncz": "Moduł decyzyjny został porawnie zakończony, wszystkie decyzje zostały anulowane."}), 200


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



        # import pprint
        # pprint.pprint(dane_users_dict[user])
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

        # ############################################################################
        # dyrektywa_wykonawcza update_db zapytanie_sql wartosci raport
        # ############################################################################
        if dyrektywa_wykonawcza == "update_db":
        # Realizacja zadania
            
            # główna aktualizacja
            zapyanie_sql = dane_do_realizacji.get("zapytanie_sql", "")
            values = dane_do_realizacji.get("wartosci", "")

            msq.insert_to_database(zapyanie_sql, values)

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
            msq.insert_to_database(zapytanie_sql_raport, values_raport)
        
        # ############################################################################
        # dyrektywa_wykonawcza run_function ... .... raport
        # ############################################################################
        if dyrektywa_wykonawcza == "run_function":
            # Realizacja zadania
            if current_procedure_name == "WYSYLANIE_EMAILI":
                procedura = dane_do_realizacji.get("procedura")
                email_list = dane_do_realizacji.get("email_list", [])
                title = dane_do_realizacji.get("title", "")
                content = dane_do_realizacji.get("content", "")
                send_emails(procedura, email_list, title, content)
            
        # procedury przygotowania do kolejnych zadań
        dane_poziomu_0 = dane_users_dict.get(user, {}).get(f"0", {}).get("dane", {})
        dane_poziomu_1 = dane_users_dict.get(user, {}).get(f"1", {}).get("dane", {})

        raport_cancel = ""
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
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2 | '
            del dane_users_dict[user][f"2"]["szablon"]
            raport_cancel +=f'Wykasowano wybór dla poziomu: 1 | '
            del dane_users_dict[user][f"1"]["wybor"]
            for lvels_up in range(2, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    raport_cancel +=f'Wykasowano wybór dla poziomu: {lvels_up} | '
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}
            
            
            saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            payload_1 = {
                "primary_key": gotowy_wybor_poziom_1,
                "user": user,
                "api_key": api_key,
                "api_url": api_url
            }
            # przekazać do realizacji string json tak aby procedura zaczęła się od poziomu 1 dla kolejnego wyboru z listy poczekalnia_1
            try:
                response = requests.post(api_url, json=payload_1)
                response.raise_for_status()  # Upewnia się, że nie ma błędów
            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500

            return jsonify({"success": True, "procedura_zakonczona": f"System został ustawiony dla użytkownika {user} do realizacji zaplanowanych wyborów z poziomu 1"}), 200
        
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
            raport_cancel +=f'Wykasowano szablon dla poziomu: 1 | '
            del dane_users_dict[user][f"1"]["szablon"]
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2 | '
            del dane_users_dict[user][f"2"]["szablon"]
            raport_cancel +=f'Wykasowano wybór dla poziomu: 0 | '
            del dane_users_dict[user][f"0"]["wybor"]
            for lvels_up in range(1, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    raport_cancel +=f'Wykasowano wybór dla poziomu: {lvels_up} | '
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")

            # przekazać do realizacji string json tak aby procedura zaczęła się od poziomu 0 dla kolejnej procedury z listy poczekalnia_0
            payload_0 = {
                "primary_key": gotowy_wybor_poziom_0,
                "user": user,
                "api_key": api_key,
                "api_url": api_url
            }
            try:
                response = requests.post(api_url, json=payload_0)
                response.raise_for_status()  # Upewnia się, że nie ma błędów
            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500
            
            return jsonify({"success": True, "procedura_zakonczona": f"System został ustawiony dla użytkownika {user} do realizacji zaplanowanych procedur z poziomu 0"}), 200
        else:
            raport_cancel +=f'Wykasowano szablon dla poziomu: 1 | '
            del dane_users_dict[user][f"1"]["szablon"]
            raport_cancel +=f'Wykasowano szablon dla poziomu: 2 | '
            del dane_users_dict[user][f"2"]["szablon"]
            for lvels_up in range(0, 4):
                if "wybor" in dane_users_dict[user][f"{lvels_up}"]:
                    del dane_users_dict[user][f"{lvels_up}"]["wybor"]

                if lvels_up == 0:
                    raport_cancel += f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    del dane_users_dict[user][f"{lvels_up}"]["dane"]["procedura"]
                    
                else:
                    raport_cancel +=f'wyzerowano: dane dla poziomu: {lvels_up} | '
                    dane_users_dict[user][f"{lvels_up}"]["dane"] = {}

            saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
            dane_users_dict =saver_ver.open_ver("MINDFORGE", "dane_users_dict")
            return jsonify({"success": True, "procedura_zakonczona": f"System został wyzerowany dla użytkownika {user}, wszystkie zaplanowane procedury zostały zrealizowane."}), 200
    
    # Zwracamy odpowiedź w formacie JSON
    return jsonify({"success": True, "raport_koncowy": raport_koncowy}), 200

if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
