# app.py
import streamlit as st
import pandas as pd
import re
import airportsdata
import json

# Importação dos nossos módulos
from database import guardar_pesquisa, carregar_historico
from scrapers.utils import iniciar_driver
from scrapers.flights import buscar_voos
from scrapers.hotels import buscar_hoteis
from urllib.request import urlopen
from scrapers.utils import obter_lista_destinos
# --- CONFIGURAÇÃO GLOBAL ---
st.set_page_config(page_title="Travel Analytics Pro", page_icon="🌍", layout="wide")

# --- PAINEL LATERAL (CONFIGURAÇÕES DO ROBÔ) ---
with st.sidebar:
    st.title("⚙️ Motor de Extração")
    st.markdown("Configure o comportamento do robô nas pesquisas.")
    
    usa_anonimo = st.toggle("Navegação Anónima", value=True, help="Evita rastreio de cookies.")
    headless_mode = st.toggle("Modo Silencioso (Background)", value=False, help="Executa sem abrir a janela do Chrome.")
    
    st.divider()
    st.subheader("📊 Histórico Local")
    df_hist = carregar_historico()
    if not df_hist.empty:
        st.success(f"{len(df_hist)} registos guardados na base de dados.")
        # Permite descarregar o histórico completo de todas as pesquisas já feitas
        csv_hist = df_hist.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("📥 Descarregar Base de Dados Completa", data=csv_hist, file_name="historico_completo.csv", mime="text/csv")
    else:
        st.info("Nenhuma pesquisa guardada ainda.")

# --- INTERFACE PRINCIPAL ---
st.title("🌍 Painel de Pesquisa de Viagens")
st.markdown("Selecione o módulo que deseja pesquisar nas abas abaixo:")

# Usamos Tabs (Abas) para separar logicamente as ferramentas
aba_voos, aba_hoteis = st.tabs(["✈️ Passagens Aéreas", "🏨 Hospedagem"])

