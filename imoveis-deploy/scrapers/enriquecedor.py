import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def buscar_nome_jusbrasil(nome):
    resultados = []
    try:
        url = f"https://www.jusbrasil.com.br/busca?q={urllib.parse.quote(nome)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.select('a[href*="/diario/"], a[href*="/dou/"], a[href*="/processo/"]')
        for link in links[:10]:
            titulo = link.get_text(strip=True)
            href = link.get('href', '')
            if titulo and len(titulo) > 10:
                resultados.append({
                    'fonte': 'Jusbrasil',
                    'titulo': titulo[:200],
                    'url': href,
                    'tipo': 'publicacao'
                })
    except:
        pass
    return resultados

def buscar_nome_google(nome, cidade='Assis SP'):
    resultados = []
    try:
        query = f"{nome} {cidade} contato telefone"
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        snippets = soup.select('div[style*="-webkit-line-clamp"], span[class*="w8qArf"], .VwiC3b')
        for snip in snippets[:5]:
            text = snip.get_text(strip=True)
            if text and len(text) > 15:
                telefones = re.findall(r'\(?\d{2}\)?\s?\d{4,5}[-]?\d{4}', text)
                resultados.append({
                    'fonte': 'Google',
                    'titulo': text[:200],
                    'telefones_encontrados': telefones,
                    'tipo': 'snippet'
                })
    except:
        pass
    return resultados

def buscar_whatsapp(telefone):
    numeros = re.sub(r'\D', '', telefone)
    if len(numeros) == 11:
        numeros = '55' + numeros
    elif len(numeros) == 10:
        numeros = '55' + numeros[:2] + '9' + numeros[2:]
    
    return f"https://api.whatsapp.com/send?phone={numeros}&text=Olá, sou corretor de imóveis em Assis-SP e gostaria de conversar sobre seu imóvel."

def sugerir_telefones(nome, cidade='Assis'):
    sugestoes = []
    
    google = buscar_nome_google(nome, cidade)
    sugestoes.extend(google)
    
    jusbrasil = buscar_nome_jusbrasil(nome)
    sugestoes.extend(jusbrasil)
    
    return sugestoes

def extrair_telefones_texto(texto):
    return re.findall(r'\(?\d{2}\)?\s?\d{4,5}[-]?\d{4}', texto)
