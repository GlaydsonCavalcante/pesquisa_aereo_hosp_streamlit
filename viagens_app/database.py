# database.py
import pandas as pd
import os
from datetime import datetime

ARQUIVO_HISTORICO = "historico_viagens.csv"

def guardar_pesquisa(df_novos_dados, tipo_pesquisa):
    """
    Guarda os resultados de uma nova pesquisa no ficheiro CSV,
    adicionando a data e hora em que a pesquisa foi feita.
    """
    if df_novos_dados.empty:
        return False
        
    # Criamos uma cópia para não alterar os dados originais da interface
    df_salvar = df_novos_dados.copy()
    
    # Adicionamos metadados importantes para análise futura
    df_salvar['Data da Pesquisa (Sistema)'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_salvar['Categoria'] = tipo_pesquisa
    
    # Se o ficheiro já existir, adicionamos os dados (append). Se não, criamos um novo.
    if os.path.exists(ARQUIVO_HISTORICO):
        df_salvar.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False, sep=';', encoding='utf-8')
    else:
        df_salvar.to_csv(ARQUIVO_HISTORICO, mode='w', header=True, index=False, sep=';', encoding='utf-8')
        
    return True

def carregar_historico():
    """
    Lê o ficheiro CSV para podermos mostrar o histórico no painel.
    """
    if os.path.exists(ARQUIVO_HISTORICO):
        return pd.read_csv(ARQUIVO_HISTORICO, sep=';', encoding='utf-8')
    return pd.DataFrame()