<div align="center">

# 🛒 Rastreador de Marketplace

**Monitoramento multi-plataforma de ofertas em tempo real com categorização automática, benchmark estatístico de preços e sincronização com Google Sheets e Telegram.**

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Architecture: Modular](https://img.shields.io/badge/architecture-SOLID%20%2F%20modular-brightgreen)]()

</div>

---

## 📌 Visão Geral

O **Rastreador de Marketplace** é uma solução de engenharia de dados e automação desenvolvida para monitorar os três maiores marketplaces do Brasil em um único fluxo unificado:
* 🟢 **OLX Brasil**
* 🟡 **Mercado Livre**
* 🟠 **Shopee**

A esteira extrai anúncios continuamente, categoriza especificações de hardware (Modelo, Chip, RAM, Armazenamento), calcula a **média de mercado em tempo real** para cada SKU e destaca automaticamente quando um item está com preço de oportunidade.

---

## 🏗️ Arquitetura

O projeto foi construído seguindo princípios **SOLID**, design patterns (*Strategy* para coletores, *Pipeline* para orquestração) e separação estrita de responsabilidades:

```text
rastreador-marketplace/
├── config.py                 # Configuração centralizada via Dataclass e variáveis de ambiente
├── models.py                 # Modelo canônico de dados (AdItem)
├── database.py               # Camada de persistência e deduplicação (SQLite)
├── filters.py                # Pipeline de validação com filtros de preço e termos negativos
├── pipeline.py               # Orquestrador do ciclo de vida da coleta
├── main.py                   # Interface de Linha de Comando (CLI)
│
├── scraper/                  # Camada de Coleta (Strategy Pattern)
│   ├── base_scraper.py       # Interface abstrata BaseScraper
│   ├── olx_scraper.py        # Coletor OLX via curl_cffi (bypass Cloudflare)
│   ├── ml_scraper.py         # Coletor Mercado Livre
│   └── shopee_scraper.py     # Coletor Shopee Brasil
│
├── analyzer/                 # Camada de Inteligência e Processamento
│   ├── spec_extractor.py     # Extrator semântico de especificações de hardware
│   └── pricing_engine.py     # Motor estatístico de benchmark e cálculo de desconto
│
├── exporter/                 # Camada de Exportação
│   ├── sheets_exporter.py    # Sincronização Google Sheets (cria aba por termo)
│   └── excel_exporter.py     # Exportação local estruturada (.xlsx e .csv)
│
└── notifier/                 # Camada de Notificação
    └── telegram_notifier.py  # Bot do Telegram com fotos, métricas e botões inline
```

---

## 📈 Lógica de Benchmark de Preços

Para responder se uma oferta é realmente vantajosa, o motor estatístico agrupa os produtos por **SKU Canônico** (ex: `MacBook Air | Apple M2 | 8GB | 256GB`) e calcula:

$$\text{Desconto} = \frac{\text{Preço Médio do SKU} - \text{Preço Anunciado}}{\text{Preço Médio do SKU}} \times 100$$

* 🔥 **SUPER OPORTUNIDADE:** $\ge 20\%$ abaixo da média do mesmo produto.
* ✅ **BOM PREÇO:** Entre $10\%$ e $19.9\%$ abaixo da média.
* ⚖️ **PREÇO NA MÉDIA:** Entre $-10\%$ e $+9.9\%$ da média.
* ⚠️ **ACIMA DA MÉDIA:** Mais de $10\%$ mais caro que a média de mercado.

---

## 📊 Estrutura da Planilha Gerada

Cada busca gera (ou atualiza) uma aba própria no Google Sheets e um arquivo correspondente em `data/`:

| Coluna | Descrição |
| :--- | :--- |
| **Data/Hora** | Data e horário da detecção |
| **Fonte** | `OLX`, `Mercado Livre` ou `Shopee` |
| **Linha** | Ex: `MacBook Air`, `MacBook Pro` |
| **Processador** | Ex: `Apple M2`, `Apple M1 Pro` |
| **Memória RAM** | Ex: `8GB`, `16GB`, `24GB` |
| **Armazenamento** | Ex: `256GB`, `512GB`, `1TB` |
| **Preço (R$)** | Valor anunciado pelo vendedor |
| **Média Mercado (R$)** | Preço médio calculado para aquele SKU |
| **Desconto vs Média (%)** | Percentual de economia em relação à média |
| **Avaliação da Oferta** | Classificação algorítmica |
| **Título do Anúncio** | Nome original do anúncio |
| **Localização** | Cidade / Estado |
| **Entrega** | `Sim` (OLX Pay / Envios) ou `Não` |
| **Link do Anúncio** | Link direto para compra |

---

## 🚀 Como Executar

### 1. Instalação

```bash
git clone https://github.com/seu-usuario/rastreador-marketplace.git
cd rastreador-marketplace
pip install -r requirements.txt
cp .env.example .env
```

### 2. Execução Pontual (Simulação / Dry-Run)

```bash
# Busca qualquer item e gera planilha em data/
python main.py --dry-run --once --query "Macbook Air M2"

# Filtrar por marketplaces específicos
python main.py --dry-run --once --query "Playstation 5" --sources olx,ml
```

### 3. Execução Contínua em Segundo Plano

```bash
python main.py --query "Macbook" --interval 10
```

---

## ☁️ Configuração do Google Sheets

1. No [Google Cloud Console](https://console.cloud.google.com/), ative a **Google Sheets API** e a **Google Drive API**.
2. Crie uma **Conta de Serviço (Service Account)** e faça o download da chave JSON com o nome `credentials.json` na raiz do projeto.
3. No Google Sheets, crie uma planilha com o nome `Rastreador de Marketplace`.
4. Compartilhe a planilha com o e-mail da sua Service Account como **Editor**.
5. Ao executar a esteira, ela criará automaticamente uma **nova aba** para cada termo de busca pesquisado.

---

## 🤖 Configuração do Telegram

Preencha no seu arquivo `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

---

## 🐳 Docker & Deploy em VPS

Para rodar 24/7 em um servidor com consumo de memória inferior a 50MB de RAM:

```bash
docker compose up -d --build
```

---

## 🧪 Testes Automatizados

O projeto conta com cobertura total de testes unitários:

```bash
pytest
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte `LICENSE` para mais informações.
