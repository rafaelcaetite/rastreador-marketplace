# OLX Deal Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir uma esteira automatizada em Python que monitora anúncios de MacBook Air M2 na OLX Brasil (R$ 3.000 a R$ 5.000 com OLX Pay / Entrega), deduplica via SQLite e envia alertas instantâneos no Telegram a cada 10 minutos.

**Architecture:** Módulos desacoplados: `scraper/` (coleta HTTP assíncrona do payload Next.js da OLX), `models.py` (dados normalizados), `filter.py` (regras de preço, entrega e palavras negativas), `database.py` (deduplicação com SQLite), `notifier/` (alertas via Telegram Bot API) e `main.py` (orquestrador com CLI para loop contínuo e modo `--dry-run`).

**Tech Stack:** Python 3.12, `httpx`, `beautifulsoup4`, `python-dotenv`, `pytest`, SQLite.

## Global Constraints

- Item alvo: MacBook Air M2
- Faixa de preço: R$ 3.000,00 a R$ 5.000,00
- Abrangência: Brasil inteiro com OLX Pay / Entrega
- Banco local: SQLite (`deals.db`)
- Alertas: Telegram Bot API com suporte a `--dry-run` para testes locais
- Frequência padrão: 10 minutos

---

### Task 1: Estrutura do Projeto, Ambiente e Modelos de Dados

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `models.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `models.AdItem`: Dataclass contendo `id`, `title`, `price`, `url`, `location`, `has_delivery`, `image_url`
  - `config.Config`: Dataclass de configuração carregada de variáveis de ambiente

- [ ] **Step 1: Criar arquivo de teste para `AdItem` e `Config`**
- [ ] **Step 2: Executar pytest para confirmar falha (vermelho)**
- [ ] **Step 3: Implementar `requirements.txt`, `.env.example`, `config.py` e `models.py`**
- [ ] **Step 4: Executar pytest para confirmar passagem (verde)**
- [ ] **Step 5: Commit git com mensagem descritiva**

---

### Task 2: Banco de Dados SQLite e Deduplicação

**Files:**
- Create: `database.py`
- Create: `tests/test_database.py`

**Interfaces:**
- Consumes: `models.AdItem`
- Produces:
  - `database.DatabaseManager`: Métodos `is_ad_seen(ad_id: str) -> bool` e `mark_ad_seen(ad: AdItem) -> None`

- [ ] **Step 1: Criar testes unitários para inicialização do banco, verificação e inserção de anúncios**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `database.py` usando `sqlite3` com tabela `seen_ads` e queries parametrizadas**
- [ ] **Step 4: Executar pytest e garantir passagem**
- [ ] **Step 5: Commit git**

---

### Task 3: Mecanismo de Filtragem (Preço, Entrega e Palavras-Chave)

**Files:**
- Create: `filters.py`
- Create: `tests/test_filters.py`

**Interfaces:**
- Consumes: `models.AdItem`, `config.Config`
- Produces:
  - `filters.AdFilter`: Método `is_valid(ad: AdItem) -> tuple[bool, str]` retornando se o anúncio é aceito e o motivo do descarte caso rejeitado.

- [ ] **Step 1: Escrever testes unitários com casos reais:**
  - Anúncio válido (MacBook Air M2, R$ 3.800, com entrega) -> aceito
  - Anúncio fora do preço (R$ 2.500 ou R$ 5.500) -> rejeitado
  - Anúncio sem entrega -> rejeitado
  - Anúncio de carcaça / defeito ("MacBook Air M2 tela trincada para peças") -> rejeitado
  - Anúncio falso positivo ("Capa para MacBook Air M2", "Carregador") -> rejeitado
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `filters.py` com regex e normalização de texto**
- [ ] **Step 4: Executar pytest e garantir cobertura de 100% dos casos de borda**
- [ ] **Step 5: Commit git**

---

### Task 4: Notificador Telegram (com modo Dry-Run)

**Files:**
- Create: `notifier/telegram_notifier.py`
- Create: `tests/test_notifier.py`

**Interfaces:**
- Consumes: `models.AdItem`, `config.Config`
- Produces:
  - `notifier.TelegramNotifier`: Método `async send_alert(ad: AdItem) -> bool`

- [ ] **Step 1: Escrever testes unitários mockando chamadas HTTP para a API do Telegram e testando modo dry-run**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `notifier/telegram_notifier.py` usando `httpx.AsyncClient` com envio de foto e texto formatado**
- [ ] **Step 4: Executar pytest e garantir aprovação**
- [ ] **Step 5: Commit git**

---

### Task 5: Scraper da OLX (Extração de Payload Next.js e Requisições HTTP)

**Files:**
- Create: `scraper/olx_scraper.py`
- Create: `tests/test_scraper.py`
- Create: `tests/fixtures/olx_mock_page.html`

**Interfaces:**
- Consumes: `config.Config`
- Produces:
  - `scraper.OLXScraper`: Método `async search(query: str) -> list[AdItem]`

- [ ] **Step 1: Criar fixture com HTML representativo da OLX e teste unitário do parser de JSON `__NEXT_DATA__` e fallback**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `scraper/olx_scraper.py` com extração de `props.pageProps.ads` e headers de navegação realistas**
- [ ] **Step 4: Executar pytest e validar parsing**
- [ ] **Step 5: Commit git**

---

### Task 6: Orquestrador da Esteira e CLI Principal

**Files:**
- Create: `pipeline.py`
- Create: `main.py`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: Todos os módulos anteriores
- Produces:
  - CLI com flags `--once`, `--dry-run` e agendamento de loop a cada 10 min

- [ ] **Step 1: Escrever teste de integração ponta a ponta da esteira (pipeline)**
- [ ] **Step 2: Implementar `pipeline.py` orquestrando busca -> filtro -> banco -> alerta**
- [ ] **Step 3: Implementar `main.py` com loop assíncrono e tratamento de sinais de interrupção (Ctrl+C)**
- [ ] **Step 4: Criar `Dockerfile` e `docker-compose.yml` para facilitar deploy em VPS**
- [ ] **Step 5: Executar suite completa de testes com pytest**
- [ ] **Step 6: Executar teste real no terminal via `python main.py --dry-run --once`**
- [ ] **Step 7: Commit final git**
