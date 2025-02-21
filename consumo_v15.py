import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats.mstats import winsorize
import openpyxl
from statsmodels.tsa.seasonal import seasonal_decompose

# 🔹 Configuração do Streamlit
st.title("📊 Análise de Consumo de Energia e Sazonalidade")
st.write("Selecione uma empresa, ajuste o limite de desvios padrões, defina o intervalo de datas e veja a sazonalidade do consumo de energia para ajustar contratos.")

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
    
    # 🔹 Criar coluna de Ano_Mes para agrupamento
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

    # 🔹 Análise de sazonalidade
    # Decomposição da série temporal para detectar padrões sazonais
    result = seasonal_decompose(df_mensal['Consumo Médio Total'], model='additive', period=12)
    
    # Obtendo o componente sazonal e ajustando para percentual
    sazonalidade = result.seasonal
    sazonalidade_percentual = (sazonalidade / np.mean(sazonalidade)) * 100

    # 🔹 Calcular o impacto da sazonalidade
    sazonalidade_media = np.mean(sazonalidade_percentual)

    # 🔹 Exibir informações sobre sazonalidade
    st.write(f"Sazonalidade média em %: {sazonalidade_media:.2f}%")

    # 🔹 Calcular o consumo total em MWh e suas variações
    consumo_mwh_2022 = df_empresa[df_empresa["Data"].dt.year == 2022]["CONSUMO_TOTAL"].sum()
    consumo_mwh_2023 = df_empresa[df_empresa["Data"].dt.year == 2023]["CONSUMO_TOTAL"].sum()
    consumo_mwh_2024 = (df_empresa[df_empresa["Data"].dt.year == 2024]["CONSUMO_TOTAL"].sum()) / 1000000
    variacao_2022_2023 = (consumo_mwh_2023 - consumo_mwh_2022) / consumo_mwh_2022 * 100
    variacao_2023_2024 = (consumo_mwh_2024 - consumo_mwh_2023) / consumo_mwh_2023 * 100

    # 🔹 Criar gráfico de Consumo
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.8, label="Consumo Mensal", width=0.5)
    ax1.axhline(y=media_ajustada, color="green", linestyle="--", label=f"Média Ajustada: {media_ajustada:.2f}")
    ax1.axhline(y=limite_superior, color="orangered", linestyle="--", label=f"Limite Superior (+{num_mad} σ): {limite_superior:.2f}")
    ax1.axhline(y=limite_inferior, color="orangered", linestyle="--", label=f"Limite Inferior (-{num_mad} σ): {limite_inferior:.2f}")
    ax1.legend(title=f"Flexibilidade Estimada: {flexibilidade_estimativa:.2f}%", loc="lower right")
    ax1.set_xticklabels(df_mensal["Ano_Mes"], rotation=50)
    ax1.set_ylabel("Consumo Médio Total")
    ax1.set_title(f"Consumo Histórico - {empresa_filtro}")
    
    # Exibir gráfico de consumo no Streamlit
    st.pyplot(fig1)

    # 🔹 Criar gráfico de Sazonalidade
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(df_mensal["Ano_Mes"], sazonalidade_percentual, color="orange", label="Índice de Sazonalidade (%)", marker='o', linestyle='--')
    ax2.set_xticklabels(df_mensal["Ano_Mes"], rotation=50)
    ax2.set_ylabel("Sazonalidade (%)")
    ax2.set_title(f"Sazonalidade do Consumo - {empresa_filtro}")
    ax2.legend()
    
    # Exibir gráfico de sazonalidade no Streamlit
    st.pyplot(fig2)
