import requests
import pandas as pd
import streamlit as st

# Configuração do Streamlit
st.title("Consulta de Dados Abertos da CCEE - teste")

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
    batch_size = 5000  # Agora buscamos 5000 por vez para otimizar
    all_records = []

    # Extraindo todos os dados de uma vez, baseado no total_records
    with st.spinner("Baixando os dados..."):
        for offset in range(0, total_records, batch_size):
            params = {"resource_id": RESOURCE_ID, "limit": batch_size, "offset": offset}
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            
            # Se houver dados, adicionamos ao total
            if "result" in data and "records" in data["result"]:
                records = data["result"]["records"]
                all_records.extend(records)
            else:
                st.error(f"Erro ao buscar dados na página com offset {offset}.")
                break

            st.write(f"Registros baixados: {len(all_records)} / {total_records}")

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
