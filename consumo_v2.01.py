import requests
import pandas as pd
import streamlit as st

# Configuração da página no Streamlit
st.title("Base de Dados da CCEE")

# Definição da URL base e do resource_id
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"
base_url = f"https://dadosabertos.ccee.org.br/api/3/action/datastore_search?resource_id={resource_id}"

# Lista para armazenar todos os registros
all_records = []
limit = 10000  # Número máximo de registros por requisição
offset = 0     # Inicia do primeiro registro

with st.spinner("Carregando os dados..."):
    while True:
        # Faz a requisição com paginação
        url = f"{base_url}&limit={limit}&offset={offset}"
        response = requests.get(url)
        data = response.json()

        # Obtém os registros retornados
        records = data.get("result", {}).get("records", [])

        if not records:
            break  # Sai do loop se não houver mais dados

        all_records.extend(records)  # Adiciona os registros à lista
        offset += limit  # Atualiza o offset para a próxima requisição

# Converte para DataFrame do pandas
df = pd.DataFrame(all_records)

# Exibe os dados no Streamlit
st.write("### Dados da CCEE")
st.write(df)
