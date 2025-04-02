import requests
import pandas as pd
import streamlit as st

# Configuração do Streamlit
st.title("Consulta de Dados Abertos da CCEE")

# URL da API
BASE_URL = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
RESOURCE_ID = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

# Obtendo o número total de registros
params = {"resource_id": RESOURCE_ID, "limit": 1}
response = requests.get(BASE_URL, params=params)
data = response.json()

if "result" in data and "total" in data["result"]:
    total_records = data["result"]["total"]  # Número total de registros
    st.write(f"Total de registros disponíveis: {total_records}")

    # Parâmetros de extração
    batch_size = 100
    offset = 0
    all_records = []

    # Extraindo todos os dados
    with st.spinner("Baixando os dados..."):
        while offset < total_records:
            params = {"resource_id": RESOURCE_ID, "limit": batch_size, "offset": offset}
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            
            if "result" in data and "records" in data["result"]:
                all_records.extend(data["result"]["records"])
            else:
                st.error("Erro ao buscar dados")
                break

            offset += batch_size

    # Convertendo para DataFrame
    df = pd.DataFrame(all_records)

    # Exibir no Streamlit
    st.write("### Dados extraídos:")
    st.dataframe(df)

    # Opção para baixar os dados
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", csv, "dados_ccee.csv", "text/csv", key="download-csv")
else:
    st.error("Não foi possível obter os dados da API.")
