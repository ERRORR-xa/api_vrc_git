from flask import Flask, request, jsonify
import requests
import base64
import json
import uuid
import os

app = Flask(__name__)

GITHUB_TOKEN = os.getenv('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')
GITHUB_USERNAME = os.getenv('ERRORR-xa') 
VERCEL_TOKEN = os.getenv('Wmchn44a5tnWTgR6dI6IUdFL')

@app.route('/')
def home():
    return jsonify({
        "status": "active", 
        "service": "Vercel Deployer API",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/deploy', methods=['POST'])
def deploy_project():
    try:
        data = request.json
        
        if not data or 'files' not in data:
            return jsonify({"success": False, "error": "Missing files data"})
        
        repo_name = data.get('repo_name', f"project-{uuid.uuid4().hex[:8]}")
        files = data.get('files', {})
        
        if 'app.py' not in files:
            return jsonify({"success": False, "error": "app.py is required"})
        
        repo_url = create_github_repo(repo_name, files)
        
        if not repo_url:
            return jsonify({"success": False, "error": "Failed to create GitHub repository"})
        
        vercel_url = f"https://{repo_name}.vercel.app"
        
        return jsonify({
            "success": True,
            "repo_name": repo_name,
            "github_url": repo_url,
            "vercel_url": vercel_url,
            "deploy_button": f"https://vercel.com/new/clone?repository-url={repo_url}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def create_github_repo(repo_name, files_dict):
    try:
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "name": repo_name,
            "description": "Auto-deployed by API",
            "private": False,
            "auto_init": False
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [201, 200]:
            for filename, content in files_dict.items():
                upload_file_to_repo(repo_name, filename, content)
            
            upload_required_files(repo_name)
            
            return f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
        return None
        
    except Exception as e:
        print(f"GitHub Error: {e}")
        return None

def upload_required_files(repo_name):
    requirements_content = "flask==2.3.3\nrequests==2.31.0\naiohttp==3.8.5\n"
    upload_file_to_repo(repo_name, "requirements.txt", requirements_content)
    
    vercel_config = {
        "version": 2,
        "builds": [{"src": "*.py", "use": "@vercel/python"}],
        "routes": [{"src": "/(.*)", "dest": "/app.py"}]
    }
    upload_file_to_repo(repo_name, "vercel.json", json.dumps(vercel_config, indent=2))

def upload_file_to_repo(repo_name, file_path, content):
    try:
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"Add {file_path}",
            "content": base64.b64encode(content.encode()).decode(),
            "branch": "main"
        }
        
        response = requests.put(url, headers=headers, json=data)
        return response.status_code in [201, 200]
        
    except Exception as e:
        print(f"Upload Error: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
