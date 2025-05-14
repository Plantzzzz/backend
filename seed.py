from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)

# Firebase povezava
cred = credentials.Certificate('petalbot-2c6e7-firebase-adminsdk-fbsvc-f153790767.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Funkcija za pridobivanje seznam rastlin iz Perenual API
def get_plants_list():
    api_key = 'sk-CVAw6824734ae5c6710442'
    url = f'https://perenual.com/api/v2/species-list?key={api_key}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code}")

# Funkcija za pridobivanje podrobnosti rastline iz Perenual API
def get_plant_details(plant_id):
    api_key = 'sk-CVAw6824734ae5c6710442'
    url = f'https://perenual.com/api/v2/species/details/{plant_id}?key={api_key}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code}")

# Funkcija za shranjevanje podatkov v Firestore
def save_plants_to_firestore(plants_data):
    for plant in plants_data['data']:
        plant_id = plant['id']
        plant_name = plant['common_name']
        
        # Pridobivanje podrobnosti o rastlini
        plant_details = get_plant_details(plant_id)
        
        # Priprava podatkov za shranjevanje
        plant_info = {
            'name': plant_name,
            'scientific_name': plant['scientific_name'],
            'common_name': plant['common_name'],
            'family': plant_details.get('family', 'No information'),
            'watering': plant_details.get('watering', 'No information'),
            'sunlight': plant_details.get('sunlight', 'No information'),
            'growth_rate': plant_details.get('growth_rate', 'No information'),
            'care_level': plant_details.get('care_level', 'No information'),
            'description': plant_details.get('description', 'No description available'),
            'image': plant_details['default_image']['regular_url']
        }
        
        # Dodajanje rastline v Firestore
        doc_ref = db.collection('plants').document(plant_name)
        doc_ref.set(plant_info)
        print(f"Added {plant_name} to Firestore")

@app.route('/add_plants', methods=['GET'])
def add_plants():
    try:
        print("Requesting plant list...")
        # Pridobivanje seznam rastlin iz Perenual API
        plants_data = get_plants_list()
        print(f"Found {len(plants_data['data'])} plants")
        
        # Shranjevanje podatkov v Firestore
        save_plants_to_firestore(plants_data)
        
        return "Plants added to Firestore successfully!"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
