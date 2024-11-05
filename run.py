from flask import Flask, jsonify, request
import json
import os
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
                        addDataLogs(f'MOnotoroeanie grup FB o id-cyklu:{taskID} przebiegło pomyślnie!', 'success')
                        return jsonify({"message": "Finished"})
                    else:
                        return jsonify({"error": 500})
                    
            elif action == 'error':
                taskID = request.headers.get('taskID')
                errorMessage = request.headers.get('error')
                message_flag = request.headers.get('message')
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

                elif message_flag == 'error-facebook':
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
                
                elif message_flag == 'error-adresowo':
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

                elif message_flag == 'error-allegro':
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

                elif message_flag == 'error-otodom':
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
                
                elif message_flag == 'error-chat':
                    action_taks = f'''
                        UPDATE chat_task
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)

                elif message_flag == 'error-system-logs':
                    action_taks = f'''
                        UPDATE system_logs_monitor
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)

                elif message_flag == 'error-fbmonitor':
                    action_taks = f'''
                        UPDATE fbgroups_stats_monitor
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 2, errorMessage, taskID)
                
                elif message_flag == 'error-career-fbgroups':
                    action_taks = f'''
                        UPDATE ogloszenia_fbgroups
                        SET 
                            active_task=%s,
                            status=%s,
                            errors=%s,
                        WHERE id_zadania = %s;
                    '''
                    values = (0, 4, errorMessage, taskID)


                if msq.insert_to_database(action_taks, values):
                    # add_aifaLog(f'Uwaga! Zaleziono błędy {errorMessage}, o fladze: {message_flag} dla idZadania: {taskID}.')
                    addDataLogs(f'Uwaga! Zaleziono błędy {errorMessage}, o fladze: {message_flag} dla idZadania: {taskID}.', 'danger')
                    return jsonify({"message": "The error description has been saved"})
                else:
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
    


if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
