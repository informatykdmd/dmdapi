MAIN_MENU_level_0 = """
Wybierz potrzebne narzędzia, aktualizując wartość `true` przy wybranych opcjach w przesyłanym obiekcie JSON.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz niezmieniony obiekt, model decyzyjny zostanie wyłączony.  
Komunikuj się wyłącznie w formacie JSON, odpowiadając dokładnie w wymaganej strukturze!  
Zastosuj się do instrukcji i odeślij poprawiony obiekt JSON!
"""

AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_1 = """
Wybierz ogłoszenie do aktualizacji, zmieniając wartość na `true` przy wybranej opcji.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz dokładnie ten sam obiekt (niezmieniony), proces zostanie anulowany i powrócisz do poprzedniego etapu lub menu.  
Komunikuj się wyłącznie w formacie JSON, odpowiadając zgodnie z wymaganiami!  
Prześlij poprawiony obiekt JSON zgodnie z instrukcjami!
"""
AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_2 = """
Przejrzyj szczegóły oferty i dokonaj niezbędnych zmian, aktualizując wartości odpowiednich parametrów.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz dokładnie ten sam obiekt (niezmieniony), anulujesz aktualne zadanie i wrócisz do poprzedniego etapu procesu lub menu.  
Pamiętaj, że rozumiem tylko język JSON, odpowiadaj wyłącznie jsonem, komunikując się ze mną!

Szczególna uwaga na pole 'Opis':
    - Pole 'Opis' to string w formacie pseudo-JSON, który zostanie przekształcony na poprawny obiekt JSON.  
    - Jego strukturę tworzy lista słowników zawierających pary klucz-wartość (np. [{^p^: ^wartość^}, {^strong^: ^wartość^}]).  
    - Możesz używać wyłącznie następujących kluczy:  
        ^p^, ^strong^, ^h1^, ^h2^, ^h3^, ^h1-strong^, ^h2-strong^, ^h3-strong^, ^li^.  

Zasady:
    1. Klucze i wartości muszą pozostać zgodne z wytycznymi — każde odstępstwo, takie jak brak wymaganych nawiasów, niepoprawne klucze czy znaki, spowoduje błąd walidacji.  
    2. Zachowaj strukturę listy — nawet gdy opis zawiera tylko jeden element (np. [{^p^: ^wartość^}]).  
    3. Zamień cudzysłowy (`"`) na karaty (`^`) w kluczach i wartościach pseudo jsona pola 'Opis', ponieważ pełnią one funkcję znaczników.  
    4. Nie używaj znaków ucieczki (`\\`) — format musi być dokładnie zgodny z szablonem.  

Przykłady poprawnej struktury pola 'Opis':
1. Pojedynczy element:
"Opis": "[{^p^: ^To jest przykładowy paragraf.^}]"

Zachowaj integralność struktury JSON, upewniając się, że nie ma niezgodności w formacie.  
Jeśli odeślesz niezmieniony obiekt, zadanie zostanie anulowane, a proces cofnie się do poprzedniego etapu.  
Komunikuj się wyłącznie w języku JSON, spełniając wymagania walidacyjne. Prześlij poprawiony obiekt JSON!
"""
AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_WYNAJEM_level_3 = """
Aby zakończyć proces aktualizacji, wypełnij pole raportu zgodnie z instrukcją.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Dopiero po przesłaniu poprawnie wypełnionego raportu zmiany zostaną wprowadzone.  
Jeśli odeślesz obiekt bez zmian, powrócisz do poprzedniego kroku decyzyjnego, a zmiany nie zostaną zapisane.  
Komunikuj się wyłącznie w formacie JSON i prześlij poprawiony obiekt zgodnie z wymaganiami!
"""


AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_1 = """
Wybierz ogłoszenie do aktualizacji, zmieniając wartość na `true` przy wybranej opcji.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz dokładnie ten sam obiekt (niezmieniony), proces zostanie anulowany i powrócisz do poprzedniego etapu lub menu.  
Komunikuj się wyłącznie w formacie JSON, odpowiadając zgodnie z wymaganiami!  
Prześlij poprawiony obiekt JSON zgodnie z instrukcjami!
"""
AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_2 = """
Przejrzyj szczegóły oferty i dokonaj niezbędnych zmian, aktualizując wartości odpowiednich parametrów.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz dokładnie ten sam obiekt (niezmieniony), anulujesz aktualne zadanie i wrócisz do poprzedniego etapu procesu lub menu.  
Pamiętaj, że rozumiem tylko język JSON, odpowiadaj wyłącznie jsonem, komunikując się ze mną!

Szczególna uwaga na pole 'Opis':
    - Pole 'Opis' to string w formacie pseudo-JSON, który zostanie przekształcony na poprawny obiekt JSON.  
    - Jego strukturę tworzy lista słowników zawierających pary klucz-wartość (np. [{^p^: ^wartość^}, {^strong^: ^wartość^}]).  
    - Możesz używać wyłącznie następujących kluczy:  
        ^p^, ^strong^, ^h1^, ^h2^, ^h3^, ^h1-strong^, ^h2-strong^, ^h3-strong^, ^li^.

Zasady:
    1. Klucze i wartości muszą pozostać zgodne z wytycznymi — każde odstępstwo, takie jak brak wymaganych nawiasów, niepoprawne klucze czy znaki, spowoduje błąd walidacji.  
    2. Zachowaj strukturę listy — nawet gdy opis zawiera tylko jeden element (np. [{^p^: ^wartość^}]).  
    3. Zamień cudzysłowy (`"`) na karaty (`^`) w kluczach i wartościach pseudo jsona pola 'Opis', ponieważ pełnią one funkcję znaczników.  
    4. Nie używaj znaków ucieczki (`\\`) — format musi być dokładnie zgodny z szablonem.  

Przykłady poprawnej struktury pola 'Opis':
1. Pojedynczy element:
    "Opis": "[{^p^: ^To jest przykładowy paragraf.^}]"

Zachowaj integralność struktury JSON, upewniając się, że nie ma niezgodności w formacie.  
Jeśli odeślesz niezmieniony obiekt, zadanie zostanie anulowane, a proces cofnie się do poprzedniego etapu.  
Komunikuj się wyłącznie w języku JSON, spełniając wymagania walidacyjne. Prześlij poprawiony obiekt JSON!
"""
AKTUALIZACJA_OGLOSZEN_NIERUCHOMOSCI_NA_SPRZEDAZ_level_3 = """
Aby zakończyć proces aktualizacji, wypełnij pole raportu zgodnie z instrukcją.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Dopiero po przesłaniu poprawnie wypełnionego raportu zmiany zostaną wprowadzone.  
Jeśli odeślesz obiekt bez zmian, powrócisz do poprzedniego kroku decyzyjnego, a zmiany nie zostaną zapisane.  
Komunikuj się wyłącznie w formacie JSON i prześlij poprawiony obiekt zgodnie z wymaganiami!
"""

WYSYLANIE_EMAILI_level_1 = """
Wybierz osoby, do których chcesz wysłać wiadomość email, aktualizując wartość na `true` przy wybranych osobach.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Jeśli odeślesz dokładnie ten sam obiekt (niezmieniony), proces zostanie anulowany i wrócisz do poprzedniego etapu lub menu.  
Komunikuj się wyłącznie w formacie JSON, odpowiadając zgodnie z wymaganiami!  
Prześlij poprawiony obiekt JSON zgodnie z instrukcjami!
"""
WYSYLANIE_EMAILI_level_2 = """
Sprawdź wybrane adresy email i uzupełnij brakujące dane, takie jak tytuł oraz treść wiadomości, edytując odpowiednie pola.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Zachowaj integralność struktury JSON, upewniając się, że format danych jest zgodny z wymaganiami.  
Jeśli odeślesz niezmieniony obiekt, proces zostanie anulowany, a zadanie cofnie się do poprzedniego kroku lub menu.  
Komunikuj się wyłącznie w języku JSON i prześlij poprawiony obiekt zgodnie z instrukcjami!

"""
WYSYLANIE_EMAILI_level_3 = """
Aby zakończyć proces wysyłania wiadomości, wypełnij pole raportu zgodnie z instrukcjami.  
Ilość kluczy i ich nazwy muszą zostać niezmienione — aktualizujesz wyłącznie wartości!  
Dopiero po przesłaniu poprawnie wypełnionego raportu wiadomości zostaną wysłane.  
Jeśli odeślesz obiekt bez zmian, wrócisz do poprzedniego kroku decyzyjnego, a wiadomości nie zostaną wysłane.  
Komunikuj się wyłącznie w formacie JSON i prześlij poprawiony obiekt zgodnie z wymaganiami!
"""