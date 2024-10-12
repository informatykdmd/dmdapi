### Raport zmiany: Przeniesienie wywołania funkcji `getMainResponder()` po weryfikacji klucza API

#### 1. **Opis zmiany:**
Zmiana polegała na przeniesieniu wywołania funkcji `getMainResponder()` **po weryfikacji** klucza API (`api_key`) w metodzie GET na głównym endpointcie (`/`). Wcześniej funkcja była wywoływana niezależnie od tego, czy użytkownik posiadał prawidłowy klucz API. Teraz funkcja ta jest wywoływana dopiero po pozytywnej weryfikacji autoryzacji, co zapobiega nieautoryzowanemu przetwarzaniu danych.

#### 2. **Zmodyfikowany kod:**
**Przed zmianą:**

```python
@app.route("/", methods=['GET'])
def index():
    data = getMainResponder()  # Funkcja wywoływana przed weryfikacją klucza API
    api_key = request.headers.get('api_key')
    if api_key and api_key in allowed_API_KEYS:
        if 'action' in request.headers:
            action = request.headers.get('action')
            if action == 'get_json':
                print(data)
                return jsonify(data)
    return jsonify({"error": "Unauthorized"}), 401
```

**Po zmianie:**

```python
@app.route("/", methods=['GET'])
def index():
    api_key = request.headers.get('api_key')  # Weryfikacja klucza API przed wywołaniem funkcji
    if api_key and api_key in allowed_API_KEYS:
        if 'action' in request.headers:
            action = request.headers.get('action')
            if action == 'get_json':
                return jsonify(getMainResponder())  # Funkcja wywoływana dopiero po weryfikacji
    return jsonify({"error": "Unauthorized"}), 401
```

#### 3. **Przyczyna zmiany:**

Problem wynikał z faktu, że funkcja `getMainResponder()` była wywoływana przed weryfikacją klucza API. **Był to krytyczny błąd**, który prowadził do niepożądanych efektów:
- **Zadania były modyfikowane** (np. zmiana `active_task` na 1) przez nieautoryzowane żądania, co powodowało, że te zadania nie były brane pod uwagę w kolejnych wywołaniach.
- **Dziwne i niezrozumiałe tracenie zadań**: Zadania były zmieniane, ale nie zwracane użytkownikowi, jeśli klucz API był niepoprawny.
- **Zmiany statusów bez rezultatów**: Flagi `active_task` były modyfikowane przez nieautoryzowane żądania, co powodowało, że zadania nie były już dostępne przy kolejnym wywołaniu funkcji.

#### 4. **Niesłuszne założenie o błędzie funkcji `getMainResponder()`**:
Na początku zakładano, że funkcja `getMainResponder()` działa nieprawidłowo, ponieważ zwracała tylko jedno zadanie, a kolejne zadania były "gubione". Jednak **to założenie było błędne**. Funkcja działała **zgodnie z założeniami**, zwracając tylko jedno zadanie z odpowiedniej kategorii i platformy, ustawionymi w odpowiedniej hierarchii (`create`, `update`, `delete`, itd.).

Problemem nie była sama funkcja `getMainResponder()`, lecz fakt, że **boty lub inne nieautoryzowane żądania** zmieniały status zadania (`active_task`), co powodowało, że funkcja nie uwzględniała tych zadań przy kolejnym wywołaniu. Funkcja zakładała, że zadania, których status został zmieniony, są już przetworzone.

#### 5. **Skutki problemu:**
- **Nieautoryzowane modyfikacje danych** przez boty lub nieuprawnionych użytkowników mogły wpływać na status zadań, co prowadziło do ich "tracenia".
- **Niezrozumiałe zachowanie aplikacji**: Zadania zmieniały status, ale nie były zwracane, co powodowało zamieszanie, ponieważ system nie pokazywał tych zadań przy kolejnym wywołaniu.

#### 6. **Korzyści z wprowadzonej zmiany:**
- **Poprawa bezpieczeństwa**: Wywołanie funkcji `getMainResponder()` dopiero po weryfikacji klucza API zapobiega nieautoryzowanemu przetwarzaniu danych, co eliminuje problem niezrozumiałych zmian statusu zadań.
- **Stabilność i przewidywalność**: Funkcja `getMainResponder()` działa teraz w bardziej kontrolowanym środowisku, co zapobiega przypadkowemu przetwarzaniu zadań przez nieautoryzowane żądania.
- **Lepsza kontrola przetwarzania zadań**: Funkcja zwraca zadania tylko dla autoryzowanych użytkowników, co rozwiązuje problem "znikających" zadań spowodowanych przez nieautoryzowane zmiany statusów.

#### 7. **Testy i zmiana wersji:**
Po wprowadzeniu zmiany przeprowadzono **testy w środowisku produkcyjnym**, które potwierdziły poprawne działanie rozwiązania. Wersja endpointa została zaktualizowana do **7.41.24.10**, co odzwierciedla implementację i naprawę tego krytycznego błędu.

#### 8. **Podsumowanie:**
Zmiana była konieczna z powodu **krytycznego błędu**, który powodował nieautoryzowane modyfikacje danych i zmiany statusów zadań, co prowadziło do ich utraty. Funkcja `getMainResponder()` działała poprawnie, zwracając jedno zadanie na raz zgodnie z założeniami, ale problem wynikał z faktu, że nieautoryzowane żądania zmieniały statusy zadań, co sprawiało, że nie były one zwracane przy kolejnych wywołaniach. Przeniesienie wywołania funkcji po weryfikacji klucza API rozwiązuje ten problem i zwiększa bezpieczeństwo aplikacji.