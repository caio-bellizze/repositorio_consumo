import requests
import pandas as pd
import streamlit as st

st.title("Base de Dados da CCEE")

# URL base da API
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"
base_url = f"https://dadosabertos.ccee.org.br/api/3/action/datastore_search?resource_id={resource_id}"

# Função para carregar os dados da API e armazenar em cache
@st.cache_data(show_spinner=True)
def carregar_dados():
    all_records = []
    limit = 10000
    offset = 0

    while True:
        url = f"{base_url}&limit={limit}&offset={offset}"
        response = requests.get(url)
        data = response.json()
        records = data.get("result", {}).get("records", [])

        if not records:
            break

        all_records.extend(records)
        offset += limit  # Próxima página

    return pd.DataFrame(all_records)

# Carregando os dados com cache
df = carregar_dados()

# Exibir apenas uma amostra para evitar travamentos
st.write(f"Base completa tem {df.shape[0]} registros. Exibindo preview abaixo:")
st.dataframe(df.head(5000))  # Mostra apenas 5000 registros para evitar travamento

# Botão para baixar o dataset completo
st.download_button(
    label="📥 Baixar Dados Completos",
    data=df.to_csv(index=False, encoding="utf-8"),
    file_name="base_ccee_completa.csv",
    mime="text/csv"
)
