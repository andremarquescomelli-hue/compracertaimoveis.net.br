"""
Notificador automatico - Roda em segundo plano
Envia WhatsApp 3 horas antes da visita para cliente E corretor
Execute: python notificador.py
"""
import os
import sys
import time
import subprocess
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Lembrete

def formatar_telefone(telefone):
    """Formata telefone para WhatsApp"""
    if not telefone:
        return ''
    tel_limpo = ''.join(filter(str.isdigit, telefone))
    if tel_limpo.startswith('0'):
        tel_limpo = '55' + tel_limpo[2:]
    elif not tel_limpo.startswith('55'):
        tel_limpo = '55' + tel_limpo
    if len(tel_limpo) >= 12:
        return tel_limpo
    return ''

def enviar_whatsapp(telefone, texto):
    """Abre WhatsApp e envia mensagem"""
    if not telefone:
        return False
    try:
        import urllib.parse
        texto_encoded = urllib.parse.quote(texto)
        url = f"https://web.whatsapp.com/send?phone={telefone}&text={texto_encoded}"
        subprocess.Popen(['start', '', url], shell=True)
        time.sleep(8)
        subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        return True
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return False

def criar_mensagem(lembrete, tipo="lembrete"):
    """Cria mensagem formatada"""
    data_formatada = lembrete.data_visita.strftime('%d/%m/%Y às %H:%M')
    imovel_endereco = ''
    if lembrete.imovel:
        imovel_endereco = f"{lembrete.imovel.endereco}, {lembrete.imovel.bairro} - {lembrete.imovel.cidade}"
    
    if tipo == "aviso":
        titulo_msg = "⏰ LEMBRETE IMPORTANTE - Compra Certa Imóveis"
    else:
        titulo_msg = "🔔 LEMBRETE DE VISITA - Compra Certa Imóveis"
    
    return f"""{titulo_msg}

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA:* {data_formatada}
📍 *LOCAL:* {lembrete.local or imovel_endereco or 'A combinar'}

🏠 *IMÓVEL:*
{lembrete.imovel.titulo if lembrete.imovel else 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {lembrete.cliente_nome or 'Não informado'}
Telefone: {lembrete.cliente_telefone or 'Não informado'}

👔 *DADOS DO CORRETOR:*
Nome: {lembrete.corretor_nome or 'Andre Comelli'}
Telefone: {lembrete.corretor_telefone or '(18) 99762-8360'}

📝 *OBSERVAÇÕES:*
{lembrete.observacoes or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *NÃO ESQUEÇA DA VISITA!*

Obrigado pela atenção!
Compra Certa Imóveis
(18) 99762-8360"""

def verificar_lembretes():
    """Verifica lembretes e envia notificacoes"""
    with app.app_context():
        agora = datetime.now()
        
        # 3 horas em segundos = 10800
        tempo_aviso = 3 * 3600  # 3 horas
        
        lembretes = Lembrete.query.all()
        
        for lembrete in lembretes:
            if lembrete.lembrado:
                continue
            
            diff_segundos = (lembrete.data_visita - agora).total_seconds()
            
            # Se faltam menos de 3 horas E mais de 0 (visita ainda não aconteceu)
            if 0 < diff_segundos <= 10800:
                print(f"⏰ Enviando aviso: {lembrete.titulo} (faltam {diff_segundos/3600:.1f}h)")
                
                mensagem = criar_mensagem(lembrete, "aviso")
                
                # Envia para cliente
                tel_cliente = formatar_telefone(lembrete.cliente_telefone)
                if tel_cliente:
                    threading.Thread(target=enviar_whatsapp, args=(tel_cliente, mensagem)).start()
                    time.sleep(3)
                
                # Envia para corretor
                tel_corretor = formatar_telefone(lembrete.corretor_telefone)
                if tel_corretor:
                    threading.Thread(target=enviar_whatsapp, args=(tel_corretor, mensagem)).start()
                
                # Marca como lembrado
                lembrete.lembrado = True
                db.session.commit()
                
                print(f"✅ Aviso enviado para: {lembrete.cliente_nome or 'Cliente'} e {lembrete.corretor_nome or 'Corretor'}")

def main():
    print("=" * 50)
    print("🔔 NOTIFICADOR DE VISITAS - Compra Certa Imóveis")
    print("=" * 50)
    print()
    print("Este script ira enviar WhatsApp automaticamente")
    print("3 horas antes de cada visita cadastrada.")
    print()
    print("Enviando para CLIENTE e CORRETOR.")
    print()
    print("Pressione Ctrl+C para parar.")
    print("=" * 50)
    print()
    
    # Verifica imediatamente
    print(f"[{datetime.now().strftime('%H:%M')}] Verificando lembretes...")
    verificar_lembretes()
    print(f"[{datetime.now().strftime('%H:%M')}] Verificacao concluida.")
    print()
    
    # Loop infinito - verifica a cada 5 minutos
    while True:
        time.sleep(300)  # 5 minutos
        print(f"[{datetime.now().strftime('%H:%M')}] Verificando lembretes...")
        verificar_lembretes()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("=" * 50)
        print("👋 Notificador encerrado!")
        print("=" * 50)
