import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats.mstats import winsorize
import openpyxl
import re

# 🔹 Configuração do Streamlit
st.title("📊 Análise de Consumo de Energia")
st.write("Selecione uma empresa, ajuste o limite de desvios padrões e defina o intervalo de datas.")

# 🔹 Função para carregar os dados com cache
@st.cache_data
def carregar_dados(arquivo, planilha):
    return pd.read_excel(arquivo, sheet_name=planilha, engine="openpyxl")

# 🔹 Ler os dados
arquivo = "base_de_dados_filtrada_v3.xlsx"
planilha = "base_de_dados"
df = carregar_dados(arquivo, planilha)

# 🔹 Criar lista de empresas únicas
empresas = sorted(df["NOME_EMPRESARIAL"].unique())
empresa_filtro = st.selectbox("Selecione uma empresa", options=empresas, index=None, placeholder="Escolha a empresa")

# 🔹 Adicionar um slider para o número de MADs
num_mad = st.slider("Escolha o número de desvios padrões para determinar os limites", min_value=1, max_value=5, value=2)

# 🔹 Adicionar seleção de intervalo de datas
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
data_inicio = st.date_input("Data Inicial", value=pd.to_datetime("2022-01-01"))
data_fim = st.date_input("Data Final", value=pd.to_datetime("2024-12-31"))

# 🔹 Criar botão para gerar o gráfico
if st.button("Calcular") and empresa_filtro:
    df_empresa = df[df["NOME_EMPRESARIAL"] == empresa_filtro].copy()
    df_empresa.dropna(subset=["Data"], inplace=True)
    
    # 🔹 Aplicar filtro de datas
    df_empresa = df_empresa[(df_empresa["Data"] >= pd.to_datetime(data_inicio)) & 
                             (df_empresa["Data"] <= pd.to_datetime(data_fim))]
    
    df_empresa["Ano_Mes"] = df_empresa["Data"].dt.to_period("M")
    df_mensal = df_empresa.groupby("Ano_Mes")["Consumo Médio Total"].sum().reset_index()
    df_mensal["Ano_Mes"] = df_mensal["Ano_Mes"].dt.to_timestamp(how="start")

    # 🔹 Cálculo do Modified Z-score
    mediana_consumo = np.median(df_mensal["Consumo Médio Total"])
    mad = np.median(np.abs(df_mensal["Consumo Médio Total"] - mediana_consumo))

    # 🔹 Cálculo dos limites dinâmicos com base no slider
    limite_superior = mediana_consumo + num_mad * mad / 0.6745
    limite_inferior = mediana_consumo - num_mad * mad / 0.6745

    # 🔹 Filtragem para flexibilidade
    df_filtrado = df_mensal[(df_mensal["Consumo Médio Total"] >= limite_inferior) & 
                             (df_mensal["Consumo Médio Total"] <= limite_superior)].copy()
    df_filtrado["Distancia_Media"] = np.abs(df_filtrado["Consumo Médio Total"] - mediana_consumo)

    # 🔹 Cálculo da flexibilidade estimada
    flexibilidade_estimativa = (df_filtrado["Distancia_Media"].mean() + num_mad * mad) / mediana_consumo * 100

    # 🔹 Recalcular a média considerando apenas os valores dentro dos limites
    media_ajustada = df_filtrado["Consumo Médio Total"].mean()

    # 🔹 Função para buscar informações da tabela
    def buscar_informacoes(df_empresa):
        if df_empresa.empty:
            return pd.DataFrame()
        
        mes_mais_recente = df_empresa["Data"].max()
        df_mes_recente = df_empresa[df_empresa["Data"] == mes_mais_recente]

        tabela_df = df_mes_recente.groupby("CNPJ_CARGA").agg({
            "SIGLA_PARCELA_CARGA": "count",  # Contar número de unidades
            "CIDADE": "first",
            "ESTADO_UF": "first",
            "RAMO_ATIVIDADE": lambda x: ", ".join(x.unique()),  # Concatenar ramos únicos
            "Consumo Médio Total": "sum"
        }).reset_index()

        if tabela_df.empty:
            return pd.DataFrame()

        # Pegando o CNPJ da Matriz (o menor CNPJ geralmente é o da matriz)
        cnpj_matriz = tabela_df["CNPJ_CARGA"].astype(str).min().split(".")[0]  # Remover casas decimais indesejadas

        # Criar nova tabela consolidada
        tabela_final = pd.DataFrame({
            "CNPJ": [format_cnpj(cnpj_matriz)],
            "Unidades": [tabela_df["SIGLA_PARCELA_CARGA"].sum()],
            "Cidade": [tabela_df["CIDADE"].mode()[0]],  # Cidade mais frequente
            "Estado": [tabela_df["ESTADO_UF"].mode()[0]],  # Estado mais frequente
            "Ramo": [", ".join(tabela_df["RAMO_ATIVIDADE"].unique())],  # Concatenar ramos únicos
        })

        return tabela_final

    # 🔹 Função para formatar o CNPJ
    def format_cnpj(cnpj):
        return re.sub(r'(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', r'\1.\2.\3/\4-\5', cnpj)

    # 🔹 Exibir tabela abaixo do gráfico
    tabela = buscar_informacoes(df_empresa)
    st.write("### 📋 Informações da Empresa")
    st.dataframe(tabela, hide_index=True)
