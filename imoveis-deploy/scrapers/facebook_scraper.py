import urllib.parse

def get_facebook_marketplace_urls(cidade='Assis-SP'):
    cidade_slug = cidade.lower().replace(' ', '-').replace('-', '')
    
    urls = {
        'imoveis_venda': f'https://www.facebook.com/marketplace/{cidade_slug}/property-sales',
        'imoveis_aluguel': f'https://www.facebook.com/marketplace/{cidade_slug}/property-rentals',
        'grupos_imoveis': f'https://www.facebook.com/search/groups?q=imoveis%20{urllib.parse.quote(cidade)}',
        'busca_direto': f'https://www.facebook.com/search/posts?q=imovel%20direto%20proprietario%20{urllib.parse.quote(cidade)}',
    }
    return urls

def get_facebook_search_url(cidade='Assis-SP', tipo='venda'):
    cidade_slug = cidade.lower().replace(' ', '-').replace('-', '')
    if tipo == 'venda':
        return f'https://www.facebook.com/marketplace/{cidade_slug}/property-sales'
    return f'https://www.facebook.com/marketplace/{cidade_slug}/property-rentals'
