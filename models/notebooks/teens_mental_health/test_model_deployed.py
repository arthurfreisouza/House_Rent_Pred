import requests
import json
import os
from dotenv import load_dotenv
# URL from the 'Details' tab in your screenshot
url = "http://20.54.32.244/api/v1/endpoint/k8s-mental-health-api/score"

def environment_primary_key():
    load_dotenv()
    return os.getenv("AZURE_ML_KEY")

# Replace with the actual key from the 'Consume' tab
api_key = environment_primary_key()

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

# Sample data representing 12 features (Age, Gender, Sleep, etc.)
sample_data = {
    "data": [
        [18, 0, 8.5, 1, 3.2, 0.6, 2, 0.7, 1, 7, 8, 9]
    ]
}

print("Sending request to model...")
response = requests.post(url, json=sample_data, headers=headers)

if response.status_code == 200:
    print("Prediction successful!")
    print("Model Response:", response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.text)