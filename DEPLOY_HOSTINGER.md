# Deploy no Hostinger - Compra Certa Imóveis

## Opção 1: Hostinger com cPanel (Mais Fácil)

### 1. Acesse o Hostinger
- Login em: https://hpanel.hostinger.com
- Vá em **Hospedagem** → Seu domínio

### 2. Configurar Python no Hostinger

1. No cPanel, procure **"Configurações de Aplicação"** ou **"Python App"**
2. Clique em **"Criar Aplicação"**
3. Preencha:
   - **Diretório**: `public_html/imoveis`
   - **Versão Python**: `3.11` ou `3.10`
   - **Modo**: `Produção`

4. Clique em **Criar**

### 3. Upload dos arquivos

1. Compacte todos os arquivos do projeto em `.zip`
2. No cPanel, vá em **Gerenciador de Arquivos**
3. Navegue até `public_html/imoveis`
4. Clique em **Upload** e selecione o .zip
5. Clique com botão direito → **Extrair**

### 4. Configurar variáveis

Volte para **Python App** e clique no app criado:
- **Command**: `gunicorn app:app`
- **Application Startup File**: `app.py`
- Adicione variável `SECRET_KEY`: `sua-chave-secreta-hostinger`

### 5. Instalar dependências

No mesmo painel Python App, clique em **SSH** ou use o terminal:
```bash
cd imoveis
pip install -r requirements.txt
```

### 6. Iniciar banco

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 7. Acessar

- Admin: `https://compracertaimoveis.net.br/imoveis/admin`
- Site: `https://compracertaimoveis.net.br/imoveis`

---

## Opção 2: Hostinger VPS (SSH) - Recomendado para mais controle

### 1. Acesse SSH
```bash
ssh usuario@seu-ip
```

### 2. Instalar Python
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

### 3. Criar diretório
```bash
mkdir -p /var/www/imoveis
cd /var/www/imoveis
```

### 4. Upload do projeto
```bash
# Do seu PC local:
scp -r ./imoveis-crm/* usuario@seu-ip:/var/www/imoveis/
```

### 5. Setup virtual environment
```bash
cd /var/www/imoveis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 6. Configurar Nginx
```bash
sudo nano /etc/nginx/sites-available/imoveis
```

```nginx
server {
    listen 80;
    server_name compracertaimoveis.net.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/imoveis/static/;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/imoveis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Criar systemd service
```bash
sudo nano /etc/systemd/system/imoveis.service
```

```ini
[Unit]
Description=Compra Certa Imoveis CRM
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/imoveis
Environment="PATH=/var/www/imoveis/venv/bin"
ExecStart=/var/www/imoveis/venv/bin/gunicorn --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start imoveis
sudo systemctl enable imoveis
```

### 8. SSL (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d compracertaimoveis.net.br
```

---

## Atualizar DNS no Hostinger

Para direcionar seu domínio:

1. Vá em **Domínios** → **DNS**
2. Configure:
   - **A**: `seu-ip-do-vps` (para VPS)
   - Ou use os nameservers do Hostinger (para cPanel)

---

## Teste Final

1. Acesse: `https://compracertaimoveis.net.br/admin`
2. Login: `imoveis2026`
3. Teste criar um lembrete

---

## Problemas Comuns

### Erro 500
```bash
# Ver logs
sudo journalctl -u imoveis -f
```

### Pasta não encontrada
```bash
# Verificar estrutura
ls -la /var/www/imoveis/
```

### Banco não criado
```bash
cd /var/www/imoveis
source venv/bin/activate
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```