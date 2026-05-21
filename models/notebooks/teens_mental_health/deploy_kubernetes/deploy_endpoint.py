import os
from dotenv import load_dotenv
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    KubernetesOnlineEndpoint, 
    KubernetesOnlineDeployment, 
    Model, 
    Environment, 
    CodeConfiguration,
    ResourceSettings  # Add this import
)
import requests
from azure.identity import DefaultAzureCredential

# 1. Load Environment Variables
load_dotenv()

# (Initialization of ml_client remains the same as your previous script)
config = {
    "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
    "resource_group": os.getenv("AZURE_RESOURCE_GROUP"),
    "workspace_name": os.getenv("AZURE_WORKSPACE_NAME")
}

ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=config["subscription_id"],
    resource_group_name=config["resource_group"],
    workspace_name=config["workspace_name"]
)

# 2. Define the Kubernetes Endpoint
endpoint_name = "k8s-mental-health-api"

# Use KubernetesOnlineEndpoint instead of ManagedOnlineEndpoint
endpoint = KubernetesOnlineEndpoint(
    name=endpoint_name, 
    compute="arthurkubertest", # The name you gave the cluster when attaching it
    description="Kubernetes endpoint for teen mental health predictions",
    auth_mode="key"
)
print("Creating Kubernetes endpoint...")
ml_client.begin_create_or_update(endpoint).result()

# 3. Get the latest model
latest_model = ml_client.models.get(name="randomforest", label="latest")

# 4. Define the Custom Environment (Same as before to fix numpy version)[cite: 19, 20]
custom_env = Environment(
    name="teens-k8s-env",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    conda_file="conda.yaml" # Path to your conda.yaml
)

# 5. Define the Kubernetes Deployment
# We specify CPU and Memory requests instead of an instance_type[cite: 19]
# 5. Define the Kubernetes Deployment
# 5. Define the Kubernetes Deployment
deployment = KubernetesOnlineDeployment(
    name="blue",
    endpoint_name=endpoint_name,
    model=latest_model,
    code_configuration=CodeConfiguration(
        code="./",  
        scoring_script="score.py"
    ),
    environment=custom_env,
    # FIX: Use cpu and memory directly as arguments
    resources=ResourceSettings(
        cpu="1",
        memory="2Gi"
    )
)

print("Creating Kubernetes deployment...")
ml_client.online_deployments.begin_create_or_update(deployment).result()

# 6. Set traffic
endpoint.traffic = {"blue": 100}
ml_client.begin_create_or_update(endpoint).result()

print(f"K8s Deployment successful! Scoring URI: {endpoint.scoring_uri}")