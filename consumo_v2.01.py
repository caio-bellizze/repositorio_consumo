import streamlit as st
import requests
import pandas as pd
import json
 
limit = 10000
cnpj = ""
cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
query = cnpj_limpo
url = f"https://dadosabertos.ccee.org.br/api/3/action/datastore_search?resource_id=b854f7bc-94a3-423a-96b7-2d4756ec77d1&limit={limit}&q={query}"
 
response = requests.get(url)
data = response.json()
records = data.get("result", {}).get("records", [])
df = pd.DataFrame(records)

st.dataframe(df, hide_index=True)
