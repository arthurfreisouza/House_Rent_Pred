import os
from dotenv import load_dotenv
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint, 
    ManagedOnlineDeployment, 
    Model, 
    Environment, 
    CodeConfiguration
)
from azure.identity import DefaultAzureCredential

# 1. Load Environment Variables immediately
load_dotenv()

def return_environment_variables():
    return {
        "AZURE_SUBSCRIPTION_ID": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "AZURE_RESOURCE_GROUP": os.getenv("AZURE_RESOURCE_GROUP"),
        "AZURE_WORKSPACE_NAME": os.getenv("AZURE_WORKSPACE_NAME")
    }

config = return_environment_variables()
ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=config["AZURE_SUBSCRIPTION_ID"],
    resource_group_name=config["AZURE_RESOURCE_GROUP"],
    workspace_name=config["AZURE_WORKSPACE_NAME"]
)

# 2. Define the Endpoint name
endpoint_name = "mental-heallth-test"

# 3. Create the Endpoint[cite: 1]
endpoint = ManagedOnlineEndpoint(
    name=endpoint_name, 
    description="Online endpoint for teen mental health predictions",
    auth_mode="key"
)
print("Creating endpoint...")
ml_client.begin_create_or_update(endpoint).result()

# 4. Get the latest version of your registered model[cite: 4]
model_name = "randomforest"
latest_model = ml_client.models.get(name=model_name, label="latest")

# 5. Define a Custom Environment
# This step is critical to fix the 'numpy._core' and Scikit-learn version errors
custom_env = Environment(
    name="teens-mental-health-env",
    description="Custom environment to support Numpy 2.0 and Scikit-learn 1.5+",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    conda_file={
        "channels": ["conda-forge"],
        "dependencies": [
            "python=3.10",
            "numpy>=2.0.0",
            "scikit-learn>=1.5.1",
            "pip",
            {"pip": [
                "azureml-inference-server-http",
                "joblib",
                "pandas"
            ]}
        ]
    }
)

# 6. Define and Create the Deployment[cite: 1, 5]
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name=endpoint_name,
    model=latest_model,
    code_configuration=CodeConfiguration(
        code="./",  
        scoring_script="score.py"
    ),
    environment=custom_env, # Use the custom environment defined above
    instance_type="Standard_DS2_v2", # Upgraded from DS2 to DS3
    instance_count=1,
)

print("Creating deployment (this can take 5-10 minutes as it builds the new image)...")
ml_client.online_deployments.begin_create_or_update(deployment).result()

# 7. Route 100% of traffic to this deployment
endpoint.traffic = {"blue": 100}
ml_client.begin_create_or_update(endpoint).result()

print(f"Deployment successful! Scoring URI: {endpoint.scoring_uri}")