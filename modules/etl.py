import pandas as pd
import streamlit as st

@st.cache_data
def carregar_motor_sinapi(caminho_arquivo):
    """
    Motor ETL para o banco de dados do SINAPI.
    """
    try:
        df = pd.read_excel(caminho_arquivo, skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        df = df.dropna(subset=['DESCRICAO DA COMPOSICAO'])
        df = df.drop_duplicates(subset=['DESCRICAO DA COMPOSICAO'])
        
        col_custo = [c for c in df.columns if 'CUSTO' in c and 'TOTAL' in c]
        if col_custo:
            nome_col = col_custo[0]
            df['CUSTO TOTAL'] = df[nome_col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['CUSTO TOTAL'] = pd.to_numeric(df['CUSTO TOTAL'], errors='coerce').fillna(0.0)
            
        return df
    except Exception as e:
        st.error(f"[ERRO DE ETL] Falha ao processar a planilha SINAPI: {e}")
        return pd.DataFrame()
