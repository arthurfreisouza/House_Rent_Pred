import os
import sys
from dotenv import load_dotenv
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential
from azure.ai.ml.constants import AssetTypes

# 1. Load the .env file into the environment
load_dotenv()

def get_azure_config():
    config = {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "resource_group": os.getenv("AZURE_RESOURCE_GROUP"),
        "workspace_name": os.getenv("AZURE_WORKSPACE_NAME")
    }
    
    # Validation: Ensure no variables are None
    for key, value in config.items():
        if not value:
            raise ValueError(f"Environment variable {key.upper()} is missing. check your .env file.")
    return config

# 2. Connect to the Workspace
try:
    config = get_azure_config()
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=config["subscription_id"],
        resource_group_name=config["resource_group"],
        workspace_name=config["workspace_name"]
    )
    print(f"Connected to workspace: {config['workspace_name']}")
except Exception as e:
    print(f"Failed to initialize MLClient: {e}")
    sys.exit(1)

# 3. Handle Arguments or Input
# sys.argv[0] is the script name, [1] is name, [2] is path
model_name = sys.argv[1] if len(sys.argv) > 1 else input("Enter model name: ")
local_model_path = sys.argv[2] if len(sys.argv) > 2 else input("Enter model path: ")

# 4. Define and Register the model
model_config = Model(
    path=local_model_path,
    type=AssetTypes.CUSTOM_MODEL,
    name=model_name,
    description="Random Forest model for teen mental health prediction."
)

print(f"Registering model '{model_name}' from {local_model_path}...")

try:
    registered_model = ml_client.models.create_or_update(model_config)
    print(f"Registration successful!")
    print(f"Name: {registered_model.name}")
    print(f"Version: {registered_model.version}")
except Exception as e:
    print(f"Error during registration: {e}")