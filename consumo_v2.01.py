import requests
import pandas as pd
import streamlit as st

# Configuração da API
base_url = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

limit = 10000  # Registros por requisição
offset = 0  # Começa do primeiro registro
all_records = []

st.title("Importação de Dados - API CCEE")
progress_bar = st.progress(0)  # Barra de progresso no Streamlit

max_records = 20000  # Limite para testes, pode remover depois

# Paginação para pegar todos os dados
while True:
    url = f"{base_url}?resource_id={resource_id}&limit={limit}&offset={offset}"
    response = requests.get(url, timeout=30)
    data = response.json()
    
    records = data.get("result", {}).get("records", [])
    if not records:
        break  # Sai do loop se não houver mais dados
    
    all_records.extend(records)
    offset += limit  # Avança para a próxima página

    # Atualiza a barra de progresso
    progress_bar.progress(min(1.0, offset / max_records))

    # Interrompe se atingir o limite para testes
    if len(all_records) >= max_records:
        break

# Criar DataFrame com todos os dados coletados
df = pd.DataFrame(all_records)

# Exibir no Streamlit
st.write(f"Total de registros carregados: {df.shape[0]}")
st.dataframe(df)  # Mostra um dataframe interativo no Streamlit
