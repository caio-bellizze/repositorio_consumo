import requests
import pandas as pd
import streamlit as st

# Configuração do Streamlit
st.title("Consulta de Dados Abertos da CCEE")

# URL da API
BASE_URL = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
RESOURCE_ID = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

@st.cache_data  # Cache para evitar múltiplas chamadas desnecessárias
def fetch_data():
    """ Função para baixar todos os dados da API e armazenar no cache """
    params = {"resource_id": RESOURCE_ID, "limit": 1}
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "result" in data and "total" in data["result"]:
        total_records = data["result"]["total"]
        st.write(f"Total de registros disponíveis: {total_records}")

        # Ajuste do batch size para otimizar sem sobrecarregar a API
        batch_size = 5000
        all_records = []

        # Loop para baixar os dados
        for offset in range(0, total_records, batch_size):
            params = {"resource_id": RESOURCE_ID, "limit": batch_size, "offset": offset}
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            # Se a API retorna os registros corretamente
            if "result" in data and "records" in data["result"]:
                records = data["result"]["records"]
                all_records.extend(records)
            else:
                st.error(f"Erro ao buscar dados na página com offset {offset}. Parando...")
                break  # Evita loop infinito se a API falhar

            # Atualiza a tela com progresso
            st.write(f"Registros baixados: {len(all_records)} / {total_records}")

        return pd.DataFrame(all_records)

    else:
        st.error("Não foi possível obter os dados da API.")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


# Chama a função e exibe os dados no Streamlit
df = fetch_data()

if not df.empty:
    st.write("### Dados extraídos:")
    st.dataframe(df)

    # Opção para baixar os dados
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", csv, "dados_ccee.csv", "text/csv", key="download-csv")

else:
    st.warning("Nenhum dado foi carregado.")
