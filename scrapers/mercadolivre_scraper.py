import requests
from bs4 import BeautifulSoup
import time
import json

def scrape_mercado_livre(cidade, tipo='venda', filtros=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    categoria = 'imoveis' if tipo == 'venda' else 'imoveis-aluguel'
    url = f'https://imoveis.mercadolivre.com.br/{cidade}/'
    
    anuncios = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cards = soup.select('.ui-search-result__content')
        
        for card in cards:
            titulo_el = card.select_one('.ui-search-item__title')
            preco_el = card.select_one('.ui-search-price__part')
            endereco_el = card.select_one('.ui-search-card__location')
            img_el = card.select_one('img')
            
            foto_url = ''
            if img_el:
                foto_url = img_el.get('src', '') or img_el.get('data-src', '')
            
            if titulo_el:
                link_el = titulo_el.select_one('a')
                url = link_el.get('href', '') if link_el else ''
                
                telefone_el = card.select_one('[class*="phone"]')
                
                anuncio = {
                    'portal': 'Mercado Livre',
                    'titulo': titulo_el.get_text(strip=True),
                    'preco': preco_el.get_text(strip=True) if preco_el else '',
                    'endereco': endereco_el.get_text(strip=True) if endereco_el else cidade,
                    'telefone': telefone_el.get_text(strip=True) if telefone_el else '',
                    'url': url.split('?')[0] if url else '',
                    'contato_nome': '',
                    'foto_url': foto_url
                }
                anuncios.append(anuncio)
                
                if len(anuncios) >= 20:
                    break
        
        time.sleep(2)
        
    except requests.RequestException as e:
        print(f"Erro ao acessar Mercado Livre: {e}")
    
    return anuncios
