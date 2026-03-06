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

@st.cache_data
    def obter_lista_destinos():
        # Busca todas as cidades brasileiras via API oficial do IBGE
        try:
            url_ibge = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
            with urlopen(url_ibge) as response:
                municipios = json.loads(response.read().decode())
                cidades_br = [f"{m['nome']}, {m['microrregiao']['mesorregiao']['UF']['sigla']}" for m in municipios]
        except Exception:
            # Fallback caso a API esteja indisponível
            cidades_br = ["Foz do Iguaçu, PR", "Rio de Janeiro, RJ", "São Paulo, SP"]

        # Lista manual das principais cidades estrangeiras
        cidades_int = [
            "Paris, FRA", "Londres, ING", "Nova York, EUA", "Lisboa, POR", 
            "Roma, ITA", "Tóquio, JAP", "Buenos Aires, ARG", "Dubai, EAU", 
            "Madri, ESP", "Berlim, ALE", "Amsterdã, HOL", "Orlando, EUA"
        ]
        
        # Consolida, ordena e adiciona a opção de busca manual
        return sorted(cidades_br + cidades_int) + ["Outro"]

    destinos_populares = obter_lista_destinos()