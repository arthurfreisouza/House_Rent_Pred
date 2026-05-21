import sys
import os
import tempfile
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    Model,
    KubernetesOnlineEndpoint, 
    KubernetesOnlineDeployment,
    CodeConfiguration
)
from azure.identity import DefaultAzureCredential

ENV_CONFIG = {"dev": "rg-ArthurRReis-dev", "prod": "rg-ArthurRReis-prod"}
WS_CONFIG = {"dev": "mlw-ArthurRReis-dev", "prod": "mlw-ArthurRReis-prod"}

def promote(model_name, dev_key, prod_key):
    credential = DefaultAzureCredential()
    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    
    dev_client = MLClient(credential, sub_id, ENV_CONFIG[dev_key], WS_CONFIG[dev_key])
    prod_client = MLClient(credential, sub_id, ENV_CONFIG[prod_key], WS_CONFIG[prod_key])

    # 1. Promote Model (Dev Storage -> Runner -> Prod Storage)
    print(f"Promoting model {model_name}...")
    dev_model = dev_client.models.get(name=model_name, label="latest")
    with tempfile.TemporaryDirectory() as tmp_dir:
        dev_client.models.download(name=model_name, version=dev_model.version, download_path=tmp_dir)
        prod_model_result = prod_client.models.create_or_update(
            Model(path=os.path.join(tmp_dir, model_name), name=model_name, type=dev_model.type)
        )

    # 2. Promote Environment Definition
    endpoint_name = "k8s-mental-health-api"
    dev_deployment = dev_client.online_deployments.get("blue", endpoint_name)
    
    env_name = dev_deployment.environment.split('/')[-3]
    env_version = dev_deployment.environment.split('/')[-1]
    dev_env_obj = dev_client.environments.get(name=env_name, version=env_version)
    prod_env_result = prod_client.environments.create_or_update(dev_env_obj)

    # 3. Setup Prod Infrastructure with Local Code Reference
    prod_endpoint_name = f"{endpoint_name}-prod"
    print(f"Setting up endpoint: {prod_endpoint_name}...")
    
    endpoint = KubernetesOnlineEndpoint(
        name=prod_endpoint_name, 
        compute="arthurkubernetes", 
        auth_mode="key"
    )
    
    # FIX: Define CodeConfiguration manually to force a fresh Prod upload
    # This replaces the Dev ID with a local path reference
    prod_code_config = CodeConfiguration(
        code="models/notebooks/teens_mental_health/deploy_kubernetes/",
        scoring_script="score.py" 
    )

    deployment = KubernetesOnlineDeployment(
        name="blue",
        endpoint_name=prod_endpoint_name,
        model=prod_model_result,
        environment=prod_env_result,
        code_configuration=prod_code_config, # Now points to the correct subdirectory
        resources=dev_deployment.resources
    )

    # 4. Execute Deployment
    print("Executing production deployment...")
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    prod_client.online_deployments.begin_create_or_update(deployment).result()
    
    endpoint.traffic = {"blue": 100}
    prod_client.online_endpoints.begin_create_or_update(endpoint).result()
    
    final_uri = prod_client.online_endpoints.get(prod_endpoint_name).scoring_uri
    print(f"Success! Production URI: {final_uri}")

if __name__ == "__main__":
    m_name = sys.argv[1].strip()
    d_env = sys.argv[2].strip()
    p_env = sys.argv[3].strip()
    promote(m_name, d_env, p_env)