# ==========================================
# MÓDULO 1: PASSAGENS AÉREAS (UX SÊNIOR)
# ==========================================
with aba_voos:
    st.subheader("Configurar Rota e Passageiros")
    
    # 1. Carrega a base de dados mundial exaustiva (em cache para ser ultrarrápido)
    @st.cache_data
    def carregar_aeroportos():
        import airportsdata
        db = airportsdata.load('IATA')
        dicionario_formatado = {}
        
        # 1. Carregamos primeiro os destaques
        dicionario_formatado["⭐ Brasília - BSB"] = "BSB"
        dicionario_formatado["⭐ São Paulo (Todos) - SAO"] = "SAO"
        dicionario_formatado["⭐ Rio de Janeiro (Todos) - RIO"] = "RIO"
        dicionario_formatado["⭐ Foz do Iguaçu - IGU"] = "IGU"
        dicionario_formatado["⭐ Lisboa, Portugal - LIS"] = "LIS"
        
        # 2. Carregamos o resto do mundo com proteção contra erros (Anti-Quebra)
        for iata, info in db.items():
            # O "or" garante que se o dado for nulo (None), usamos um texto padrão
            cidade = info.get('city') or 'Cidade Desconhecida'
            nome = info.get('name') or 'Aeroporto'
            pais = info.get('country') or 'País Desconhecido'
            
            chave = f"{cidade}, {pais} - {nome} ({iata})"
            
            # Só adiciona se não for um dos destaques (para não ficar duplicado)
            if iata not in ["SAO", "RIO", "BSB", "IGU", "LIS"]:
                dicionario_formatado[chave] = iata
            
        return dicionario_formatado
    
    AEROPORTOS = carregar_aeroportos()
    lista_nomes = list(AEROPORTOS.keys())
    
    # Linha 1: Origem e Destino com Auto-complete Mundial
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        origem_sel = st.selectbox("Origem", lista_nomes, key="origem_sel")
        origem = AEROPORTOS[origem_sel]
            
    with col_v2:
        # Coloca Foz do Iguaçu ou outro como padrão (index 3 da nossa lista de destaques)
        destino_sel = st.selectbox("Destino", lista_nomes, index=3, key="destino_sel")
        destino_voo = AEROPORTOS[destino_sel]
        
    # Linha 2: Datas
    col_v3, col_v4 = st.columns(2)
    with col_v3:
        data_ida = st.date_input("Data de Ida", key="data_ida")
    with col_v4:
        # Toggle para viagem de ida e volta
        tem_volta = st.checkbox("Incluir voo de regresso", value=True)
        if tem_volta:
            data_volta = st.date_input("Data de Volta", key="data_volta")
        else:
            data_volta = None

    # Linha 3: Passageiros e Moeda
    col_v5, col_v6, col_v7 = st.columns(3)
    with col_v5:
        voo_adt = st.number_input("Adultos", min_value=1, value=1, key="voo_adt")
    with col_v6:
        voo_chd = st.number_input("Crianças", min_value=0, value=0, key="voo_chd")
    with col_v7:
        modo_pag_voo = st.selectbox("Moeda:", ["R$ (Dinheiro)"]) # Restrito a R$ para focar no Google Flights por agora

    # Ação de Pesquisa
    if st.button("🚀 Pesquisar Voos", type="primary", use_container_width=True):
        if not origem or not destino_voo:
            st.error("⚠️ Origem e Destino são obrigatórios.")
        elif tem_volta and data_volta <= data_ida:
            st.error("⚠️ A data de volta deve ser posterior à data de ida.")
        else:
            with st.spinner("A consultar o Google Flights e a extrair preços reais..."):
                driver = iniciar_driver(anonimo=usa_anonimo, oculto=headless_mode)
                try:
                    d_ida_str = data_ida.strftime("%Y-%m-%d")
                    d_volta_str = data_volta.strftime("%Y-%m-%d") if data_volta else None
                    
                    df_voos = buscar_voos(origem, destino_voo, d_ida_str, d_volta_str, voo_adt, voo_chd, driver)
                    
                    if not df_voos.empty:
                        # UX: Ordenação automática do menor preço
                        df_voos = df_voos.sort_values(by="Preço Numérico", ascending=True)
                        guardar_pesquisa(df_voos, "Voos")
                        
                        st.success("🎉 Voos reais encontrados!")
                        
                        # UX: Filtros Pós-Busca Dinâmicos
                        st.subheader("⚙️ Refinar Resultados")
                        c_f1, c_f2, c_f3 = st.columns(3)
                        with c_f1:
                            cias_disp = df_voos['Companhia'].unique().tolist()
                            cias_sel = st.multiselect("Companhias:", cias_disp, default=cias_disp)
                        with c_f2:
                            escalas_disp = df_voos['Escalas'].unique().tolist()
                            escalas_sel = st.multiselect("Escalas:", escalas_disp, default=escalas_disp)
                        with c_f3:
                            preco_max = st.slider(
                                "Preço Máximo", 
                                min_value=int(df_voos['Preço Numérico'].min()), 
                                max_value=int(df_voos['Preço Numérico'].max()), 
                                value=int(df_voos['Preço Numérico'].max())
                            )
                            
                        # Aplicação dos Filtros
                        df_filtrado = df_voos[
                            (df_voos['Companhia'].isin(cias_sel)) & 
                            (df_voos['Escalas'].isin(escalas_sel)) &
                            (df_voos['Preço Numérico'] <= preco_max)
                        ]
                        
                        if not df_filtrado.empty:
                            st.metric(label="🏆 Voo Mais Barato (Filtro Atual)", value=f"R$ {df_filtrado.iloc[0]['Preço Numérico']:,.2f}")
                            
                            # Removemos a coluna numérica técnica e mostramos a tabela limpa
                            df_visual = df_filtrado.drop(columns=['Preço Numérico'])
                            st.dataframe(
                                df_visual, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Link Original": st.column_config.LinkColumn("Comprar", display_text="Ver Oferta 🔗")
                                }
                            )
                        else:
                            st.warning("Nenhum voo corresponde aos filtros.")
                    else:
                        st.error("❌ Os preços não carregaram. O site pode ter bloqueado o acesso automático. Tente sem o Modo Silencioso.")
                finally:
                    driver.quit()

