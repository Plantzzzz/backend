import io
import json
import pytest
from app import app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# --- Test za /identify ---
@patch("app.requests.post")
@patch("app.requests.get")
def test_identify_success(mock_get, mock_post, client):
    # Mock POST (PlantNet API)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [{
            "species": {
                "scientificNameWithoutAuthor": "Ficus lyrata"
            }
        }]
    }

    # Mock GET (Perenual API)
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "data": [{"common_name": "Fiddle Leaf Fig"}]
    }

    # Pošlji testno sliko (simulacija)
    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/identify', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "plantnet_result" in json_data
    assert "care_data" in json_data


# --- Test za /get-plant-care ---
@patch("app.requests.post")
def test_get_plant_care_success(mock_post, client):
    # Mock Gemini API response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "Water your Monstera once a week. Keep it in indirect sunlight."
                }]
            }
        }]
    }

    response = client.post('/get-plant-care', json={"plant": "Monstera"})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "care_instructions" in json_data
    assert "Monstera" in json_data["care_instructions"] or json_data["care_instructions"] != ""


def test_identify_no_image(client):
    response = client.post('/identify', data={})
    assert response.status_code == 400
    assert b"Image not found" in response.data


# --- Test: PlantNet API vrne napako ---
@patch("app.requests.post")
def test_identify_plantnet_api_error(mock_post, client):
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Internal Server Error"

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/identify', content_type='multipart/form-data', data=data)
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data["error"].startswith("PlantNet API error")


# --- Test: PlantNet API ne vrne rezultatov ---
@patch("app.requests.post")
def test_identify_no_results(mock_post, client):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": []
    }

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/identify', content_type='multipart/form-data', data=data)
    assert response.status_code == 404
    assert b"No results from PlantNet" in response.data


# --- Test: PlantNet rezultat brez znanstvenega imena ---
@patch("app.requests.post")
def test_identify_no_scientific_name(mock_post, client):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [{
            "species": {}
        }]
    }

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/identify', content_type='multipart/form-data', data=data)
    assert response.status_code == 400
    assert b"Scientific name not found" in response.data


# --- Test: Perenual API vrne napako ---
@patch("app.requests.post")
@patch("app.requests.get")
def test_perenual_api_error(mock_get, mock_post, client):
    # PlantNet OK
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [{
            "species": {
                "scientificNameWithoutAuthor": "Ficus lyrata"
            }
        }]
    }

    # Perenual ERROR
    mock_get.return_value.status_code = 503
    mock_get.return_value.text = "Service Unavailable"

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/identify', content_type='multipart/form-data', data=data)
    assert response.status_code == 503
    json_data = response.get_json()
    assert "Perenual care guide API error" in json_data["error"]


# --- Test: Gemini API vrne napako ---
@patch("app.requests.post")
def test_get_plant_care_gemini_error(mock_post, client):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Gemini Internal Error"
    mock_post.return_value = mock_response

    response = client.post('/get-plant-care', json={"plant": "Monstera"})
    assert response.status_code == 500
    json_data = response.get_json()
    assert "Gemini API error" in json_data["error"]



@patch("app.requests.post")
def test_get_plant_care_success(mock_post, client):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Monstera prefers bright indirect light and moderate watering."}
                    ]
                }
            }
        ]
    }

    mock_post.return_value = mock_response

    response = client.post('/get-plant-care', json={"plant": "Monstera"})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "care_instructions" in json_data
    assert "Monstera prefers bright indirect light" in json_data["care_instructions"]
