# list_models.py
import requests
from config import GEMINI_CONFIG

api_key = GEMINI_CONFIG["api_key"]
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print("Modelos disponibles:")
    for model in response.json().get("models", []):
        print(f"- {model['name']} (Versión: {model.get('version')}")
except Exception as e:
    print(f"Error: {str(e)}")