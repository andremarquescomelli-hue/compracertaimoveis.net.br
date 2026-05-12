#!/bin/bash
# Setup para Hostinger - Compra Certa Imóveis

echo "=== Setup Compra Certa Imóveis no Hostinger ==="

# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar banco de dados
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Banco criado com sucesso!')"

# 4. Criar diretório de uploads
mkdir -p static/uploads

echo ""
echo "=== Setup concluído! ==="
echo "Para iniciar: gunicorn app:app -b 0.0.0.0:8000"