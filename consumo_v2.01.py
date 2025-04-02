import requests
import pandas as pd
import streamlit as st

# URL base da API
base_url = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"  # ID do conjunto de dados
limit = 1000  # Número de registros por requisição (ajustável)
offset = 0  # Inicia do primeiro registro
all_records = []  # Lista para armazenar todos os registros

# Loop para percorrer todas as páginas de dados
while True:
    url = f"{base_url}?resource_id={resource_id}&limit={limit}&offset={offset}"
    response = requests.get(url)
    data = response.json()
    
    records = data.get("result", {}).get("records", [])
    if not records:
        break  # Sai do loop quando não houver mais registros

    all_records.extend(records)
    offset += limit  # Avança para a próxima página

# Criando DataFrame com todos os registros
df = pd.DataFrame(all_records)

# Exibindo no Streamlit
st.write(df)
