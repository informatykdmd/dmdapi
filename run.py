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
    
def getMainResponder():
    task_data = {
        "create": [],
        "update": [],
        "delete": [],
        "hold": [],
        "resume": [],
        "promotion": []
    }

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
    print(api_key)
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
                print(taskID)
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
                    values = (0, 4, errorMessage, taskID)
                    
                if msq.insert_to_database(action_taks, values):
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
                

            return jsonify({"error": "Bad structure json file!"})
        return jsonify({"error": "Bad POST data!"})
        

    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Zwrot kodu 401 w przypadku braku autoryzacji
    


if __name__ == "__main__":
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4040)
