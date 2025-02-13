import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats.mstats import winsorize
import openpyxl

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

    # 🔹 Formatar a coluna 'Ano_Mes' para exibição no gráfico
    df_mensal["Ano_Mes"] = df_mensal["Ano_Mes"].dt.strftime("%Y-%m")

    # 🔹 Criar gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.7, label="Consumo Mensal", width=0.5)
    ax.axhline(y=media_ajustada, color="green", linestyle="--", label=f"Média Ajustada: {media_ajustada:.2f}")
    ax.axhline(y=limite_superior, color="red", linestyle="--", label=f"Limite Superior (+{num_mad} σ): {limite_superior:.2f}")
    ax.axhline(y=limite_inferior, color="red", linestyle="--", label=f"Limite Inferior (-{num_mad} σ): {limite_inferior:.2f}")
    
    ax.legend(title=f"Flexibilidade Estimada: {flexibilidade_estimativa:.2f}%", loc="lower right")
    
    # Adicionando linha divisória entre anos
    ax.axvline(x=11.5, color='black', linestyle='dashed', ymin=-0.5, ymax=1)  # Linha divisória entre os anos
    ax.axvline(x=23.5, color='black', linestyle='dashed', ymin=-0.5, ymax=1)  # Linha divisória entre os anos

    # Ajustando os rótulos do eixo X
    ax.set_xticklabels(df_mensal["Ano_Mes"], rotation=90)
    ax.set_ylabel("Consumo Médio Total")
    ax.set_title(f"Consumo Histórico - {empresa_filtro}")
    
    # Adicionando os anos abaixo do eixo X
    for i, ano in enumerate(["2022" , "2023", "2024"]):
        ax.text(i * 12 + 5.5, -4, ano, fontsize=12, ha="center", color="black")  # Y reduzido para afastar mais

    ax.grid(True, linestyle="--", alpha=0.5)

    # 🔹 Exibir gráfico no Streamlit
    st.pyplot(fig)
