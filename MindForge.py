import json
import prompts


def validate_response_structure(template, response):
    """
    Sprawdza, czy struktura i typy danych w odpowiedzi są zgodne ze wzorem (template). 
    Funkcja zwraca szczegóły o zgodności struktury i różnicach w wartościach.

    Args:
        template (dict): Wzór JSON, do którego ma być porównywana odpowiedź.
        response (dict): Odpowiedź JSON, która ma być zweryfikowana względem wzoru.

    Returns:
        dict: Wynik zawierający:
            - 'zgodnosc_struktury' (bool): True, jeśli struktura jest zgodna, False w przeciwnym razie.
            - 'error' (str lub None): Informacja o błędzie, jeśli wystąpił, w przeciwnym razie None.
            - 'success' (bool): True, jeśli struktura i typy danych są zgodne, False w przeciwnym razie.
            - 'rozne_wartosci' (dict): Klucze i wartości z odpowiedzi, które różnią się od wzoru.
            - 'anuluj_zadanie' (bool): True, jeśli wszystkie dane są niezmienione, False w przeciwnym razie.
    """
    def check_structure_and_types(template, response, path=""):
        if isinstance(template, dict):
            if not isinstance(response, dict):
                return f"Klucz '{path}' powinien być typu dict, a jest typu {type(response).__name__}."
            for key, tmpl_value in template.items():
                if key not in response:
                    return f"Brak klucza '{path + '.' + key}' w odpowiedzi."
                error = check_structure_and_types(tmpl_value, response[key], path + "." + key)
                if error:
                    return error
        elif isinstance(template, list):
            if not isinstance(response, list):
                return f"Klucz '{path}' powinien być typu list, a jest typu {type(response).__name__}."
            if template:
                for idx, tmpl_value in enumerate(template):
                    if idx < len(response):
                        error = check_structure_and_types(tmpl_value, response[idx], f"{path}[{idx}]")
                        if error:
                            return error
                    else:
                        return f"Brak elementu na pozycji {idx} w odpowiedzi w ścieżce '{path}'."
        else:
            if type(template) != type(response):
                return f"Klucz '{path}' powinien być typu {type(template).__name__}, a jest typu {type(response).__name__}."
        return None

    def find_different_values(template, response, path=""):
        different_values = {}
        if isinstance(template, dict):
            for key, tmpl_value in template.items():
                if isinstance(tmpl_value, (dict, list)):
                    nested_diff = find_different_values(tmpl_value, response[key], path + "." + key)
                    if nested_diff:
                        different_values.update(nested_diff)
                else:
                    if response[key] != tmpl_value:
                        different_values[path + "." + key] = response[key]
        elif isinstance(template, list):
            for idx, tmpl_value in enumerate(template):
                if idx < len(response):
                    if isinstance(tmpl_value, (dict, list)):
                        nested_diff = find_different_values(tmpl_value, response[idx], f"{path}[{idx}]")
                        if nested_diff:
                            different_values.update(nested_diff)
                    else:
                        if response[idx] != tmpl_value:
                            different_values[f"{path}[{idx}]"] = response[idx]
        return different_values

    # 1. Sprawdź strukturę i typy danych
    structure_error = check_structure_and_types(template, response)
    if structure_error:
        return {
            "zgodnosc_struktury": False,
            "error": structure_error,
            "success": False,
            "rozne_wartosci": None,
            "anuluj_zadanie": False
        }

    # 2. Znajdź różnice w wartościach
    different_values = find_different_values(template, response)
    if different_values:
        return {
            "zgodnosc_struktury": True,
            "error": None,
            "success": False,
            "rozne_wartosci": different_values,
            "anuluj_zadanie": False
        }

    # 3. Jeśli wszystkie dane są identyczne, anuluj zadanie
    return {
        "zgodnosc_struktury": True,
        "error": None,
        "success": True,
        "rozne_wartosci": None,
        "anuluj_zadanie": True
    }

def resumeJson_structure(string_structure_with_roof):
    """Przywraca cudzysłowy w stringu, który zawiera strukturę JSON z ^ zamiast "."""
    
    def is_json_like_string(text):
        """
            Sprawdza, czy string wygląda na strukturę JSON z parzystą ilością ^, 
            zawiera kluczowe znaki JSON, ale nie ma cudzysłowów ".
        """
        json_chars = ['{', '[', ']', ':', '^']
        contains_json_structure = any(char in text for char in json_chars)
        even_caret_count = text.count('^') % 2 == 0
        no_double_quotes = '"' not in text  # Sprawdza, czy nie ma cudzysłowów
        
        # Zwraca True tylko, jeśli są kluczowe znaki, parzysta ilość ^ i brak "
        return contains_json_structure and even_caret_count and no_double_quotes

    # Sprawdzamy, czy string spełnia warunki i zamieniamy ^ na "
    if isinstance(string_structure_with_roof, str) and is_json_like_string(string_structure_with_roof):
        return string_structure_with_roof.replace("^", '"').replace('\n', ' ')
    
    return string_structure_with_roof

def template_managment(dane_userow, user, level, set_data):
    dane_userow[user][f"{level}"]["dane"] = set_data
    return dane_userow

def get_next_template(dane_usera):
    """Sprawdza, na którym poziomie użytkownik nie ma klucza 'wybor', i zwraca odpowiedni szablon."""
    for level in ["0", "1", "2", "3"]:
        if not dane_usera.get(level, {}).get("wybor"):
            return {"odpowiedz": dane_usera.get(level, {}).get("szablon", "{}"), "prompt": dane_usera.get(level, {}).get("dane", {}).get("prompt", None), "ostatni_level": level}
    return {"odpowiedz": "Proces ukończony", "ostatni_level": level}

