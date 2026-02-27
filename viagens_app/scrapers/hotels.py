# scrapers/hotels.py
import time
import pandas as pd
from bs4 import BeautifulSoup

# --- 1. LISTA EXAUSTIVA DE SITES DE HOSPEDAGEM ---
SITES_HOSPEDAGEM = {
    "Booking": "https://www.booking.com/searchresults.pt-br.html?ss={destino}&checkin={data}",
    "Airbnb": "https://www.airbnb.com.br/s/{destino}/homes?checkin={data}",
    "Hoteis.com": "https://www.hoteis.com/Hotel-Search?destination={destino}&startDate={data}",
    "Trivago": "https://www.trivago.com.br/pt-BR/srl/hotéis-{destino}?search=200-{destino};dr-{data}",
}

# --- 2. LÓGICA DE EXTRAÇÃO ESPECÍFICA (EXEMPLO BOOKING) ---
def extrair_booking(soup, url, destino, data_checkin):
    hoteis_encontrados = []
    
    # O Booking usa o atributo 'data-testid' que é muito mais estável que classes CSS aleatórias
    cards = soup.find_all('div', attrs={'data-testid': 'property-card'})
    
    for card in cards:
        try:
            # 1. Título / Nome
            titulo_tag = card.find('div', attrs={'data-testid': 'title'})
            titulo = titulo_tag.text.strip() if titulo_tag else "Sem nome"
            
            # 2. Preço
            preco_tag = card.find('span', attrs={'data-testid': 'price-and-discounted-price'})
            preco = preco_tag.text.strip() if preco_tag else "Ver no site"
            
            # 3. Avaliação / Estrelas
            nota_tag = card.find('div', attrs={'data-testid': 'review-score'})
            nota = nota_tag.text.strip().split()[0] if nota_tag else "Sem avaliação"
            
            # 4. Tipo de Estadia (Dedução baseada no título)
            tipo_estadia = "Outros"
            titulo_lower = titulo.lower()
            if "hotel" in titulo_lower: tipo_estadia = "Hotel"
            elif "apartament" in titulo_lower or "flat" in titulo_lower: tipo_estadia = "Apartamento"
            elif "casa" in titulo_lower or "home" in titulo_lower: tipo_estadia = "Casa"
            elif "pousada" in titulo_lower: tipo_estadia = "Pousada"
            elif "resort" in titulo_lower: tipo_estadia = "Resort"
            elif "sítio" in titulo_lower or "chácara" in titulo_lower: tipo_estadia = "Sítio/Chácara"
            
            hoteis_encontrados.append({
                "Site": "Booking",
                "Tipo": tipo_estadia,
                "Nome": titulo,
                "Destino": destino,
                "Avaliação": nota,
                "Preço": preco,
                "Link Original": url
            })
        except Exception as e:
            continue
            
    return hoteis_encontrados

# --- 3. MOTOR PRINCIPAL DE HOSPEDAGEM ---
def buscar_hoteis(destino, data_checkin, driver):
    resultados_totais = []
    
    for nome_site, url_base in SITES_HOSPEDAGEM.items():
        print(f"A investigar alojamentos em: {nome_site}...")
        
        try:
            # Monta o link
            url = url_base.format(destino=destino, data=data_checkin)
            driver.get(url)
            time.sleep(8) # Tempo para imagens e preços carregarem
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Redireciona para o extrator correto
            if nome_site == "Booking":
                dados_site = extrair_booking(soup, url, destino, data_checkin)
                resultados_totais.extend(dados_site)
            else:
                # Para Airbnb e outros, enquanto não mapeamos as classes CSS,
                # devolvemos o link direto para o utilizador.
                resultados_totais.append({
                    "Site": nome_site,
                    "Tipo": "Vários (Ver Link)",
                    "Nome": f"Pesquisa geral em {nome_site}",
                    "Destino": destino,
                    "Avaliação": "-",
                    "Preço": "Abrir para ver",
                    "Link Original": url
                })
                
        except Exception as e:
            print(f"Erro no site {nome_site}: {e}")
            
    return pd.DataFrame(resultados_totais)