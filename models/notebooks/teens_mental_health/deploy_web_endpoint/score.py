import os
import joblib
import json
import numpy as np

def init():
    global model
    # AZUREML_MODEL_DIR is an environment variable created by Azure pointing to your model
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "random_forest_model.pkl")
    model = joblib.load(model_path)

def run(raw_data):
    try:
        # Expecting JSON: {"data": [[age, gender, daily_hours, ...]]}
        data = json.loads(raw_data)["data"]
        data = np.array(data)
        
        # Perform prediction
        result = model.predict(data)
        
        # Return the results as a list
        return result.tolist()
    except Exception as e:
        return {"error": str(e)}