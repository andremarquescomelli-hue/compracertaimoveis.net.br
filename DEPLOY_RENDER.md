# Deploy Gratuito no Render.com - Passo a Passo

## 1. Criar Conta no Render

1. Acesse: **https://render.com**
2. Clique em **"Get Started for Free"**
3. Cadastre com GitHub (recomendado) ou email

## 2. Colocar Código no GitHub

### Se não tem GitHub:
1. Acesse: **https://github.com** → Sign up
2. Crie um repositório novo: `imoveis-crm`
3. Faça upload dos arquivos do projeto

### Se já tem GitHub:
1. Instale GitHub Desktop ou use o site
2. Crie repo `imoveis-crm`
3. Push do projeto

## 3. Criar Web Service no Render

1. No painel do Render, clique em **"New +"** → **"Web Service"**
2. Conecte seu GitHub e selecione `imoveis-crm`
3. Preencha:
   - **Name**: `imoveis-crm`
   - **Region**: Virginia (mais perto do Brasil)
   - **Branch**: `main`
   - **Root Directory**: Deixe em branco
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Clique em **"Advanced"** e adicione:
   - **Environment Variable**:
     - `SECRET_KEY`: digite qualquer coisa secreta
5. Clique em **"Create Web Service"**

## 4. Adicionar Banco de Dados (PostgreSQL)

Render free tier apaga SQLite a cada deploy. Use PostgreSQL grátis:

1. No painel Render, **"New +"** → **"PostgreSQL"**
2. Preencha:
   - **Name**: `imoveis-db`
   - **Region**: Virginia (mesmo do web service)
3. Clique em **"Create Database"**
4. Copie a **Internal Database URL**

## 5. Conectar Banco ao Web Service

1. Volte ao **Web Service** → aba **Environment**
2. Adicione:
   - **Key**: `DATABASE_URL`
   - **Value**: Cole a Internal Database URL
3. Clique em **"Save Changes"**
4. O Render vai fazer deploy automático

## 6. Inicializar Banco

1. No painel do Web Service → aba **Shell**
2. Rode:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('OK')"
```

## 7. Acessar

Seu site: **https://imoveis-crm.onrender.com**

Compartilhe: **https://imoveis-crm.onrender.com/imoveis/1/compartilhar**

## Limitações do Free Tier

| Recurso | Limite |
|---------|--------|
| RAM | 512 MB |
| CPU | 0.1 vCPU |
| Banco | 1 GB |
| App dorme | Após 15min sem uso (acorda em ~30s) |
| Tráfego | 100 GB/mês |

## Atualizar o Código

1. Faça push para o GitHub
2. Render detecta e faz deploy automático
3. Aguarde 2-3 minutos
