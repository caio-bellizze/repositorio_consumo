import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats.mstats import winsorize
import openpyxl
import matplotlib.dates as mdates

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

# 🔹 Adicionar checkboxes para selecionar linhas de crescimento
mostrar_crescimento_exponencial = st.checkbox("Mostrar Crescimento Exponencial")
mostrar_cagr_acumulado = st.checkbox("Mostrar CAGR Acumulado")

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

    # 🔹 Função para calcular a média móvel exponencial
    def calcular_ema(consumo, span=12):
        return consumo.ewm(span=span, adjust=False).mean()

    # 🔹 Função para calcular o CAGR acumulado
    def calcular_cagr_acumulado(consumo):
        anos = len(consumo) / 12  # Convertendo meses para anos
        cagr_acumulado = (consumo.iloc[-1] / consumo.iloc[0]) ** (1 / anos) - 1
        y_pred_cagr_acumulado = consumo.iloc[0] * (1 + cagr_acumulado) ** (np.arange(len(consumo)) / 12)
        return y_pred_cagr_acumulado

    # 🔹 Calcular as linhas de crescimento exponencial e CAGR acumulado se selecionadas
    if mostrar_crescimento_exponencial:
        y_pred_exponencial = calcular_ema(df_filtrado["Consumo Médio Total"])
    
    if mostrar_cagr_acumulado:
        y_pred_cagr_acumulado = calcular_cagr_acumulado(df_mensal["Consumo Médio Total"])

    # 🔹 Calcular a variação de consumo em % entre um ano e outro
    consumo_por_ano = df_filtrado.groupby(df_filtrado['Ano_Mes'].dt.year)['Consumo Médio Total'].sum()
    variacao_consumo = consumo_por_ano.pct_change() * 100

    # 🔹 Criar gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.7, label="Consumo Mensal", width=0.6)
    ax.axhline(y=media_ajustada, color="green", linestyle="--", label=f"Média Ajustada: {media_ajustada:.2f}")
    ax.axhline(y=limite_superior, color="red", linestyle="--", label=f"Limite Superior (+{num_mad} σ): {limite_superior:.2f}")
    ax.axhline(y=limite_inferior, color="red", linestyle="--", label=f"Limite Inferior (-{num_mad} σ): {limite_inferior:.2f}")

    # 🔹 Adicionar as linhas de crescimento exponencial e CAGR acumulado se selecionadas
    if mostrar_crescimento_exponencial:
        ax.plot(df_filtrado["Ano_Mes"], y_pred_exponencial, color="orange", label="Crescimento Exponencial", linewidth=2)
    
    if mostrar_cagr_acumulado:
        ax.plot(df_mensal["Ano_Mes"], y_pred_cagr_acumulado, color="purple", label="CAGR Acumulado", linewidth=2)

    # 🔹 Mostrar a flexibilidade estimada e outros elementos na legenda principal
    handles, labels = ax.get_legend_handles_labels()
    flexibilidade_label = f"Flexibilidade Estimada: {flexibilidade_estimativa:.2f}%"
    handles.append(plt.Line2D([0], [0], color='w', label=flexibilidade_label))
    ax.legend(handles=handles, loc="upper right")

    # Adicionar variação de consumo em % como texto no gráfico em Lower Left sem título e sem linhas à esquerda das variações
    for year in range(data_inicio.year + 1, data_fim.year + 1):
        if year in variacao_consumo.index:
            variacao = variacao_consumo[year]
            ax.text(pd.Timestamp(f"{year}-07-01"), ax.get_ylim()[0] - (ax.get_ylim()[1] * 0.1), f"Variação {year-1}-{year}: {variacao:.2f}%", ha='center', va='top', fontsize=10, color='black')

    # Formatar datas no eixo x trimestralmente e em 45 graus no formato AAAA-MM
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    # Adicionar linha vertical para separar os anos
    for year in range(data_inicio.year, data_fim.year + 1):
        ax.axvline(pd.Timestamp(f"{year}-01-01"), color='gray', linestyle='--', linewidth=1)

    ax.set_xlabel("Data")
    ax.set_ylabel("Consumo Médio Total")
    ax.set_title(f"Consumo Histórico - {empresa_filtro}")
    ax.grid(True, linestyle="--", alpha=0.5)

    # 🔹 Exibir gráfico no Streamlit
    st.pyplot(fig)
