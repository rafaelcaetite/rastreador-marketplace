# Design Spec: Esteira Automatizada de Monitoramento de Ofertas (OLX -> Telegram)

- **Data:** 2026-11-05
- **Status:** Aprovado
- **Alvo Inicial:** MacBook Air M2 (Preço: R$ 3.000,00 a R$ 5.000,00 com Entrega/OLX Pay em todo o Brasil)
- **Canal de Notificação:** Bot do Telegram
- **Frequência de Checagem:** 10 minutos

---

## 1. Visão Geral e Objetivos

O projeto consiste em uma esteira contínua e autônoma desenvolvida em Python para monitorar novas ofertas na OLX Brasil de itens específicos de alto interesse (iniciando com o MacBook Air M2).

### Objetivos Principais:
1. Extrair os anúncios mais recentes da OLX via extração leve de dados (SSR Next.js `__NEXT_DATA__` e requisições HTTP otimizadas).
2. Aplicar regras de filtragem rigorosas para evitar falsos positivos (acessórios, peças, carcaças quebradas ou modelos anteriores).
3. Deduplicar anúncios utilizando banco de dados SQLite local, garantindo que nenhum anúncio seja notificado mais de uma vez.
4. Enviar alertas em tempo real via Telegram Bot API com foto, detalhes e link direto.
5. Permitir execução contínua (daemon) a cada 10 minutos, com modo de diagnóstico rápido (`--dry-run`).

---

## 2. Arquitetura do Sistema

A solução segue arquitetura modular desacoplada:

```text
black_friday/
├── .env.example              # Template das variáveis de ambiente
├── .env                      # Credenciais reais locais (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
├── config.py                 # Dataclasses de configuração (parâmetros de busca, filtros, timming)
├── database.py               # Gerenciador de persistência e deduplicação (SQLite)
├── models.py                 # Modelos de dados (ex: AdItem)
├── scraper/
│   ├── __init__.py
│   └── olx_scraper.py        # Coletor HTTP assíncrono para busca na OLX
├── notifier/
│   ├── __init__.py
│   └── telegram_notifier.py  # Módulo de envio de mensagens e mídia para Telegram
├── pipeline.py               # Orquestrador do fluxo (Scrape -> Filter -> Store -> Notify)
├── main.py                   # Ponto de entrada (CLI para --dry-run ou agendamento a cada 10 min)
├── requirements.txt          # Dependências do projeto
└── tests/
    └── test_pipeline.py      # Testes unitários de filtros, deduplicação e parsing
```

---

## 3. Modelo de Dados (`models.py`)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class AdItem:
    id: str
    title: str
    price: float
    url: str
    location: str
    has_delivery: bool
    image_url: Optional[str] = None
    created_at: Optional[str] = None
```

---

## 4. Pipeline de Filtragem

Cada anúncio coletado passa pelo pipeline de validação:

1. **Filtro de Preço:**
   * Mínimo: `R$ 3.000,00` (elimina anúncios de capinhas, cabos, caixas vazias ou anúncios falsos de R$ 50).
   * Máximo: `R$ 5.000,00` (foco em ofertas e oportunidades reais).
2. **Filtro de Entrega (Brasil):**
   * Deve possuir `has_delivery = True` (anúncios que aceitam OLX Pay / Entrega Fácil em território nacional).
3. **Filtro Positivo de Título/Texto:**
   * Título deve conter `"macbook"` e `"m2"`.
4. **Filtro Negativo (Anti-Ruído / Peças / Defeitos):**
   * Descarte se contiver: `["peça", "peças", "defeito", "quebrado", "sucata", "bloqueado", "icloud", "compro", "apenas caixa", "capinha", "carregador", "tela trincada"]`.

---

## 5. Persistência e Deduplicação (`database.py`)

* **Banco:** SQLite local (`deals.db`).
* **Tabela:** `seen_ads`
  ```sql
  CREATE TABLE IF NOT EXISTS seen_ads (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      price REAL NOT NULL,
      url TEXT NOT NULL,
      first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
* **Lógica:**
  * `is_ad_seen(ad_id: str) -> bool`
  * `mark_ad_seen(ad: AdItem) -> None`

---

## 6. Coletor OLX (`scraper/olx_scraper.py`)

* Utiliza `httpx.AsyncClient` com headers de navegador real (Chrome / Edge atualizados, `sec-ch-ua`, `Accept-Language: pt-BR`).
* URL alvo formatada: `https://www.olx.com.br/brasil?q=Macbook+Air+M2&sf=1`
* Parser extrai o JSON embutido na tag `<script id="__NEXT_DATA__" type="application/json">` ou, como fallback, estrutura os cards de anúncios da página.
* Converte cada resultado para uma lista de objetos `AdItem`.

---

## 7. Notificador Telegram (`notifier/telegram_notifier.py`)

* Utiliza a API HTTP oficial do Telegram (`https://api.telegram.org/bot<TOKEN>/...`).
* Envia com foto (`sendPhoto`) ou mensagem de texto enriquecida com HTML/Markdown e inline keyboard com link direto para o anúncio.
* Suporta modo silencioso ou `--dry-run` para testes locais sem credenciais.

---

## 8. Agendador e CLI (`main.py`)

* Argumentos via CLI:
  * `--once`: Executa apenas um ciclo de busca e encerra.
  * `--dry-run`: Executa a busca, aplica os filtros, exibe os anúncios no terminal e não envia para o Telegram nem marca como visto.
  * Padrão (sem argumentos): Executa em loop a cada 10 minutos com logs informativos.

---

## 9. Plano de Testes

1. `test_filter_price`: Garante que anúncios abaixo de 3000 ou acima de 5000 são rejeitados.
2. `test_filter_negative_keywords`: Garante que termos como "bloqueado icloud" ou "com defeito" são rejeitados mesmo na faixa de preço.
3. `test_filter_delivery`: Garante que itens sem OLX Pay/entrega são descartados quando a regra estiver ativa.
4. `test_sqlite_deduplication`: Garante que o mesmo `ad_id` só é processado uma única vez.
