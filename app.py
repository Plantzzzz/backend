from flask import Flask, request, jsonify
import requests
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Ključi
PLANTNET_API_KEY = "2b10i98sqc00Pe5mJAJTwoG4e"
PERENUAL_API_KEY = "sk-CVAw6824734ae5c6710442"

# API URL-ji
PLANTNET_API_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"
PERENUAL_SEARCH_URL = "https://perenual.com/api/v2/species-list"

@app.route("/identify", methods=["POST"])
def identify():
    if 'image' not in request.files:
        return jsonify({"error": "Image not found"}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)

    files = {
        'images': (filename, image.read(), image.content_type),
    }
    data = {
        'organs': 'leaf'
    }

    # 1. Pošlji sliko na PlantNet API
    response = requests.post(PLANTNET_API_URL, files=files, data=data)

    if response.status_code != 200:
        return jsonify({
            "error": f"PlantNet API error {response.status_code}",
            "details": response.text
        }), response.status_code

    plantnet_result = response.json()

    if not plantnet_result.get("results"):
        return jsonify({"error": "No results from PlantNet"}), 404

    # 2. Prva rastlina z največjo verjetnostjo
    best_guess = plantnet_result["results"][0]
    scientific_name = best_guess["species"].get("scientificNameWithoutAuthor")

    if not scientific_name:
        return jsonify({
            "error": "Scientific name not found in PlantNet result"
        }), 400

    # 3. Išči v Perenual API po znanstvenem imenu
    search_params = {
        "key": PERENUAL_API_KEY,
        "q": scientific_name
    }
    perenual_search = requests.get(PERENUAL_SEARCH_URL, params=search_params)

    if perenual_search.status_code != 200:
        return jsonify({
            "error": f"Perenual API error {perenual_search.status_code}",
            "details": perenual_search.text
        }), perenual_search.status_code

    # Preverimo, če imamo rezultate za iskanje
    perenual_data = perenual_search.json().get("data", [])
    
    if not perenual_data:
        return jsonify({
            "plantnet_result": plantnet_result,
            "perenual_error": "No matching plant found in Perenual"
        })
    
    # 4. Vrnimo samo ime rastline
    plant_name = perenual_data[0].get("common_name", scientific_name)

    # 5. Vrnimo rezultat
    return jsonify({
        "plantnet_result": plantnet_result,
        "plant_name": plant_name
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
