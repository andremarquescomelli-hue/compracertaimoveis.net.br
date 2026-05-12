import requests
from bs4 import BeautifulSoup
import time
import json

def scrape_olx(cidade, tipo='venda', filtros=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    cidade_slug = cidade.lower().replace(' ', '-')
    if tipo == 'venda':
        url = f'https://www.olx.com.br/imoveis/brasil/{cidade_slug}'
    else:
        url = f'https://www.olx.com.br/imoveis/aluguel/brasil/{cidade_slug}'
    
    if filtros:
        if filtros.get('tipo_imovel'):
            url += f'/{filtros["tipo_imovel"]}'
    
    anuncios = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cards = soup.select('a[href*="/imv-"], a[href*="/ap-"]')
        
        for card in cards:
            if not card.find_parent('script') and not card.find_parent('style'):
                titulo_el = card.select_one('span[class*="title"]')
                preco_el = card.select_one('span[class*="price"]')
                loc_el = card.select_one('span[class*="location"]')
                img_el = card.select_one('img')
                
                foto_url = ''
                if img_el:
                    foto_url = img_el.get('src', '') or img_el.get('data-src', '')
                
                if titulo_el:
                    anuncio = {
                        'portal': 'OLX',
                        'titulo': titulo_el.get_text(strip=True),
                        'preco': preco_el.get_text(strip=True) if preco_el else '',
                        'endereco': loc_el.get_text(strip=True) if loc_el else cidade,
                        'telefone': '',
                        'url': card.get('href', '').split('?')[0] if card.get('href') else '',
                        'contato_nome': '',
                        'foto_url': foto_url
                    }
                    anuncios.append(anuncio)
                    
                    if len(anuncios) >= 20:
                        break
        
        time.sleep(2)
        
    except requests.RequestException as e:
        print(f"Erro ao acessar OLX: {e}")
    
    return anuncios
