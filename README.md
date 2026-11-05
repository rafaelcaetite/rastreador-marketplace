# 🚀 Plataforma de Inteligência de Ofertas (OLX + Mercado Livre -> Google Sheets & Telegram)

Plataforma autônoma em Python para monitoramento, extração de dados e inteligência estatística de preços de eletrônicos e hardware, com categorização semântica, cálculo de desconto em relação à média de mercado e exportação automática para **Google Sheets** (com abas dedicadas por produto) e alertas no **Telegram**.

---

## 🌟 Principais Funcionalidades

1. **Inteligência de Mercado e Benchmark de Preços:**
   * Agrupa anúncios por **SKU canônico** (ex: `MacBook Air | Apple M2 | 8GB | 256GB`).
   * Calcula a média de mercado do modelo exato e o desconto percentual.
   * Classifica automaticamente cada oferta:
     * 🔥 **SUPER OPORTUNIDADE** ($\ge 20\%$ abaixo da média)
     * ✅ **BOM PREÇO** ($10\%$ a $19.9\%$ abaixo da média)
     * ⚖️ **PREÇO NA MÉDIA** ($-10\%$ a $+9.9\%$ da média)
     * ⚠️ **ACIMA DA MÉDIA** ($> 10\%$ acima da média)

2. **Extrator Semântico de Hardware:**
   * Identifica automaticamente a partir de títulos e descrições:
     * **Linha:** MacBook Air, MacBook Pro, MacBook
     * **Processador:** Apple M1, M1 Pro/Max, M2, M3, M4, Intel Core i5/i7
     * **Memória RAM:** 8GB, 16GB, 24GB, 32GB, 64GB
     * **Armazenamento:** 128GB, 256GB, 512GB, 1TB, 2TB
     * **Tela:** 13", 13.6", 14", 15", 16"

3. **Exportação Dinâmica para Planilhas:**
   * **Google Sheets:** Conecta via `gspread` e cria automaticamente uma **nova Aba (Worksheet)** para cada termo de busca (ex: aba `"MacBook"`, aba `"Macbook Air M2"`).
   * **Backup Local Automático:** Sempre gera e atualiza planilhas em `data/<termo>.xlsx` e `data/<termo>.csv` com 14 colunas estruturadas e auto-ajustadas.

4. **Multi-Fonte e Resiliência Anti-Bot:**
   * Coletor otimizado com `curl_cffi` para contornar Cloudflare na OLX.
   * Conector preparado para Mercado Livre.
   * SQLite (`deals.db`) para deduplicação instantânea.

---

## 📊 Estrutura das Colunas na Planilha

| Coluna | Descrição |
| :--- | :--- |
| **Data/Hora** | Timestamp da coleta (`DD/MM/AAAA HH:MM`) |
| **Fonte** | Origem do anúncio (`OLX` ou `Mercado Livre`) |
| **Linha** | Ex: `MacBook Air`, `MacBook Pro` |
| **Processador** | Ex: `Apple M2`, `Apple M1 Pro` |
| **Memória RAM** | Ex: `8GB`, `16GB` |
| **Armazenamento** | Ex: `256GB`, `512GB`, `1TB` |
| **Preço (R$)** | Preço anunciado pelo vendedor |
| **Média Mercado (R$)** | Média de preço calculada para esse SKU |
| **Desconto vs Média (%)** | Percentual de economia em relação à média |
| **Avaliação da Oferta** | Classificação (ex: `🔥 SUPER OPORTUNIDADE`, `✅ BOM PREÇO`) |
| **Título do Anúncio** | Nome original postado |
| **Localização** | Cidade e Estado |
| **Entrega** | `Sim` (OLX Pay / Envios) ou `Não` |
| **Link do Anúncio** | URL direta para compra |

---

## ⚡ Como Rodar o Projeto

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Rodar Teste no Terminal (com geração de planilha)
```bash
# Busca qualquer produto e gera a planilha correspondente em data/
python main.py --dry-run --once --query "Macbook Air M2"
```
A planilha formatada será salva imediatamente em `data/macbook_air_m2.xlsx` e `data/macbook_air_m2.csv`.

### 3. Rodar a Esteira Contínua (a cada 10 minutos)
```bash
python main.py --query "Macbook" --interval 10
```

---

## 🔗 Configuração do Google Sheets (Service Account)

Para sincronizar suas planilhas diretamente no seu Google Drive:
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto e ative a **Google Sheets API** e a **Google Drive API**.
3. Vá em **Contas de Serviço (Service Accounts)** e crie uma nova conta.
4. Gere uma chave do tipo **JSON** e baixe-a para a pasta do projeto com o nome `credentials.json`.
5. Crie uma planilha vazia no seu Google Sheets chamada `"Radar de Ofertas - Hardware"`.
6. Compartilhe a planilha com o e-mail da sua Service Account (ex: `bot@seu-projeto.iam.gserviceaccount.com`) com permissão de **Editor**.
7. Pronto! A cada execução, o Python criará abas correspondentes ao termo pesquisado.

---

## 🤖 Configuração do Telegram

No arquivo `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_do_bot
TELEGRAM_CHAT_ID=seu_chat_id
```

---

## ☁️ Rodando em VPS com Docker
```bash
docker compose up -d --build
```
