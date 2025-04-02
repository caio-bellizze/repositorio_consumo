import requests
import pandas as pd
import streamlit as st

# Configuração da API
base_url = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
resource_id = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

limit = 10000  # Registros por requisição
offset = 0  # Começa do primeiro registro
total_max = 100000  # Estimativa de total de registros, para evitar loop infinito
all_records = []

st.title("Importação de Dados - API CCEE")
progress_bar = st.progress(0)  # Barra de progresso

# Teste inicial: baixar apenas uma pequena quantidade
max_records = 1000000  # Ajuste para testes

while True:
    url = f"{base_url}?resource_id={resource_id}&limit={limit}&offset={offset}"

    # Tenta fazer a requisição com tratamento de erro
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Verifica erros HTTP

        data = response.json()
        records = data.get("result", {}).get("records", [])

        if not records:
            break  # Sai do loop se não houver mais dados

        all_records.extend(records)
        offset += limit  # Avança para a próxima página

        # Atualiza a barra de progresso
        progress_bar.progress(min(1.0, offset / total_max))

        # Para testes: interrompe se atingir o limite
        if len(all_records) >= max_records:
            break

        # Evita sobrecarregar a API
        st.write(f"Registros coletados: {len(all_records)}")
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição: {e}")
        break

# Criar DataFrame com todos os dados coletados
df = pd.DataFrame(all_records)

# Exibir no Streamlit
st.write(f"Total de registros carregados: {df.shape[0]}")
st.write(df)  # Dataframe interativo no Streamlit
