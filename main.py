import argparse
import asyncio
import logging
import signal
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from config import Config
from database import DatabaseManager
from filters import AdFilter
from notifier.telegram_notifier import TelegramNotifier
from pipeline import DealPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("main")

stop_requested = False

def handle_exit_signal(sig, frame):
    global stop_requested
    logger.info("Sinal de parada recebido. Encerrando esteira suavemente...")
    stop_requested = True

def parse_args():
    parser = argparse.ArgumentParser(description="Esteira Automatizada de Ofertas na OLX")
    parser.add_argument("--once", action="store_true", help="Executa apenas uma rodada de busca e finaliza")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulação: não envia alertas ao Telegram")
    parser.add_argument("--query", type=str, default=None, help="Termo de busca (ex: 'Macbook Air M2')")
    parser.add_argument("--min-price", type=float, default=None, help="Preço mínimo (ex: 3000)")
    parser.add_argument("--max-price", type=float, default=None, help="Preço máximo (ex: 5000)")
    parser.add_argument("--interval", type=int, default=None, help="Intervalo em minutos entre checagens")
    return parser.parse_args()

async def main():
    args = parse_args()
    config = Config.load_from_env()

    # Sobrescreve com parâmetros da CLI se informados
    if args.dry_run:
        config.dry_run = True
    if args.query:
        config.query = args.query
    if args.min_price is not None:
        config.min_price = args.min_price
    if args.max_price is not None:
        config.max_price = args.max_price
    if args.interval is not None:
        config.interval_minutes = args.interval

    logger.info("==================================================")
    logger.info("🚀 ESTEIRA DE OFERTAS OLX INICIADA")
    logger.info(f"🔍 Alvo: {config.query}")
    logger.info(f"💰 Faixa de Preço: R$ {config.min_price:,.2f} a R$ {config.max_price:,.2f}")
    logger.info(f"📦 Exigir OLX Pay/Entrega: {'Sim' if config.require_delivery else 'Não'}")
    logger.info(f"⏱️ Intervalo: {config.interval_minutes} minuto(s)")
    logger.info(f"📡 Modo Dry-Run: {'Ativo (Simulação)' if config.dry_run else 'Desativado (Envio real ao Telegram)'}")
    logger.info("==================================================")

    db = DatabaseManager(config.db_path)
    ad_filter = AdFilter(config)
    notifier = TelegramNotifier(config)
    pipeline = DealPipeline(config=config, db=db, ad_filter=ad_filter, notifier=notifier)

    if args.once:
        await pipeline.run_cycle()
        return

    # Loop contínuo a cada X minutos
    while not stop_requested:
        try:
            await pipeline.run_cycle()
        except Exception as e:
            logger.error(f"Erro inesperado no ciclo: {e}", exc_info=True)

        if stop_requested:
            break

        logger.info(f"Aguardando {config.interval_minutes} minutos até a próxima checagem...")
        sleep_seconds = config.interval_minutes * 60
        for _ in range(sleep_seconds):
            if stop_requested:
                break
            await asyncio.sleep(1)

    logger.info("Esteira finalizada com sucesso.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)
    asyncio.run(main())
