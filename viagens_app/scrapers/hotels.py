# scrapers/hotels.py
import time
import pandas as pd
from bs4 import BeautifulSoup

def buscar_hoteis(destino, data_checkin, driver):
    """
    Procura hotéis usando o driver fornecido.
    Retorna um DataFrame do Pandas com os resultados.
    """
    resultados = []
    
    try:
        # URL de exemplo baseada no Booking.com
        url = f"https://www.booking.com/searchresults.pt-br.html?ss={destino}&checkin={data_checkin}"
            
        driver.get(url)
        time.sleep(6) # Tempo para o site carregar os resultados
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Simulando a extração de dados (atualizar classes CSS no futuro)
        resultados.append({
            "Tipo": "Hotel",
            "Destino": destino,
            "Check-in": data_checkin,
            "Alojamento": "Hotel Exemplo Centro",
            "Preço": "Consultar site (Ex: R$ 450/noite)",
            "Link Original": url
        })
        
    except Exception as e:
        print(f"Erro ao procurar hotéis: {e}")
        
    return pd.DataFrame(resultados)