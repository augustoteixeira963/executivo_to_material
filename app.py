import streamlit as st
import pandas as pd
from modules.etl import carregar_motor_sinapi
from modules.ai import extrair_servicos_pdf_ia

# ==============================================================================
# 🎯 MÓDULO PRINCIPAL: Gerador de Orçamento com IA
# ==============================================================================
# Este arquivo é o "maestro" da aplicação. Ele conecta:
# 1. A interface visual (Streamlit)
# 2. O processamento de dados (Pandas)
# 3. As funções de inteligência artificial (módulo 'ai')
# 4. As funções de leitura de banco de dados (módulo 'etl', para o SINAPI)

# --- CONFIGURAÇÃO E CACHE (ETL) ---
# Define o título da aba do navegador e o layout "wide" (tela cheia)
st.set_page_config(page_title="Gerador de Orçamento IA", layout="wide")

# Nome do arquivo base do SINAPI (Sistema Nacional de Pesquisa de Custos e Índices da Construção Civil)
NOME_ARQUIVO = "data/SINAPI_Custo_Ref_Composicoes_Analitico_SP_202412_NaoDesonerado.xlsx"

# Carrega o banco de dados do SINAPI na memória ram.
# A função 'carregar_motor_sinapi' foi separada em outro arquivo (modules/etl.py) para organização.
df_sinapi = carregar_motor_sinapi(NOME_ARQUIVO)

# --- MEMÓRIA DA SESSÃO (STATE MACHINE) ---
# O Streamlit roda o script inteiro a cada clique. Por isso, usamos o 'session_state'
# para "lembrar" das variáveis entre as interações (ex: manter a lista de serviços carregada).

if 'orcamento_final' not in st.session_state:
    # Cria um DataFrame vazio para armazenar o orçamento final
    st.session_state['orcamento_final'] = pd.DataFrame(columns=["PÁGINA", "SERVIÇO ORIGINAL", "COMPOSIÇÃO SINAPI", "QTD", "UND", "CUSTO UNIT.", "TOTAL"])
if 'fila_servicos' not in st.session_state:
    # Lista vazia que vai receber os itens extraídos do PDF
    st.session_state['fila_servicos'] = []
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = None
if 'busca_atual' not in st.session_state:
    st.session_state['busca_atual'] = []
if 'msg_busca_status' not in st.session_state:
    st.session_state['msg_busca_status'] = None

def buscar_sinapi_callback(id_widget, termos_alt, df):
    """
    Callback para buscar no SINAPI.
    Executa ANTES do re-render, permitindo atualizar o widget de texto sem erro.
    """
    # Limpa status anterior
    st.session_state['msg_busca_status'] = None
    st.session_state['busca_atual'] = []
    
    # Pega o valor atual do widget (o que o usuário digitou ou estava lá)
    termo_busca = st.session_state.get(f"term_{id_widget}", "")
    
    tentativas = [termo_busca] + termos_alt
    resultados_encontrados = False
    palavras_ignoradas = ['DE', 'DA', 'DO', 'COM', 'SEM', 'PARA', 'POR', 'EM', 'UMA', 'UM', 'E', 'OU']
    
    for termo_tentativa in tentativas:
        palavras_chave = [p for p in termo_tentativa.upper().split() if p not in palavras_ignoradas and len(p) > 1]
        
        if not palavras_chave:
            continue
            
        base_busca = df['DESCRICAO DA COMPOSICAO'].astype(str).str.upper()
        mascara = pd.Series([True] * len(df), index=df.index)
        
        for palavra in palavras_chave:
            mascara = mascara & base_busca.str.contains(palavra, regex=False, na=False)
        
        resultados_df = df[mascara]
        
        if not resultados_df.empty:
            # SUCESSO!
            # Atualiza o WIDGET para o termo que funcionou (Isso é permitido aqui dentro do callback)
            st.session_state[f"term_{id_widget}"] = termo_tentativa
            
            # Salva Mensagem de Sucesso para exibir no app
            st.session_state['msg_busca_status'] = ("success", f"✅ Encontrado com: '{termo_tentativa}'")
            
            linhas = []
            for index, linha in resultados_df.head(10).iterrows():
                linhas.append({
                    "COMPOSIÇÃO": linha['DESCRICAO DA COMPOSICAO'],
                    "UND": linha.get('UNIDADE', 'UN'),
                    "CUSTO": linha.get('CUSTO TOTAL', 0.0)
                })
            st.session_state['busca_atual'] = linhas
            resultados_encontrados = True
            break
            
    if not resultados_encontrados:
        st.session_state['msg_busca_status'] = ("warning", f"⚠️ Zero resultados encontrados para '{termo_busca}' e {len(termos_alt)} alternativas.")

