# Design Spec: Plataforma de Inteligência de Ofertas (OLX + Mercado Livre -> Google Sheets & Telegram)

- **Data:** 2026-11-05
- **Status:** Aprovado
- **Escopo:** Monitoramento multi-fonte (OLX Brasil + Mercado Livre) de qualquer produto (iniciando com "MacBook"), com extração semântica de hardware, benchmark estatístico de preço justo (cálculo de média e % de desconto) e exportação para Google Sheets (com abas dedicadas por termo de busca) e alertas de super ofertas no Telegram.

---

## 1. Arquitetura Modular

```text
black_friday/
├── .env.example
├── .env
├── config.py                 # Configurações dinâmicas (termo de busca, Google Sheets ID, etc.)
├── models.py                 # Modelo AdItem expandido (source, model, processor, ram, ssd, deal_rating)
├── database.py               # SQLite (deduplicação e histórico para benchmark de preços)
├── scraper/
│   ├── __init__.py
│   ├── base_scraper.py       # Interface abstrata BaseScraper
│   ├── olx_scraper.py        # Coletor OLX via curl_cffi
│   └── ml_scraper.py         # Coletor Mercado Livre via httpx / curl_cffi
├── analyzer/
│   ├── __init__.py
│   ├── spec_extractor.py     # Parser regex para Linha, Chip, RAM e SSD
│   └── pricing_engine.py     # Cálculo de média de mercado e classificação de desconto
├── exporter/
│   ├── __init__.py
│   ├── sheets_exporter.py    # Integração Google Sheets via gspread com abas dinâmicas
│   └── excel_exporter.py     # Fallback local em .xlsx com openpyxl
├── notifier/
│   ├── __init__.py
│   └── telegram_notifier.py  # Alertas com cálculo de desconto e comparativo de média
├── pipeline.py               # Orquestrador unificado
├── main.py                   # CLI avançada (--query, --min-price, --max-price, --dry-run)
└── tests/                    # Testes unitários de cada módulo
```

---

## 2. Extração Semântica de Hardware (`spec_extractor.py`)

A partir do título e descrição, identifica:
* `line`: "MacBook Air", "MacBook Pro", "MacBook"
* `chip`: "M1", "M1 Pro", "M1 Max", "M2", "M2 Pro", "M2 Max", "M3", "M3 Pro", "M3 Max", "M4", "Intel Core i5", "Intel Core i7", etc.
* `ram`: "8GB", "16GB", "24GB", "32GB", etc.
* `ssd`: "128GB", "256GB", "512GB", "1TB", "2TB", etc.
* `sku_key`: Chave canônica para agrupamento (ex: `MacBook Air | M2 | 8GB | 256GB`).

---

## 3. Motor Estatístico de Precificação (`pricing_engine.py`)

* Agrupa por `sku_key`.
* Calcula a média de mercado dos itens equivalentes.
* Calcula a métrica:
  $$\text{discount\_pct} = \frac{\text{Preço Médio} - \text{Preço}}{\text{Preço Médio}} \times 100$$
* Classificação:
  * $\ge 20\%$: `🔥 SUPER OPORTUNIDADE`
  * $10\%$ a $19.9\%$: `✅ BOM PREÇO`
  * $-10\%$ a $+9.9\%$: `⚖️ PREÇO NA MÉDIA`
  * $< -10\%$: `⚠️ ACIMA DA MÉDIA`

---

## 4. Integração Google Sheets (`sheets_exporter.py`)

* Utiliza `gspread` e autenticação com `credentials.json` (Google Service Account).
* Acessa a planilha definida em `GOOGLE_SHEET_NAME` ou cria automaticamente.
* Para cada termo de busca (`SEARCH_QUERY`), cria ou atualiza uma aba própria (ex: aba `"MacBook"`).
* Adiciona cabeçalhos estilizados e insere apenas anúncios novos/não duplicados.
* Fallback local: Grava sempre uma cópia em `data/<termo>.xlsx`.
