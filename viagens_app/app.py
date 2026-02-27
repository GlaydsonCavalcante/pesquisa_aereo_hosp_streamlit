# app.py
import streamlit as st
import pandas as pd
import re

# Importação dos nossos módulos
from database import guardar_pesquisa, carregar_historico
from scrapers.utils import iniciar_driver
from scrapers.flights import buscar_voos
from scrapers.hotels import buscar_hoteis

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
# MÓDULO 1: PASSAGENS AÉREAS
# ==========================================
with aba_voos:
    st.subheader("Configurar Rota e Passageiros")
    
    # Linha 1: Origem e Destino
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        origem = st.text_input("Origem (IATA)", placeholder="Ex: BSB", key="origem_voo").upper()
    with col_v2:
        destino_voo = st.text_input("Destino (IATA)", placeholder="Ex: IGU", key="destino_voo").upper()
        
    # Linha 2: Datas e Moeda
    col_v3, col_v4, col_v5 = st.columns(3)
    with col_v3:
        data_ida = st.date_input("Data de Ida", key="data_ida")
    with col_v4:
        # Deixamos a volta opcional por enquanto (pode ser útil no futuro)
        data_volta = st.date_input("Data de Volta (Opcional)", value=None, key="data_volta")
    with col_v5:
        modo_pag_voo = st.selectbox("Moeda de Pagamento:", ["R$ (Dinheiro)", "Milhas / Pontos"])

    # Linha 3: Passageiros
    col_v6, col_v7 = st.columns(2)
    with col_v6:
        voo_adt = st.number_input("Adultos", min_value=1, value=1, key="voo_adt")
    with col_v7:
        voo_chd = st.number_input("Crianças", min_value=0, value=0, key="voo_chd")

    # Ação de Pesquisa
    if st.button("🚀 Iniciar Pesquisa de Voos", type="primary", use_container_width=True):
        if not origem or not destino_voo:
            st.error("⚠️ Origem e Destino são obrigatórios.")
        else:
            with st.spinner("A iniciar motor de busca de voos..."):
                driver = iniciar_driver(anonimo=usa_anonimo, oculto=headless_mode)
                try:
                    data_str = data_ida.strftime("%Y-%m-%d")
                    df_voos = buscar_voos(origem, destino_voo, data_str, modo_pag_voo, voo_adt, voo_chd, driver)
                    
                    if not df_voos.empty:
                        # Guarda no nosso banco de dados local
                        guardar_pesquisa(df_voos, "Voos")
                        
                        st.success("🎉 Resultados capturados e guardados no histórico!")
                        st.dataframe(df_voos, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Sem resultados.")
                finally:
                    driver.quit()

# ==========================================
# MÓDULO 2: HOSPEDAGEM (NOVA ESTRUTURA UX/UI)
# ==========================================
with aba_hoteis:
    st.subheader("Configurar Estadia e Preferências")
    
    # Lista predefinida para UX melhorada (Auto-complete)
    destinos_populares = [
        "Foz do Iguaçu, PR", "Rio de Janeiro, RJ", "São Paulo, SP", 
        "Gramado, RS", "Salvador, BA", "Florianópolis, SC", "Maceió, AL", "Outro"
    ]
    
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