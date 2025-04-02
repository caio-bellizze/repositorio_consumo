import requests
import pandas as pd
import streamlit as st

# Configuração do Streamlit
st.title("Consulta de Dados Abertos da CCEE")

# URL da API
BASE_URL = "https://dadosabertos.ccee.org.br/api/3/action/datastore_search"
RESOURCE_ID = "b854f7bc-94a3-423a-96b7-2d4756ec77d1"

@st.cache_data  # Cache para evitar reprocessamento sempre que a página for atualizada
def fetch_all_data():
    """ Baixa TODOS os registros da API em lotes """
    limit = 10000  # Quantidade de registros por requisição
    offset = 0
    all_records = []

    # Obtendo o número total de registros
    response = requests.get(f"{BASE_URL}?resource_id={RESOURCE_ID}&limit=1")
    data = response.json()

    if "result" in data and "total" in data["result"]:
        total_records = data["result"]["total"]
        st.write(f"Total de registros disponíveis: {total_records}")

        with st.spinner("Baixando os dados..."):
            while offset < total_records:
                url = f"{BASE_URL}?resource_id={RESOURCE_ID}&limit={limit}&offset={offset}"
                response = requests.get(url)
                data = response.json()

                # Se houver dados, adicionamos ao total
                records = data.get("result", {}).get("records", [])
                if not records:
                    break  # Se a resposta vier vazia, paramos o loop
                
                all_records.extend(records)
                offset += limit  # Atualiza o offset para pegar o próximo lote

                st.write(f"Registros baixados: {len(all_records)} / {total_records}")

        return pd.DataFrame(all_records)

    else:
        st.error("Não foi possível obter os dados da API.")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


# Chama a função e exibe os dados no Streamlit
df = fetch_all_data()

if not df.empty:
    st.write("### Dados extraídos:")
    st.dataframe(df)

    # Opção para baixar os dados
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", csv, "dados_ccee.csv", "text/csv", key="download-csv")

else:
    st.warning("Nenhum dado foi carregado.")
