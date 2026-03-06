# scrapers/flights.py
import time
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def limpar_preco(texto_preco):
    """Transforma 'R$ 1.500' no número 1500.0 para ordenação."""
    try:
        numeros = re.sub(r'[^\d]', '', texto_preco)
        if numeros: return float(numeros)
        return 0.0
    except:
        return 0.0

def extrair_google_flights(soup, url, origem, destino):
    voos_encontrados = []
    
    # O Google Flights costuma usar a classe 'pIav2d' para os cartões de voo, 
    # mas adicionamos um fallback para 'role="listitem"' caso mudem o CSS.
    itens_voo = soup.find_all('li', class_='pIav2d')
    if not itens_voo:
        itens_voo = soup.find_all('div', attrs={'role': 'listitem'})
    
    for item in itens_voo:
        try:
            cia_tag = item.find('div', class_='sSHqwe')
            cia = cia_tag.text.strip() if cia_tag else "Companhia Aérea"
            
            # Procura qualquer tag que contenha o símbolo R$
            preco_tag = item.find(string=re.compile(r'R\$'))
            preco_texto = preco_tag.strip() if preco_tag else ""
            preco_num = limpar_preco(preco_texto)
            
            # Deduz as escalas
            escalas = "1+ Paradas"
            texto_card = item.text.lower()
            if "direto" in texto_card or "nonstop" in texto_card:
                escalas = "Direto"
            
            # Só guardamos se encontrarmos um preço real! Fim da falsa esperança.
            if preco_num > 0:
                voos_encontrados.append({
                    "Site": "Google Flights",
                    "Companhia": cia,
                    "Escalas": escalas,
                    "Origem": origem,
                    "Destino": destino,
                    "Preço Texto": preco_texto,
                    "Preço Numérico": preco_num, # Usado internamente para ordenar
                    "Link Original": url
                })
        except Exception:
            continue
            
    return voos_encontrados

def buscar_voos(origem, destino, data_ida, data_volta, adultos, criancas, driver):
    """Constrói a URL, espera o carregamento e extrai os voos."""
    
    # 1. PARAMETRIZAÇÃO REAL DA URL
    # Construímos a query exata que o Google Flights usa
    query = f"Flights to {destino} from {origem} on {data_ida}"
    if data_volta:
        query += f" through {data_volta}"
        
    url = f"https://www.google.com/travel/flights?q={query.replace(' ', '%20')}"
    
    resultados = []
    try:
        driver.get(url)
        
        # 2. ESPERA INTELIGENTE (Anti-Bot Level 1)
        # Espera até 15 segundos para que os voos apareçam na tela
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li.pIav2d, div[role="listitem"]'))
        )
        time.sleep(2) # Tempo para o JavaScript renderizar os preços finais
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        resultados = extrair_google_flights(soup, url, origem, destino)
        
    except Exception as e:
        print(f"Erro ou bloqueio ao capturar Google Flights: {e}")

    return pd.DataFrame(resultados)