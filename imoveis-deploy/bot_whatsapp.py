"""
Bot de WhatsApp para comandos do CRM
Ouvindo mensagens e executando comandos

Comandos disponíveis:
- cadastrar cliente: NOME | TELEFONE | BAIRRO
- cadastrar imovel: TITULO | ENDERECO | PRECO
- lembrete: TITULO | CLIENTE | DATA | HORA
- ver clientes
- ver imoveis
- ver lembretes
"""
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Lead, Imovel, Lembrete

# Seu número de WhatsApp (para receber confirmações)
MEU_WHATSAPP = '5518997628360'

def formatar_telefone(telefone):
    """Formata telefone para WhatsApp"""
    if not telefone:
        return ''
    tel_limpo = ''.join(filter(str.isdigit, telefone))
    if tel_limpo.startswith('0'):
        tel_limpo = '55' + tel_limpo[2:]
    elif not tel_limpo.startswith('55'):
        tel_limpo = '55' + tel_limpo
    return tel_limpo if len(tel_limpo) >= 12 else ''

def enviar_mensagem(telefone, mensagem):
    """Envia mensagem via WhatsApp"""
    try:
        import urllib.parse
        texto_encoded = urllib.parse.quote(mensagem)
        url = f"https://web.whatsapp.com/send?phone={telefone}&text={texto_encoded}"
        os.system(f'start "" "{url}"')
        time.sleep(8)
        import pyautogui
        pyautogui.press('enter')
        return True
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return False

def processar_comando(mensagem):
    """Processa comando recebido"""
    mensagem = mensagem.lower().strip()
    
    # Comando para cadastrar cliente
    if mensagem.startswith('cadastrar cliente:'):
        return cadastrar_cliente(mensagem)
    
    # Comando para cadastrar imovel
    elif mensagem.startswith('cadastrar imovel:'):
        return cadastrar_imovel(mensagem)
    
    # Comando para criar lembrete
    elif mensagem.startswith('lembrete:'):
        return criar_lembrete(mensagem)
    
    # Ver clientes
    elif mensagem == 'ver clientes':
        return ver_clientes()
    
    # Ver imoveis
    elif mensagem == 'ver imoveis':
        return ver_imoveis()
    
    # Ver lembretes
    elif mensagem == 'ver lembretes':
        return ver_lembretes()
    
    # Ajuda
    elif mensagem in ['ajuda', 'help', 'comandos']:
        return mostrar_ajuda()
    
    else:
        return "Comando não reconhecido. Digite 'ajuda' para ver os comandos disponíveis."

def cadastrar_cliente(mensagem):
    """Cadastra novo cliente"""
    try:
        # Formato: cadastrar cliente: NOME | TELEFONE | BAIRRO
        partes = mensagem.replace('cadastrar cliente:', '').strip().split('|')
        
        nome = partes[0].strip() if len(partes) > 0 else ''
        telefone = partes[1].strip() if len(partes) > 1 else ''
        bairro = partes[2].strip() if len(partes) > 2 else ''
        
        if not nome or not telefone:
            return "Formato incorreto! Use:\ncadastrar cliente: NOME | TELEFONE | BAIRRO"
        
        with app.app_context():
            lead = Lead(
                nome=nome,
                telefone=telefone,
                interesse=bairro,
                status='novo',
                origem='whatsapp'
            )
            db.session.add(lead)
            db.session.commit()
        
        return f"""✅ *CLIENTE CADASTRADO!*

Nome: {nome}
Telefone: {telefone}
Bairro: {bairro or 'Não informado'}

Cliente salvo no sistema!"""
    
    except Exception as e:
        return f"Erro ao cadastrar: {e}"

def cadastrar_imovel(mensagem):
    """Cadastra novo imovel"""
    try:
        # Formato: cadastrar imovel: TITULO | ENDERECO | PRECO
        partes = mensagem.replace('cadastrar imovel:', '').strip().split('|')
        
        titulo = partes[0].strip() if len(partes) > 0 else ''
        endereco = partes[1].strip() if len(partes) > 1 else ''
        preco = partes[2].strip() if len(partes) > 2 else ''
        
        if not titulo or not endereco:
            return "Formato incorreto! Use:\ncadastrar imovel: TITULO | ENDERECO | PRECO"
        
        with app.app_context():
            imovel = Imovel(
                titulo=titulo,
                endereco=endereco,
                preco=preco,
                status='ativo'
            )
            db.session.add(imovel)
            db.session.commit()
        
        return f"""✅ *IMÓVEL CADASTRADO!*

Título: {titulo}
Endereço: {endereco}
Preço: {preco or 'A combinar'}

Imóvel salvo no sistema!"""
    
    except Exception as e:
        return f"Erro ao cadastrar: {e}"

