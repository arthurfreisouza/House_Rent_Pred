import sys
import os
import tempfile
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    Model,
    KubernetesOnlineEndpoint, 
    KubernetesOnlineDeployment
)
from azure.identity import DefaultAzureCredential

# Environment Mappings
ENV_CONFIG = {
    "dev": "rg-ArthurRReis-dev",
    "prod": "rg-ArthurRReis-prod"
}

WS_CONFIG = {
    "dev": "mlw-ArthurRReis-dev",
    "prod": "mlw-ArthurRReis-prod"
}

def promote(model_name, dev_key, prod_key):
    credential = DefaultAzureCredential()
    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    
    dev_client = MLClient(credential, sub_id, ENV_CONFIG[dev_key], WS_CONFIG[dev_key])
    prod_client = MLClient(credential, sub_id, ENV_CONFIG[prod_key], WS_CONFIG[prod_key])

    # 1. Fetch Model Metadata and Download
    print(f"Fetching metadata for {model_name} from {dev_key}...")
    dev_model = dev_client.models.get(name=model_name, label="latest")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Downloading and re-uploading model to {prod_key}...")
        dev_client.models.download(name=model_name, version=dev_model.version, download_path=tmp_dir)
        downloaded_model_path = os.path.join(tmp_dir, model_name)

        prod_model = Model(
            path=downloaded_model_path,
            name=model_name,
            description=dev_model.description,
            type=dev_model.type
        )
        prod_client.models.create_or_update(prod_model)

    # 2. Define Unique Endpoint Names
    # FIX: Use environment-specific names to avoid cluster collisions
    dev_endpoint_name = "k8s-mental-health-api"
    prod_endpoint_name = f"{dev_endpoint_name}-{prod_key}" # Becomes k8s-mental-health-api-prod

    dev_deployment = dev_client.online_deployments.get("blue", dev_endpoint_name)

    # 3. Create Infrastructure in Prod[cite: 1]
    print(f"Setting up endpoint: {prod_endpoint_name}...")
    endpoint = KubernetesOnlineEndpoint(
        name=prod_endpoint_name, 
        compute="arthurkubernetes", 
        auth_mode="key"
    )
    
    deployment = KubernetesOnlineDeployment(
        name="blue",
        endpoint_name=prod_endpoint_name,
        model=model_name,
        code_configuration=dev_deployment.code_configuration,
        environment=dev_deployment.environment,
        resources=dev_deployment.resources
    )

    # 4. Deploy and Route Traffic[cite: 1]
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    prod_client.online_deployments.begin_create_or_update(deployment).result()
    
    endpoint.traffic = {"blue": 100}
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    print(f"Successfully deployed to: {prod_endpoint_name}")

if __name__ == "__main__":
    promote(sys.argv[1], sys.argv[2], sys.argv[3])