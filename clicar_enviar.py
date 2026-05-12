"""
Script para clicar automaticamente no botao Enviar do WhatsApp Web
"""
import time
import pyautogui

def enviar_enter():
    """Pressiona Enter para enviar"""
    try:
        print("Pressionando Enter para enviar...")
        pyautogui.press('enter')
        print("OK - Enter pressionado!")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == '__main__':
    print("Testando clique automatico...\n")
    
    # Espera o WhatsApp abrir
    print("Aguardando WhatsApp carregar (8 segundos)...")
    time.sleep(8)
    
    # Tenta pressionar Enter
    if enviar_enter():
        print("\nMensagem enviada com Enter!")
    else:
        print("\nNao foi possivel enviar.")
