# scrapers/hotels.py
import time
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SITES_HOSPEDAGEM = {
    "Booking": "https://www.booking.com/searchresults.pt-br.html?ss={destino}&checkin={checkin}&checkout={checkout}&group_adults={adultos}&no_rooms={quartos}&group_children={criancas}",
}

def limpar_preco(texto_preco):
    """Transforma 'R$ 1.500' no número 1500.0 para podermos filtrar."""
    try:
        # Extrai apenas os números
        numeros = re.sub(r'[^\d]', '', texto_preco)
        if numeros:
            return float(numeros)
        return 0.0
    except:
        return 0.0

def extrair_booking(soup, url, destino):
    hoteis_encontrados = []
    cards = soup.find_all('div', attrs={'data-testid': 'property-card'})
    
    for card in cards:
        try:
            titulo_tag = card.find('div', attrs={'data-testid': 'title'})
            titulo = titulo_tag.text.strip() if titulo_tag else "Sem nome"
            
            preco_tag = card.find('span', attrs={'data-testid': 'price-and-discounted-price'})
            preco_texto = preco_tag.text.strip() if preco_tag else "Esgotado"
            preco_num = limpar_preco(preco_texto)
            
            nota_tag = card.find('div', attrs={'data-testid': 'review-score'})
            nota = nota_tag.text.strip().split()[-1] if nota_tag else "Sem avaliação"
            
            tipo_estadia = "Outros"
            t_lower = titulo.lower()
            if "hotel" in t_lower: tipo_estadia = "Hotel"
            elif "apartament" in t_lower or "flat" in t_lower or "studio" in t_lower: tipo_estadia = "Apartamento"
            elif "casa" in t_lower or "home" in t_lower or "villa" in t_lower: tipo_estadia = "Casa"
            elif "pousada" in t_lower: tipo_estadia = "Pousada"
            elif "resort" in t_lower: tipo_estadia = "Resort"
            
            # Só adicionamos se o preço for maior que 0 (ignora hotéis esgotados)
            if preco_num > 0:
                hoteis_encontrados.append({
                    "Site": "Booking",
                    "Tipo": tipo_estadia,
                    "Nome": titulo,
                    "Destino": destino,
                    "Avaliação": nota,
                    "Preço Texto": preco_texto,
                    "Preço Numérico": preco_num, # Usado para os filtros no Streamlit
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
                # Espera 10 segundos pelos cartões.
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="property-card"]'))
                )
                time.sleep(2) # Pausa extra para renderização do JavaScript
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                dados_site = extrair_booking(soup, url, destino)
                resultados_totais.extend(dados_site)
        except Exception as e:
            print(f"Erro em {nome_site}: {e}")
            continue
            
    return pd.DataFrame(resultados_totais)