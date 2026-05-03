import sys
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    KubernetesOnlineEndpoint, KubernetesOnlineDeployment
)
from azure.identity import DefaultAzureCredential

# Maps your command arguments to the correct Resource Groups
ENV_CONFIG = {
    "dev": "rg-ArthurRReis-dev",
    "prod": "rg-ArthurRReis-prod"
}

# Maps your command arguments to the correct Workspace Names
WS_CONFIG = {
    "dev": "mlw-ArthurRReis-dev",
    "prod": "mlw-ArthurRReis-prod" # Verified from your portal screenshot
}

def promote(model_name, dev_key, prod_key):
    credential = DefaultAzureCredential()
    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    
    # 1. Connect to environments using their specific RGs and Workspace names
    dev_client = MLClient(credential, sub_id, ENV_CONFIG[dev_key], WS_CONFIG[dev_key])
    prod_client = MLClient(credential, sub_id, ENV_CONFIG[prod_key], WS_CONFIG[prod_key])

    print(f"Fetching model {model_name} from {dev_key}...")
    dev_model = dev_client.models.get(name=model_name, label="latest")
    
    # 2. Extract configuration from the current Dev deployment
    endpoint_name = "k8s-mental-health-api"
    dev_deployment = dev_client.online_deployments.get("blue", endpoint_name)

    # 3. Register and Deploy to Prod
    print(f"Promoting to {prod_key} workspace: {WS_CONFIG[prod_key]}...")
    prod_client.models.create_or_update(dev_model)

    endpoint = KubernetesOnlineEndpoint(
        name=endpoint_name, 
        compute="arthurkubernetes", # Ensure this is attached in the Prod workspace too
        auth_mode="key"
    )
    
    deployment = KubernetesOnlineDeployment(
        name="blue",
        endpoint_name=endpoint_name,
        model=dev_model,
        code_configuration=dev_deployment.code_configuration,
        environment=dev_deployment.environment,
        resources=dev_deployment.resources
    )

    # Execute Deployment
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    prod_client.online_deployments.begin_create_or_update(deployment).result()
    
    # Route 100% traffic to the new deployment
    endpoint.traffic = {"blue": 100}
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    print(f"Successfully promoted {model_name} to Production!")

if __name__ == "__main__":
    promote(sys.argv[1], sys.argv[2], sys.argv[3])