# --- FRONT-END E SIDEBAR ---
st.title("🏗️ Extrator e Precificador IA")

# Cria a barra lateral para configurações globais
with st.sidebar:
    st.header("Configurações")
    # Campo de senha para a API Key (tipo 'password' esconde os caracteres)
    api_key = st.text_input("Chave API OpenRouter", type="password")
    # Widget de upload de arquivo
    arquivo_pdf = st.file_uploader("Upload do Projeto Executivo (PDF)", type=["pdf"])

# Divide a tela principal em duas colunas iguais (1 para 1)
col1, col2 = st.columns([1, 1])

# --- COLUNA 1: EXTRAÇÃO E CONSTRUÇÃO ---
with col1:
    st.header("1. Extração de Prancha")
    
    # Campo numérico para o usuário escolher a página
    pag_input = st.number_input("Qual página do projeto deseja analisar?", min_value=1, step=1, key="input_pagina_alvo")
    
    # Botão que aciona a IA
    if st.button("📄 Extrair Serviços com IA"):
        if arquivo_pdf and api_key:
            # st.spinner mostra um "loading" enquanto a função roda
            with st.spinner(f"Lendo página {pag_input} e processando com IA..."):
                st.session_state['pagina_atual'] = pag_input
                # Lê os bytes do arquivo enviado
                pdf_bytes = arquivo_pdf.getvalue() 
                # Chama a função inteligente do módulo 'ai'
                st.session_state['fila_servicos'] = extrair_servicos_pdf_ia(pdf_bytes, pag_input, api_key)
                st.session_state['busca_atual'] = [] 
                # Reinicia o app para atualizar a tela com os novos dados
                st.rerun()
        else:
            st.warning("Faça o upload do PDF e insira a chave da API na barra lateral.")

    st.divider()

    # Verifica se há serviços na fila para serem processados
    if st.session_state['fila_servicos']:
        st.header("2. Validação e Precificação")
        
        # --- SELECTBOX EM VEZ DE FILA (Melhoria de UX) ---
        # Cria uma lista formatada para o selectbox
        opcoes_servicos = [f"{i}: {s.get('servico_original', 'Desconhecido')}" for i, s in enumerate(st.session_state['fila_servicos'])]
        
        # Permite ao usuário escolher qualquer item da lista
        indice_selecionado = st.sidebar.selectbox(
            "📋 Fila de Serviços (Selecione um para editar)",
            options=range(len(opcoes_servicos)),
            format_func=lambda x: opcoes_servicos[x]
        )
        
        # Pega o objeto de serviço baseado na escolha do usuário
        servico_foco = st.session_state['fila_servicos'][indice_selecionado]
        
        # Extrai os dados do dicionário JSON retornado pela IA
        servico_original = servico_foco.get('servico_original', 'Desconhecido')
        termo_principal = servico_foco.get('termo_principal', servico_original)
        termos_alt = servico_foco.get('termos_alternativos', [])
        
        # Cria um ID único para os widgets do Streamlit não conflitarem entre recargas
        id_unico = f"{st.session_state['pagina_atual']}_{servico_original[:10]}"
        
        st.info(f"**Projeto:** {servico_original.upper()}\n### Sugestão IA: {termo_principal}")
        
        # Input numérico para quantidade (já vem preenchido pela IA se possível)
        qtd_medida = st.number_input(
            "Quantos metros/unidades no total?", 
            min_value=0.0, 
            value=float(servico_foco.get('quantidade', 1.0)),
            format="%.2f", 
            key=f"qtd_{id_unico}"
        )
        
        # Campo de busca editável
        termo_busca = st.text_input(
            "Refinar termo de busca no SINAPI:", 
            value=termo_principal, 
            key=f"term_{id_unico}"
        )
        
        # Exibe os termos alternativos como uma dica amigável (UX/UI para o orçamentista)
        if termos_alt:
            st.caption("💡 **Termos alternativos gerados pela IA (Copie e cole se precisar):** " + " | ".join(termos_alt))
        
        # Lógica de Busca no Banco de Dados (Pandas)
        # O botão agora usa um CALLBACK (on_click) para processar a busca antes de recarregar a tela.
        # Isso permite atualizar o input text (termo_busca) sem causar o erro StreamlitAPIException.
        st.button(
            "🔍 Buscar no SINAPI", 
            key=f"btn_busca_{id_unico}",
            on_click=buscar_sinapi_callback,
            args=(id_unico, termos_alt, df_sinapi)
        )
        
        # Exibe mensagens de status (processadas no callback)
        if st.session_state.get('msg_busca_status'):
            tipo, msg = st.session_state['msg_busca_status']
            if tipo == 'success':
                st.success(msg)
            elif tipo == 'warning':
                st.warning(msg)
            # Limpa a mensagem após exibir (para não ficar persistente sem sentido)
            st.session_state['msg_busca_status'] = None

        # Exibe os resultados da busca com botões para adicionar
        if st.session_state['busca_atual']:
            st.write("### Selecione a composição correta:")
            for idx, row in enumerate(st.session_state['busca_atual']):
                c_texto, c_botao = st.columns([4, 1])
                c_texto.write(f"**{row['COMPOSIÇÃO']}** (R$ {row['CUSTO']:.2f} / {row['UND']})")
                
                if c_botao.button("➕ Adicionar", key=f"add_{id_unico}_{idx}"):
                    # Cria um novo DataFrame com UMA linha contendo o item escolhido
                    novo_item = pd.DataFrame([{
                        "PÁGINA": st.session_state['pagina_atual'],
                        "SERVIÇO ORIGINAL": servico_original,
                        "COMPOSIÇÃO SINAPI": row['COMPOSIÇÃO'],
                        "QTD": qtd_medida,
                        "UND": row['UND'],
                        "CUSTO UNIT.": row['CUSTO'],
                        "TOTAL": qtd_medida * row['CUSTO']
                    }])
                    
                    # Concatena ao DataFrame principal do orçamento
                    st.session_state['orcamento_final'] = pd.concat([st.session_state['orcamento_final'], novo_item], ignore_index=True)
                    # Remove da fila de pendências usando o índice selecionado
                    st.session_state['fila_servicos'].pop(indice_selecionado) 
                    st.session_state['busca_atual'] = []
                    st.rerun()

        # Botão para pular o item se não encontrar correspondência
        if st.button("⏭️ Ignorar e remover da lista", key=f"skip_{id_unico}"):
            st.session_state['fila_servicos'].pop(indice_selecionado) # Remove o item selecionado
            st.session_state['busca_atual'] = []
            st.rerun()

    elif st.session_state['pagina_atual'] is not None:
        st.success("✅ Fila vazia! Todos os serviços desta página foram analisados.")


