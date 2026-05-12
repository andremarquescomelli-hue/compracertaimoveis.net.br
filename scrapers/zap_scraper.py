import requests
from bs4 import BeautifulSoup
import time

def scrape_zap(cidade, tipo='venda', filtros=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    tipo_transacao = 'venda' if tipo == 'venda' else 'aluguel'
    
    api_url = (
        f'https://gateway-api.zapimoveis.com/api/v2/listings'
        f'?business={tipo_transacao}'
        f'&city={cidade}'
        f'&unitTypes=Apartamento,Casa'
        f'&size=20'
    )
    
    anuncios = []
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            listings = data.get('listings', [])
            
            for item in listings:
                address = item.get('address', {})
                pricing = item.get('pricing', {})
                photos = item.get('photos', [])
                foto_url = photos[0].get('url', '') if photos else ''
                
                anuncio = {
                    'portal': 'Zap Imóveis',
                    'titulo': item.get('title', '') or f"Imóvel em {address.get('city', cidade)}",
                    'preco': f"R$ {pricing.get('price', 0):,.2f}" if pricing.get('price') else '',
                    'endereco': f"{address.get('street', '')}, {address.get('neighborhood', '')} - {address.get('city', '')}",
                    'area': f"{item.get('unitSize', '')} m²" if item.get('unitSize') else '',
                    'quartos': f"{item.get('bedrooms', '')}" if item.get('bedrooms') else '',
                    'telefone': '',
                    'url': item.get('listingUrl', ''),
                    'contato_nome': item.get('contact', {}).get('name', ''),
                    'foto_url': foto_url
                }
                anuncios.append(anuncio)
        else:
            url_fallback = f'https://www.zapimoveis.com.br/venda/{cidade.lower().replace(" ", "-")}/'
            response = requests.get(url_fallback, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                cards = soup.select('.js-card-property')
                for card in cards[:20]:
                    titulo_el = card.select_one('.card-property__heading-link')
                    preco_el = card.select_one('.card-property__price')
                    endereco_el = card.select_one('.card-property__address')
                    img_el = card.select_one('img')
                    
                    foto_url = ''
                    if img_el:
                        foto_url = img_el.get('src', '') or img_el.get('data-src', '')
                    
                    if titulo_el:
                        anuncio = {
                            'portal': 'Zap Imóveis',
                            'titulo': titulo_el.get_text(strip=True),
                            'preco': preco_el.get_text(strip=True) if preco_el else '',
                            'endereco': endereco_el.get_text(strip=True) if endereco_el else cidade,
                            'telefone': '',
                            'url': titulo_el.get('href', ''),
                            'contato_nome': '',
                            'foto_url': foto_url
                        }
                        anuncios.append(anuncio)
        
        time.sleep(2)
        
    except requests.RequestException as e:
        print(f"Erro ao acessar Zap Imóveis: {e}")
    
    return anuncios
