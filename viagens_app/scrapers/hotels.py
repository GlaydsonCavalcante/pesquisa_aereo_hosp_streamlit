# scrapers/hotels.py
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1. URLs PARAMETRIZADAS CORRETAMENTE
SITES_HOSPEDAGEM = {
    "Booking": "https://www.booking.com/searchresults.pt-br.html?ss={destino}&checkin={checkin}&checkout={checkout}&group_adults={adultos}&no_rooms={quartos}&group_children={criancas}",
    "Airbnb": "https://www.airbnb.com.br/s/{destino}/homes?checkin={checkin}&checkout={checkout}&adults={adultos}",
}

def extrair_booking(soup, url, destino):
    hoteis_encontrados = []
    cards = soup.find_all('div', attrs={'data-testid': 'property-card'})
    
    for card in cards:
        try:
            titulo_tag = card.find('div', attrs={'data-testid': 'title'})
            titulo = titulo_tag.text.strip() if titulo_tag else "Sem nome"
            
            preco_tag = card.find('span', attrs={'data-testid': 'price-and-discounted-price'})
            preco = preco_tag.text.strip() if preco_tag else "Esgotado / Ver site"
            
            nota_tag = card.find('div', attrs={'data-testid': 'review-score'})
            # Limpeza do texto sujo (ex: "Com 8,5" vira "8,5")
            nota = nota_tag.text.strip().split()[-1] if nota_tag else "Sem avaliação"
            
            tipo_estadia = "Outros"
            t_lower = titulo.lower()
            if "hotel" in t_lower: tipo_estadia = "Hotel"
            elif "apartament" in t_lower or "flat" in t_lower or "studio" in t_lower: tipo_estadia = "Apartamento"
            elif "casa" in t_lower or "home" in t_lower or "villa" in t_lower: tipo_estadia = "Casa"
            elif "pousada" in t_lower: tipo_estadia = "Pousada"
            elif "resort" in t_lower: tipo_estadia = "Resort"
            
            hoteis_encontrados.append({
                "Site": "Booking",
                "Tipo": tipo_estadia,
                "Nome": titulo,
                "Destino": destino,
                "Avaliação": nota,
                "Preço Total": preco,
                "Link Original": url
            })
        except:
            continue
            
    return hoteis_encontrados

def buscar_hoteis(destino, checkin, checkout, adultos, criancas, quartos, driver):
    resultados_totais = []
    
    for nome_site, url_base in SITES_HOSPEDAGEM.items():
        try:
            url = url_base.format(
                destino=destino, checkin=checkin, checkout=checkout, 
                adultos=adultos, criancas=criancas, quartos=quartos
            )
            driver.get(url)
            
            if nome_site == "Booking":
                # ESPERA INTELIGENTE: Aguarda até 15 segundos para os cartões de hotéis aparecerem
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="property-card"]'))
                )
                # Pausa extra de 2 segs para garantir que os valores em R$ carregaram no JavaScript
                time.sleep(2) 
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                dados_site = extrair_booking(soup, url, destino)
                resultados_totais.extend(dados_site)
            else:
                resultados_totais.append({
                    "Site": nome_site,
                    "Tipo": "Vários",
                    "Nome": f"Pesquisa geral em {nome_site}",
                    "Destino": destino,
                    "Avaliação": "-",
                    "Preço Total": "Abrir link",
                    "Link Original": url
                })
        except Exception as e:
            print(f"Erro em {nome_site}: {e}")
            continue
            
    return pd.DataFrame(resultados_totais)