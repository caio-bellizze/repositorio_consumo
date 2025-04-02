import requests
import pandas as pd
import streamlit as st

base_url = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

limit = 10000  # Máximo por requisição
offset = 0  # Começa do primeiro registro
all_records = []

while True:
    url = f"{base_url}?resource_id={resource_id}&limit={limit}&offset={offset}"
    response = requests.get(url, timeout=30)
    data = response.json()
    
    records = data.get("result", {}).get("records", [])
    if not records:
        break  # Sai do loop se não houver mais dados
    
    all_records.extend(records)
    offset += limit  # Avança para a próxima página

    print(f"Registros coletados: {len(all_records)}")

# Criar DataFrame com todos os dados coletados
df = pd.DataFrame(all_records)
print(f"Total de registros carregados: {df.shape[0]}")


# Criando DataFrame com todos os registros
df = pd.DataFrame(all_records)

# Exibindo no Streamlit
st.write(df)
