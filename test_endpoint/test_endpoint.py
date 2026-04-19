import requests
import json

# The URL you provided
url = "https://houserent-predictor.westeurope.inference.ml.azure.com/score"

# Replace this with your actual key from the 'Consume' tab
api_key = ""

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

# Values taken directly from the first row of your 'diabetes-training' image
data = {
    "input_data": {
        "columns": [
            "PatientID", "Pregnancies", "PlasmaGlucose", "DiastolicBloodPressure", 
            "TricepsThickness", "SerumInsulin", "BMI", "DiabetesPedigree", "Age"
        ],
        "index": [0],
        "data": [
            [1354778, 0, 171, 80, 34, 304, 29.51, 1.213, 43]
        ]
    }
}

# Sending the request
response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print("Prediction successful!")
    print("Result:", response.json())
else:
    print(f"Request failed with status code: {response.status_code}")
    print(response.text)