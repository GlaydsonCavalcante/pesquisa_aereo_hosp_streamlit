# app.py
import streamlit as st
import pandas as pd

# Importamos os nossos scrapers personalizados
from scrapers.utils import iniciar_driver
from scrapers.flights import buscar_voos
from scrapers.hotels import buscar_hoteis

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Hub de Viagens Pro", page_icon="✈️", layout="wide")

# --- MICRO PAINEL LATERAL ---
with st.sidebar:
    st.title("🛠️ Painel de Controlo")
    tipo_servico = st.selectbox("O que desejas procurar?", ["Passagens Aéreas", "Hospedagem"])
    
    # Só mostramos a opção de pagamento se for voo
    if tipo_servico == "Passagens Aéreas":
        modo_pagamento = st.radio("Moeda de troca:", ["R$ (Dinheiro)", "Milhas / Pontos"])
    else:
        modo_pagamento = "R$ (Dinheiro)"
    
    st.divider()
    st.subheader("Configurações do Robô")
    usa_anonimo = st.toggle("Aba Anónima (Recomendado)", value=True, help="Impede que os sites aumentem o preço baseando-se nas tuas visitas.")
    headless_mode = st.toggle("Modo Silencioso", value=False, help="Executa a pesquisa sem abrir a janela do navegador.")

# --- ÁREA PRINCIPAL ---
st.header(f"🔍 Pesquisa de {tipo_servico}")

col1, col2, col3 = st.columns(3)
with col1:
    origem = st.text_input("Origem (IATA)", placeholder="Ex: GRU").upper()
with col2:
    destino = st.text_input("Destino", placeholder="Ex: MCO ou Orlando").upper()
with col3:
    data_viagem = st.date_input("Data da Viagem")

# Formata a data para texto (YYYY-MM-DD), que é o padrão da maioria dos sites
data_str = data_viagem.strftime("%Y-%m-%d")

# --- AÇÃO DO UTILIZADOR ---
if st.button("🚀 Iniciar Captura de Preços", type="primary"):
    
    # Validação simples
    if not destino or (tipo_servico == "Passagens Aéreas" and not origem):
        st.error("⚠️ Por favor, preenche os campos de Origem e Destino corretamente.")
    else:
        with st.spinner("A inicializar os motores e a pesquisar em aba anónima..."):
            # 1. Iniciamos o navegador centralizado
            driver = iniciar_driver(anonimo=usa_anonimo, oculto=headless_mode)
            
            try:
                # 2. Encaminhamos para o ficheiro correto com base na escolha
                if tipo_servico == "Passagens Aéreas":
                    df_resultados = buscar_voos(origem, destino, data_str, modo_pagamento, driver)
                else:
                    df_resultados = buscar_hoteis(destino, data_str, driver)
                
                # 3. Exibimos os resultados
                if not df_resultados.empty:
                    st.success("🎉 Busca concluída com sucesso!")
                    st.dataframe(df_resultados, use_container_width=True)
                    
                    # Botão para exportar
                    csv = df_resultados.to_csv(index=False, sep=';').encode('utf-8')
                    st.download_button("📥 Descarregar Planilha CSV", data=csv, file_name="pesquisa_viagem.csv", mime="text/csv")
                else:
                    st.warning("Não foram encontrados resultados. Tenta alterar as datas ou locais.")
            
            finally:
                # 4. Fechamos sempre o navegador no final, mesmo que dê erro
                driver.quit()