# ==========================================
# MÓDULO 2: HOSPEDAGEM (NOVA ESTRUTURA UX/UI)
# ==========================================
with aba_hoteis:
    st.subheader("Configurar Estadia e Preferências")
    
    # Lista predefinida para UX melhorada (Auto-complete)
    destinos_populares = obter_lista_destinos()
    
    col_h_dest1, col_h_dest2 = st.columns([2, 1])
    with col_h_dest1:
        destino_selecionado = st.selectbox("Cidade / Região de Destino", destinos_populares, key="destino_hotel_sel")
    with col_h_dest2:
        # Se escolher "Outro", abre uma caixa de texto
        if destino_selecionado == "Outro":
            destino_hotel = st.text_input("Digite o Destino", placeholder="Ex: Paris", key="destino_hotel_txt")
        else:
            destino_hotel = destino_selecionado
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        checkin = st.date_input("Check-in", key="checkin")
    with col_h2:
        checkout = st.date_input("Check-out", key="checkout")
        
    col_h3, col_h4, col_h5 = st.columns(3)
    with col_h3:
        hotel_adt = st.number_input("Adultos", min_value=1, value=2, key="hotel_adt")
    with col_h4:
        hotel_chd = st.number_input("Crianças", min_value=0, value=0, key="hotel_chd")
    with col_h5:
        hotel_quartos = st.number_input("Quartos", min_value=1, value=1, key="hotel_quartos")

    if st.button("🚀 Pesquisar Hospedagem", type="primary", use_container_width=True):
        if not destino_hotel or checkout <= checkin:
            st.error("⚠️ Verifique o destino e garanta que o Check-out é após o Check-in.")
        else:
            with st.spinner(f"A extrair alojamentos em {destino_hotel}..."):
                driver = iniciar_driver(anonimo=usa_anonimo, oculto=headless_mode)
                try:
                    ci_str = checkin.strftime("%Y-%m-%d")
                    co_str = checkout.strftime("%Y-%m-%d")
                    df_hoteis = buscar_hoteis(destino_hotel, ci_str, co_str, hotel_adt, hotel_chd, hotel_quartos, driver)
                    
                    if not df_hoteis.empty:
                        # UX: ORDENAÇÃO AUTOMÁTICA DO MAIS BARATO
                        df_hoteis = df_hoteis.sort_values(by="Preço Numérico", ascending=True)
                        guardar_pesquisa(df_hoteis, "Hospedagem")
                        
                        st.success("🎉 Pesquisa concluída e ordenada pelo menor preço!")
                        
                        # UX: FILTROS PÓS-BUSCA
                        st.subheader("⚙️ Refinar Resultados")
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            tipos_disp = df_hoteis['Tipo'].unique().tolist()
                            tipos_sel = st.multiselect("Filtrar por Tipo:", tipos_disp, default=tipos_disp)
                        with col_f2:
                            preco_max = st.slider(
                                "Preço Máximo (R$)", 
                                min_value=int(df_hoteis['Preço Numérico'].min()), 
                                max_value=int(df_hoteis['Preço Numérico'].max()), 
                                value=int(df_hoteis['Preço Numérico'].max())
                            )
                        
                        # Aplicação dos filtros
                        df_filtrado = df_hoteis[
                            (df_hoteis['Tipo'].isin(tipos_sel)) & 
                            (df_hoteis['Preço Numérico'] <= preco_max)
                        ]
                        
                        if not df_filtrado.empty:
                            # UX: DESTAQUE DO MELHOR PREÇO
                            st.metric(label="🏆 Opção Mais Barata Encontrada", value=f"R$ {df_filtrado.iloc[0]['Preço Numérico']:,.2f}")
                            
                            # Esconde a coluna numérica usada apenas para lógica e exibe a tabela
                            df_visual = df_filtrado.drop(columns=['Preço Numérico'])
                            
                            st.dataframe(
                                df_visual, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Link Original": st.column_config.LinkColumn("Reservar", display_text="Ver Oferta 🔗")
                                }
                            )
                        else:
                            st.warning("Nenhum hotel corresponde aos filtros selecionados.")
                    else:
                        st.error("❌ Não foi possível carregar os preços. Tente desativar o Modo Silencioso.")
                finally:
                    driver.quit()