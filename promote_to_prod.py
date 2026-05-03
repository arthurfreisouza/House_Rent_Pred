import sys
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    KubernetesOnlineEndpoint, KubernetesOnlineDeployment
)
from azure.identity import DefaultAzureCredential

# Map keys to your specific Resource Groups
ENV_CONFIG = {
    "dev": "rg-ArthurRReis-dev",
    "prod": "rg-ArthurRReis-prod"
}

def promote(model_name, dev_key, prod_key):
    credential = DefaultAzureCredential()
    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    workspace = os.getenv("AZURE_WORKSPACE_NAME")

    # Guard clause to prevent the ValueError you saw
    if not workspace or not sub_id:
        raise ValueError("Missing environment variables: AZURE_WORKSPACE_NAME or AZURE_SUBSCRIPTION_ID")

    # 1. Connect to both Resource Groups
    dev_client = MLClient(credential, sub_id, ENV_CONFIG[dev_key], workspace)
    prod_client = MLClient(credential, sub_id, ENV_CONFIG[prod_key], workspace)

    print(f"Fetching model {model_name} from {dev_key}...")
    dev_model = dev_client.models.get(name=model_name, label="latest")
    
    # 2. Get existing Dev Deployment info to mirror it
    endpoint_name = "k8s-mental-health-api"
    dev_deployment = dev_client.online_deployments.get("blue", endpoint_name)

    # 3. Register and Deploy to Prod
    print(f"Promoting to {prod_key}...")
    prod_client.models.create_or_update(dev_model)

    endpoint = KubernetesOnlineEndpoint(
        name=endpoint_name, 
        compute="arthurkubernetes", 
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

    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    prod_client.online_deployments.begin_create_or_update(deployment).result()
    
    endpoint.traffic = {"blue": 100}
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Promotion Complete!")

if __name__ == "__main__":
    promote(sys.argv[1], sys.argv[2], sys.argv[3])