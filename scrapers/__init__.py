from scrapers.olx_scraper import scrape_olx
from scrapers.zap_scraper import scrape_zap
from scrapers.mercadolivre_scraper import scrape_mercado_livre
from scrapers.enriquecedor import sugerir_telefones, buscar_whatsapp, extrair_telefones_texto

def buscar_imoveis(portal, cidade, tipo='venda', filtros=None):
    if portal == 'olx':
        return scrape_olx(cidade, tipo, filtros)
    elif portal == 'zap':
        return scrape_zap(cidade, tipo, filtros)
    elif portal == 'mercadolivre':
        return scrape_mercado_livre(cidade, tipo, filtros)
    else:
        return []

def buscar_todos_portais(cidade, tipo='venda', filtros=None):
    resultados = []
    for portal in ['olx', 'zap', 'mercadolivre']:
        try:
            imoveis = buscar_imoveis(portal, cidade, tipo, filtros)
            resultados.extend(imoveis)
        except Exception as e:
            print(f"Erro ao buscar no {portal}: {e}")
    return resultados
