import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from werkzeug.utils import secure_filename
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)


PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
PERENUAL_API_KEY = os.getenv("PERENUAL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    print("[plantnet] Podatki za plantnet")
    print(plantnet_result)
    print("[Perenual] Podatki o skrbi za rastlino (care guide):")
    print(care_data)  # tukaj printaš celoten JSON odgovor v konzolo

    return jsonify({
        "plantnet_result": plantnet_result,
        "care_data": care_data
    })

@app.route('/get-plant-care', methods=['POST'])
def get_plant_care():
    data = request.get_json()
    plant_name = data.get('plant', 'unknown plant')

    prompt = (
        f"You are PetalBot, a helpful gardening assistant. "
        f"In a few sentences, explain how to take care of the plant \"{plant_name}\". "
        f"Include ideal sun exposure, watering frequency, and any special care tips. "
        f"Be brief and practical."
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {'Content-Type': 'application/json'}

    gemini_response = requests.post(gemini_url, headers=headers, json=payload)

    if gemini_response.ok:
        result = gemini_response.json()
        content = result.get("candidates", [{}])[0].get("content", {})
        parts = content.get("parts", [])
        care_instructions = parts[0].get("text", "") if parts else "No response from Gemini."
        return jsonify({'care_instructions': care_instructions})
    else:
        return jsonify({'error': 'Gemini API error'}), 500



if __name__ == "__main__":
    print("[Flask] Strežnik se zažene na http://localhost:5000")
    app.run(debug=True, port=5000)
