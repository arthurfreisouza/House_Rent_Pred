import streamlit as st
import requests
import json

# Page config for a clean engineer-ready layout
st.set_page_config(page_title="UFMG House Price Predictor", layout="wide")

st.title("🏠 Real Estate Price Estimation")
st.markdown("---")

# Replace this with the Primary Key from your 'Consume' tab
#API_KEY = "YOUR_PRIMARY_KEY_HERE"
# URL = "https://price-prediction-04192134.brazilsouth.inference.ml.azure.com/score"

API_KEY = "8OeOEvPZLBfG1Op8N9LMhDHXkb3TFUL8nS4hc1njFh73Wa4wV2zWJQQJ99CDAAAAAAAAAAAAINFRAZML2ZqG"
URL = "https://price-prediction-04192134.brazilsouth.inference.ml.azure.com/score"

# --- SIDEBAR INPUTS ---
st.sidebar.header("Property Details")
area = st.sidebar.number_input("Area (sq ft)", value=1360, step=10)
bedrooms = st.sidebar.slider("Bedrooms", 1, 10, 6)
bathrooms = st.sidebar.slider("Bathrooms", 1, 5, 2)
floors = st.sidebar.number_input("Total Floors", 1, 5, 2)
age = st.sidebar.number_input("Property Age (years)", 0, 100, 9)
distance = st.sidebar.number_input("Distance to Center (km)", 0, 50, 10)

# --- AMENITIES ---
st.sidebar.header("Amenities")
garage = st.sidebar.checkbox("Garage Available", value=False)
parking = st.sidebar.checkbox("Parking Space", value=False)
garden = st.sidebar.checkbox("Garden", value=True)
security = st.sidebar.checkbox("24/7 Security", value=False)

# --- REGIONAL DATA ---
st.sidebar.header("Neighborhood Metrics")
crime_rate = st.sidebar.number_input("Crime Rate (%)", 0.0, 100.0, 6.93)
pop_density = st.sidebar.number_input("Population Density", 0, 20000, 7242)
location = st.sidebar.selectbox("Location Grade", ["premium", "suburban", "rural"])
income_level = st.sidebar.selectbox("Neighborhood Income", ["low", "medium", "high"])

# --- NEARBY FACILITIES ---
st.sidebar.header("Proximity")
school = st.sidebar.checkbox("School Nearby", value=True)
hospital = st.sidebar.checkbox("Hospital Nearby", value=False)
mall = st.sidebar.checkbox("Shopping Mall Nearby", value=True)
transport = st.sidebar.checkbox("Public Transport", value=False)

# --- PREDICTION LOGIC ---
if st.button("Generate Price Prediction"):
    # Constructing the payload in the exact order requested by the model
    # We convert booleans to 0/1 to match common AutoML numerical types
    data_row = [
        area, bedrooms, bathrooms, floors, age, distance,
        1 if garage else 0, 1 if parking else 0, 1 if garden else 0, 
        1 if security else 0, 1 if school else 0, 1 if hospital else 0,
        1 if mall else 0, 1 if transport else 0,
        crime_rate, pop_density, location, income_level
    ]

    payload = {
        "input_data": {
            "columns": [
                "area", "bedrooms", "bathrooms", "floors", "age", "distance",
                "garage", "parking", "garden", "security", "school_nearby",
                "hospital_nearby", "shopping_mall_nearby", "public_transport",
                "crime_rate", "population_density", "location", "income_level"
            ],
            "index": [0],
            "data": [data_row]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "azureml-model-deployment": "price-v1" # Target specific deployment
    }

    with st.spinner("Requesting inference from brazilsouth..."):
        try:
            response = requests.post(URL, json=payload, headers=headers)
            response.raise_for_status() # Check for HTTP errors
            
            prediction = response.json()[0]
            
            # Displaying the result in a clean metric card
            st.success("Prediction Received")
            st.metric(label="Estimated Market Value", value=f"${prediction:,.2f}")
            
        except Exception as e:
            st.error(f"Failed to reach endpoint: {e}")