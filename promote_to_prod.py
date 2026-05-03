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

    # 1. Fetch Model Metadata from Dev
    print(f"Fetching metadata for {model_name} from {dev_key}...")
    dev_model = dev_client.models.get(name=model_name, label="latest")
    
    # 2. Download the actual model files to the runner
    # This bridges the gap between the two different storage accounts
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Downloading model files from {dev_key} storage...")
        dev_client.models.download(name=model_name, version=dev_model.version, download_path=tmp_dir)
        
        # The SDK downloads into a subfolder named after the model
        downloaded_model_path = os.path.join(tmp_dir, model_name)

        # 3. Register a fresh model in Prod (this triggers the upload to Prod storage)
        print(f"Uploading model files to {prod_key} storage...")
        prod_model = Model(
            path=downloaded_model_path,
            name=model_name,
            description=dev_model.description,
            type=dev_model.type
        )
        prod_client.models.create_or_update(prod_model)

    # 4. Replicate the Deployment Infrastructure
    endpoint_name = "k8s-mental-health-api"
    dev_deployment = dev_client.online_deployments.get("blue", endpoint_name)

    print(f"Setting up Kubernetes infrastructure in {prod_key}...")
    endpoint = KubernetesOnlineEndpoint(
        name=endpoint_name, 
        compute="arthurkubernetes", 
        auth_mode="key"
    )
    
    deployment = KubernetesOnlineDeployment(
        name="blue",
        endpoint_name=endpoint_name,
        model=model_name, # Use the name of the newly registered prod model
        code_configuration=dev_deployment.code_configuration,
        environment=dev_deployment.environment,
        resources=dev_deployment.resources
    )

    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    prod_client.online_deployments.begin_create_or_update(deployment).result()
    
    endpoint.traffic = {"blue": 100}
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    print(f"Successfully promoted and deployed {model_name} to Prod!")

if __name__ == "__main__":
    promote(sys.argv[1], sys.argv[2], sys.argv[3])