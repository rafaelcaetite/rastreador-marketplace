# 🚀 Esteira Automatizada de Monitoramento de Ofertas (OLX -> Telegram)

Esteira de alta performance desenvolvida em Python para monitorar em tempo real ofertas da **OLX Brasil**, aplicando filtros rigorosos de preço, entrega (OLX Pay) e palavras-chave anti-ruído, com alertas instantâneos no **Telegram**.

---

## 🎯 Configuração Padrão
* **Alvo:** MacBook Air M2
* **Faixa de Preço:** R$ 3.000,00 a R$ 5.000,00
* **Entrega:** Apenas anúncios com OLX Pay / Entrega habilitada em todo o Brasil
* **Intervalo:** A cada 10 minutos (configurável)
* **Deduplicação:** SQLite local (`deals.db`) para não reenviar anúncios já alertados

---

## 📋 Pré-requisitos
* Python 3.10 ou superior
* (Opcional) Docker e Docker Compose se for rodar em VPS

---

## ⚡ Instalação Rápida

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Crie o arquivo de configuração `.env`:**
   ```bash
   cp .env.example .env
   ```

---

## 🤖 Como Configurar o Telegram em 2 Minutos

1. Abra o Telegram e procure por **`@BotFather`**.
2. Envie o comando `/newbot` e siga as instruções para escolher nome e username.
3. Copie o **Token do Bot** gerado (ex: `123456789:ABCdefGHIjkl...`).
4. Agora procure pelo bot **`@userinfobot`** no Telegram e envie qualquer mensagem. Ele responderá com o seu **Id numérico** (ex: `987654321`).
5. Abra o seu bot recém-criado e clique em **Começar / Start** (para autorizá-lo a enviar mensagens para você).
6. Abra o arquivo `.env` e preencha:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjkl...
   TELEGRAM_CHAT_ID=987654321
   ```

---

## 🖥️ Como Executar

### 1. Modo Simulação / Teste (Dry-Run)
Para testar a busca e ver os anúncios reais no terminal sem disparar mensagens no Telegram:
```bash
python main.py --dry-run --once
```

### 2. Executar Contínuo (Loop a cada 10 minutos)
```bash
python main.py
```

### 3. Personalizar via Linha de Comando (Opcional)
Você pode testar qualquer outro produto ou faixa de preço sem mexer no `.env`:
```bash
python main.py --query "Playstation 5" --min-price 2500 --max-price 3500 --interval 5
```

---

## ☁️ Como Rodar em uma VPS (24/7)

Se quiser deixar a esteira rodando na nuvem sem precisar do computador ligado:

### Opção A: Com Docker Compose (Recomendado)
```bash
# Na sua VPS:
git clone <seu-repo>
cd black_friday
cp .env.example .env
# Edite com seu nano .env colocando o token do Telegram
docker compose up -d --build
```

Para ver os logs em tempo real:
```bash
docker compose logs -f
```

### Opção B: Em segundo plano via `nohup` (Linux)
```bash
nohup python3 main.py > monitor.log 2>&1 &
```

---

## 🧪 Rodando os Testes Automatizados

A esteira conta com cobertura total de testes unitários e de integração:
```bash
pytest
```
