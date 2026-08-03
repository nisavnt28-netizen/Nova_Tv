import os
from huggingface_hub import HfApi, hf_hub_download

def sync_databases():
    token = os.environ.get("HF_TOKEN")
    repo_id = os.environ.get("HF_REPO_ID")
    
    if not token or not repo_id:
        return "Environment Variables (HF_TOKEN, HF_REPO_ID) set nahi hain!"
        
    try:
        api = HfApi()
        # HF par kaun-kaun si files hain, unki list lo
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token)
        
        downloaded = []
        for file in files:
            # Sirf .db, .csv ya .zip wali files download karo
            if file.endswith(('.db', '.csv', '.zip')):
                if not os.path.exists(file):
                    print(f"Downloading {file}...")
                    hf_hub_download(repo_id=repo_id, filename=file, repo_type="dataset", token=token, local_dir=".")
                    downloaded.append(file)
                    
        if not downloaded:
            return "Sab files pehle se synced hain. Koi nayi file nahi mili."
        else:
            return f"Successfully Downloaded: {', '.join(downloaded)}"
            
    except Exception as e:
        return f"Error: {str(e)}"
