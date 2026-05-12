import os
import sys
import zipfile
import io
import time
import requests
import base64

USERNAME = input("PythonAnywhere username: ").strip()
API_TOKEN = input("PythonAnywhere API token: ").strip()
DOMAIN = f"{USERNAME}.pythonanywhere.com"
API_BASE = "https://www.pythonanywhere.com/api/v0"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def upload_file(remote_path, local_path):
    with open(local_path, 'rb') as f:
        content = f.read()
    
    url = f"{API_BASE}/user/{USERNAME}/files/path{remote_path}"
    encoded = base64.b64encode(content).decode('utf-8')
    
    response = requests.put(url, headers={
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }, json={"content": encoded})
    
    if response.status_code in [200, 201, 204]:
        print(f"  [OK] {remote_path}")
        return True
    else:
        print(f"  [ERRO] {remote_path}: {response.status_code} {response.text}")
        return False

def upload_directory(local_dir, remote_dir):
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, local_dir)
            remote_path = f"{remote_dir}/{rel_path.replace(os.sep, '/')}"
            upload_file(remote_path, local_path)

def create_webapp():
    url = f"{API_BASE}/user/{USERNAME}/webapps/"
    
    response = requests.post(url, headers=headers, json={
        "domain_name": DOMAIN,
        "python_version": "python310"
    })
    
    if response.status_code in [200, 201]:
        print(f"[OK] Web app criado: {DOMAIN}")
        return True
    elif response.status_code == 400:
        print(f"[INFO] Web app já existe: {DOMAIN}")
        return True
    else:
        print(f"[ERRO] Criar webapp: {response.status_code} {response.text}")
        return False

def configure_webapp():
    url = f"{API_BASE}/user/{USERNAME}/webapps/{DOMAIN}/"
    project_path = f"/home/{USERNAME}/imoveis-crm"
    
    response = requests.patch(url, headers=headers, json={
        "source_directory": project_path,
        "working_directory": project_path
    })
    
    if response.status_code in [200, 204]:
        print("[OK] Web app configurado")
        return True
    else:
        print(f"[ERRO] Configurar: {response.status_code} {response.text}")
        return False

def upload_wsgi():
    wsgi_content = f"""import sys
import os

path = '/home/{USERNAME}/imoveis-crm'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)

from app import app as application
"""
    wsgi_path = f"/var/www/{DOMAIN}_wsgi.py"
    
    url = f"{API_BASE}/user/{USERNAME}/files/path{wsgi_path}"
    encoded = base64.b64encode(wsgi_content.encode()).decode()
    
    response = requests.put(url, headers={
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }, json={"content": encoded})
    
    if response.status_code in [200, 201, 204]:
        print("[OK] WSGI file configurado")
        return True
    else:
        print(f"[ERRO] WSGI: {response.status_code} {response.text}")
        return False

def create_static_mapping():
    url = f"{API_BASE}/user/{USERNAME}/webapps/{DOMAIN}/static_files/"
    
    response = requests.post(url, headers=headers, json={
        "url": "/static/",
        "path": f"/home/{USERNAME}/imoveis-crm/static/"
    })
    
    if response.status_code in [200, 201]:
        print("[OK] Static files configurados")
        return True
    elif response.status_code == 400:
        print("[INFO] Static mapping já existe")
        return True
    else:
        print(f"[ERRO] Static: {response.status_code} {response.text}")
        return False

def reload_webapp():
    url = f"{API_BASE}/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    
    response = requests.post(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print("[OK] Web app reload!")
        return True
    else:
        print(f"[ERRO] Reload: {response.status_code} {response.text}")
        return False

def run_console_command(command, wait_seconds=10):
    url = f"{API_BASE}/user/{USERNAME}/consoles/"
    
    response = requests.post(url, headers=headers, json={
        "executable": "bash",
        "working_directory": f"/home/{USERNAME}/imoveis-crm"
    })
    
    if response.status_code in [200, 201]:
        console_id = response.json()["console_id"]
        print(f"[OK] Console criado: {console_id}")
        
        time.sleep(3)
        
        input_url = f"{API_BASE}/user/{USERNAME}/consoles/{console_id}/send_input/"
        requests.post(input_url, headers=headers, json={"input": f"{command}\n"})
        
        print(f"[INFO] Comando executado, aguarde {wait_seconds}s...")
        time.sleep(wait_seconds)
        
        return True
    else:
        print(f"[ERRO] Console: {response.status_code} {response.text}")
        return False

def main():
    print(f"\n{'='*50}")
    print(f"  Deploy: Imóveis CRM -> {DOMAIN}")
    print(f"{'='*50}\n")
    
    print("[1/7] Criando web app...")
    if not create_webapp():
        print("Falha ao criar web app. Verifique suas credenciais.")
        return
    
    print("\n[2/7] Configurando web app...")
    configure_webapp()
    
    print("\n[3/7] Fazendo upload do WSGI file...")
    upload_wsgi()
    
    print("\n[4/7] Configurando static files...")
    create_static_mapping()
    
    print("\n[5/7] Fazendo upload dos arquivos do projeto...")
    
    files_to_upload = [
        ("app.py", "app.py"),
        ("models.py", "models.py"),
        ("requirements.txt", "requirements.txt"),
    ]
    
    remote_base = f"/home/{USERNAME}/imoveis-crm"
    
    for local_name, remote_name in files_to_upload:
        local_path = os.path.join(PROJECT_DIR, local_name)
        if os.path.exists(local_path):
            upload_file(f"{remote_base}/{remote_name}", local_path)
    
    print("\n[6/7] Fazendo upload de pastas (scrapers, static, templates)...")
    
    for folder in ["scrapers", "static", "templates"]:
        folder_path = os.path.join(PROJECT_DIR, folder)
        if os.path.exists(folder_path):
            upload_directory(folder_path, f"{remote_base}/{folder}")
    
    print("\n[7/7] Instalando dependências e inicializando banco...")
    
    run_console_command(
        f"cd /home/{USERNAME}/imoveis-crm && "
        f"pip3 install --user -r requirements.txt && "
        f"python3 -c \"from app import app, db; "
        f"app.app_context().push(); db.create_all(); "
        f"print('Banco criado!')\""
    )
    
    print("\nRecarregando web app...")
    reload_webapp()
    
    print(f"\n{'='*50}")
    print(f"  DEPLOY CONCLUÍDO!")
    print(f"  Acesse: https://{DOMAIN}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
