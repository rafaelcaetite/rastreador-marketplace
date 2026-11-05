# Multi-Source Deal Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir a esteira para suportar monitoramento multi-fonte (OLX + Mercado Livre), extração automática de especificações de hardware (Modelo, Chip, RAM, SSD), motor de precificação comparativa (média de mercado e classificação de oferta) e exportação em abas dedicadas no Google Sheets e Excel local.

**Architecture:** Estrutura modular: `analyzer/spec_extractor.py`, `analyzer/pricing_engine.py`, `scraper/base_scraper.py`, `scraper/ml_scraper.py`, `exporter/sheets_exporter.py`, `exporter/excel_exporter.py`, unificados no `pipeline.py`.

**Tech Stack:** Python 3.12, `curl_cffi`, `beautifulsoup4`, `gspread`, `openpyxl`, `pytest`.

## Global Constraints
- Suporte a qualquer termo de busca dinâmico (default: "Macbook")
- Fontes: OLX e Mercado Livre com interface base extensível
- Google Sheets: Cria/atualiza aba com o nome do termo de busca
- Backup local: Salva em `data/<termo>.xlsx`
- Alertas Telegram: Notificações com cálculo de desconto percentual e comparação com a média

---

### Task 1: Modelo AdItem Expandido e Extrator de Especificações (`spec_extractor.py`)

**Files:**
- Modify: `models.py`
- Create: `analyzer/__init__.py`
- Create: `analyzer/spec_extractor.py`
- Create: `tests/test_spec_extractor.py`

**Interfaces:**
- Produces: `analyzer.spec_extractor.HardwareSpecExtractor`:
  - `extract(title: str, description: str = "") -> dict` com `line`, `chip`, `ram`, `ssd`, `sku_key`

- [ ] **Step 1: Escrever testes unitários com diversos títulos reais de MacBooks**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar regex para extração de Linha (Air/Pro), Chip (M1..M4, Intel), RAM e SSD**
- [ ] **Step 4: Executar pytest e garantir 100% de passagem**
- [ ] **Step 5: Commit git**

---

### Task 2: Motor de Precificação Estatística (`pricing_engine.py`)

**Files:**
- Create: `analyzer/pricing_engine.py`
- Create: `tests/test_pricing_engine.py`

**Interfaces:**
- Produces: `analyzer.pricing_engine.PricingEngine`:
  - `calculate_market_metrics(ads: list[AdItem]) -> list[AdItem]`
  - Atualiza em cada anúncio: `market_avg_price`, `discount_pct`, `rating`

- [ ] **Step 1: Escrever testes unitários para cálculo de média, percentual de desconto e classificação de oportunidade**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `pricing_engine.py`**
- [ ] **Step 4: Executar pytest e validar métricas**
- [ ] **Step 5: Commit git**

---

### Task 3: Coletor do Mercado Livre (`scraper/ml_scraper.py` e `scraper/base_scraper.py`)

**Files:**
- Create: `scraper/base_scraper.py`
- Modify: `scraper/olx_scraper.py` (herdar de BaseScraper)
- Create: `scraper/ml_scraper.py`
- Create: `tests/test_ml_scraper.py`

**Interfaces:**
- Produces: `scraper.ml_scraper.MercadoLivreScraper`:
  - `async search(query: str) -> list[AdItem]` com `source="Mercado Livre"`

- [ ] **Step 1: Criar fixture e teste do parser de listagens do Mercado Livre**
- [ ] **Step 2: Executar pytest para confirmar falha**
- [ ] **Step 3: Implementar `scraper/ml_scraper.py` com extração de título, preço limpo, link e entrega**
- [ ] **Step 4: Executar pytest e validar com mock e live request**
- [ ] **Step 5: Commit git**

---

### Task 4: Exportadores para Google Sheets e Excel Local (`exporter/`)

**Files:**
- Create: `exporter/__init__.py`
- Create: `exporter/excel_exporter.py`
- Create: `exporter/sheets_exporter.py`
- Create: `tests/test_exporters.py`

**Interfaces:**
- Produces:
  - `exporter.excel_exporter.ExcelExporter`: `export(ads: list[AdItem], query: str) -> str`
  - `exporter.sheets_exporter.GoogleSheetsExporter`: `export(ads: list[AdItem], query: str) -> bool`

- [ ] **Step 1: Escrever testes para formatação de planilhas locais e estrutura de linhas**
- [ ] **Step 2: Implementar `exporter/excel_exporter.py` gerando `.xlsx` com colunas auto-ajustadas e estilos profissionais**
- [ ] **Step 3: Implementar `exporter/sheets_exporter.py` integrando com `gspread` e criando aba por termo**
- [ ] **Step 4: Executar pytest**
- [ ] **Step 5: Commit git**

---

### Task 5: Integração Completa da Esteira e CLI Atualizada

**Files:**
- Modify: `notifier/telegram_notifier.py` (incluir métricas de desconto e média)
- Modify: `pipeline.py` (orquestrar OLX + ML -> Spec Extractor -> Pricing Engine -> Sheets/Excel -> Telegram)
- Modify: `config.py` e `main.py`
- Modify: `README.md`

- [ ] **Step 1: Atualizar testes de pipeline para o fluxo multi-fonte e benchmark**
- [ ] **Step 2: Integrar os módulos no `pipeline.py`**
- [ ] **Step 3: Executar rodada completa com `python main.py --dry-run --once --query "Macbook"`**
- [ ] **Step 4: Verificar a planilha Excel gerada na pasta `data/`**
- [ ] **Step 5: Commit final git**
