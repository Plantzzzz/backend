# 🌿 Backend za Prepoznavo Rastlin
Dobrodošli v backend delu aplikacije  **PetalBot**, ki temelji na ogrodju **Flask**. Ta aplikacija omogoča preprosto vzpostavitev REST API-ja za pridobivanje podatkov o rastlinah preko posredovane slike iz frontenda projekta, ter pridobivanje nasvetov o rastlini.
<br>
<br>

## 📁 Struktura projekta
backend/ <br>
├── app.py # Glavna Flask aplikacija (API logika) <br>
├── test_app.py # Osnovni testi za preverjanje API delovanja <br>
├── seed.py # Skripta za inicializacijo vzorčnih podatkov <br>
├── requirements.txt # Seznam vseh potrebnih Python knjižnic <br>
├── Procfile # Konfiguracija za Heroku zagon <br>
├── render.yaml # Konfiguracija za Render.com <br>
├── .gitignore # Izključene datoteke iz Git sledenja <br>
└── README.md # Dokumentacija projekta (ta datoteka) <br>
<br>
<br>

## 📦 Tehnologije in knjižnice
- Python 3
- Flask – ogrodje za spletne aplikacije in REST API
- gunicorn – WSGI strežnik za produkcijsko okolje
- unittest – za osnovno testiranje
- render.yaml / Procfile – za enostavno oblačno gostovanje
<br>
<br>

## 📡 API
Aplikacija za delovanje uporablja 
-PlantNet API (prepoznava rasltine)
-Perenual API (pridobivanje dodatnih informacij) 
-Gemini API (pridobivanje nasveta)


