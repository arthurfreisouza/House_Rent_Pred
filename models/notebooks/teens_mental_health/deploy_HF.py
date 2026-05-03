from huggingface_hub import login, HfApi

# 1. Provide your "Write" token directly here
login(token="")

api = HfApi()

# 2. Make sure "your-actual-username" matches your HF profile exactly
username = "Arthur-Reis" 
repo_id = f"{username}/teen-mental-health-random-forest"

# Create the repo
api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

# Upload the local model file
api.upload_file(
    repo_id=repo_id,
    path_or_fileobj="random_forest_model.pkl",
    path_in_repo="random_forest_model.pkl"
)