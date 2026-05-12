# Deploy no PythonAnywhere - Passo a Passo

## 1. Criar Conta

1. Acesse: **https://www.pythonanywhere.com**
2. Clique em **"Sign up"** (plano gratuito: Beginner)
3. Escolha um username (ex: `seunome`)
4. Confirme o email

## 2. Fazer Upload dos Arquivos

### Opção A: Via Painel Web (mais fácil)

1. No painel, clique em **"Files"**
2. Clique em **"Upload a file"**
3. Envie TODOS os arquivos do projeto `imoveis-crm`:
   - `app.py`
   - `models.py`
   - `wsgi.py`
   - `requirements.txt`
4. Envie a pasta `scrapers/` inteira (upload de pasta)
5. Envie a pasta `static/` inteira
6. Envie a pasta `templates/` inteira

### Opção B: Via Git (mais organizado)

1. No painel, abra o **"Consoles" > "Bash"**
2. Rode:
```bash
git clone https://github.com/SEU_USUARIO/imoveis-crm.git
```

## 3. Instalar Dependências

1. No painel, vá em **"Consoles" > "Bash"**
2. Rode:
```bash
cd imoveis-crm
pip3 install --user -r requirements.txt
```

## 4. Configurar Web App

1. Vá na aba **"Web"**
2. Clique em **"Add a new web app"**
3. Escolha **"Manual configuration"**
4. Selecione **Python 3.10** (ou mais recente disponível)

## 5. Configurar o WSGI

1. Na página de configuração do web app, clique no link **"WSGI configuration file"**
2. Apague TODO o conteúdo
3. Cole o conteúdo do seu `wsgi.py`:

```python
import sys
import os

path = '/home/SEU_USERNAME/imoveis-crm'
if path not in sys.path:
    sys.path.append(path)

os.environ['FLASK_APP'] = 'app.py'

from app import app as application
```

⚠️ **IMPORTANTE**: Troque `SEU_USERNAME` pelo seu username do PythonAnywhere!

## 6. Configurar Caminho da Aplicação

1. Volte para a aba **"Web"**
2. Em **"Code"**, preencha:
   - **Source code**: `/home/SEU_USERNAME/imoveis-crm`
   - **Working directory**: `/home/SEU_USERNAME/imoveis-crm`
3. Em **"Virtualenv"**, deixe em branco (não precisa)

## 7. Inicializar o Banco de Dados

1. No **"Bash console"**, rode:
```bash
cd /home/SEU_USERNAME/imoveis-crm
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Banco criado!')"
```

## 8. Recarregar o App

1. Na aba **"Web"**, clique no botão verde **"Reload"**
2. Aguarde alguns segundos

## 9. Acessar

Seu app estará disponível em:

**https://SEU_USERNAME.pythonanywhere.com**

## Atualizações

Para atualizar o código:

1. Faça upload dos arquivos alterados (ou git pull)
2. Clique em **"Reload"** na aba Web

## Limitações do Plano Gratuito

| Recurso | Limite |
|---------|--------|
| App offline | 1h/dia |
| Tráfego | 512 MB/dia |
| CPU | Limitado |
| Banco | 512 MB |
| Domínio | SEU_USERNAME.pythonanywhere.com |

## Segurança

Depois de confirmar que funciona:

1. Edite `app.py` e mude a `SECRET_KEY`
2. No painel Web > Security, ative **HTTPS** (já ativado por padrão)
3. Considere adicionar autenticação de login para proteger o CRM