def json_string_to_dict_old(response_text):
    """Parsuje strukturę JSON zawartą w tekście odpowiedzi SI."""
    
    json_str = ""
    brace_count = 0
    in_json = False
    json_blocks = []
    
    for char in str(response_text):
        if char == '{':
            in_json = True
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                in_json = False
                json_str += char
                json_blocks.append(json_str)
                json_str = ""
                continue
        if in_json:
            json_str += char

    if len(json_blocks) > 1:
        return {"error": "Więcej niż jedna struktura JSON.", "json": None, "success": False}
    elif not json_blocks:
        return {"error": "Brak struktury JSON w tekście.", "json": None, "success": False}

    try:
        parsed_json = json.loads(json_blocks[0])
        return {"error": None, "json": parsed_json, "success": True}
    except json.JSONDecodeError:
        return {"error": "Błąd parsowania JSON.", "json": None, "success": False}

def json_string_to_dict(response_text, return_type="json"):
    """Parsuje strukturę JSON zawartą w tekście odpowiedzi SI i zwraca pozostały tekst, jeśli istnieje."""
    
    json_str = ""
    remaining_text = ""
    brace_count = 0
    in_json = False
    json_blocks = []
    
    for char in str(response_text):
        if char == '{':
            in_json = True
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                in_json = False
                json_str += char
                json_blocks.append(json_str)
                json_str = ""
                continue
        if in_json:
            json_str += char
        elif not in_json and brace_count == 0:
            remaining_text += char  # Zapisuje tekst poza blokiem JSON
    
    if len(json_blocks) > 1:
        return {"error": "Więcej niż jedna struktura JSON.", "json": None, "remaining_text": remaining_text.strip(), "success": False}
    elif not json_blocks:
        return {"error": "Brak struktury JSON w tekście.", "json": None, "remaining_text": remaining_text.strip(), "success": False}

    try:
        parsed_json = json.loads(json_blocks[0])
        if return_type == "json":
            return {"error": None, "json": parsed_json, "remaining_text": None, "success": True}
        elif return_type == "string":
            return {"error": None, "json": None, "remaining_text": remaining_text.strip(), "success": True}
    except json.JSONDecodeError:
        return {"error": "Błąd parsowania JSON.", "json": None, "remaining_text": remaining_text.strip(), "success": False}

def dict_to_json_string(data):
    """Konwertuje słownik Python na format JSON w postaci stringa."""
    try:
        # Używamy ensure_ascii=False, aby zachować polskie znaki
        json_string = json.dumps(data, ensure_ascii=False, indent=4)
        return {"success": True, "json_string": json_string}
    except TypeError as e:
        return {"success": False, "error": f"Błąd konwersji: {e}"}

def get_main_template():
    """Zwraca główny szablon JSON STRING."""
    """{\n"AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM": false,\n"AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ": false,\n"ZARZADZANIE_KAMPANIAMI_NIERUCHOMOSCI": false,\n"KAMPANIE_FB": false,\n"ZARZADZANIE_SEKCJA_KARIERA": false,\n"KAMPANIE_ANONIMOWE_FB": false,\n"WYSYLANIE_EMAILI": false,\n"ZARZADZANIE_PRACOWNIKAMI": false,\n"ZARZADZANIE_BLOGIEM": false\n}\n"""
    mainTemplate = """{\n"AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM": false,\n"AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ": false,\n"WYSYLANIE_EMAILI": false\n}\n"""
    return mainTemplate

def get_prompt_by_level_task(level: int, task=None):
    this_prompt = "Odpowiedz Jsonem!"
    if level == 0 and task==None:
        this_prompt = prompts.MAIN_MENU_level_0
    elif level == 1 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_1
    elif level == 2 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_2
    elif level == 3 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_3

    elif level == 1 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_1
    elif level == 2 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_2
    elif level == 3 and task=="AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ":
        this_prompt = prompts.AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_3
    
    elif level == 1 and task=="WYSYLANIE_EMAILI":
        this_prompt = prompts.WYSYLANIE_EMAILI_level_1
    elif level == 2 and task=="WYSYLANIE_EMAILI":
        this_prompt = prompts.WYSYLANIE_EMAILI_level_2
    elif level == 3 and task=="WYSYLANIE_EMAILI":
        this_prompt = prompts.WYSYLANIE_EMAILI_level_3

    return this_prompt

def addNewUser(dane_users_dict, user_name: str, prompt_level_0=None):
    """Dodaje nowego użytkownika do bazy danych."""
    # dane_users_dict = saver_ver.open_ver("MINDFORGE", "dane_users_dict")

    if prompt_level_0 is None:
        prompt_level_0 = "Wybierz potrzebne narzędzia, odsyłając obiekt JSON, aktualizując wartość true przy wybranych opcjach.\nJeśli odeślesz niezmieniony obiekt, model decyzyjny zostanie dezaktywowany.\nPamiętaj, że rozumiem tylko język JSON, odpowiadaj tylko jsonem komunikując się zemną! Zastosuj się do moich instrukcji i odeślij zaktualizowany obiekt json!\n"

    if user_name not in dane_users_dict:
        dane_users_dict[user_name] = {
            "0":{
                "dane":{"prompt": prompt_level_0},
                "szablon": get_main_template(),
            },
            "1":{
                "szablon": None,
            },
            "2":{
                "szablon": None,
            },
            "3":{
                "szablon": """{\n"raport": ""\n}"""
            }
        }
    
    # return saver_ver.save_ver("MINDFORGE", "dane_users_dict", dane_users_dict)
    return dane_users_dict