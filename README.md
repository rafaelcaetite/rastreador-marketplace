# Rastreador de Marketplace

Pipeline autônomo em Python para monitoramento de ofertas em tempo real nos principais marketplaces brasileiros (**OLX**, **Mercado Livre** e **Shopee**). Inclui normalização semântica de especificações técnicas, benchmark estatístico de preços para detecção de anomalias (ofertas abaixo da média de mercado), exportação automatizada para **Google Sheets** (com particionamento por abas) e disparo de alertas via **Telegram**.

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest%2017%2F17%20passing-brightgreen)]()
[![Code Style](https://img.shields.io/badge/code%20style-pep8-black)](https://peps.python.org/pep-0008/)

---

## Arquitetura

O sistema adota separação estrita de camadas e design patterns (*Strategy* nos coletores, *Pipeline* no orquestrador de dados):

```text
rastreador-marketplace/
├── config.py                 # Configurações tipadas via Dataclass e variáveis de ambiente
├── models.py                 # Modelo de dados canônico (AdItem)
├── database.py               # Camada de persistência e deduplicação via SQLite
├── filters.py                # Pipeline de validação, limites de preço e filtros negativos
├── pipeline.py               # Orquestrador unificado (Scrape -> Analyze -> Export -> Notify)
├── main.py                   # Interface de Linha de Comando (CLI)
│
├── scraper/                  # Strategy Pattern para plataformas de busca
│   ├── base_scraper.py       # Interface abstrata BaseScraper
│   ├── olx_scraper.py        # Coletor OLX via curl_cffi com bypass de TLS/Cloudflare
│   ├── ml_scraper.py         # Coletor Mercado Livre
│   └── shopee_scraper.py     # Coletor Shopee Brasil
│
├── analyzer/                 # Processamento semântico e precificação
│   ├── spec_extractor.py     # Parser regex para Linha, Chip, RAM e Armazenamento
│   └── pricing_engine.py     # Motor estatístico de média móvel e cálculo de desconto
│
├── exporter/                 # Exportação de relatórios
│   ├── sheets_exporter.py    # Sincronização direta com Google Sheets API via gspread
│   └── excel_exporter.py     # Geração de arquivos locais (.xlsx e .csv)
│
└── notifier/                 # Canal de alerta
    └── telegram_notifier.py  # Despachante de mensagens e fotos via Telegram Bot API
```

---

## Mecanismo de Inteligência de Preço

A avaliação de atratividade de cada anúncio não utiliza valores arbitrários; ela agrupa os itens pelo **SKU Canônico** resultante da extração de especificações (ex: `MacBook Air | Apple M2 | 8GB | 256GB`) e calcula a variação em relação à média de mercado daquele modelo exato:

$$\Delta\% = \left(\frac{\bar{P}_{SKU} - P_{\text{anúncio}}}{\bar{P}_{SKU}}\right) \times 100$$

| Classificação | Condição | Ação |
| :--- | :--- | :--- |
| **SUPER OPORTUNIDADE** | $\Delta\% \ge 20\%$ | Alerta prioritário no Telegram + Linha na Planilha |
| **BOM PREÇO** | $10\% \le \Delta\% < 20\%$ | Alerta no Telegram + Linha na Planilha |
| **PREÇO NA MÉDIA** | $-10\% \le \Delta\% < 10\%$ | Registrado na Planilha para base histórica |
| **ACIMA DA MÉDIA** | $\Delta\% < -10\%$ | Registrado na Planilha para base histórica |

---

## Estrutura de Dados da Planilha

Cada termo consultado gera uma aba independente com 14 colunas normalizadas:

| Coluna | Tipo | Exemplo |
| :--- | :--- | :--- |
| **Data/Hora** | String | `05/11/2026 09:19` |
| **Fonte** | String | `OLX`, `Mercado Livre` ou `Shopee` |
| **Linha** | String | `MacBook Air`, `MacBook Pro` |
| **Processador** | String | `Apple M2`, `Apple M1 Pro` |
| **Memória RAM** | String | `8GB`, `16GB`, `24GB` |
| **Armazenamento** | String | `256GB`, `512GB`, `1TB` |
| **Preço (R$)** | Float | `4200.00` |
| **Média Mercado (R$)** | Float | `4901.55` |
| **Desconto vs Média (%)** | String | `14.3%` |
| **Avaliação da Oferta** | String | `BOM PREÇO` |
| **Título do Anúncio** | String | Título original publicado |
| **Localização** | String | Cidade - UF |
| **Entrega** | Boolean | `Sim` / `Não` |
| **Link do Anúncio** | URL | Link direto do produto |

---

## Instalação e Execução

### Pré-requisitos
* Python 3.10 ou superior
* Git

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/rafaelcaetite/rastreador-marketplace.git
cd rastreador-marketplace
pip install -r requirements.txt
cp .env.example .env
```

### 2. Modos de Uso da CLI

```bash
# Execução pontual com saída no terminal (modo dry-run / simulação)
python main.py --dry-run --once --query "Macbook Air M2"

# Filtrar por marketplaces específicos (olx, ml ou shopee)
python main.py --dry-run --once --query "Playstation 5" --sources olx,ml

# Execução em modo contínuo (daemon a cada 10 minutos)
python main.py --query "Macbook" --interval 10
```

---

## Integrações

### Google Sheets

1. No Google Cloud Console, crie uma **Service Account** e ative a **Google Sheets API** e a **Google Drive API**.
2. Baixe o arquivo de credenciais JSON para a raiz do repositório com o nome `credentials.json`.
3. Crie uma planilha no Google Sheets com o nome configurado em `GOOGLE_SHEET_NAME` (padrão: `Rastreador de Marketplace`).
4. Compartilhe a planilha com o e-mail da Service Account com permissão de **Editor**.
5. O pipeline criará automaticamente uma aba separada para cada valor informado em `--query`.

### Telegram Bot

Preencha no arquivo `.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
TELEGRAM_CHAT_ID=987654321
```

---

## Deploy em Servidor (VPS / Docker)

O projeto inclui manifesto Docker otimizado para baixo consumo de memória (< 50MB RAM):

```bash
docker compose up -d --build
docker compose logs -f
```

---

## Testes

Suite de testes automatizados com `pytest`:

```bash
pytest
```

---

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter detalhes.