with col2:
    st.header("3. Orçamento Consolidado")
    
    if not st.session_state['orcamento_final'].empty:
        # st.data_editor permite edição nativa como no Excel
        df_editado = st.data_editor(
            st.session_state['orcamento_final'], 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic", # MÁGICA: Permite deletar (Delete/Backspace) ou adicionar linhas
            key="editor_tabela_orcamento", # Chave única de renderização
            column_config={
                "QTD": st.column_config.NumberColumn("QTD", format="%.2f"),
                "CUSTO UNIT.": st.column_config.NumberColumn("CUSTO UNIT.", format="R$ %.2f"),
                "TOTAL": st.column_config.NumberColumn("TOTAL", format="R$ %.2f")
            }
        )

        # (O seu st.data_editor continua aqui em cima)
        
        # TRAVA DE SEGURANÇA: Remove qualquer linha onde o Serviço ou Custo seja nulo (Fantasma)
        df_editado = df_editado.dropna(subset=['SERVIÇO ORIGINAL', 'CUSTO UNIT.'])
        df_editado = df_editado[df_editado['SERVIÇO ORIGINAL'].astype(str).str.strip() != 'None']
        
        # (O restante do código de total e exportação continua aqui para baixo)
        # Salva as exclusões na memória para não voltarem quando a página atualizar
        st.session_state['orcamento_final'] = df_editado
        
        # Recalcula o total baseado na tabela já com as linhas excluídas
        total = df_editado['TOTAL'].sum()
        st.metric("Custo Estimado (Base SINAPI)", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Prepara a exportação (Padrão Excel BR)
        df_export = df_editado.copy()
        for col in ['QTD', 'CUSTO UNIT.', 'TOTAL']:
            df_export[col] = df_export[col].apply(lambda x: f"{x:.2f}".replace('.', ','))
            
        csv = df_export.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Exportar Orçamento (CSV)",
            data=csv,
            file_name='orcamento_final.csv',
            mime='text/csv',
        )
        
        # Botão de pânico (Boas práticas de UI)
        if st.button("🗑️ Limpar Todo o Orçamento"):
            st.session_state['orcamento_final'] = st.session_state['orcamento_final'].iloc[0:0]
            st.rerun()
    else:
        st.info("O orçamento final aparecerá aqui após adicionar itens.")