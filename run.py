from flask import Flask, jsonify, request
import json

app = Flask(__name__)

def getMainResponder(file_name='responder.json', encodingJson='utf-8'):
    try:
        # Dane do zwrócenia w formacie JSON
        with open(file_name, 'r', encoding=encodingJson) as responder:
            data = json.load(responder)
        return data
    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Error decoding JSON"}


def updateJsonFile(taskID, file_name='responder.json', encodingJson='utf-8'):
    responderFile = getMainResponder(file_name, encodingJson)
    
    for key, val in responderFile["ads"].items():
        for idx, task in enumerate(val):
            if task["task_id"] == int(taskID):
                responderFile["ads"][key].pop(idx)
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
