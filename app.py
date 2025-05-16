from flask import Flask, request, jsonify
import requests
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PLANTNET_API_KEY = "2b10i98sqc00Pe5mJAJTwoG4e"
PERENUAL_API_KEY = "sk-CVAw6824734ae5c6710442"

PLANTNET_API_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"
PERENUAL_CARE_URL = "https://perenual.com/api/species-care-guide-list"

@app.route("/identify", methods=["POST"])
def identify():
    if 'image' not in request.files:
        return jsonify({"error": "Image not found"}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)

    print(f"[PlantNet] Pošiljam sliko z imenom: {filename}")
    print(f"[PlantNet] MIME tip slike: {image.content_type}")

    files = {
        'images': (filename, image.read(), image.content_type),
    }
    data = {
        'organs': 'leaf'
    }

    print(f"[PlantNet] Kličem URL: {PLANTNET_API_URL}")
    response = requests.post(PLANTNET_API_URL, files=files, data=data)

    if response.status_code != 200:
        print(f"[PlantNet] Napaka pri odgovoru: {response.status_code}")
        print(response.text)
        return jsonify({
            "error": f"PlantNet API error {response.status_code}",
            "details": response.text
        }), response.status_code

    plantnet_result = response.json()

    if not plantnet_result.get("results"):
        print("[PlantNet] Ni rezultatov.")
        return jsonify({"error": "No results from PlantNet"}), 404

    best_guess = plantnet_result["results"][0]
    scientific_name = best_guess["species"].get("scientificNameWithoutAuthor")

    print(f"[PlantNet] Znanstveno ime iz PlantNet: {scientific_name}")

    if not scientific_name:
        return jsonify({
            "error": "Scientific name not found in PlantNet result"
        }), 400

    # Kličemo Perenual species-care-guide-list API z q parametrom = znanstveno ime rastline
    params = {
        "key": PERENUAL_API_KEY,
        "q": scientific_name
    }

    print(f"[Perenual] Kličem species-care-guide-list API z URL: {PERENUAL_CARE_URL}")
    print(f"[Perenual] Parametri: {params}")

    care_response = requests.get(PERENUAL_CARE_URL, params=params)

    if care_response.status_code != 200:
        print(f"[Perenual] Napaka {care_response.status_code}: {care_response.text}")
        return jsonify({
            "error": f"Perenual care guide API error {care_response.status_code}",
            "details": care_response.text
        }), care_response.status_code

    care_data = care_response.json()
    print("[Perenual] Podatki o skrbi za rastlino (care guide):")
    print(care_data)  # tukaj printaš celoten JSON odgovor v konzolo

    return jsonify({
        "plantnet_result": plantnet_result,
        "care_data": care_data
    })


if __name__ == "__main__":
    print("[Flask] Strežnik se zažene na http://localhost:5000")
    app.run(debug=True, port=5000)
