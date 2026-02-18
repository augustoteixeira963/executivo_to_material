import fitz  # PyMuPDF
import json
import streamlit as st
from openai import OpenAI

def extrair_servicos_pdf_ia(arquivo_pdf_bytes, pagina: int, api_key: str):
    """Lê a página do PDF e usa IA para extrair e traduzir termos para o padrão SINAPI."""
    if not api_key:
        st.error("⚠️ Digite sua chave da API do OpenRouter na barra lateral.")
        return []

    try:
        doc = fitz.open(stream=arquivo_pdf_bytes, filetype="pdf")
        indice_real = pagina - 1

        if indice_real < 0 or indice_real >= len(doc):
            st.error(f"A página {pagina} não existe no documento.")
            return []

        texto_pagina = doc.load_page(indice_real).get_text("text")
        
        if not texto_pagina.strip():
            st.warning("Página em branco ou ilegível (sem texto pesquisável).")
            return []

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        # O PROMPT MESTRE
        prompt = f"""
        Atue como um Engenheiro de Custos sênior especialista na base de dados SINAPI.
        Sua missão é extrair os serviços da prancha de arquitetura e traduzir a "Linguagem de Arquiteto" para a "Linguagem Técnica do SINAPI", fornecendo os melhores termos de busca.
        
        Pense nos jargões do SINAPI:
        - O SINAPI frequentemente usa "REMOÇÃO" em vez de "DEMOLIÇÃO" para itens de acabamento (pisos, portas, bancadas).
        - "Fazer parede" vira "ALVENARIA DE VEDAÇÃO".
        - "Pintar" vira "PINTURA ACRÍLICA" ou "EMASSAMENTO".
        - "Colocar piso" vira "ASSENTAMENTO DE PISO" ou "REVESTIMENTO CERÂMICO".
        
        Regras de Saída:
        1. Retorne EXCLUSIVAMENTE um array JSON puro, sem markdown.
        2. Siga EXATAMENTE esta estrutura de chaves:
        [
          {{
            "servico_original": "Texto exato como está na prancha",
            "termo_principal": "MELHOR TERMO SINAPI (ex: REMOÇÃO DE PISO)",
            "termos_alternativos": ["DEMOLIÇÃO DE PISO", "RETIRADA DE REVESTIMENTO", "PISO CERÂMICO"],
            "quantidade": 1.0,
            "unidade": "vb",
            "observacao": "..."
          }}
        ]
        3. Forneça sempre de 4 a 6 termos alternativos bem focados em substantivos técnicos DO SINAPI.
        
        Texto bruto da prancha:
        {texto_pagina}
        """
        
        resposta = client.chat.completions.create(
            model="google/gemini-2.5-flash", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        resultado = resposta.choices[0].message.content.strip()
        resultado = resultado.replace("```json", "").replace("```", "").strip()

        dados = json.loads(resultado)
        return dados
        
    except json.JSONDecodeError:
        st.error("A IA falhou na formatação. Clique em extrair novamente.")
        return []
    except Exception as e:
        st.error(f"Falha de Integração: {e}")
        return []
