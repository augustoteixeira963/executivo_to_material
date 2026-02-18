# Gerador de Orçamento com IA e SINAPI

Este projeto utiliza Inteligência Artificial (OpenAI/Google Gemini via OpenRouter) para extrair serviços de arquivos PDF de arquitetura (plantas baixas) e precificá-los automaticamente utilizando a base de dados oficial do SINAPI.

## Funcionalidades

- **Extração com IA**: Lê PDFs de engenharia/arquitetura e identifica serviços.
- **Tradução Técnica**: Converte termos de projeto (" colocar piso") para termos técnicos ("ASSENTAMENTO DE PISO CERÂMICO").
- **Precificação SINAPI**: Busca automática na tabela SINAPI (Excel) e calcula custos.
- **Edição e Exportação**: Interface visual para ajustar quantidades, escolher composições e exportar para CSV/Excel.

## Como Usar

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Execute o app:

   ```bash
   streamlit run app.py
   ```

3. Na interface:
   - Insira sua chave de API (OpenRouter).
   - Faça upload do PDF.
   - Digite o número da página a analisar.
   - Clique em "Extrair Serviços".

## Estrutura

- `app.py`: Aplicação principal Streamlit.
- `modules/`: Módulos agnósticos (ETL, AI).
- `data/`: Arquivos de dados (SINAPI).

## Requisitos

- Python 3.8+
- Chave de API OpenRouter
