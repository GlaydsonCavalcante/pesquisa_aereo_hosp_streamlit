# scrapers/flights.py
import time
import pandas as pd
from bs4 import BeautifulSoup

SITES_VIAGENS = {
    "R$ (Dinheiro)": {
        "Google Flights": "https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data}",
        "MaxMilhas": "https://www.maxmilhas.com.br/busca-passagens-aereas/sow/{origem}/{destino}/{data}"
    },
    "Milhas / Pontos": {
        "Azul Fidelidade": "https://www.voeazul.com.br/br/pt/home",
        "Livelo": "https://www.livelo.com.br/use-seus-pontos/viagens",
        "Smiles (Gol)": "https://www.smiles.com.br/passagens-aereas/{origem}/{destino}/{data}"
    }
}

def extrair_google_flights(soup, url, origem, destino, data_viagem):
    voos_encontrados = []
    itens_voo = soup.find_all('li', class_='pIav2d') 
    
    for item in itens_voo:
        try:
            cia_aerea_tag = item.find('div', class_='sSHqwe')
            preco_tag = item.find('div', class_='YMlKvd')
            
            # Tenta encontrar a informação de paradas/escalas (o Google Flights usa classes variadas, procuramos texto)
            escalas = "1+ Paradas"
            texto_item = item.text.lower()
            if "direto" in texto_item or "nonstop" in texto_item:
                escalas = "Direto"
            
            if cia_aerea_tag and preco_tag:
                voos_encontrados.append({
                    "Site": "Google Flights",
                    "Companhia": cia_aerea_tag.text.strip(),
                    "Escalas": escalas,
                    "Origem": origem,
                    "Destino": destino,
                    "Data": data_viagem,
                    "Preço/Pontos": preco_tag.text.strip(),
                    "Link Original": url
                })
        except:
            continue
            
    return voos_encontrados

def buscar_voos(origem, destino, data_viagem, tipo_pagamento, adultos, criancas, driver):
    resultados_totais = []
    data_short = data_viagem.replace("-", "")[2:] 
    sites_alvo = SITES_VIAGENS.get(tipo_pagamento, {})
    
    for nome_site, url_base in sites_alvo.items():
        print(f"A pesquisar em: {nome_site}...")
        try:
            url = url_base.format(origem=origem, destino=destino, data=data_viagem, data_short=data_short)
            # Dica: Muitos sites aceitam o número de passageiros na URL. Para simplificar esta etapa, 
            # o robô fará a busca padrão, e indicaremos as quantidades na interface de análise.
            
            driver.get(url)
            time.sleep(10) 
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            if nome_site == "Google Flights":
                dados_site = extrair_google_flights(soup, url, origem, destino, data_viagem)
                resultados_totais.extend(dados_site)
            else:
                resultados_totais.append({
                    "Site": nome_site,
                    "Companhia": "Várias",
                    "Escalas": "-",
                    "Origem": origem,
                    "Destino": destino,
                    "Data": data_viagem,
                    "Preço/Pontos": "Verificar no site",
                    "Link Original": url
                })
        except Exception as e:
            continue

    return pd.DataFrame(resultados_totais)