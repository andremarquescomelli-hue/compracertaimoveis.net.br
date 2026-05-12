# Compra Certa Imóveis - Deploy no Hostinger

## Arquivos Prepared

- `imoveis-deploy.zip` - Todos os arquivos do projeto
- `setup_hostinger.sh` - Script de instalação
- `DEPLOY_HOSTINGER.md` - Guia completo

---

## Passo a Passo

### 1. Upload no Hostinger

1. Acesse https://hpanel.hostinger.com
2. Vá em **Hospedagem** → **Gerenciador de Arquivos**
3. Navegue até `public_html`
4. Clique em **Upload** → selecione `imoveis-deploy.zip`
5. Após upload, clique com botão direito → **Extrair**

### 2. Configurar Python App

1. No cPanel, procure **"Setup Python App"** ou **"Python App"**
2. Clique em **"Create Application"**
3. Configure:
   - **Application Directory**: `public_html/imoveis`
   - **Python Version**: `3.11`
   - **Application startup file**: `app.py`
   - **Application command**: `gunicorn app:app`

4. Clique **Create**

### 3. Instalar Dependências

No painel Python App, clique em **"Run pip install"**:
```
-r requirements.txt
```

Ou pelo terminal SSH:
```bash
cd imoveis
pip install -r requirements.txt
```

### 4. Inicializar Banco

```bash
cd imoveis
source venv/bin/activate  # se criou venv
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 5. Acessar

- **Admin**: https://compracertaimoveis.net.br/imoveis/admin
- **Login**: `imoveis2026`

---

## Se usar VPS (SSH)

```bash
# Upload do zip
scp imoveis-deploy.zip usuario@seu-ip:/var/www/

# SSH
ssh usuario@seu-ip

# Extrair e configurar
cd /var/www
unzip imoveis-deploy.zip
cd imoveis
chmod +x setup_hostinger.sh
./setup_hostinger.sh

# Iniciar
gunicorn app:app -b 0.0.0.0:8000
```

---

## Problemas?

### Erro 500
```bash
# Ver logs
tail -f /var/log/nginx/error.log
```

### Banco não funciona
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Pasta não encontrada
Verifique se extraiu corretamente:
```bash
ls -la /var/www/imoveis/
```

---

## Arquivos Incluídos

- `app.py` - Flask application
- `models.py` - Modelos do banco
- `templates/` - HTML templates
- `static/` - CSS, JS, imagens, uploads
- `scrapers/` - Scripts de busca
- `requirements.txt` - Dependências Python
- `imoveis_crm.db` - Banco SQLite
- `notificador.py` - Notificações WhatsApp
- `bot_whatsapp.py` - Bot de comandos
- `clicar_enviar.py` - Auto-envio WhatsApp