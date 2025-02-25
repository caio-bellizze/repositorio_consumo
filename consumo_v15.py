import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import re
from scipy.stats.mstats import winsorize
import openpyxl

# 🔹 Função para formatar o CNPJ corretamente
def format_cnpj(CNPJ):
    cnpj = str(int(cnpj))  # Garantir que o CNPJ seja tratado como inteiro para evitar ".0"
    cnpj = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
    return cnpj

# 🔹 Função para carregar os dados com cache
@st.cache_data
def carregar_dados(arquivo, planilha):
    return pd.read_excel(arquivo, sheet_name=planilha, engine="openpyxl")

# 🔹 Configuração do Streamlit
st.title("📊 Análise de Consumo de Energia")
st.write("Selecione uma empresa, ajuste o limite de desvios padrões e defina o intervalo de datas.")

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

    # Calcular o consumo total em MWh e suas variações
    consumo_mwh_2022 = df_empresa[df_empresa["Data"].dt.year == 2022]["CONSUMO_TOTAL"].sum()
    consumo_mwh_2023 = df_empresa[df_empresa["Data"].dt.year == 2023]["CONSUMO_TOTAL"].sum()
    consumo_mwh_2024 = (df_empresa[df_empresa["Data"].dt.year == 2024]["CONSUMO_TOTAL"].sum())/1000000
    variacao_2022_2023 = ( consumo_mwh_2023 - consumo_mwh_2022 ) / consumo_mwh_2022 * 100
    variacao_2023_2024 = ( consumo_mwh_2024 - consumo_mwh_2023 ) / consumo_mwh_2023 * 100

    # 🔹 Formatar a coluna 'Ano_Mes' para exibição no gráfico
    df_mensal["Ano_Mes"] = df_mensal["Ano_Mes"].dt.strftime("%b-%y")

    # 🔹 Criar gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(df_mensal["Ano_Mes"], df_mensal["Consumo Médio Total"], color="blue", alpha=0.8, label="Consumo Mensal", width=0.5)
    ax.axhline(y=media_ajustada, color="green", linestyle="--", label=f"Média Ajustada: {media_ajustada:.2f}")
    ax.axhline(y=limite_superior, color="orangered", linestyle="--", label=f"Limite Superior (+{num_mad} σ): {limite_superior:.2f}")
    ax.axhline(y=limite_inferior, color="orangered", linestyle="--", label=f"Limite Inferior (-{num_mad} σ): {limite_inferior:.2f}")
    
    ax.legend(title=f"Flexibilidade Estimada: {flexibilidade_estimativa:.2f}%", loc="lower right")

    # Criar um box com informações adicionais no gráfico
    texto_legenda = (
    f"Variação no consumo 2022-2023: {variacao_2022_2023:.2f}%\n"
    f"Variação no consumo 2023-2024: {variacao_2023_2024:.2f}%")

    # Adicionando o box ao gráfico
    ax.text(
    0.02, 0.02, texto_legenda, transform=ax.transAxes, fontsize=10,
    verticalalignment='bottom', horizontalalignment='left',
    bbox=dict(boxstyle="square,pad=0.4", edgecolor="lightgray", facecolor="white", alpha=0.9))

    # Adicionando linha divisória entre anos
    ax.axvline(x=11.5, color='gray', linestyle='dashed', ymin=0, ymax=1)  # Linha divisória entre os anos
    ax.axvline(x=23.5, color='gray', linestyle='dashed', ymin=0, ymax=1)  # Linha divisória entre os anos

    # Ajustando os rótulos do eixo X
    ax.set_xticklabels(df_mensal["Ano_Mes"], rotation=50)
    ax.set_ylabel("Consumo Médio Total")
    ax.set_title(f"Consumo Histórico - {empresa_filtro}")

    # 🔹 Exibir gráfico no Streamlit
    st.pyplot(fig)

    # 🔹 Função para buscar informações da tabela
    def buscar_informacoes(df_empresa):
        mes_mais_recente = df_empresa["Data"].max()
        df_mes_recente = df_empresa[df_empresa["Data"] == mes_mais_recente]

        tabela_df = df_mes_recente.groupby("CNPJ_CARGA").agg({
            "SIGLA_PARCELA_CARGA": "count",  # Contar número de unidades
            "CIDADE": "first",
            "ESTADO_UF": "first",
            "RAMO_ATIVIDADE": lambda x: ", ".join(x.unique()),  # Concatenar ramos únicos
            "Consumo Médio Total": "sum"
        }).reset_index()

        # Pegando o CNPJ da Matriz (o menor CNPJ geralmente é o da matriz)
        cnpj_matriz = tabela_df["CNPJ_CARGA"].astype(str).min()

        # Criar nova tabela consolidada
        tabela_final = pd.DataFrame({
            "CNPJ": [format_cnpj(cnpj_matriz)],
            "Unidades": [tabela_df["SIGLA_PARCELA_CARGA"].sum()],
            "Cidade": [tabela_df["CIDADE"].mode()[0]],  # Cidade mais frequente
            "Estado": [tabela_df["ESTADO_UF"].mode()[0]],  # Estado mais frequente
            "Ramo": [", ".join(tabela_df["RAMO_ATIVIDADE"].unique())],  # Concatenar ramos únicos
            "Consumo Médio Total": [tabela_df["Consumo Médio Total"].sum()]
        })

        return tabela_final

    # 🔹 Exibir tabela abaixo do gráfico
    tabela = buscar_informacoes(df_empresa)
    st.write("### 📋 Informações da Empresa")
    st.dataframe(tabela, hide_index=True)

    # 🔹 Botão "Exibir mais" para mostrar informações completas
    if st.button("Exibir mais"):
        tabela_completa = df_empresa.groupby("CNPJ_CARGA").agg({
            "SIGLA_PARCELA_CARGA": "count",  # Contar número de unidades
            "CIDADE": "first",
            "ESTADO_UF": "first",
            "RAMO_ATIVIDADE": lambda x: ", ".join(x.unique()),  # Concatenar ramos únicos
            "Consumo Médio Total": "sum"
        }).reset_index()

        # Formatar o CNPJ corretamente
        tabela_completa["CNPJ_CARGA"] = tabela_completa["CNPJ_CARGA"].apply(lambda x: format_cnpj(x))
        
        # Exibir a tabela completa
        st.write("### 📋 Informações Completas de Todas as Unidades")
        st.dataframe(tabela_completa, hide_index=True)
