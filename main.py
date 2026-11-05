import argparse
import asyncio
import logging
import signal
import sys
from config import Config
from database import DatabaseManager
from filters import AdFilter
from notifier.telegram_notifier import TelegramNotifier
from pipeline import DealPipeline

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("main")

stop_requested = False

def handle_exit_signal(sig, frame):
    global stop_requested
    logger.info("Encerrando execução...")
    stop_requested = True

def parse_args():
    parser = argparse.ArgumentParser(description="Rastreador de Marketplace — OLX, Mercado Livre e Shopee")
    parser.add_argument("--once", action="store_true", help="Executa uma única busca e encerra")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulação: exibe alertas no terminal sem enviar ao Telegram")
    parser.add_argument("--query", type=str, default=None, help="Termo de pesquisa (ex: 'Macbook', 'Playstation 5')")
    parser.add_argument("--min-price", type=float, default=None, help="Preço mínimo em R$")
    parser.add_argument("--max-price", type=float, default=None, help="Preço máximo em R$")
    parser.add_argument("--interval", type=int, default=None, help="Intervalo em minutos entre varreduras")
    parser.add_argument("--sources", type=str, default=None, help="Marketplaces ativos separados por vírgula (ex: 'olx,ml,shopee')")
    parser.add_argument("--allow-pickup", action="store_true", help="Permite anúncios sem entrega (apenas retirada local)")
    return parser.parse_args()

async def main():
    args = parse_args()
    config = Config.load_from_env()

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
    if args.sources:
        if args.sources.lower() == "all":
            config.active_sources = ["olx", "ml", "shopee"]
        else:
            config.active_sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    if args.allow_pickup:
        config.require_delivery = False

    logger.info("==================================================")
    logger.info("🚀 RASTREADOR DE MARKETPLACE INICIADO")
    logger.info(f"🔍 Termo de busca: {config.query}")
    logger.info(f"🛒 Marketplaces ativos: {', '.join(config.active_sources).upper()}")
    logger.info(f"💰 Faixa de Preço: R$ {config.min_price:,.2f} a R$ {config.max_price:,.2f}")
    logger.info(f"📊 Planilha Google Sheets: '{config.google_sheet_name}'")
    logger.info(f"⏱️ Intervalo: {config.interval_minutes} minuto(s)")
    logger.info(f"📡 Modo Dry-Run: {'Ativo (Simulação)' if config.dry_run else 'Desativado'}")
    logger.info("==================================================")

    db = DatabaseManager(config.db_path)
    ad_filter = AdFilter(config)
    notifier = TelegramNotifier(config)
    pipeline = DealPipeline(config=config, db=db, ad_filter=ad_filter, notifier=notifier)

    if args.once:
        await pipeline.run_cycle()
        return

    while not stop_requested:
        try:
            await pipeline.run_cycle()
        except Exception as e:
            logger.error(f"Erro no ciclo de monitoramento: {e}", exc_info=True)

        if stop_requested:
            break

        logger.info(f"Aguardando {config.interval_minutes} minutos até a próxima varredura...")
        sleep_seconds = config.interval_minutes * 60
        for _ in range(sleep_seconds):
            if stop_requested:
                break
            await asyncio.sleep(1)

    logger.info("Execução finalizada com sucesso.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)
    asyncio.run(main())
