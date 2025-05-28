from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)

# Firebase povezava
cred = credentials.Certificate('petalbot-2c6e7-firebase-adminsdk-fbsvc-f153790767.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# API ključ
PERENUAL_API_KEY = 'sk-CVAw6824734ae5c6710442'

# Seznam pogostih rastlin
indoor_plants = [
    "Snake Plant", "Spider Plant", "Peace Lily", "Pothos", "ZZ Plant", "Aloe Vera", "Philodendron",
    "Fiddle Leaf Fig", "Rubber Plant", "Dracaena", "Dieffenbachia", "Chinese Evergreen", "Areca Palm",
    "Bamboo Palm", "Boston Fern", "Calathea", "Prayer Plant", "Croton", "Jade Plant", "Peperomia",
    "Schefflera", "Kalanchoe", "Anthurium", "Begonia", "Oxalis", "African Violet", "Cast Iron Plant",
    "English Ivy", "Norfolk Island Pine", "Hoya"
]

outdoor_plants = [
    "Tomato", "Basil", "Lavender", "Rosemary", "Mint", "Cilantro", "Thyme", "Chives", "Parsley", "Oregano",
    "Sunflower", "Marigold", "Petunia", "Geranium", "Zinnia", "Begonia", "Dahlia", "Peony", "Hosta", "Daylily",
    "Hydrangea", "Lilac", "Rhododendron", "Azalea", "Boxwood", "Iris", "Coneflower", "Snapdragon", "Calendula", "Salvia"
]

def get_plant_by_name(plant_name):
    """Vrne podatke za prvo rastlino, ki se ujema z imenom"""
    url = f"https://perenual.com/api/v2/species-list?key={PERENUAL_API_KEY}&q={plant_name}"
    response = requests.get(url)

    if response.status_code == 200:
        results = response.json().get("data", [])
        if results:
            return results[0]  # prva najdena
    return None

def get_plant_details(plant_id):
    url = f"https://perenual.com/api/v2/species/details/{plant_id}?key={PERENUAL_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return {}

def save_plant_to_firestore(name, category, basic_data, details):
    try:
        plant_doc = {
            'type': category,
            'name': name,
            'scientific_name': basic_data.get('scientific_name', 'Unknown'),
            'common_name': basic_data.get('common_name', name),
            'family': details.get('family', 'No information'),
            'watering': details.get('watering', 'No information'),
            'sunlight': ", ".join(details.get('sunlight', [])),
            'growth_rate': details.get('growth_rate', 'No information'),
            'care_level': details.get('care_level', 'No information'),
            'description': details.get('description', 'No description available'),
            'image': (details.get('default_image') or {}).get('regular_url', '')
        }
        db.collection('plants').document(name).set(plant_doc)
        print(f"[OK] Added: {name}")
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)}")

@app.route('/add_common_plants', methods=['GET'])
def add_common_plants():
    errors = []
    total = 0

    for plant_name in indoor_plants:
        result = get_plant_by_name(plant_name)
        if result:
            details = get_plant_details(result['id'])
            save_plant_to_firestore(plant_name, "indoor", result, details)
            total += 1
        else:
            errors.append(plant_name)

    for plant_name in outdoor_plants:
        result = get_plant_by_name(plant_name)
        if result:
            details = get_plant_details(result['id'])
            save_plant_to_firestore(plant_name, "outdoor", result, details)
            total += 1
        else:
            errors.append(plant_name)

    return f"✅ Shranjenih rastlin: {total}, ❌ Ni jih bilo mogoče najti: {len(errors)} — {errors}"

if __name__ == '__main__':
    app.run(debug=True)
