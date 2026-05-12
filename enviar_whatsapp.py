"""
Script para enviar lembrete automático no WhatsApp
Clica automaticamente no botão de enviar após abrir o WhatsApp
"""
import os
import sys
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def enviar_lembrete_automatico(titulo, data, hora, cliente, telefone, imovel, local, obs):
    """Abre WhatsApp e clica em enviar automaticamente"""
    try:
        import pyautogui
        
        # Mensagem formatada
        texto = f"""🔔 *LEMBRETE DE VISITA - Compra Certa Imóveis*

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA:* {data} às {hora}
📍 *LOCAL:* {local or 'A combinar'}

🏠 *IMÓVEL:*
{imovel or 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {cliente or 'Não informado'}
Telefone: {telefone or 'Não informado'}

📝 *OBSERVAÇÕES:*
{obs or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *NÃO ESQUEÇA DA VISITA!*

Obrigado pela atenção!
Compra Certa Imóveis
(18) 99762-8360"""
        
        # Abre WhatsApp Web com a mensagem
        url = f"https://web.whatsapp.com/send?phone=5518997628360&text={__import__('urllib.parse').quote(texto)}"
        
        print(f"🔄 Abrindo WhatsApp Web...")
        webbrowser.open(url)
        
        # Espera o WhatsApp abrir
        print(f"⏳ Aguardando WhatsApp carregar...")
        time.sleep(8)
        
        # Clica no botão de enviar
        print(f"🖱️ Clicando no botão Enviar...")
        pyautogui.click(x=800, y=700)  # Posição aproximada do botão Enviar
        time.sleep(1)
        
        print(f"✅ Lembrete enviado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")
        return False

def main():
    # Teste com dados fictícios
    print("🧪 Testando envio automático de lembrete...\n")
    
    enviar_lembrete_automatico(
        titulo="Visitar imóvel",
        data="25/05/2026",
        hora="14:00",
        cliente="João Silva",
        telefone="(18) 99999-9999",
        imovel="Casa 3 quartos centro",
        local="Rua X, Centro - Assis",
        obs="Cliente muito interessado"
    )

if __name__ == '__main__':
    main()
