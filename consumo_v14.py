import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats.mstats import winsorize
import openpyxl
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX

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

    # 🔹 Modelo de Regressão Linear
    X = np.arange(len(df_mensal)).reshape(-1, 1)
    y = df_mensal["Consumo Médio Total"].values
    modelo_lr = LinearRegression()
    modelo_lr.fit(X, y)
    y_pred_lr = modelo_lr.predict(X)

    # 🔹 Modelo SARIMA
    modelo_sarima = SARIMAX(df_mensal["Consumo Médio Total"], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    resultado_sarima = modelo_sarima.fit()
    previsao_sarima = resultado_sarima.predict(start=0, end=len(df_mensal)-1)
    previsao_futura_sarima = resultado_sarima.forecast(steps=24)

    # 🔹 Criar gráfico com regressão linear
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.7, label="Consumo Mensal", width=0.5)
    ax.plot(df_mensal["Ano_Mes"], y_pred_lr, color="orange", label="Tendência Linear", linewidth=2)
    ax.axhline(y=limite_superior, color="red", linestyle="--", label=f"Limite Superior (+{num_mad} σ): {limite_superior:.2f}")
    ax.axhline(y=limite_inferior, color="red", linestyle="--", label=f"Limite Inferior (-{num_mad} σ): {limite_inferior:.2f}")
    ax.legend(loc="upper left")
    ax.set_xticklabels(df_mensal["Ano_Mes"], rotation=90)
    ax.set_xlabel("Data")
    ax.set_ylabel("Consumo Médio Total")
    ax.set_title(f"Consumo Histórico - {empresa_filtro}")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)
    
    # 🔹 Criar gráfico com previsão SARIMA
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.7, label="Consumo Mensal", width=0.5)
    ax2.plot(df_mensal["Ano_Mes"], y_pred_lr, color="orange", label="Tendência Linear", linewidth=2)
    ax2.bar(pd.date_range(df_mensal["Ano_Mes"].iloc[-1], periods=24, freq='M'), previsao_futura_sarima, color="purple", alpha=0.6, label="Previsão SARIMA", width=15)
    ax2.legend(loc="upper left")
    ax2.set_xticklabels(df_mensal["Ano_Mes"], rotation=90)
    ax2.set_xlabel("Data")
    ax2.set_ylabel("Consumo Médio Total")
    ax2.set_title(f"Consumo Histórico e Previsão - {empresa_filtro}")
    ax2.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig2)
