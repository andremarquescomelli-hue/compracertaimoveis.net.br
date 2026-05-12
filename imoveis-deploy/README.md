# Imóveis CRM - Sistema para Corretores

Sistema web completo para corretores de imóveis gerenciarem leads, consultarem matrículas e buscarem imóveis nos principais portais.

## Funcionalidades

### CRM de Leads
- Cadastro completo de leads (nome, telefone, email, origem, interesse)
- Status pipeline: Novo, Em Contato, Visita Agendada, Proposta, Negociação, Fechado, Perdido
- Registro de interações (ligação, WhatsApp, email, visita, reunião)
- Histórico completo de cada lead
- Busca rápida por nome, telefone ou email

### Gerenciador de Matrículas
- Registro de consultas de matrícula de imóveis
- Dados do proprietário (quando disponíveis em cartório)
- Controle de situação: Pendente, Em Andamento, Concluída, Negado
- Follow-up com data de retorno
- Armazenamento de documentos e links

### Scrapers de Portais
- Busca de imóveis em OLX, Zap Imóveis e Mercado Livre
- Captura de título, preço, endereço, telefone e URL
- Conversão de anúncios em leads
- Histórico de anúncios capturados

## Instalação

```bash
cd imoveis-crm

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar a aplicação
python app.py
```

Acesse: `http://localhost:5000`

## Estrutura

```
imoveis-crm/
├── app.py                 # Aplicação Flask principal
├── models.py              # Modelos do banco de dados
├── requirements.txt       # Dependências
├── scrapers/
│   ├── __init__.py
│   ├── olx_scraper.py
│   ├── zap_scraper.py
│   └── mercadolivre_scraper.py
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── leads.html
    ├── lead_form.html
    ├── lead_detalhes.html
    ├── matriculas.html
    ├── matricula_form.html
    ├── scrapers.html
    ├── scrapers_resultado.html
    └── anuncios.html
```

## Banco de Dados

SQLite com as seguintes tabelas:
- `lead` - Cadastro de leads
- `interacao` - Histórico de interações
- `matricula` - Consultas de matrícula
- `anuncio_portal` - Anúncios capturados dos portais

## Uso

1. **Dashboard**: Visão geral com estatísticas e ações rápidas
2. **Leads**: Cadastre e gerencie seus contatos
3. **Matrículas**: Acompanhe consultas de cartório
4. **Portais**: Busque imóveis e converta em leads

## Deploy Gratuito

Para hospedar online gratuitamente, veja **DEPLOY_PYTHONANYWHERE.md**

Resumo rápido:
1. Crie conta em pythonanywhere.com
2. Faça upload dos arquivos
3. Instale dependências: `pip3 install --user -r requirements.txt`
4. Configure o Web App (aba Web)
5. Clique em Reload

Seu site: **https://SEU_USERNAME.pythonanywhere.com**

## Notas

- Os scrapers podem ter limitações dependendo da disponibilidade dos portais
- Sempre respeite os termos de uso de cada site
- Dados de matrícula devem ser obtidos legalmente via cartório
