# scrapers/utils.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def iniciar_driver(anonimo=True, oculto=False):
    """
    Inicia o navegador Chrome com as configurações desejadas.
    """
    options = Options()
    
    # Adiciona a aba anónima (muito importante para viagens!)
    if anonimo:
        options.add_argument("--incognito")
        
    # Roda em segundo plano (sem abrir a janela)
    if oculto:
        options.add_argument("--headless")
        
    # Evita que o site detete facilmente que somos um robô
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Inicia o driver gerindo a versão do ChromeDriver automaticamente
    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=options)
    
    return driver