def criar_lembrete(mensagem):
    """Cria novo lembrete"""
    try:
        # Formato: lembrete: TITULO | CLIENTE | DATA | HORA
        partes = mensagem.replace('lembrete:', '').strip().split('|')
        
        titulo = partes[0].strip() if len(partes) > 0 else ''
        cliente = partes[1].strip() if len(partes) > 1 else ''
        data = partes[2].strip() if len(partes) > 2 else ''
        hora = partes[3].strip() if len(partes) > 3 else ''
        
        if not titulo or not data or not hora:
            return "Formato incorreto! Use:\nlembrete: TITULO | CLIENTE | DATA | HORA\nEx: lembrete: Visitar casa | João | 15/05 | 14:00"
        
        # Converte data
        data_visita = datetime.strptime(f"{data} {hora}", "%d/%m %H:%M")
        
        with app.app_context():
            lembrete = Lembrete(
                titulo=titulo,
                cliente_nome=cliente,
                corretor_nome='Andre Comelli',
                corretor_telefone='(18) 99762-8360',
                data_visita=data_visita,
                lembrado=False
            )
            db.session.add(lembrete)
            db.session.commit()
        
        return f"""✅ *LEMBRETE CRIADO!*

Título: {titulo}
Cliente: {cliente}
Data: {data} às {hora}

O sistema enviará lembretes automáticos!"""
    
    except Exception as e:
        return f"Erro ao criar lembrete: {e}"

def ver_clientes():
    """Mostra lista de clientes"""
    try:
        with app.app_context():
            clientes = Lead.query.order_by(Lead.id.desc()).limit(5).all()
            
            if not clientes:
                return "Nenhum cliente cadastrado."
            
            texto = "📋 *ÚLTIMOS CLIENTES:*\n\n"
            for c in clientes:
                texto += f"• {c.nome} - {c.telefone}\n"
            
            return texto
    
    except Exception as e:
        return f"Erro: {e}"

def ver_imoveis():
    """Mostra lista de imóveis"""
    try:
        with app.app_context():
            imoveis = Imovel.query.filter_by(status='ativo').order_by(Imovel.id.desc()).limit(5).all()
            
            if not imoveis:
                return "Nenhum imóvel cadastrado."
            
            texto = "🏠 *IMÓVEIS CADASTRADOS:*\n\n"
            for i in imoveis:
                texto += f"• {i.titulo}\n  {i.endereco}\n  {i.preco or 'Consulte'}\n\n"
            
            return texto
    
    except Exception as e:
        return f"Erro: {e}"

def ver_lembretes():
    """Mostra lista de lembretes"""
    try:
        with app.app_context():
            lembretes = Lembrete.query.filter_by(lembrado=False).order_by(Lembrete.data_visita.asc()).limit(5).all()
            
            if not lembretes:
                return "Nenhum lembrete pendente."
            
            texto = "📅 *LEMBRETES:*\n\n"
            for l in lembretes:
                texto += f"• {l.titulo}\n  Cliente: {l.cliente_nome}\n  {l.data_visita.strftime('%d/%m às %H:%M')}\n\n"
            
            return texto
    
    except Exception as e:
        return f"Erro: {e}"

def mostrar_ajuda():
    """Mostra ajuda"""
    return """🤖 *COMANDOS DO BOT:*

📝 *Cadastrar Cliente:*
cadastrar cliente: NOME | TELEFONE | BAIRRO

📝 *Cadastrar Imóvel:*
cadastrar imovel: TITULO | ENDEREÇO | PRECO

📅 *Criar Lembrete:*
lembrete: TITULO | CLIENTE | DATA | HORA
Ex: lembrete: Visitar casa | João | 15/05 | 14:00

👁️ *Ver Informações:*
ver clientes
ver imoveis
ver lembretes

Exemplo completo:
cadastrar cliente: Maria Silva | (18) 99999-8888 | Centro"""

def main():
    print("=" * 50)
    print("🤖 BOT DE COMANDOS - Compra Certa Imóveis")
    print("=" * 50)
    print()
    print("Este bot responde aos comandos via WhatsApp.")
    print()
    print("Para testar, envie uma mensagem com comando.")
    print()
    print("Exemplo de comando:")
    print("  cadastrar cliente: João Silva | (18) 99999-9999 | Centro")
    print()
    print("=" * 50)
    
    # Testa comando
    teste = input("Testar comando (ou ENTER para sair): ")
    if teste:
        resultado = processar_comando(teste)
        print()
        print("=" * 50)
        print("RESPOSTA:")
        print("=" * 50)
        print(resultado)

if __name__ == '__main__':
    main()
